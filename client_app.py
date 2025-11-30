#!/usr/bin/env python3
"""
Ecoute Desktop Client
A desktop application that captures system audio and sends it to the web app for transcription.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import base64
import io
import wave
import socketio
import pyaudio
import platform
import queue

# Platform-specific imports
if platform.system() == "Windows":
    import PyAudioWPatch as pyaudio
else:
    import pyaudio

class AudioCapture:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.stream = None
        self.audio_queue = queue.Queue()
        
        # Audio settings
        self.chunk_size = 1024
        self.sample_rate = 16000
        self.channels = 1
        self.format = pyaudio.paInt16
        
    def get_audio_devices(self):
        """Get list of available audio devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': info['name'],
                'max_input_channels': info['maxInputChannels'],
                'max_output_channels': info['maxOutputChannels']
            })
        return devices
    
    def get_default_speakers(self):
        """Get default speakers/output device for system audio capture"""
        try:
            if platform.system() == "Windows":
                # On Windows, look for WASAPI loopback devices
                devices = self.get_audio_devices()
                for device in devices:
                    if "WASAPI" in device['name'] and "loopback" in device['name'].lower():
                        return device['index']
                
                # Fallback to default output device
                default_output = self.audio.get_default_output_device_info()
                return default_output['index']
            else:
                # On macOS/Linux, use default input device (user needs to set up audio routing)
                default_input = self.audio.get_default_input_device_info()
                return default_input['index']
        except Exception:
            return 0
    
    def start_recording(self, device_index=None):
        """Start recording audio"""
        if self.is_recording:
            return False
            
        try:
            if device_index is None:
                device_index = self.get_default_speakers()
            
            device_info = self.audio.get_device_info_by_index(device_index)
            
            # Adjust settings based on device capabilities
            max_channels = device_info.get('maxInputChannels', 1)
            if max_channels == 0 and platform.system() == "Windows":
                # For Windows WASAPI loopback, use output channels
                max_channels = device_info.get('maxOutputChannels', 1)
            
            channels = min(self.channels, max_channels) if max_channels > 0 else 1
            
            self.stream = self.audio.open(
                format=self.format,
                channels=channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.stream.start_stream()
            return True
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def get_audio_data(self):
        """Get audio data from queue"""
        audio_chunks = []
        while not self.audio_queue.empty():
            try:
                chunk = self.audio_queue.get_nowait()
                audio_chunks.append(chunk)
            except queue.Empty:
                break
        
        if audio_chunks:
            return b''.join(audio_chunks)
        return None
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_recording()
        self.audio.terminate()

class EcouteClient:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Ecoute Desktop Client")
        self.window.geometry("800x600")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Client state
        self.server_url = "http://localhost:5001"
        self.sio = socketio.Client()
        self.audio_capture = AudioCapture()
        self.is_connected = False
        self.is_streaming = False
        
        # Setup UI
        self.setup_ui()
        self.setup_socketio()
        
        # Start audio processing thread
        self.audio_thread = threading.Thread(target=self.audio_processing_loop, daemon=True)
        self.audio_thread.start()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Connection section
        conn_frame = ttk.LabelFrame(main_frame, text="Server Connection", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(conn_frame, text="Server URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_var = tk.StringVar(value=self.server_url)
        self.url_entry = ttk.Entry(conn_frame, textvariable=self.url_var, width=40)
        self.url_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=2, padx=(10, 0))
        
        # Status
        self.status_var = tk.StringVar(value="Disconnected")
        self.status_label = ttk.Label(conn_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Audio section
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Capture", padding="10")
        audio_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Device selection
        ttk.Label(audio_frame, text="Audio Device:").grid(row=0, column=0, sticky=tk.W)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(audio_frame, textvariable=self.device_var, width=50)
        self.device_combo.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        self.refresh_btn = ttk.Button(audio_frame, text="Refresh", command=self.refresh_devices)
        self.refresh_btn.grid(row=0, column=2, padx=(10, 0))
        
        # Recording controls
        control_frame = ttk.Frame(audio_frame)
        control_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        self.record_btn = ttk.Button(control_frame, text="Start Recording", command=self.toggle_recording)
        self.record_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.clear_btn = ttk.Button(control_frame, text="Clear Transcript", command=self.clear_transcript)
        self.clear_btn.grid(row=0, column=1)
        
        # Transcript section
        transcript_frame = ttk.LabelFrame(main_frame, text="Live Transcript", padding="10")
        transcript_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.transcript_text = scrolledtext.ScrolledText(transcript_frame, height=15, state=tk.DISABLED)
        self.transcript_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Download section
        download_frame = ttk.Frame(main_frame)
        download_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.download_btn = ttk.Button(download_frame, text="Download Client", command=self.download_client)
        self.download_btn.grid(row=0, column=0)
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        conn_frame.columnconfigure(1, weight=1)
        audio_frame.columnconfigure(1, weight=1)
        transcript_frame.columnconfigure(0, weight=1)
        transcript_frame.rowconfigure(0, weight=1)
        
        # Initial device refresh
        self.refresh_devices()
    
    def setup_socketio(self):
        """Setup SocketIO event handlers"""
        @self.sio.event
        def connect():
            self.window.after(0, self._on_connected)
        
        @self.sio.event
        def disconnect():
            self.window.after(0, self._on_disconnected)
        
        @self.sio.event
        def transcript_update(data):
            self.window.after(0, self._on_transcript_update, data)
        
        @self.sio.event
        def error(data):
            self.window.after(0, self._on_error, data)
    
    def refresh_devices(self):
        """Refresh audio device list"""
        try:
            devices = self.audio_capture.get_audio_devices()
            device_names = []
            
            for device in devices:
                name = f"{device['name']} (Index: {device['index']})"
                if device['max_input_channels'] > 0:
                    name += " [Input]"
                if device['max_output_channels'] > 0:
                    name += " [Output]"
                device_names.append(name)
            
            self.device_combo['values'] = device_names
            
            # Try to select default device
            default_index = self.audio_capture.get_default_speakers()
            for i, name in enumerate(device_names):
                if f"Index: {default_index}" in name:
                    self.device_combo.current(i)
                    break
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh devices: {e}")
    
    def toggle_connection(self):
        """Toggle connection to server"""
        if not self.is_connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()
    
    def connect_to_server(self):
        """Connect to the transcription server"""
        try:
            self.server_url = self.url_var.get()
            self.sio.connect(self.server_url)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
    
    def disconnect_from_server(self):
        """Disconnect from the transcription server"""
        try:
            if self.is_streaming:
                self.toggle_recording()
            self.sio.disconnect()
        except Exception as e:
            messagebox.showerror("Disconnect Error", f"Failed to disconnect: {e}")
    
    def toggle_recording(self):
        """Toggle audio recording"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to the server first.")
            return
        
        if not self.is_streaming:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio"""
        try:
            device_text = self.device_var.get()
            if not device_text:
                messagebox.showwarning("No Device", "Please select an audio device.")
                return
            
            # Extract device index from the combo box text
            import re
            match = re.search(r'Index: (\d+)', device_text)
            if match:
                device_index = int(match.group(1))
            else:
                device_index = None
            
            if self.audio_capture.start_recording(device_index):
                self.is_streaming = True
                self.record_btn.config(text="Stop Recording")
                self.status_var.set("Connected - Recording")
            else:
                messagebox.showerror("Recording Error", "Failed to start recording.")
                
        except Exception as e:
            messagebox.showerror("Recording Error", f"Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop recording audio"""
        self.audio_capture.stop_recording()
        self.is_streaming = False
        self.record_btn.config(text="Start Recording")
        self.status_var.set("Connected - Not Recording")
    
    def clear_transcript(self):
        """Clear the transcript"""
        if self.is_connected:
            self.sio.emit('clear_transcript')
    
    def download_client(self):
        """Open browser to download client"""
        try:
            import webbrowser
            webbrowser.open(f"{self.server_url}/download")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open download page: {e}")
    
    def audio_processing_loop(self):
        """Process audio data in a separate thread"""
        while True:
            try:
                if self.is_streaming and self.is_connected:
                    audio_data = self.audio_capture.get_audio_data()
                    if audio_data:
                        # Convert to WAV format
                        wav_buffer = io.BytesIO()
                        with wave.open(wav_buffer, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)  # 16-bit
                            wav_file.setframerate(16000)
                            wav_file.writeframes(audio_data)
                        
                        wav_data = wav_buffer.getvalue()
                        encoded_audio = base64.b64encode(wav_data).decode('utf-8')
                        
                        # Send to server
                        self.sio.emit('audio_data', {'audio': encoded_audio})
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"Audio processing error: {e}")
                time.sleep(1)
    
    def _on_connected(self):
        """Handle connection event"""
        self.is_connected = True
        self.connect_btn.config(text="Disconnect")
        self.status_var.set("Connected")
        self.record_btn.config(state=tk.NORMAL)
    
    def _on_disconnected(self):
        """Handle disconnection event"""
        self.is_connected = False
        self.is_streaming = False
        self.connect_btn.config(text="Connect")
        self.record_btn.config(text="Start Recording", state=tk.DISABLED)
        self.status_var.set("Disconnected")
        self.audio_capture.stop_recording()
    
    def _on_transcript_update(self, data):
        """Handle transcript update"""
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete(1.0, tk.END)
        self.transcript_text.insert(1.0, data['transcript'])
        self.transcript_text.config(state=tk.DISABLED)
        self.transcript_text.see(tk.END)
    
    def _on_error(self, data):
        """Handle error event"""
        messagebox.showerror("Server Error", data.get('message', 'Unknown error'))
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_connected:
            self.disconnect_from_server()
        self.audio_capture.cleanup()
        self.window.destroy()
    
    def run(self):
        """Run the application"""
        self.window.mainloop()

if __name__ == "__main__":
    # Check if required packages are installed
    try:
        import pyaudio
        import socketio
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install pyaudio python-socketio")
        if platform.system() == "Windows":
            print("For Windows system audio: pip install PyAudioWPatch")
        exit(1)
    
    app = EcouteClient()
    app.run()