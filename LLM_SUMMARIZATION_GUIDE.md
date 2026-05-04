# Groq LLM Integration Guide

## Overview
The Doctor Patient Summarizer backend now includes LLM-based medical summarization using **Groq API** (llama3-70b-8192 model).

## New Endpoint: POST /summarize

### Purpose
Summarize medical transcripts and extract structured answers to questions.

### Request

**Endpoint**: `POST /summarize`

**Content-Type**: `application/json`

**Body**:
```json
{
  "transcript": "Doctor: Good morning. Patient: Hi, I have been experiencing chest pain for the last 3 days...",
  "questions": [
    "What is the patient's main complaint?",
    "How long has the patient been experiencing symptoms?",
    "Any allergies mentioned?"
  ]
}
```

### Response

**Success (200 OK)**:
```json
{
  "summary": "Patient presents with chest pain of 3 days duration. Symptoms appear to be cardiac in nature. Patient reports no previous similar episodes.",
  "qa": [
    {
      "question": "What is the patient's main complaint?",
      "answer": "Chest pain"
    },
    {
      "question": "How long has the patient been experiencing symptoms?",
      "answer": "3 days"
    },
    {
      "question": "Any allergies mentioned?",
      "answer": "Not mentioned"
    }
  ],
  "success": true
}
```

**Error (400/500)**:
```json
{
  "error": "Missing required field: \"transcript\"",
  "success": false
}
```

---

## Setup Instructions

### 1. Get Groq API Key

1. Go to [Groq Console](https://console.groq.com)
2. Sign up / Log in
3. Create API key
4. Copy the key

### 2. Configure Environment Variable

**Local Development** - Create `.env` file:
```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
```

**EC2 Deployment** - Set environment variable:
```bash
export GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
```

Or add to `.bashrc`:
```bash
echo 'export GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx' >> ~/.bashrc
source ~/.bashrc
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**New packages added**:
- `groq==0.4.2` - Groq API client
- `python-dotenv==1.0.0` - Environment variable management

---

## Testing the Endpoint

### Using cURL

```bash
curl -X POST http://localhost:5000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Doctor: How are you feeling? Patient: I have headache and fever for 2 days.",
    "questions": ["What symptoms does the patient have?", "How long have symptoms lasted?"]
  }'
```

### Using Python

```python
import requests

url = "http://localhost:5000/summarize"
payload = {
    "transcript": "Doctor: Good morning. Patient: I have chest pain and difficulty breathing.",
    "questions": [
        "What is the main complaint?",
        "Any respiratory issues?"
    ]
}

response = requests.post(url, json=payload)
print(response.json())
```

### Using Postman

1. Method: `POST`
2. URL: `http://localhost:5000/summarize`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "transcript": "Doctor conversation here",
  "questions": ["question1", "question2"]
}
```

---

## API Response Validation

✅ All responses are **guaranteed valid JSON**  
✅ Fallback handling for LLM parsing errors  
✅ Auto-generated Q&A if parsing fails  
✅ Safe error messages  

---

## Error Handling

| Error | HTTP Code | Solution |
|-------|-----------|----------|
| Missing transcript | 400 | Include "transcript" field |
| Questions not a list | 400 | Ensure "questions" is array |
| Groq API key not set | 500 | Set GROQ_API_KEY environment |
| Groq API error | 500 | Check API key validity, rate limits |
| JSON parsing fails | 200 | Returns fallback with raw response |

---

## Performance Notes

- **First request**: 2-5 seconds (Groq API call)
- **Subsequent requests**: 2-5 seconds (consistent)
- **Timeout**: Configured for 120 seconds (safe for long transcripts)
- **Token limit**: 2048 tokens (sufficient for medical summaries)

---

## Security

✅ API key never hardcoded  
✅ Loaded from environment variables  
✅ Error messages don't expose system details  
✅ Input validation on all fields  
✅ Safe JSON parsing with fallbacks  

---

## Deployed Endpoints

### Test Server
```
POST http://18.191.229.114:5000/summarize
```

### Health Check
```
GET http://18.191.229.114:5000/health
```

Response includes Groq initialization status.

---

## Troubleshooting

### "Groq LLM service not initialized"
**Solution**: Set `GROQ_API_KEY` environment variable

### "Invalid API key"
**Solution**: Verify key from https://console.groq.com

### "Rate limit exceeded"
**Solution**: Wait 1 minute before retrying. Groq has rate limits on free tier.

### "JSON parsing failed"
**Solution**: This is handled gracefully. You'll still get a response with the raw summary.

---

## Future Enhancements

- ✅ Caching for identical transcripts
- ✅ Batch processing for multiple transcripts
- ✅ Custom prompt templates
- ✅ Supported language specification
- ✅ Response streaming for long outputs

---

## References

- [Groq API Docs](https://console.groq.com/docs)
- [Llama 3 70B Model](https://console.groq.com/docs/models)
- [Flask Documentation](https://flask.palletsprojects.com)
