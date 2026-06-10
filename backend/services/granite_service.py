import os
import json
import google.generativeai as genai
from backend.config import Config
from backend.utils.prompts import (
    SCREENPLAY_PROMPT,
    SOUND_DESIGN_PROMPT,
    PRODUCTION_PLAN_PROMPT,
    BUDGET_PLAN_PROMPT
)
from backend.utils.helpers import clean_json_response, clean_prose_data
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
            os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "llama-3.1-8b-instant"
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
                    print(f">>> GraniteService: Groq API returned 429 rate limit error for model {model}. Activating 30s cooldown.")
                    GROQ_COOLDOWN_UNTIL = time.time() + 30.0
                    break
                else:
                    print(f">>> GraniteService Groq API returned error {response.status_code} for model {model}: {response.text}")
                    # If unauthorized or forbidden, stop trying other models
                    if response.status_code in [401, 403]:
                        break
            except Exception as e:
                print(f">>> GraniteService Exception calling Groq API with model {model}: {e}")
                
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

    def generate_screenplay(self, story_idea, genre, characters_list, duration_length="Short Film"):
        """Generates a professional screenplay script."""
        chars_str = ", ".join([c.get("name", "") for c in characters_list]) if isinstance(characters_list, list) else str(characters_list)
        formatted_prompt = SCREENPLAY_PROMPT.format(
            story_idea=story_idea,
            genre=genre,
            characters_list=chars_str,
            duration_length=duration_length
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1500)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt, max_tokens=1500)
            
        if response_text:
            return response_text.strip()
            
        # Mock Fallback
        return self._mock_screenplay(story_idea, genre, characters_list)

    def generate_sound_design(self, story_idea, genre, characters_list=None, scenes_list=None):
        """Generates background music, ambience, foley, vocal treatment, sound notes."""
        chars_str = ", ".join([c.get("name", "") if isinstance(c, dict) else str(c) for c in characters_list]) if isinstance(characters_list, list) else str(characters_list or "as described in the story")
        scenes_str = ""
        if isinstance(scenes_list, list):
            scenes_str = "\n".join([f"Scene {s.get('scene_number', i+1)}: {s.get('location', 'INT. SCENE - DAY')} - Characters: {s.get('characters', '')} - Objective: {s.get('objective', '')}" for i, s in enumerate(scenes_list)])
        else:
            scenes_str = str(scenes_list or "as described in the story")

        formatted_prompt = SOUND_DESIGN_PROMPT.format(
            story_idea=story_idea,
            genre=genre,
            characters_list=chars_str,
            scenes_list=scenes_str
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

    def generate_production_plan(self, story_idea, genre, characters_list=None, scenes_list=None):
        """Generates shooting locations, props, equipment, crew, and estimated shoot days."""
        chars_str = ", ".join([c.get("name", "") if isinstance(c, dict) else str(c) for c in characters_list]) if isinstance(characters_list, list) else str(characters_list or "as described in the story")
        scenes_str = ""
        if isinstance(scenes_list, list):
            scenes_str = "\n".join([f"Scene {s.get('scene_number', i+1)}: {s.get('location', 'INT. SCENE - DAY')} - Characters: {s.get('characters', '')} - Objective: {s.get('objective', '')}" for i, s in enumerate(scenes_list)])
        else:
            scenes_str = str(scenes_list or "as described in the story")

        formatted_prompt = PRODUCTION_PLAN_PROMPT.format(
            story_idea=story_idea,
            genre=genre,
            characters_list=chars_str,
            scenes_list=scenes_str
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

    def generate_budget_plan(self, story_idea, genre, characters_list=None, scenes_list=None):
        """Generates dynamic pre-production, production, and post-production budget estimates."""
        chars_str = ", ".join([c.get("name", "") if isinstance(c, dict) else str(c) for c in characters_list]) if isinstance(characters_list, list) else str(characters_list or "as described in the story")
        scenes_str = ""
        if isinstance(scenes_list, list):
            scenes_str = "\n".join([f"Scene {s.get('scene_number', i+1)}: {s.get('location', 'INT. SCENE - DAY')} - Characters: {s.get('characters', '')} - Objective: {s.get('objective', '')}" for i, s in enumerate(scenes_list)])
        else:
            scenes_str = str(scenes_list or "as described in the story")

        formatted_prompt = BUDGET_PLAN_PROMPT.format(
            story_idea=story_idea,
            genre=genre,
            characters_list=chars_str,
            scenes_list=scenes_str
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

    def generate_scene_script(self, story_idea, genre, characters_list, duration_length, scene, all_scenes):
        """Generates a professional screenplay script for a specific scene."""
        scene_number = scene.get("scene_number", 1)
        location = scene.get("location", "INT. LOCATION - DAY")
        scene_characters = scene.get("characters", "")
        objective = scene.get("objective", "")
        duration = scene.get("duration", "2 mins")
        
        # Build scene breakdown summary for context
        scene_breakdown_summary = ""
        for s in all_scenes:
            scene_breakdown_summary += f"Scene {s.get('scene_number')}: {s.get('location')} - Characters: {s.get('characters')} - Objective: {s.get('objective')}\n"
            
        chars_str = ", ".join([c.get("name", "") for c in characters_list]) if isinstance(characters_list, list) else str(characters_list)
        
        from backend.utils.prompts import GENERATE_SCENE_PROMPT
        formatted_prompt = GENERATE_SCENE_PROMPT.format(
            story_idea=story_idea,
            genre=genre,
            characters_list=chars_str,
            duration_length=duration_length,
            scene_number=scene_number,
            location=location,
            scene_characters=scene_characters,
            objective=objective,
            duration=duration,
            scene_breakdown_summary=scene_breakdown_summary
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
            location=location,
            scene_characters=scene_characters,
            objective=objective,
            duration=duration,
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
