import datetime
from flask import Blueprint, request
from .auth_routes import login_required
from ..services.firebase_service import firebase_service
from ..services.granite_service import granite_service
from ..utils.helpers import success_response, error_response

screenplay_bp = Blueprint("screenplay", __name__)

@screenplay_bp.route("/generate-screenplay", methods=["POST"])
@login_required
def generate_screenplay():
    """Generates professional screenplay using IBM Granite/Groq AI, scene-by-scene."""
    data = request.get_json() or {}
    project_id = data.get("project_id")
    scene_number = data.get("scene_number")  # Optional: generate specific scene
    
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

    # 1. Check or auto-generate scene breakdown
    scene_doc = firebase_service.get_document("scene_breakdowns", project_id)
    if not scene_doc or "scenes" not in scene_doc or not scene_doc["scenes"]:
        from backend.services.gemini_service import gemini_service
        scenes_data = gemini_service.generate_scenes(story_idea, genre, duration_length, project_id=project_id)
        if not scenes_data or "error" in scenes_data or not scenes_data.get("scenes"):
            # Create a simple default list of scenes if generation fails
            scenes_data = {
                "scenes": [
                    {
                        "scene_number": 1,
                        "location": "INT. APARTMENT LIVING ROOM - DAY",
                        "characters": "Main Characters",
                        "objective": "Introduction and setup of the story goals",
                        "duration": "3 mins"
                    }
                ]
            }
        scenes_data["project_id"] = project_id
        scenes_data["created_at"] = datetime.datetime.utcnow().isoformat()
        firebase_service.set_document("scene_breakdowns", project_id, scenes_data)
        scene_doc = scenes_data

    scenes = scene_doc.get("scenes", [])

    # 2. Retrieve or auto-generate character profiles
    characters_doc = firebase_service.get_document("characters", project_id)
    if not characters_doc or "characters" not in characters_doc or not characters_doc["characters"]:
        from backend.services.gemini_service import gemini_service
        characters_doc = gemini_service.generate_characters(story_idea, genre, project_id=project_id)
        if characters_doc and "characters" in characters_doc:
            characters_doc["project_id"] = project_id
            characters_doc["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("characters", project_id, characters_doc)
            
    characters_list = []
    if characters_doc and "characters" in characters_doc:
        characters_list = characters_doc["characters"]
        
    # 3. Retrieve existing screenplay document or initialize
    screenplay_doc = firebase_service.get_document("screenplays", project_id) or {}
    scene_scripts = screenplay_doc.get("scene_scripts", {})
    if not isinstance(scene_scripts, dict):
        scene_scripts = {}

    # 4. Generate scripts
    if scene_number is not None:
        # Generate specific scene
        try:
            s_num_int = int(scene_number)
        except ValueError:
            return error_response("Invalid 'scene_number' format. Must be an integer.", 400)
            
        target_scene = None
        for s in scenes:
            s_num = s.get("scene_number")
            if s_num is not None:
                try:
                    if int(s_num) == s_num_int:
                        target_scene = s
                        break
                except (ValueError, TypeError):
                    pass

        if not target_scene:
            return error_response(f"Scene number {s_num_int} not found in the project's scene breakdown.", 404)
            
        scene_text = granite_service.generate_scene_script(
            story_idea, genre, characters_list, duration_length, target_scene, scenes, project_id=project_id
        )
        if not scene_text or "error" in scene_text.lower():
            from backend.utils.story_generator import generate_mock_scene_script
            scene_text = generate_mock_scene_script(
                story_idea, genre, s_num_int,
                target_scene.get("location", "INT. SCENE - DAY"),
                target_scene.get("characters", "Characters"),
                target_scene.get("objective", "Objective"),
                target_scene.get("duration", "3 mins"),
                characters_list
            )
            
        scene_scripts[str(s_num_int)] = scene_text
    else:
        # Generate all scenes in parallel
        from concurrent.futures import ThreadPoolExecutor
        
        def gen_scene(scene_item):
            s_num = scene_item.get("scene_number", 1)
            text = granite_service.generate_scene_script(
                story_idea, genre, characters_list, duration_length, scene_item, scenes, project_id=project_id
            )
            return s_num, text
            
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(gen_scene, scenes))
            
        for s_num, text in results:
            if not text or "error" in text.lower():
                from backend.utils.story_generator import generate_mock_scene_script
                scene_item = next((s for s in scenes if s.get("scene_number") == s_num), {})
                text = generate_mock_scene_script(
                    story_idea, genre, s_num,
                    scene_item.get("location", "INT. SCENE - DAY"),
                    scene_item.get("characters", "Characters"),
                    scene_item.get("objective", "Objective"),
                    scene_item.get("duration", "3 mins"),
                    characters_list
                )
            scene_scripts[str(s_num)] = text

    # 5. Compile full screenplay text for compatibility and export
    compiled_text = ""
    sorted_scene_keys = sorted(scene_scripts.keys(), key=int)
    for k in sorted_scene_keys:
        if compiled_text:
            compiled_text += "\n\n"
        compiled_text += scene_scripts[k]

    screenplay_data = {
        "project_id": project_id,
        "screenplay_text": compiled_text,
        "scene_scripts": scene_scripts,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    firebase_service.set_document("screenplays", project_id, screenplay_data)
    
    return success_response(screenplay_data, "Screenplay script generated and saved successfully.")

