import os
import json
import google.generativeai as genai
from backend.config import Config
from backend.utils.prompts import (
    GLOBAL_RULES,
    GENRE_GUIDELINES,
    SCREENPLAY_PROMPT,
    SOUND_DESIGN_PROMPT,
    PRODUCTION_PLAN_PROMPT,
    BUDGET_PLAN_PROMPT
)
from backend.utils.helpers import clean_json_response, clean_prose_data, parse_combined_story_idea
from backend.utils.story_generator import generate_mock_story

# Global/module level variables for rate limit cooldowns
GROQ_COOLDOWN_UNTIL = 0.0
GEMINI_COOLDOWN_UNTIL = 0.0
GEMINI_QUOTA_EXCEEDED = False

class GraniteService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.groq_key = Config.GROQ_API_KEY
        self.initialized = bool(self.api_key)
        if self.initialized:
            try:
                genai.configure(api_key=self.api_key)
            except Exception:
                pass
            print(">>> Google Gemini API configured successfully (routed from GraniteService).")
        else:
            print(">>> Gemini API key not found in GraniteService. Using local mock generator.")

        if self.groq_key:
            print(">>> Groq API client configured successfully in GraniteService.")

    def _generate_groq(self, prompt, max_tokens=1024):
        """Internal helper to call Groq API when GROQ_API_KEY is configured with rate-limit cooldown."""
        global GROQ_COOLDOWN_UNTIL
        import time
        
        if not self.groq_key:
            return None
            
        if time.time() < GROQ_COOLDOWN_UNTIL:
            print(">>> GraniteService: Groq API rate limit cooldown active. Skipping call.")
            return None
            
        import requests
        
        # List of models to try in order of preference
        models = [
            os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant"),
            "llama-3.3-70b-versatile"
        ]
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        
        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.0,
                "max_tokens": max_tokens
            }
            
            try:
                print(f">>> GraniteService trying Groq API with model: {model}...")
                response = requests.post(url, json=payload, headers=headers, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    content = res_json["choices"][0]["message"]["content"]
                    print(f">>> GraniteService Groq API call succeeded using model {model}.")
                    return content
                elif response.status_code == 429:
                    print(f">>> GraniteService: Groq API returned 429 rate limit error for model {model}. Trying fallback model...")
                    continue
                else:
                    print(f">>> GraniteService Groq API returned error {response.status_code} for model {model}: {response.text}")
                    # If unauthorized or forbidden, stop trying other models
                    if response.status_code in [401, 403]:
                        break
            except Exception as e:
                print(f">>> GraniteService Exception calling Groq API with model {model}: {e}")
                
        # If all models failed, set cooldown
        print(">>> GraniteService: All Groq models failed. Activating 30s cooldown.")
        GROQ_COOLDOWN_UNTIL = time.time() + 30.0
        return None

    def _generate(self, prompt, max_tokens=1024):
        """Internal helper to call Gemini API with rate-limit cooldown and fail-fast."""
        global GEMINI_QUOTA_EXCEEDED, GEMINI_COOLDOWN_UNTIL
        import time
        
        if GEMINI_QUOTA_EXCEEDED:
            print(">>> Gemini API quota previously exceeded in GraniteService. Skipping call.")
            return None
            
        if time.time() < GEMINI_COOLDOWN_UNTIL:
            print(">>> GraniteService: Gemini API rate limit cooldown active. Skipping call.")
            return None
            
        if not self.initialized:
            return None
            
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            generation_config = genai.types.GenerationConfig(max_output_tokens=max_tokens, temperature=0.0)
            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "limit" in err_str.lower():
                if any(x in err_str.lower() for x in ["billing", "credits", "plan", "free tier"]):
                    print(">>> Gemini API billing quota block detected in GraniteService. Disabling Gemini.")
                    GEMINI_QUOTA_EXCEEDED = True
                else:
                    print(">>> GraniteService: Gemini API rate limit hit (429). Activating cooldown for 30 seconds.")
                    GEMINI_COOLDOWN_UNTIL = time.time() + 30.0
            else:
                print(f"Error calling Gemini API in GraniteService: {e}")
            return None

    def generate_screenplay(self, story_idea, genre, characters_list, duration_length="Short Film", project_id=None):
        """Generates a professional screenplay script."""
        dummy_scene = {
            "scene_number": 1,
            "location": "INT. APARTMENT - DAY",
            "characters": ", ".join([c.get("name", "") if isinstance(c, dict) else str(c) for c in characters_list]) if characters_list else "Characters",
            "objective": "Introduction of characters and goals.",
            "duration": "2 mins"
        }
        return self.generate_scene_script(story_idea, genre, characters_list, duration_length, dummy_scene, [dummy_scene], project_id)

    def generate_sound_design(self, story_idea, genre, characters_list=None, scenes_list=None, project_id=None):
        """Generates background music, ambience, foley, vocal treatment, sound notes."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        if not characters_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                chars_doc = firebase_service.get_document("characters", project_id)
                if chars_doc and "characters" in chars_doc:
                    characters_list = chars_doc["characters"]
            except Exception:
                pass
                
        if not scenes_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                scenes_doc = firebase_service.get_document("scene_breakdowns", project_id)
                if scenes_doc and "scenes" in scenes_doc:
                    scenes_list = scenes_doc["scenes"]
            except Exception:
                pass
                
        chars_json = json.dumps({"characters": characters_list or []}, indent=2)
        scenes_json = json.dumps({"scenes": scenes_list or []}, indent=2)
        
        formatted_prompt = SOUND_DESIGN_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_analysis=parsed_idea["story_analysis"],
            characters_json=chars_json,
            scenes_json=scenes_json
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1024)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt, max_tokens=1024)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "background_music" in parsed:
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_sound_design(story_idea, genre, characters_list))

    def generate_production_plan(self, story_idea, genre, characters_list=None, scenes_list=None, project_id=None):
        """Generates shooting locations, props, equipment, crew, and estimated shoot days."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        if not characters_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                chars_doc = firebase_service.get_document("characters", project_id)
                if chars_doc and "characters" in chars_doc:
                    characters_list = chars_doc["characters"]
            except Exception:
                pass
                
        if not scenes_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                scenes_doc = firebase_service.get_document("scene_breakdowns", project_id)
                if scenes_doc and "scenes" in scenes_doc:
                    scenes_list = scenes_doc["scenes"]
            except Exception:
                pass
                
        chars_json = json.dumps({"characters": characters_list or []}, indent=2)
        scenes_json = json.dumps({"scenes": scenes_list or []}, indent=2)
        
        formatted_prompt = PRODUCTION_PLAN_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_idea=parsed_idea["pitch"],
            characters_json=chars_json,
            scenes_json=scenes_json
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1024)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt, max_tokens=1024)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "shooting_locations" in parsed:
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_production_plan(story_idea, genre, characters_list))

    def generate_budget_plan(self, story_idea, genre, characters_list=None, scenes_list=None, project_id=None):
        """Generates dynamic pre-production, production, and post-production budget estimates."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        if not characters_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                chars_doc = firebase_service.get_document("characters", project_id)
                if chars_doc and "characters" in chars_doc:
                    characters_list = chars_doc["characters"]
            except Exception:
                pass
                
        if not scenes_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                scenes_doc = firebase_service.get_document("scene_breakdowns", project_id)
                if scenes_doc and "scenes" in scenes_doc:
                    scenes_list = scenes_doc["scenes"]
            except Exception:
                pass
                
        chars_json = json.dumps({"characters": characters_list or []}, indent=2)
        scenes_json = json.dumps({"scenes": scenes_list or []}, indent=2)
        
        formatted_prompt = BUDGET_PLAN_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_analysis=parsed_idea["story_analysis"],
            characters_json=chars_json,
            scenes_json=scenes_json
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1024)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt, max_tokens=1024)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "pre_production" in parsed:
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_budget_plan(story_idea, genre, characters_list))

    def generate_scene_script(self, story_idea, genre, characters_list, duration_length, scene, all_scenes, project_id=None):
        """Generates a professional screenplay script for a specific scene."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        # 1. narrative_structure
        narrative_structure_str = ""
        if project_id:
            try:
                from backend.services.firebase_service import firebase_service
                ns_doc = firebase_service.get_document("narrative_structures", project_id)
                if ns_doc:
                    ns_clean = {k: v for k, v in ns_doc.items() if k not in ["project_id", "created_at", "id"]}
                    narrative_structure_str = json.dumps(ns_clean, indent=2)
            except Exception:
                pass
        if not narrative_structure_str:
            narrative_structure_str = "Three-act structure following the story guidelines."
            
        # 2. characters_json
        if not characters_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                chars_doc = firebase_service.get_document("characters", project_id)
                if chars_doc and "characters" in chars_doc:
                    characters_list = chars_doc["characters"]
            except Exception:
                pass
        chars_json = json.dumps({"characters": characters_list or []}, indent=2)
        
        # 3. scene_breakdown
        scene_breakdown_str = json.dumps({"scenes": all_scenes or []}, indent=2)
        
        # 4. previous_scene
        previous_scene_str = ""
        scene_number = scene.get("scene_number", 1)
        if scene_number > 1 and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                screenplay_doc = firebase_service.get_document("screenplays", project_id)
                if screenplay_doc and "scene_scripts" in screenplay_doc:
                    prev_scene_text = screenplay_doc["scene_scripts"].get(str(scene_number - 1))
                    if prev_scene_text:
                        previous_scene_str = prev_scene_text.strip()
            except Exception:
                pass
                
        if not previous_scene_str:
            prev_scene = next((s for s in all_scenes if int(s.get("scene_number", 0)) == scene_number - 1), None)
            if prev_scene:
                previous_scene_str = f"Scene {scene_number - 1}: {prev_scene.get('location')} - Objective: {prev_scene.get('objective')}."
            else:
                previous_scene_str = "No previous scene (this is the opening scene)."
                
        # 5. current_scene
        current_scene_str = json.dumps({
            "scene_number": scene_number,
            "location": scene.get("location", "INT. SCENE - DAY"),
            "characters": scene.get("characters", ""),
            "objective": scene.get("objective", ""),
            "duration": scene.get("duration", "2 mins")
        }, indent=2)
        
        # 6. genre_guidance
        genre_guidance = GENRE_GUIDELINES.get(genre, "")
        
        formatted_prompt = SCREENPLAY_PROMPT.format(
            story_analysis=parsed_idea["story_analysis"],
            narrative_structure=narrative_structure_str,
            characters_json=chars_json,
            scene_breakdown=scene_breakdown_str,
            previous_scene=previous_scene_str,
            current_scene=current_scene_str,
            genre_guidance=genre_guidance
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1500)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt, max_tokens=1500)
            
        if response_text:
            return response_text.strip()
            
        # Mock Fallback
        from backend.utils.story_generator import generate_mock_scene_script
        return generate_mock_scene_script(
            story_idea=story_idea,
            genre=genre,
            scene_number=scene_number,
            location=scene.get("location", "INT. SCENE - DAY"),
            scene_characters=scene.get("characters", ""),
            objective=scene.get("objective", ""),
            duration=scene.get("duration", "2 mins"),
            characters_list=characters_list
        )

    # --- MOCK GENERATION FALLBACKS ---
    def _mock_screenplay(self, story_idea, genre, characters_list):
        return generate_mock_story(
            story_idea=story_idea,
            genre=genre,
            characters_list=characters_list
        )["screenplay"]

    def _mock_sound_design(self, story_idea, genre, characters_list=None):
        return generate_mock_story(
            story_idea=story_idea,
            genre=genre,
            characters_list=characters_list
        )["sound_design"]

    def _mock_production_plan(self, story_idea, genre, characters_list=None):
        return generate_mock_story(
            story_idea=story_idea,
            genre=genre,
            characters_list=characters_list
        )["production_plan"]

    def _mock_budget_plan(self, story_idea, genre, characters_list=None):
        return generate_mock_story(
            story_idea=story_idea,
            genre=genre,
            characters_list=characters_list
        )["budget_plan"]

# Instantiate service singleton
granite_service = GraniteService()
