# Doctor Patient Summarizer - Transcription API

A Python Flask backend API that transcribes audio files using the open-source faster-whisper model. This API is designed to be deployed on AWS EC2 and provides a simple REST endpoint for audio transcription.

## 🎯 Features

- **Audio Transcription**: Convert audio files to text using OpenAI's Whisper model
- **LLM Summarization**: Medical summarization and Q&A extraction using Groq's llama3-70b-8192 model
- **Multiple Format Support**: WAV, MP3, FLAC, M4A, OGG, WebM, MP4
- **REST API**: Simple JSON-based REST API
- **Error Handling**: Comprehensive error handling and validation
- **Health Check**: Built-in health check endpoint
- **Lightweight**: Uses faster-whisper for CPU-optimized inference

## 📋 Requirements

- Python 3.8+
- pip (Python package manager)
- ~500MB disk space for the Whisper Model
- Groq API key (get free tier from https://console.groq.com)

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/underlineit-dev-13/docconvo-backend.git
cd docconvo-backend
```

### 2. Create Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **flask**: Web framework for the API
- **faster-whisper**: Fast CPU-optimized Whisper implementation
- **groq**: Groq API client for LLM summarization
- **python-dotenv**: Environment variable management

## 🏃 Running Locally

### Start the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000`

You should see output like:
```
 * Running on http://0.0.0.0:5000
 * WARNING in app.run(): This is a development server. Do not use it in production.
```

### Test the API

```bash
# Health check
curl http://localhost:5000/health

# Get API info
curl http://localhost:5000/

# Transcribe an audio file
curl -X POST -F "audio=@path/to/audio.wav" http://localhost:5000/transcribe
```

## 📡 API Endpoints

### 1. POST `/transcribe`

Transcribe an audio file to text.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with `audio` file field

**Example with curl:**
```bash
curl -X POST -F "audio=@sample.wav" http://localhost:5000/transcribe
```

**Example with Python requests:**
```python
import requests

with open('sample.wav', 'rb') as f:
    files = {'audio': f}
    response = requests.post('http://localhost:5000/transcribe', files=files)
    print(response.json())
```

**Success Response (200 OK):**
```json
{
  "transcript": "Your transcribed text here",
  "success": true,
  "language": "en",
  "duration": 5.32
}
```

**Error Response (400/500):**
```json
{
  "error": "Error description",
  "success": false
}
```

### 2. GET `/health`

Check if the API is running and the model is initialized.

**Request:**
- Method: `GET`

**Response:**
```json
{
  "status": "healthy",
  "model_initialized": true,
  "model": "base"
}
```

### 3. POST `/summarize`

Summarize transcripts and extract structured Q&A using LLM.

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body: JSON with `transcript` and `questions` array

**Example with curl:**
```bash
curl -X POST http://localhost:5000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Doctor: How are you feeling? Patient: I have chest pain and fever.",
    "questions": ["What are the symptoms?", "How long?"]
  }'
```

**Success Response (200 OK):**
```json
{
  "summary": "Patient presents with chest pain and fever. Symptoms appear acute.",
  "qa": [
    {
      "question": "What are the symptoms?",
      "answer": "Chest pain and fever"
    },
    {
      "question": "How long?",
      "answer": "Not specified"
    }
  ],
  "success": true
}
```

### 4. GET `/health`

Check if the API is running and models are initialized.

**Request:**
- Method: `GET`

**Response:**
```json
{
  "status": "healthy",
  "transcription_model": "base",
  "groq_initialized": true,
  "timestamp": "2026-05-04T12:34:56.789012"
}
```

### 5. GET `/`

Get API information and available endpoints.

**Request:**
- Method: `GET`

**Response:**
```json
{
  "name": "Doctor Patient Summarizer - Transcription & Summarization API",
  "version": "3.0.0 (With LLM Summarization)",
  "endpoints": {
    "POST /transcribe": "Transcribe audio file to text",
    "POST /summarize": "Summarize transcript and answer questions using LLM",
    "GET /health": "Health check endpoint",
    "GET /": "API information"
  },
  "supported_formats": ["wav", "mp3", "flac", "m4a", "ogg", "webm", "mp4"],
  "models": {
    "transcription": "base",
    "summarization": "llama3-70b-8192 (via Groq)"
  },
  "features": ["⚡ Fast audio transcription", "🧠 LLM-based medical summarization", "📋 Structured Q&A extraction"]
}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=gsk_your_api_key_here
```

Get your key from: https://console.groq.com

### Whisper Model Configuration

Edit the following variables in `app.py` to customize behavior:

```python
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg', 'webm', 'mp4'}  # Supported audio formats
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large
```

**Model comparison:**
- **tiny**: Fastest, least accurate (~40MB)
- **base**: Good balance (~140MB) - *Recommended for initial setup*
- **small**: Better accuracy (~466MB)
- **medium**: High accuracy (~1.5GB)
- **large**: Highest accuracy (~3GB)

## 🌐 Deploying on AWS EC2

### Prerequisites

- AWS EC2 instance (Ubuntu 20.04 or later recommended)
- Instance type: `t3.medium` or larger (for better performance)
- Security group allowing port 5000

### Deployment Steps

1. **SSH into your instance:**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

2. **Install Python and pip:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv -y
```

3. **Clone and setup:**
```bash
git clone https://github.com/underlineit-dev-13/docconvo-backend.git
cd docconvo-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Configure Groq API key:**
```bash
echo 'GROQ_API_KEY=your_api_key_here' > .env
```

5. **Run with Gunicorn (Production):**
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
```

6. **Optional: Run as a service**

Create `/etc/systemd/system/transcription-api.service`:
```ini
[Unit]
Description=Doctor Patient Summarizer Transcription API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/docconvo-backend
ExecStart=/home/ubuntu/docconvo-backend/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable transcription-api
sudo systemctl start transcription-api
```

## 🚨 Error Handling

The API returns appropriate HTTP status codes and error messages:

| Status | Scenario |
|--------|----------|
| 200 | Successful transcription |
| 400 | No file provided or invalid file format |
| 500 | Transcription failed or model not initialized |

**Example errors:**
```json
// No file provided
{
  "error": "No audio file provided. Please include \"audio\" field in multipart/form-data",
  "success": false
}

// Invalid file format
{
  "error": "File type not allowed. Supported formats: wav, mp3, flac, m4a, ogg, webm, mp4",
  "success": false
}

// Transcription failure
{
  "error": "Transcription failed: [error details]",
  "success": false
}
```

## 📦 Project Structure

```
docconvo-backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── venv/                 # Virtual environment (created locally)
└── .gitignore            # Git ignore file
```

## 🔐 Security Considerations

1. **Input Validation**: File type validation is enforced
2. **Temporary Files**: Uploaded files are cleaned up immediately after processing
3. **Error Messages**: Generic error messages (avoid exposing system details)
4. **Production Deployment**:
   - Set `debug=False` (already configured)
   - Use HTTPS (configure reverse proxy like Nginx)
   - Implement authentication if needed
   - Add rate limiting
   - Monitor disk space for temporary files

## 📝 Troubleshooting

### Model Download Issues
The first run will download the Whisper model (~140MB for "base"). Ensure internet connectivity.

### Out of Memory Error
If using a small EC2 instance, reduce model size or increase instance type. Alternatively, use GPU instance (g3 type).

### Port Already in Use
```bash
# Check what's using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Permission Denied
If deployed as systemd service, ensure the user has write permissions to temporary file locations.

## 🤝 Contributing

To contribute improvements:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - feel free to use this project as needed.

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review Flask and faster-whisper documentation
- Open an issue on GitHub

---

**Version**: 3.0.0  
**Last Updated**: May 2026  
**Maintainer**: Doctor Patient Summarizer Team

---

## 🧠 LLM Summarization Details

See [LLM_SUMMARIZATION_GUIDE.md](LLM_SUMMARIZATION_GUIDE.md) for detailed documentation on the `/summarize` endpoint, including:
- Setup instructions
- API usage examples
- Error handling
- Performance notes
- Troubleshooting
