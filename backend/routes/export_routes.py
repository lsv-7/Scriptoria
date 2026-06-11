from flask import Blueprint, request, Response
from .auth_routes import login_required
from ..services.firebase_service import firebase_service
from ..services.export_service import export_service
from ..utils.helpers import error_response

export_bp = Blueprint("export", __name__)

@export_bp.route("/export-project", methods=["POST"])
@login_required
def export_project():
    """
    Assembles all generated pre-production assets and streams a PDF, DOCX, or TXT file.
    Payload: { project_id, format } where format is 'pdf', 'docx', or 'txt'.
    """
    data = request.get_json() or {}
    project_id = data.get("project_id")
    export_format = data.get("format", "pdf").lower()
    
    if not project_id:
        return error_response("Field 'project_id' is required.", 400)
        
    if export_format not in ["pdf", "docx", "txt"]:
        return error_response("Invalid format. Must be 'pdf', 'docx', or 'txt'.", 400)
        
    # Get project metadata
    project = firebase_service.get_document("projects", project_id)
    if not project:
        return error_response("Project not found.", 404)
        
    # Security check: owner verification
    if project.get("user_id") != request.current_user.get("uid"):
        return error_response("Access denied.", 403)
        
    # Gather all sub-documents
    compiled_data = {
        "story_analysis": firebase_service.get_document("story_analysis", project_id) or {},
        "narrative_structure": firebase_service.get_document("narrative_structures", project_id) or {},
        "screenplay": firebase_service.get_document("screenplays", project_id) or {},
        "characters": firebase_service.get_document("characters", project_id) or {},
        "scene_breakdown": firebase_service.get_document("scene_breakdowns", project_id) or {},
        "storyboard": firebase_service.get_document("storyboards", project_id) or {},
        "sound_design": firebase_service.get_document("sound_designs", project_id) or {},
        "production_plan": firebase_service.get_document("production_plans", project_id) or {}
    }
    
    project_name = project.get("project_name", "blueprint").replace(" ", "_")
    
    try:
        if export_format == "pdf":
            file_bytes = export_service.generate_pdf(project, compiled_data)
            mimetype = "application/pdf"
            filename = f"{project_name}_preprod_blueprint.pdf"
            
        elif export_format == "docx":
            file_bytes = export_service.generate_docx(project, compiled_data)
            mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{project_name}_preprod_blueprint.docx"
            
        else: # txt
            file_bytes = export_service.generate_txt(project, compiled_data)
            mimetype = "text/plain"
            filename = f"{project_name}_preprod_blueprint.txt"
            
        return Response(
            file_bytes,
            mimetype=mimetype,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        print(f"Error compiling export documents: {e}")
        return error_response(f"Failed to generate export file: {str(e)}", 500)
