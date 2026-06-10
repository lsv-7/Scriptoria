import json
import re
from flask import jsonify

def parse_combined_story_idea(story_idea_str):
    """
    Parses a combined story idea string into a dictionary:
    {
        "pitch": str,
        "logline": str,
        "synopsis": str,
        "theme": str,
        "story_analysis": str # formatted string for prompt
    }
    """
    if not isinstance(story_idea_str, str):
        story_idea_str = str(story_idea_str or "")
        
    pitch = ""
    logline = ""
    synopsis = ""
    theme = ""
    
    # Check if we have the multi-line "Pitch:", "Logline:", "Synopsis:", "Theme:" structure
    if "pitch:" in story_idea_str.lower() and "logline:" in story_idea_str.lower():
        # Match sections
        p_match = re.search(r'(?i)Pitch:\s*(.*?)(?=\bLogline:|$)', story_idea_str, re.DOTALL)
        if p_match:
            pitch = p_match.group(1).strip()
            
        l_match = re.search(r'(?i)Logline:\s*(.*?)(?=\bSynopsis:|$)', story_idea_str, re.DOTALL)
        if l_match:
            logline = l_match.group(1).strip()
            
        s_match = re.search(r'(?i)Synopsis:\s*(.*?)(?=\bTheme:|$)', story_idea_str, re.DOTALL)
        if s_match:
            synopsis = s_match.group(1).strip()
            
        t_match = re.search(r'(?i)Theme:\s*(.*?)$', story_idea_str, re.DOTALL)
        if t_match:
            theme = t_match.group(1).strip()
    else:
        # Just a raw pitch
        pitch = story_idea_str.strip()
        
    # Reconstruct story_analysis text block
    analysis_parts = []
    if logline:
        analysis_parts.append(f"Logline: {logline}")
    if synopsis:
        analysis_parts.append(f"Synopsis: {synopsis}")
    if theme:
        analysis_parts.append(f"Theme: {theme}")
        
    story_analysis = "\n".join(analysis_parts) if analysis_parts else f"Story Idea/Pitch: {pitch}"
    
    return {
        "pitch": pitch,
        "logline": logline,
        "synopsis": synopsis,
        "theme": theme,
        "story_analysis": story_analysis
    }

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

def clean_prose_text(text):
    if not isinstance(text, str):
        return text
    
    # Import inline to avoid circular imports
    from backend.utils.story_generator import clean_location_for_prose
    
    # Matches patterns like INT. CLASSROOM - DAY or EXT. STREETS (case-insensitive)
    pattern = r'\b(?:INT|EXT|INT/EXT|EXT/INT|INT\./EXT\.|EXT\./INT\.)\.?\s+([^-\t\n\r]+)(?:\s*-\s*(?:DAY|NIGHT|DUSK|DAWN|LATER|CONTINUOUS|SAME TIME))?\b'
    
    def replacer(match):
        raw_match = match.group(0)
        return clean_location_for_prose(raw_match)
        
    return re.sub(pattern, replacer, text, flags=re.IGNORECASE)

def clean_prose_data(data, skip_keys=None):
    if skip_keys is None:
        skip_keys = {"location", "screenplay_text"}
        
    if isinstance(data, dict):
        return {k: (v if k in skip_keys else clean_prose_data(v, skip_keys)) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_prose_data(item, skip_keys) for item in data]
    elif isinstance(data, str):
        return clean_prose_text(data)
    return data
