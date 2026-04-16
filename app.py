import os
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg', 'webm', 'mp4'}
UPLOAD_FOLDER = tempfile.gettempdir()
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large

# Initialize Whisper model
try:
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
except Exception as e:
    model = None
    print(f"Warning: Failed to initialize Whisper model: {e}")


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio file using Whisper
    
    Expected request:
    - multipart/form-data with 'audio' file field
    
    Returns:
    - JSON response with 'transcript' field containing transcribed text
    """
    try:
        # Check if model is initialized
        if model is None:
            return jsonify({
                'error': 'Whisper model not initialized',
                'success': False
            }), 500
        
        # Check if file is in request
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No audio file provided. Please include "audio" field in multipart/form-data',
                'success': False
            }), 400
        
        file = request.files['audio']
        
        # Check if file has a filename
        if file.filename == '':
            return jsonify({
                'error': 'No file selected for uploading',
                'success': False
            }), 400
        
        # Check if file extension is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}',
                'success': False
            }), 400
        
        # Save file temporarily
        temp_path = None
        try:
            # Create temp file with original extension
            ext = Path(file.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            # Transcribe audio
            segments, info = model.transcribe(temp_path)
            
            # Collect all segments into single transcript
            transcript = "".join(segment.text for segment in segments)
            
            return jsonify({
                'transcript': transcript.strip(),
                'success': True,
                'language': info.language,
                'duration': info.duration
            }), 200
        
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Warning: Failed to delete temp file {temp_path}: {e}")
    
    except Exception as e:
        return jsonify({
            'error': f'Transcription failed: {str(e)}',
            'success': False
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_initialized': model is not None,
        'model': WHISPER_MODEL
    }), 200


@app.route('/', methods=['GET'])
def index():
    """API information endpoint"""
    return jsonify({
        'name': 'Doctor Patient Summarizer - Transcription API',
        'version': '1.0.0',
        'endpoints': {
            'POST /transcribe': 'Transcribe audio file (multipart/form-data with "audio" field)',
            'GET /health': 'Health check endpoint',
            'GET /': 'API information'
        },
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'model': WHISPER_MODEL
    }), 200


if __name__ == '__main__':
    # Run Flask app
    # Set debug=False for production
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
