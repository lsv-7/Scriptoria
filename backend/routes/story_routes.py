import datetime
from flask import Blueprint, request
from backend.routes.auth_routes import login_required
from backend.services.firebase_service import firebase_service
from backend.services.gemini_service import gemini_service
from backend.utils.helpers import success_response, error_response

story_bp = Blueprint("story", __name__)

@story_bp.route("/generate-story-analysis", methods=["POST"])
@login_required
def generate_story_analysis():
    """Generates Story Analysis (Genre Analysis, Theme, Logline, Synopsis, Audience, Tagline) via Gemini."""
    data = request.get_json() or {}
    project_id = data.get("project_id")
    
    if not project_id:
        return error_response("Field 'project_id' is required.", 400)
        
    project = firebase_service.get_document("projects", project_id)
    if not project:
        return error_response("Project not found.", 404)
        
    # Security check: verify owner
    if project.get("user_id") != request.current_user.get("uid"):
        return error_response("Access denied.", 403)
        
    story_idea = project.get("story_idea")
    genre = project.get("genre")
    target_audience = project.get("target_audience")
    
    # Generate analysis
    analysis_data = gemini_service.generate_story_analysis(story_idea, genre, target_audience)
    if not analysis_data or "error" in analysis_data:
        return error_response("Failed to generate story analysis from Gemini.", 500, details=analysis_data)
        
    # Append project details and timestamp
    analysis_data["project_id"] = project_id
    analysis_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    # Store in Firestore (with project_id as document key)
    firebase_service.set_document("story_analysis", project_id, analysis_data)
    
    return success_response(analysis_data, "Story analysis generated and saved successfully.")

@story_bp.route("/generate-structure", methods=["POST"])
@login_required
def generate_structure():
    """Generates Narrative Structure (Act 1, 2, 3) via Gemini."""
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
    
    # Generate narrative structure
    structure_data = gemini_service.generate_narrative_structure(story_idea, genre)
    if not structure_data or "error" in structure_data:
        return error_response("Failed to generate narrative structure from Gemini.", 500, details=structure_data)
        
    structure_data["project_id"] = project_id
    structure_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("narrative_structures", project_id, structure_data)
    
    return success_response(structure_data, "Narrative structure generated and saved successfully.")
