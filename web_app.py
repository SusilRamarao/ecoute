from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import os
import tempfile
import time
import TranscriberModels
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)