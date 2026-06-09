import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.services.gemini_service import gemini_service
from backend.utils.helpers import success_response, error_response

scene_bp = Blueprint("scene", __name__)

@scene_bp.route("/generate-scenes", methods=["POST"])
@login_required
def generate_scenes():
    """Generates scene breakdown (scene numbers, locations, objectives) via Google Gemini."""
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
    
    # Generate scenes
    scenes_data = gemini_service.generate_scenes(story_idea, genre)
    if not scenes_data or "error" in scenes_data:
        return error_response("Failed to generate scene breakdown from Gemini.", 500, details=scenes_data)
        
    scenes_data["project_id"] = project_id
    scenes_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("scene_breakdowns", project_id, scenes_data)
    
    return success_response(scenes_data, "Scene breakdown generated and saved successfully.")
