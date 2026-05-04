import os
import tempfile
import json
from pathlib import Path
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel
from groq import Groq
from dotenv import load_dotenv
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Suppress ONNX Runtime GPU discovery warnings (harmless on CPU-only instances)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['ONNX_LOGS'] = 'OFF'

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg', 'webm', 'mp4'}
UPLOAD_FOLDER = tempfile.gettempdir()

# Model options: tiny (fastest), base, small, medium, large (most accurate)
# For accuracy: use "small" or "medium"
# For speed: use "base" or "tiny"
# RECOMMENDED: "base" - best balance of speed and accuracy
WHISPER_MODEL = "base"  # Changed from "small" for faster transcription

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

# Initialize Groq client
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("⚠️  Warning: GROQ_API_KEY environment variable not set")
        groq_client = None
    else:
        groq_client = Groq(api_key=groq_api_key)
        print(f"✅ Groq client initialized successfully")
except Exception as e:
    groq_client = None
    print(f"❌ Warning: Failed to initialize Groq client: {e}")


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_json_safely(json_string, default_fallback=None):
    """
    Safely parse JSON with fallback handling
    
    Args:
        json_string: JSON string to parse
        default_fallback: Default value if parsing fails
    
    Returns:
        Parsed JSON object or default fallback
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        if default_fallback:
            return default_fallback
        return None


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
            
            # Transcribe with optimized parameters for speed
            segments, info = model.transcribe(
                temp_path,
                language=language,  # Language code or None for auto-detect
                beam_size=3,  # Reduced from 5 for faster processing
                best_of=3,  # Reduced from 5 for faster processing
                temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
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


@app.route('/summarize', methods=['POST'])
def summarize():
    """
    Summarize transcript and answer questions using Groq LLM
    
    Expected request:
    {
        "transcript": "string",
        "questions": ["q1", "q2", ...]
    }
    
    Returns:
    {
        "summary": "string",
        "qa": [
            {"question": "string", "answer": "string"}
        ]
    }
    """
    try:
        # Check if Groq is initialized
        if groq_client is None:
            return jsonify({
                'error': 'Groq LLM service not initialized. GROQ_API_KEY not set.',
                'success': False
            }), 500
        
        # Parse JSON request
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json',
                'success': False
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'transcript' not in data:
            return jsonify({
                'error': 'Missing required field: "transcript"',
                'success': False
            }), 400
        
        transcript = data.get('transcript', '').strip()
        questions = data.get('questions', [])
        
        # Validate transcript is not empty
        if not transcript:
            return jsonify({
                'error': 'Transcript cannot be empty',
                'success': False
            }), 400
        
        # Validate questions is a list
        if not isinstance(questions, list):
            return jsonify({
                'error': 'Questions must be a list',
                'success': False
            }), 400
        
        print(f"🧠 Processing summarization for transcript ({len(transcript)} chars)")
        print(f"📋 Processing {len(questions)} questions")
        
        # Format questions for the prompt
        questions_str = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        # Build the prompt
        system_prompt = """You are an intelligent medical assistant AI.

Analyze the doctor-patient conversation and generate:
1. A concise summary of the patient's condition
2. Structured answers to the given questions

Rules:
- Focus on patient responses
- Ignore unnecessary conversation
- Do NOT hallucinate
- If data is missing, return "Not mentioned"
- Keep answers short and medically relevant

Return ONLY valid JSON with no additional text."""
        
        user_prompt = f"""Transcript:
{transcript}

Questions:
{questions_str}

Return ONLY JSON in this exact format:
{{
  "summary": "short paragraph summary",
  "qa": [
    {{"question": "question text", "answer": "answer text"}}
  ]
}}"""
        
        # Call Groq LLM
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                model="llama3-70b-8192",
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=2048,
                top_p=1.0
            )
            
            # Extract response
            response_text = chat_completion.choices[0].message.content.strip()
            print(f"✅ Groq response received ({len(response_text)} chars)")
            
            # Parse JSON response safely
            parsed_response = parse_json_safely(response_text)
            
            if parsed_response is None:
                # Try to extract JSON from response if parsing fails
                print("⚠️  Attempting to extract JSON from response...")
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    parsed_response = parse_json_safely(json_match.group())
                
                if parsed_response is None:
                    # Fallback response
                    print("❌ Failed to parse JSON, using fallback")
                    parsed_response = {
                        "summary": response_text[:500] if response_text else "Summary generation failed",
                        "qa": [{"question": q, "answer": "Unable to generate answer"} for q in questions]
                    }
            
            # Validate response structure
            if not isinstance(parsed_response, dict):
                parsed_response = {
                    "summary": str(parsed_response)[:500],
                    "qa": [{"question": q, "answer": "Unable to generate answer"} for q in questions]
                }
            
            # Ensure required fields exist
            if 'summary' not in parsed_response:
                parsed_response['summary'] = "Summary not available"
            
            if 'qa' not in parsed_response:
                parsed_response['qa'] = []
            
            # Ensure qa is a list
            if not isinstance(parsed_response['qa'], list):
                parsed_response['qa'] = []
            
            # Validate qa items
            validated_qa = []
            for item in parsed_response['qa']:
                if isinstance(item, dict) and 'question' in item and 'answer' in item:
                    validated_qa.append({
                        'question': str(item['question']),
                        'answer': str(item['answer'])
                    })
            
            parsed_response['qa'] = validated_qa
            
            return jsonify({
                'summary': parsed_response['summary'],
                'qa': parsed_response['qa'],
                'success': True
            }), 200
        
        except Exception as e:
            print(f"❌ Groq API error: {str(e)}")
            return jsonify({
                'error': f'Groq LLM failed: {str(e)}',
                'success': False
            }), 500
    
    except Exception as e:
        print(f"❌ Unexpected error in summarize: {str(e)}")
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'success': False
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'transcription_model': WHISPER_MODEL if model else 'not_initialized',
        'groq_initialized': groq_client is not None,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """API information endpoint"""
    return jsonify({
        'name': 'Doctor Patient Summarizer - Transcription & Summarization API',
        'version': '3.0.0 (With LLM Summarization)',
        'endpoints': {
            'POST /transcribe': 'Transcribe audio file to text',
            'POST /summarize': 'Summarize transcript and answer questions using LLM',
            'GET /health': 'Health check endpoint',
            'GET /': 'API information'
        },
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'models': {
            'transcription': WHISPER_MODEL,
            'summarization': 'llama3-70b-8192 (via Groq)'
        },
        'features': [
            '⚡ Fast audio transcription',
            '🧠 LLM-based medical summarization',
            '📋 Structured Q&A extraction',
            '🔒 Secure API key handling',
            '🚀 Production-ready error handling'
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
