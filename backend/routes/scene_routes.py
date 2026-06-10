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
    
    # Check if we have refined story insights (story analysis) to represent its content
    story_analysis = firebase_service.get_document("story_analysis", project_id)
    if story_analysis:
        def format_val_str(val):
            if not val:
                return ""
            if isinstance(val, dict):
                return " ".join([f"{k.replace('_', ' ').title()}: {format_val_str(v)}" for k, v in val.items()])
            if isinstance(val, list):
                return " ".join([format_val_str(item) for item in val])
            return str(val)
        story_idea = f"Pitch: {project.get('story_idea')}\nLogline: {format_val_str(story_analysis.get('logline'))}\nSynopsis: {format_val_str(story_analysis.get('synopsis'))}\nTheme: {format_val_str(story_analysis.get('theme'))}"

    genre = project.get("genre")
    duration_length = project.get("duration_length", "Short Film")
    
    # Retrieve or auto-generate characters to maintain consistent names
    characters_doc = firebase_service.get_document("characters", project_id)
    if not characters_doc or "characters" not in characters_doc or not characters_doc["characters"]:
        characters_doc = gemini_service.generate_characters(story_idea, genre, project_id=project_id)
        if characters_doc and "characters" in characters_doc:
            characters_doc["project_id"] = project_id
            characters_doc["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("characters", project_id, characters_doc)
            
    characters_list = []
    if characters_doc and "characters" in characters_doc:
        characters_list = characters_doc["characters"]
        
    # Generate scenes
    scenes_data = gemini_service.generate_scenes(story_idea, genre, duration_length, characters_list, project_id=project_id)
    if not scenes_data or "error" in scenes_data:
        return error_response("Failed to generate scene breakdown from Gemini.", 500, details=scenes_data)
        
    scenes_data["project_id"] = project_id
    scenes_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("scene_breakdowns", project_id, scenes_data)
    
    return success_response(scenes_data, "Scene breakdown generated and saved successfully.")
