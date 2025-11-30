# Ecoute System Audio Transcription

This enhanced version of Ecoute includes a **Desktop Client** that solves the web browser limitation of not being able to capture system audio (speaker output). Now you can transcribe any audio playing on your computer!

## 🎯 What's New?

### Desktop Client Features
- **System Audio Capture**: Record what your computer is playing (music, videos, calls, etc.)
- **Real-time Transcription**: Instant transcription sent to the web app server
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Easy Setup**: Simple GUI with device selection
- **Seamless Integration**: Connects directly to your existing web app server

### Web App Enhancements
- **Client Download**: Download the desktop client directly from the web interface
- **Improved UI**: Added prominent download buttons and instructions
- **File Management**: API endpoints for client file downloads and package creation

## 🚀 Quick Start

### Option 1: Web App (Microphone Only)
1. Install web app dependencies:
   ```bash
   pip install -r web_requirements.txt
   ```

2. Run the web app:
   ```bash
   python web_app.py
   ```

3. Open your browser to `http://localhost:5000`

### Option 2: Desktop Client (System Audio)
1. Download the client from the web app (`http://localhost:5000/download`)
2. Extract the package
3. Install client dependencies:
   ```bash
   pip install -r client_requirements.txt
   ```

4. Run the client:
   ```bash
   python client_app.py
   # OR use the launcher
   python launch_client.py
   ```

## 📋 Detailed Setup

### Prerequisites
- Python 3.7 or higher
- Audio drivers and devices properly configured

### Web App Setup
```bash
# Clone/download the repository
cd ecoute

# Install web app dependencies
pip install -r web_requirements.txt

# Start the web server
python web_app.py
```

The web app will be available at `http://localhost:5000`

### Desktop Client Setup

#### Automatic Setup (Recommended)
1. Visit `http://localhost:5000/download` in your browser
2. Click "Download Complete Package (ZIP)"
3. Extract the ZIP file
4. Run the launcher: `python launch_client.py`
5. The launcher will check and install dependencies automatically

#### Manual Setup
```bash
# Install client dependencies
pip install -r client_requirements.txt

# For Windows users (recommended for system audio):
pip install PyAudioWPatch

# Run the client
python client_app.py
```

## 🖥️ Platform-Specific Notes

### Windows
- **System Audio**: Supports direct system audio capture via WASAPI loopback
- **Recommended**: Install `PyAudioWPatch` for better system audio support
- **Admin Rights**: May be required for some audio device access

### macOS
- **System Audio**: Requires additional audio routing software
- **Recommended Tools**: 
  - [Loopback](https://rogueamoeba.com/loopback/) (paid)
  - [BlackHole](https://github.com/ExistentialAudio/BlackHole) (free)
- **Setup**: Configure audio routing to create a virtual input device

### Linux
- **System Audio**: Requires ALSA loopback or PulseAudio configuration
- **Setup**: Configure audio routing using `pactl` or similar tools

## 🎛️ Using the Desktop Client

1. **Start the Web App**: Ensure the web app server is running
2. **Launch Client**: Run `python client_app.py` or `python launch_client.py`
3. **Connect**: Enter server URL (default: `http://localhost:5000`) and click Connect
4. **Select Device**: Choose your audio input device from the dropdown
   - Windows: Look for WASAPI loopback devices for system audio
   - macOS/Linux: Select configured virtual input device
5. **Start Recording**: Click "Start Recording" to begin transcription
6. **View Transcript**: Real-time transcription appears in both client and web app

## 🔧 Troubleshooting

### Common Issues

**No Audio Devices Listed**
- Run as administrator (Windows)
- Check audio drivers are properly installed
- Verify audio devices are not in use by other applications

**Can't Capture System Audio**
- **Windows**: Install PyAudioWPatch, look for WASAPI loopback devices
- **macOS**: Install and configure Loopback or BlackHole
- **Linux**: Configure ALSA loopback or PulseAudio virtual devices

**Connection Failed**
- Ensure web app server is running and accessible
- Check firewall settings
- Verify the server URL is correct

**Poor Audio Quality**
- Adjust audio device sample rate settings
- Check for audio driver updates
- Ensure sufficient system resources

**Import Errors**
- Install missing dependencies: `pip install -r client_requirements.txt`
- Check Python version (3.7+ required)
- On Windows, install Visual C++ build tools if pyaudio fails

### Audio Device Setup

#### Windows WASAPI Loopback
1. Look for devices with "WASAPI" and "loopback" in the name
2. These capture system audio directly
3. May require running as administrator

#### macOS with Loopback
1. Install Loopback application
2. Create a new virtual device
3. Set system audio as input source
4. Select the virtual device in the client

#### Linux with PulseAudio
```bash
# Create loopback module
pactl load-module module-loopback latency_msec=1

# List audio devices
pactl list short sources
```

## 📝 API Endpoints

The web app includes several new API endpoints for client management:

- `GET /download` - Client download page
- `GET /api/client-files` - List available client files
- `GET /download/<filename>` - Download individual files
- `GET /download/client-package` - Download complete ZIP package

## 🔄 How It Works

1. **Web App**: Runs Flask server with SocketIO for real-time communication
2. **Desktop Client**: 
   - Captures audio using PyAudio/PyAudioWPatch
   - Converts audio to WAV format
   - Encodes and sends to web app via SocketIO
3. **Transcription**: Web app processes audio using the same Whisper model
4. **Real-time Updates**: Transcription results sent back to both web and desktop clients

## 🎵 Audio Formats Supported

- **Input**: Any system audio (16-bit, 16kHz, mono)
- **Processing**: WAV format for transcription
- **Output**: Real-time text transcription

## 🔐 Security Notes

- Desktop client connects only to specified server
- No audio data is stored permanently
- All communication uses SocketIO with standard security
- Client files served only from web app directory

## 🤝 Contributing

Feel free to contribute improvements:
- Enhanced audio device detection
- Better platform-specific audio routing
- UI/UX improvements
- Additional audio format support

## 📄 License

Same as original Ecoute project license.

---

**Enjoy transcribing your system audio in real-time! 🎧✨**