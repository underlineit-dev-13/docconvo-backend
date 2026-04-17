import os
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel
import numpy as np

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg', 'webm', 'mp4'}
UPLOAD_FOLDER = tempfile.gettempdir()

# Model options: tiny (fastest), base, small, medium, large (most accurate)
# For accuracy: use "small" or "medium"
# For speed: use "base" or "tiny"
WHISPER_MODEL = "small"  # Changed to "small" for better accuracy

# Initialize Whisper model with optimization
try:
    # For CPU: use int8 (CPU-optimized quantization)
    # For GPU: use float16 or float32
    model = WhisperModel(
        WHISPER_MODEL, 
        device="cpu", 
        compute_type="int8"  # CPU-optimized (perfect for t2.medium)
    )
    print(f"✅ Model '{WHISPER_MODEL}' loaded successfully with int8 precision (CPU-optimized)")
except Exception as e:
    model = None
    print(f"❌ Warning: Failed to initialize Whisper model: {e}")


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio file using Whisper with language detection
    
    Expected request:
    - multipart/form-data with 'audio' file field
    - Optional: 'language' parameter (e.g., 'en', 'es', 'fr')
    
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
        
        # Get optional language parameter
        language = request.form.get('language', None)  # None = auto-detect
        
        # Save file temporarily
        temp_path = None
        try:
            # Create temp file with original extension
            ext = Path(file.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            print(f"📤 Transcribing file: {file.filename}")
            
            # Transcribe with better parameters for accuracy
            segments, info = model.transcribe(
                temp_path,
                language=language,  # Language code or None for auto-detect
                beam_size=5,  # Higher = better accuracy but slower (default: 5)
                best_of=5,  # Better accuracy (default: 5)
                temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],  # Fallback temps for robustness
                vad_filter=True,  # Remove silence for better accuracy
                vad_parameters={"threshold": 0.4}  # Remove background noise
            )
            
            # Collect all segments into single transcript
            transcript = "".join(segment.text for segment in segments).strip()
            
            print(f"✅ Transcription complete - Language: {info.language}")
            
            return jsonify({
                'transcript': transcript,
                'success': True,
                'language': info.language,
                'duration': info.duration,
                'model': WHISPER_MODEL
            }), 200
        
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return jsonify({
                'error': f'Transcription failed: {str(e)}',
                'success': False
            }), 500
        
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Warning: Failed to delete temp file {temp_path}: {e}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
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
        'version': '2.0.0 (Accuracy Optimized)',
        'endpoints': {
            'POST /transcribe': 'Transcribe audio file (multipart/form-data with "audio" field)',
            'GET /health': 'Health check endpoint',
            'GET /': 'API information'
        },
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'model': WHISPER_MODEL,
        'compute_type': 'int8 (CPU-optimized)',
        'features': [
            '🎯 High accuracy transcription',
            '🌍 Automatic language detection',
            '📊 Noise reduction (VAD filter)',
            '⚡ Optimized for CPU'
        ]
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
