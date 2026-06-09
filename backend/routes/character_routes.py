import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.services.gemini_service import gemini_service
from backend.utils.helpers import success_response, error_response

character_bp = Blueprint("character", __name__)

@character_bp.route("/generate-characters", methods=["POST"])
@login_required
def generate_characters():
    """Generates detailed character profiles via Google Gemini."""
    data = request.get_json() or {}
    project_id = data.get("project_id")
    
    if not project_id:
        return error_response("Field 'project_id' is required.", 400)
        
    project = firebase_service.get_document("projects", project_id)
    if not project:
        return error_response("Project not found.", 404)
        
    if project.get("user_id") != request.current_user.get("uid"):
        return error_response("Access denied.", 403)
        
    story_idea = project.get("story_idea")
    genre = project.get("genre")
    
    # Generate characters
    characters_data = gemini_service.generate_characters(story_idea, genre)
    if not characters_data or "error" in characters_data:
        return error_response("Failed to generate character profiles from Gemini.", 500, details=characters_data)
        
    characters_data["project_id"] = project_id
    characters_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("characters", project_id, characters_data)
    
    return success_response(characters_data, "Character profiles generated and saved successfully.")
