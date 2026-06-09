import uuid
import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.utils.validators import validate_project_input
from backend.utils.helpers import success_response, error_response

project_bp = Blueprint("project", __name__)

@project_bp.route("/create-project", methods=["POST"])
@login_required
def create_project():
    """
    Creates a new pre-production project.
    Payload: { project_name, genre, target_audience, story_idea }
    """
    data = request.get_json() or {}
    
    is_valid, err_msg = validate_project_input(data)
    if not is_valid:
        return error_response(err_msg, 400)
        
    project_id = str(uuid.uuid4())
    user_id = request.current_user.get("uid")
    
    project_schema = {
        "project_id": project_id,
        "user_id": user_id,
        "project_name": data.get("project_name").strip(),
        "genre": data.get("genre").strip(),
        "target_audience": data.get("target_audience").strip(),
        "story_idea": data.get("story_idea").strip(),
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    success = firebase_service.set_document("projects", project_id, project_schema)
    if success:
        return success_response(project_schema, "Project created successfully.", 201)
    else:
        return error_response("Failed to save project to the database.", 500)

@project_bp.route("/projects", methods=["GET"])
@login_required
def get_projects():
    """Retrieves all projects owned by the authenticated user."""
    user_id = request.current_user.get("uid")
    projects = firebase_service.get_documents_by_filter("projects", "user_id", "==", user_id)
    # Sort projects by created_at descending (newest first)
    projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return success_response(projects, "Projects retrieved successfully.")

@project_bp.route("/project/<id>", methods=["GET"])
@login_required
def get_project_by_id(id):
    """
    Retrieves a single project along with ALL generated pre-production modules
    (Story Analysis, Screenplay, Sound Design, Production Plan, etc.).
    """
    user_id = request.current_user.get("uid")
    project = firebase_service.get_document("projects", id)
    
    if not project:
        return error_response("Project not found.", 404)
        
    if project.get("user_id") != user_id:
        return error_response("Access denied. You do not own this project.", 403)
        
    # Compile all related pre-production sub-documents
    # Use fallback queries matching project_id
    compiled_data = {
        "project": project,
        "story_analysis": firebase_service.get_document("story_analysis", id),
        "narrative_structure": firebase_service.get_document("narrative_structures", id),
        "screenplay": firebase_service.get_document("screenplays", id),
        "characters": firebase_service.get_document("characters", id),
        "scene_breakdown": firebase_service.get_document("scene_breakdowns", id),
        "storyboard": firebase_service.get_document("storyboards", id),
        "sound_design": firebase_service.get_document("sound_designs", id),
        "production_plan": firebase_service.get_document("production_plans", id)
    }
    
    return success_response(compiled_data, "Project detail and module assets loaded.")

@project_bp.route("/project/<id>", methods=["DELETE"])
@login_required
def delete_project(id):
    """Deletes a project and all associated pre-production module documents."""
    user_id = request.current_user.get("uid")
    project = firebase_service.get_document("projects", id)
    
    if not project:
        return error_response("Project not found.", 404)
        
    if project.get("user_id") != user_id:
        return error_response("Access denied. You do not own this project.", 403)
        
    # Delete main project document
    firebase_service.delete_document("projects", id)
    
    # Cascade delete sub-documents (keys are identical to project_id in our database model)
    sub_collections = [
        "story_analysis",
        "narrative_structures",
        "screenplays",
        "characters",
        "scene_breakdowns",
        "storyboards",
        "sound_designs",
        "production_plans"
    ]
    for coll in sub_collections:
        firebase_service.delete_document(coll, id)
        
    return success_response(None, "Project and all pre-production data deleted successfully.")
