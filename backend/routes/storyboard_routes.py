import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.services.gemini_service import gemini_service
from backend.utils.helpers import success_response, error_response

storyboard_bp = Blueprint("storyboard", __name__)

@storyboard_bp.route("/generate-storyboard", methods=["POST"])
@login_required
def generate_storyboard():
    """Generates storyboard prompt cards for scenes using Google Gemini."""
    data = request.get_json() or {}
    project_id = data.get("project_id")
    
    if not project_id:
        return error_response("Field 'project_id' is required.", 400)
        
    project = firebase_service.get_document("projects", project_id)
    if not project:
        return error_response("Project not found.", 404)
        
    if project.get("user_id") != request.current_user.get("uid"):
        return error_response("Access denied.", 403)
        
    # Check if scene breakdown exists
    scenes_doc = firebase_service.get_document("scene_breakdowns", project_id)
    if not scenes_doc or "scenes" not in scenes_doc:
        # Generate scenes automatically if missing
        print(">>> Scene breakdown missing. Auto-generating scenes for storyboard...")
        scenes_doc = gemini_service.generate_scenes(project.get("story_idea"), project.get("genre"))
        if not scenes_doc or "scenes" not in scenes_doc:
            return error_response("Failed to generate required scene breakdown for storyboard.", 500)
            
        scenes_doc["project_id"] = project_id
        scenes_doc["created_at"] = datetime.datetime.utcnow().isoformat()
        firebase_service.set_document("scene_breakdowns", project_id, scenes_doc)
        
    scenes_list = scenes_doc["scenes"]
    story_idea = project.get("story_idea")
    
    # Generate storyboard prompts
    storyboard_data = gemini_service.generate_storyboard(story_idea, scenes_list)
    if not storyboard_data or "error" in storyboard_data:
        return error_response("Failed to generate storyboard cards from Gemini.", 500, details=storyboard_data)
        
    storyboard_data["project_id"] = project_id
    storyboard_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("storyboards", project_id, storyboard_data)
    
    return success_response(storyboard_data, "Storyboard frame planner generated and saved successfully.")
