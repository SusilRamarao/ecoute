from flask import Flask, render_template, request, session, send_file, jsonify
from flask_socketio import SocketIO, emit
import os
import tempfile
import time
import TranscriberModels
import base64
import zipfile
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables for transcription
active_transcribers = {}
audio_queues = {}

class WebAudioTranscriber:
    def __init__(self, session_id):
        self.session_id = session_id
        self.transcript_data = []
        self.model = TranscriberModels.get_model(False)  # Use local model
        
    def add_audio_data(self, audio_data):
        """Add audio data to be transcribed"""
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Transcribe audio
            transcript_text = self.model.get_transcription(temp_path)
            if transcript_text and transcript_text.strip():
                timestamp = time.strftime('%H:%M:%S')
                
                self.transcript_data.append({
                    'timestamp': timestamp,
                    'text': transcript_text.strip(),
                    'source': 'microphone'
                })
                
                # Clean up temp file
                os.unlink(temp_path)
                
                return transcript_text.strip()
                
        except Exception as e:
            print(f"Transcription error: {e}")
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        
        return None
    
    def get_transcript(self):
        """Get formatted transcript"""
        if not self.transcript_data:
            return "Listening for audio..."
        
        transcript_lines = []
        for entry in self.transcript_data[-10:]:  # Show last 10 entries
            transcript_lines.append(f"[{entry['timestamp']}] {entry['text']}")
        
        return '\n'.join(transcript_lines)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download')
def download_client():
    """Provide download page for the client application"""
    return render_template('download.html')

@app.route('/api/client-files')
def get_client_files():
    """Get information about client files available for download"""
    try:
        client_files = []
        
        # Check if client_app.py exists
        if os.path.exists('client_app.py'):
            stat_result = os.stat('client_app.py')
            client_files.append({
                'name': 'client_app.py',
                'size': stat_result.st_size,
                'description': 'Main client application (Python script)'
            })
        
        # Check if client_requirements.txt exists
        if os.path.exists('client_requirements.txt'):
            stat_result = os.stat('client_requirements.txt')
            client_files.append({
                'name': 'client_requirements.txt',
                'size': stat_result.st_size,
                'description': 'Python package requirements'
            })
        
        return jsonify({
            'files': client_files,
            'instructions': {
                'install': 'pip install -r client_requirements.txt',
                'run': 'python client_app.py'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download individual client files"""
    try:
        # Security: only allow downloading specific files
        allowed_files = ['client_app.py', 'client_requirements.txt']
        if filename not in allowed_files:
            return "File not found", 404
        
        if not os.path.exists(filename):
            return "File not found", 404
        
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Error downloading file: {e}", 500

@app.route('/download/client-package')
def download_client_package():
    """Download complete client package as ZIP"""
    try:
        # Create temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add client files
            if os.path.exists('client_app.py'):
                zipf.write('client_app.py')
            if os.path.exists('client_requirements.txt'):
                zipf.write('client_requirements.txt')
            
            # Add README for client
            readme_content = """# Ecoute Desktop Client
            
## Installation
1. Install Python 3.7 or later
2. Install requirements: `pip install -r client_requirements.txt`
3. Run the client: `python client_app.py`

## Usage
1. Start the web app server
2. Run the desktop client
3. Connect to the server (default: http://localhost:5000)
4. Select your audio device
5. Click "Start Recording" to begin system audio transcription

## Notes
- On Windows: Use PyAudioWPatch for system audio capture
- On macOS/Linux: You may need to configure audio routing (e.g., using Loopback or similar tools)
- Make sure the web app server is running before connecting the client
"""
            zipf.writestr('README.md', readme_content)
        
        return send_file(temp_zip.name, as_attachment=True, download_name='ecoute-client.zip')
        
    except Exception as e:
        return f"Error creating client package: {e}", 500

@socketio.on('connect')
def handle_connect():
    session_id = session.get('session_id', request.sid)
    session['session_id'] = session_id
    active_transcribers[session_id] = WebAudioTranscriber(session_id)
    emit('connected', {'status': 'Connected to transcription service'})

@socketio.on('disconnect')
def handle_disconnect():
    session_id = session.get('session_id')
    if session_id in active_transcribers:
        del active_transcribers[session_id]

@socketio.on('audio_data')
def handle_audio_data(data):
    session_id = session.get('session_id')
    if session_id not in active_transcribers:
        return
    
    try:
        # Decode base64 audio data
        audio_data = base64.b64decode(data['audio'])
        
        transcriber = active_transcribers[session_id]
        transcript_text = transcriber.add_audio_data(audio_data)
        
        if transcript_text:
            full_transcript = transcriber.get_transcript()
            emit('transcript_update', {
                'transcript': full_transcript,
                'new_text': transcript_text
            })
            
    except Exception as e:
        print(f"Error processing audio: {e}")
        emit('error', {'message': 'Error processing audio'})

@socketio.on('clear_transcript')
def handle_clear_transcript():
    session_id = session.get('session_id')
    if session_id in active_transcribers:
        active_transcribers[session_id].transcript_data.clear()
        emit('transcript_update', {'transcript': 'Transcript cleared. Listening for audio...'})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)