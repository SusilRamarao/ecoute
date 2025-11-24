# Ecoute Web Version

A web-based audio transcription application that works in browsers.

## Features

- 🎤 **Microphone Recording**: Real-time audio capture from microphone
- 🔄 **Live Transcription**: Real-time speech-to-text using Whisper
- 🌐 **Web Interface**: Modern, responsive web UI
- ☁️ **Cloud Ready**: Deployable to web hosting services like Hostinger

## Important Notes

⚠️ **Browser Limitations**: 
- ✅ **Microphone audio**: Supported
- ❌ **System/Speaker audio**: Not supported (browser security restriction)

## Local Development

### Prerequisites

1. Python 3.9+
2. FFmpeg installed on your system

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r web_requirements.txt
```

2. Run the web application:
```bash
python web_app.py
```

3. Open your browser and go to: `http://localhost:5000`

## Deployment to Hostinger (Docker)

### Method 1: Using Dockerfile.web

1. Build the Docker image:
```bash
docker build -f Dockerfile.web -t ecoute-web .
```

2. Run the container:
```bash
docker run -p 5000:5000 ecoute-web
```

### Method 2: Deploy to Hostinger

1. Upload your project files to Hostinger
2. Use the Dockerfile.web for containerization
3. Make sure the container exposes port 5000
4. Set environment variables if needed

## Usage Instructions

1. **Start Recording**: Click the "Start Recording" button
2. **Allow Microphone Access**: Grant permission when browser prompts
3. **Speak Clearly**: Talk into your microphone
4. **View Transcript**: See real-time transcription in the text area
5. **Clear Transcript**: Use "Clear Transcript" to start fresh

## File Structure for Web Version

```
ecoute/
├── web_app.py              # Flask web application
├── templates/
│   └── index.html          # Web interface
├── web_requirements.txt    # Web-specific dependencies
├── Dockerfile.web          # Docker configuration for web
├── AudioTranscriber.py     # Original transcriber (adapted)
├── TranscriberModels.py    # Model management
└── requirements.txt        # Core dependencies
```

## Technical Details

- **Frontend**: HTML5, CSS3, JavaScript with WebRTC
- **Backend**: Flask + SocketIO for real-time communication
- **Audio Processing**: Whisper for speech recognition
- **Containerization**: Docker for easy deployment

## Limitations

1. **No System Audio**: Web browsers cannot capture system/speaker audio for security reasons
2. **Internet Required**: Initial model download may require internet connection
3. **Browser Compatibility**: Requires modern browsers with WebRTC support

## Troubleshooting

### Microphone Access Issues
- Ensure HTTPS is used in production (required for microphone access)
- Check browser permissions for microphone access
- Try different browsers if issues persist

### Docker Deployment Issues
- Ensure port 5000 is properly exposed
- Check that FFmpeg is installed in container
- Verify all dependencies are in requirements files