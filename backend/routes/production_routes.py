import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.services.granite_service import granite_service
from backend.utils.helpers import success_response, error_response

production_bp = Blueprint("production", __name__)

@production_bp.route("/generate-production-plan", methods=["POST"])
@login_required
def generate_production_plan():
    """Generates physical production plan using IBM Granite AI."""
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
    
    # Generate production plan
    production_data = granite_service.generate_production_plan(story_idea, genre)
    if not production_data or "error" in production_data:
        return error_response("Failed to generate production plan from IBM Granite AI.", 500, details=production_data)
        
    production_data["project_id"] = project_id
    production_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("production_plans", project_id, production_data)
    
    return success_response(production_data, "Production plan generated and saved successfully.")
