def validate_project_input(data):
    """
    Validates project input dictionary.
    Returns: (is_valid, error_message)
    """
    if not data:
        return False, "Request payload is empty"
        
    required_fields = ["project_name", "genre", "target_audience", "story_idea"]
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return False, f"Field '{field}' is required and cannot be empty"
            
    # Length validations
    if len(str(data["project_name"])) > 100:
        return False, "Project name must be under 100 characters"
        
    if len(str(data["genre"])) > 50:
        return False, "Genre must be under 50 characters"
        
    if len(str(data["target_audience"])) > 100:
        return False, "Target audience must be under 100 characters"
        
    if len(str(data["story_idea"])) < 10:
        return False, "Story idea should be at least 10 characters long"
        
    if len(str(data["story_idea"])) > 2000:
        return False, "Story idea must be under 2000 characters"
        
    return True, None
