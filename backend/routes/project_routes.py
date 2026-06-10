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
    Payload: { project_name, genre, target_audience, story_idea, duration_length }
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
        "duration_length": data.get("duration_length").strip(),
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
        "production_plan": firebase_service.get_document("production_plans", id),
        "budget_plan": firebase_service.get_document("budget_plans", id)
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
        "production_plans",
        "budget_plans"
    ]
    for coll in sub_collections:
        firebase_service.delete_document(coll, id)
        
    return success_response(None, "Project and all pre-production data deleted successfully.")

@project_bp.route("/project/<id>/generate-all", methods=["POST"])
@login_required
def generate_all_preproduction(id):
    """
    Generates all 9 pre-production modules in sequential dependency stages.
    Stage 1: Story Analysis (Insights) first, then Characters using refined context.
    Stage 2: Narrative Structure, Scene Breakdown (Parallel using refined context).
    Stage 3: Screenplay, Storyboard, Sound Design, Production Plan, Budget Plan (Parallel using refined context).
    """
    user_id = request.current_user.get("uid")
    project = firebase_service.get_document("projects", id)
    if not project:
        return error_response("Project not found.", 404)
        
    if project.get("user_id") != user_id:
        return error_response("Access denied.", 403)
        
    story_idea = project.get("story_idea")
    genre = project.get("genre")
    target_audience = project.get("target_audience")
    duration_length = project.get("duration_length", "Short Film")
    
    from backend.services.gemini_service import gemini_service
    from backend.services.granite_service import granite_service
    from concurrent.futures import ThreadPoolExecutor
    
    # ----------------------------------------------------
    # STAGE 1: Generate Story Analysis First
    # ----------------------------------------------------
    analysis_res = gemini_service.generate_story_analysis(story_idea, genre, target_audience, duration_length)
    if not analysis_res or "error" in analysis_res:
        analysis_res = {
            "genre_analysis": "The story operates as a classic " + genre + ".",
            "theme": "The power of cooperation and compromise.",
            "logline": "A project based on " + story_idea,
            "synopsis": "A project based on " + story_idea,
            "audience_insights": "General audience appeal.",
            "tagline": "A bold dream."
        }
    analysis_res["project_id"] = id
    analysis_res["created_at"] = datetime.datetime.utcnow().isoformat()
    firebase_service.set_document("story_analysis", id, analysis_res)
    
    # Format refined context from Story Insights
    def format_val_str(val):
        if not val:
            return ""
        if isinstance(val, dict):
            return " ".join([f"{k.replace('_', ' ').title()}: {format_val_str(v)}" for k, v in val.items()])
        if isinstance(val, list):
            return " ".join([format_val_str(item) for item in val])
        return str(val)
        
    refined_context = f"Pitch: {story_idea}\nLogline: {format_val_str(analysis_res.get('logline'))}\nSynopsis: {format_val_str(analysis_res.get('synopsis'))}\nTheme: {format_val_str(analysis_res.get('theme'))}"
    
    # ----------------------------------------------------
    # STAGE 1.5: Generate Characters (using refined_context)
    # ----------------------------------------------------
    chars_doc = gemini_service.generate_characters(refined_context, genre, project_id=id)
    if not chars_doc or "error" in chars_doc or "characters" not in chars_doc:
        chars_doc = {
            "characters": [
                {
                    "name": "Rohan",
                    "age": "27",
                    "backstory": "A passionate filmmaker eager to tell a story.",
                    "personality": "Determined, creative.",
                    "goals": "To complete his project.",
                    "strengths": "Vision",
                    "weaknesses": "Impatient",
                    "arc": "Learns to plan."
                }
            ]
        }
    chars_doc["project_id"] = id
    chars_doc["created_at"] = datetime.datetime.utcnow().isoformat()
    firebase_service.set_document("characters", id, chars_doc)
    characters_list = chars_doc.get("characters", [])
    
    # ----------------------------------------------------
    # STAGE 2: Narrative Structure, Scene Breakdown (Parallel using refined_context)
    # ----------------------------------------------------
    structure_res = None
    scenes_res = None
    
    def run_narrative_structure():
        nonlocal structure_res
        res = gemini_service.generate_narrative_structure(refined_context, genre, duration_length, characters_list, project_id=id)
        if res and "error" not in res:
            res["project_id"] = id
            res["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("narrative_structures", id, res)
            structure_res = res
            
    def run_scene_breakdown():
        nonlocal scenes_res
        res = gemini_service.generate_scenes(refined_context, genre, duration_length, characters_list, project_id=id)
        if not res or "error" in res or "scenes" not in res:
            res = {
                "scenes": [
                    {
                        "scene_number": 1,
                        "location": "INT. APARTMENT LIVING ROOM - DAY",
                        "characters": ", ".join([c.get("name", "") for c in characters_list]),
                        "objective": "Introduction and setup of the story goals",
                        "duration": "3 mins"
                    }
                ]
            }
        res["project_id"] = id
        res["created_at"] = datetime.datetime.utcnow().isoformat()
        firebase_service.set_document("scene_breakdowns", id, res)
        scenes_res = res

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_narrative_structure)
        f2 = executor.submit(run_scene_breakdown)
    
    # Wait for futures and propagate exceptions if any occurred
    f1.result()
    f2.result()
        
    scenes_list = scenes_res.get("scenes", []) if scenes_res else []
    
    # ----------------------------------------------------
    # STAGE 3: Screenplay, Storyboard, Sound Design, Production Plan, Budget Plan (Parallel using refined_context)
    # ----------------------------------------------------
    def run_screenplay():
        scene_scripts = {}
        def gen_scene(scene_item):
            s_num = scene_item.get("scene_number", 1)
            text = granite_service.generate_scene_script(
                refined_context, genre, characters_list, duration_length, scene_item, scenes_list, project_id=id
            )
            return s_num, text
            
        with ThreadPoolExecutor(max_workers=5) as inner_exec:
            results = list(inner_exec.map(gen_scene, scenes_list))
            
        for s_num, text in results:
            if not text or "error" in text:
                from backend.utils.story_generator import generate_mock_scene_script
                scene_item = next((s for s in scenes_list if s.get("scene_number") == s_num), {})
                text = generate_mock_scene_script(
                    refined_context, genre, s_num,
                    scene_item.get("location", "INT. SCENE - DAY"),
                    scene_item.get("characters", "Characters"),
                    scene_item.get("objective", "Objective"),
                    scene_item.get("duration", "3 mins"),
                    characters_list
                )
            scene_scripts[str(s_num)] = text
                
        compiled_text = ""
        sorted_scene_keys = sorted(scene_scripts.keys(), key=int)
        for k in sorted_scene_keys:
            if compiled_text:
                compiled_text += "\n\n"
            compiled_text += screenplay_text_formatted(scene_scripts[k])
            
        screenplay_data = {
            "project_id": id,
            "screenplay_text": compiled_text,
            "scene_scripts": scene_scripts,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        firebase_service.set_document("screenplays", id, screenplay_data)

    def screenplay_text_formatted(text):
        # Helper to ensure formatting consistency
        return text

    def run_storyboard():
        res = gemini_service.generate_storyboard(refined_context, scenes_list, project_id=id)
        if not res or "error" in res:
            res = gemini_service._mock_storyboard(refined_context, scenes_list)
            
        storyboards = res.get("storyboards", [])
        if not isinstance(storyboards, list):
            storyboards = []
            
        reconciled_storyboards = []
        angles = ["Wide shot", "Close-up", "Low-angle medium shot", "Establishing overhead shot", "Two-shot tracking"]
        lightings = ["Low-key dramatic lighting", "Warm morning sunlight", "Golden hour backlight", "Cozy interior light", "Soft lamp lighting"]
        moods = ["Suspenseful", "Heartwarming", "Energetic", "Tense", "Joyful"]
        
        sb_map = {}
        for sb in storyboards:
            if isinstance(sb, dict) and sb.get("scene_number") is not None:
                try:
                    sb_map[int(sb.get("scene_number"))] = sb
                except ValueError:
                    pass
                    
        for i, scene in enumerate(scenes_list):
            num = scene.get("scene_number", i + 1)
            if num in sb_map:
                sb_card = sb_map[num]
                sb_card["scene_number"] = num
                if not sb_card.get("prompt"):
                    loc = scene.get("location", "INT. SCENE - DAY")
                    chars = scene.get("characters", "Characters")
                    angle = sb_card.get("camera_angle") or angles[i % len(angles)]
                    lighting = sb_card.get("lighting") or lightings[i % len(lightings)]
                    sb_card["prompt"] = f"Cinematic storyboard frame, {loc.lower()}, featuring {chars.lower()}, {angle.lower()}, {lighting.lower()}, film concept art style, highly detailed composition."
                if not sb_card.get("camera_angle"):
                    sb_card["camera_angle"] = angles[i % len(angles)]
                if not sb_card.get("lighting"):
                    sb_card["lighting"] = lightings[i % len(lightings)]
                if not sb_card.get("mood"):
                    sb_card["mood"] = moods[i % len(moods)]
                reconciled_storyboards.append(sb_card)
            else:
                loc = scene.get("location", "INT. SCENE - DAY")
                chars = scene.get("characters", "Characters")
                angle = angles[i % len(angles)]
                lighting = lightings[i % len(lightings)]
                mood = moods[i % len(moods)]
                prompt = f"Cinematic storyboard frame, {loc.lower()}, featuring {chars.lower()}, {angle.lower()}, {lighting.lower()}, film concept art style, highly detailed composition."
                reconciled_storyboards.append({
                    "scene_number": num,
                    "prompt": prompt,
                    "camera_angle": angle,
                    "lighting": lighting,
                    "mood": mood
                })
                
        res["storyboards"] = reconciled_storyboards
        res["project_id"] = id
        res["created_at"] = datetime.datetime.utcnow().isoformat()
        firebase_service.set_document("storyboards", id, res)
            
    def run_sound_design():
        res = granite_service.generate_sound_design(refined_context, genre, characters_list, scenes_list, project_id=id)
        if res and "error" not in res:
            res["project_id"] = id
            res["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("sound_designs", id, res)
            
    def run_production_plan():
        res = granite_service.generate_production_plan(refined_context, genre, characters_list, scenes_list, project_id=id)
        if res and "error" not in res:
            res["project_id"] = id
            res["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("production_plans", id, res)
            
    def run_budget_plan():
        res = granite_service.generate_budget_plan(refined_context, genre, characters_list, scenes_list, project_id=id)
        if res and "error" not in res:
            res["project_id"] = id
            res["created_at"] = datetime.datetime.utcnow().isoformat()
            firebase_service.set_document("budget_plans", id, res)

    with ThreadPoolExecutor(max_workers=5) as executor:
        fs = [
            executor.submit(run_screenplay),
            executor.submit(run_storyboard),
            executor.submit(run_sound_design),
            executor.submit(run_production_plan),
            executor.submit(run_budget_plan)
        ]
        
    for f in fs:
        f.result()
        
    return success_response(None, "All pre-production assets generated successfully.")
