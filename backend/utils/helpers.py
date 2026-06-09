import json
import re
from flask import jsonify

def clean_json_response(text):
    """
    Cleans markdown code blocks (e.g. ```json ... ```) from a text response
    and parses it into a Python dict/list.
    """
    if not text:
        return {}
        
    text = text.strip()
    
    # Remove markdown code formatting if present
    # Matches ```json <content> ``` or just ``` <content> ```
    pattern = r"^```(?:json)?\s*(.*?)\s*```$"
    match = re.match(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned_text = match.group(1).strip()
    else:
        # Sometimes there are trailing backticks or formatting
        cleaned_text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"\s*```$", "", cleaned_text)
        
    cleaned_text = cleaned_text.strip()
    
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        # Fallback: try to find the first '{' and last '}' and parse that substring
        try:
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(cleaned_text[start:end+1])
        except Exception:
            pass
            
        # If still failing, return raw text in a description field
        return {"error": "Failed to parse JSON response", "raw_content": text}

def success_response(data, message="Success", status_code=200):
    """Formats a standard successful API response."""
    return jsonify({
        "status": "success",
        "message": message,
        "data": data
    }), status_code

def error_response(message="An error occurred", status_code=400, details=None):
    """Formats a standard error API response."""
    response = {
        "status": "error",
        "message": message
    }
    if details:
        response["details"] = details
    return jsonify(response), status_code

def get_auth_token(request):
    """Extracts bearer token from request Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None
        
    parts = auth_header.split(" ")
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
        
    return None
