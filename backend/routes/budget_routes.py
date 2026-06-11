import datetime
from flask import Blueprint, request
from .auth_routes import login_required
from ..services.firebase_service import firebase_service
from ..services.granite_service import granite_service
from ..utils.helpers import success_response, error_response

budget_bp = Blueprint("budget", __name__)

@budget_bp.route("/generate-budget-plan", methods=["POST"])
@login_required
def generate_budget_plan():
    """Generates pre-production, production, and post-production budget estimates using IBM Granite AI."""
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
    
    # Retrieve or auto-generate character profiles to maintain synchronization
    from backend.services.gemini_service import gemini_service
    characters_doc = firebase_service.get_document("characters", project_id)
    if not characters_doc or "characters" not in characters_doc or not characters_doc["characters"]:
        characters_doc = gemini_service.generate_characters(story_idea, genre, project_id=project_id)
        if characters_doc and "characters" in characters_doc:
            characters_doc["project_id"] = project_id
            characters_doc["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("characters", project_id, characters_doc)
            
    characters_list = characters_doc.get("characters", []) if characters_doc else []

    # Retrieve or auto-generate scene breakdown to maintain synchronization
    scene_doc = firebase_service.get_document("scene_breakdowns", project_id)
    if not scene_doc or "scenes" not in scene_doc or not scene_doc["scenes"]:
        duration_length = project.get("duration_length", "Short Film")
        scene_doc = gemini_service.generate_scenes(story_idea, genre, duration_length, characters_list, project_id=project_id)
        if scene_doc and "scenes" in scene_doc:
            scene_doc["project_id"] = project_id
            scene_doc["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("scene_breakdowns", project_id, scene_doc)
            
    scenes_list = scene_doc.get("scenes", []) if scene_doc else []
    
    # Generate budget plan
    budget_data = granite_service.generate_budget_plan(story_idea, genre, characters_list, scenes_list, project_id=project_id)
    if not budget_data or "error" in budget_data:
        return error_response("Failed to generate budget plan from IBM Granite AI.", 500, details=budget_data)
        
    budget_data["project_id"] = project_id
    budget_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("budget_plans", project_id, budget_data)
    
    return success_response(budget_data, "Budget plan generated and saved successfully.")
