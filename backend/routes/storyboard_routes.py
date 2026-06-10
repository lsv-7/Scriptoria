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
        scenes_doc = gemini_service.generate_scenes(project.get("story_idea"), project.get("genre"), project.get("duration_length", "Short Film"))
        if not scenes_doc or "scenes" not in scenes_doc:
            return error_response("Failed to generate required scene breakdown for storyboard.", 500)
            
        scenes_doc["project_id"] = project_id
        scenes_doc["created_at"] = datetime.datetime.utcnow().isoformat()
        firebase_service.set_document("scene_breakdowns", project_id, scenes_doc)
        
    scenes_list = scenes_doc["scenes"]
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

    # Generate storyboard prompts
    storyboard_data = gemini_service.generate_storyboard(story_idea, scenes_list)
    if not storyboard_data or "error" in storyboard_data:
        return error_response("Failed to generate storyboard cards from Gemini.", 500, details=storyboard_data)
        
    # Reconcile storyboard cards with scenes_list to guarantee identical counts
    storyboards = storyboard_data.get("storyboards", [])
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
            
    storyboard_data["storyboards"] = reconciled_storyboards
    storyboard_data["project_id"] = project_id
    storyboard_data["created_at"] = datetime.datetime.utcnow().isoformat()
    
    firebase_service.set_document("storyboards", project_id, storyboard_data)
    
    return success_response(storyboard_data, "Storyboard frame planner generated and saved successfully.")
