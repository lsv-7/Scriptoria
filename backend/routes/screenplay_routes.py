import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.services.granite_service import granite_service
from backend.utils.helpers import success_response, error_response

screenplay_bp = Blueprint("screenplay", __name__)

@screenplay_bp.route("/generate-screenplay", methods=["POST"])
@login_required
def generate_screenplay():
    """Generates professional screenplay using IBM Granite AI."""
    data = request.get_json() or {}
    project_id = data.get("project_id")
    
    if not project_id:
        return error_response("Field 'project_id' is required.", 400)
        
    project = firebase_service.get_document("projects", project_id)
    if not project:
        return error_response("Project not found.", 404)
        
    if project.get("user_id") != request.current_user.get("uid"):
        return error_response("Access denied.", 403)
        
    # Attempt to retrieve character profiles to make the screenplay script highly accurate
    characters_doc = firebase_service.get_document("characters", project_id)
    characters_list = []
    if characters_doc and "characters" in characters_doc:
        characters_list = characters_doc["characters"]
        
    story_idea = project.get("story_idea")
    genre = project.get("genre")
    
    # Generate screenplay
    screenplay_text = granite_service.generate_screenplay(story_idea, genre, characters_list)
    if not screenplay_text:
        return error_response("Failed to generate screenplay from IBM Granite AI.", 500)
        
    screenplay_data = {
        "project_id": project_id,
        "screenplay_text": screenplay_text,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    firebase_service.set_document("screenplays", project_id, screenplay_data)
    
    return success_response(screenplay_data, "Screenplay script generated and saved successfully.")
