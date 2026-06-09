import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.services.granite_service import granite_service
from backend.utils.helpers import success_response, error_response

sound_bp = Blueprint("sound", __name__)

@sound_bp.route("/generate-sound-design", methods=["POST"])
@login_required
def generate_sound_design():
    """Generates film sound design blueprint using IBM Granite AI."""
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
    
    # Generate sound design
    sound_data = granite_service.generate_sound_design(story_idea, genre)
    if not sound_data or "error" in sound_data:
        return error_response("Failed to generate sound design from IBM Granite AI.", 500, details=sound_data)
        
    sound_data["project_id"] = project_id
    sound_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("sound_designs", project_id, sound_data)
    
    return success_response(sound_data, "Sound design blueprint generated and saved successfully.")
