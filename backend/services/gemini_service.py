import os
import json
import random
from backend.config import Config
from backend.utils.prompts import (
    GLOBAL_RULES,
    GENRE_GUIDELINES,
    STORY_ANALYSIS_PROMPT,
    NARRATIVE_STRUCTURE_PROMPT,
    CHARACTER_GENERATOR_PROMPT,
    SCENE_BREAKDOWN_PROMPT,
    STORYBOARD_PROMPT
)
from backend.utils.helpers import clean_json_response, clean_prose_data, parse_combined_story_idea
from backend.utils.story_generator import generate_mock_story

# Try to import google-generativeai. If missing, we fall back to mock generation.
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Global/module level variables for rate limit cooldowns
GROQ_COOLDOWN_UNTIL = 0.0
GEMINI_COOLDOWN_UNTIL = 0.0
GEMINI_QUOTA_EXCEEDED = False

class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.groq_api_key = Config.GROQ_API_KEY
        self.initialized = False
        
        if self.api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
            except Exception as e:
                print(f"Error configuring Gemini API: {e}")
                
        # Initialize Groq models list
        self.groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    def _generate_groq(self, prompt, max_tokens=1024, system_message=None):
        """Internal helper to call Groq API with fallback models and rate-limit cooldown."""
        global GROQ_COOLDOWN_UNTIL
        import time
        
        if not self.groq_api_key:
            return None
            
        if time.time() < GROQ_COOLDOWN_UNTIL:
            print(">>> Groq API rate limit cooldown active. Skipping call to save time.")
            return None
            
        import requests
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        sys_msg = system_message if system_message is not None else "You output JSON strictly as requested. Output only the JSON. No explanations, no markdown formatting blocks."
        
        for model in self.groq_models:
            print(f">>> Trying Groq API with model: {model}...")
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0,
                "max_tokens": max_tokens
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=25)
                if response.status_code == 200:
                    print(f">>> Groq API call succeeded using model {model}.")
                    return response.json()["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    print(f">>> Groq API returned 429 rate limit error for model {model}. Trying fallback model...")
                    continue
                else:
                    print(f">>> Groq API returned error {response.status_code} for model {model}: {response.text}")
                    # If unauthorized or forbidden, stop trying other models
                    if response.status_code in [401, 403]:
                        break
            except Exception as e:
                print(f">>> Exception calling Groq API with model {model}: {e}")
                
        # If all models failed, set cooldown
        print(">>> All Groq models failed. Activating 30s cooldown.")
        GROQ_COOLDOWN_UNTIL = time.time() + 30.0
        return None

    def _generate(self, prompt):
        """Internal helper to call Gemini API with rate-limit cooldown and fail-fast."""
        global GEMINI_QUOTA_EXCEEDED, GEMINI_COOLDOWN_UNTIL
        import time
        
        if GEMINI_QUOTA_EXCEEDED:
            print(">>> Gemini API quota previously exceeded. Skipping call to save time.")
            return None
            
        if time.time() < GEMINI_COOLDOWN_UNTIL:
            print(">>> Gemini API rate limit cooldown active. Skipping call to save time.")
            return None
            
        if not self.initialized:
            return None
            
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            generation_config = genai.types.GenerationConfig(temperature=0.0)
            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "limit" in err_str.lower():
                if any(x in err_str.lower() for x in ["billing", "credits", "plan", "free tier"]):
                    print(">>> Gemini API billing quota block detected. Disabling Gemini for this session.")
                    GEMINI_QUOTA_EXCEEDED = True
                else:
                    print(">>> Gemini API rate limit hit (429). Activating cooldown for 30 seconds.")
                    GEMINI_COOLDOWN_UNTIL = time.time() + 30.0
            else:
                print(f"Error calling Gemini API: {e}")
            return None

    def generate_story_analysis(self, story_idea, genre, target_audience, duration_length="Short Film"):
        """Generates genre analysis, theme, logline, synopsis, audience insights, tagline, tone, rating, comparable_films, festival_potential, streaming_audience_fit."""
        genre_guidance = GENRE_GUIDELINES.get(genre, "")
        formatted_prompt = STORY_ANALYSIS_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_idea=story_idea,
            genre=genre,
            genre_guidance=genre_guidance,
            target_audience=target_audience,
            duration_length=duration_length
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1200)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "genre_analysis" in parsed:
                # Merge defaults for any missing new keys
                defaults = {
                    "tone": "Suspenseful" if genre == "Thriller" else "Dramatic",
                    "rating": "PG-13",
                    "comparable_films": [],
                    "festival_potential": "Strong potential for indie film festivals.",
                    "streaming_audience_fit": "Excellent fit for SVOD streaming platforms."
                }
                for k, v in defaults.items():
                    if k not in parsed:
                        parsed[k] = v
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_story_analysis(story_idea, genre, target_audience, duration_length))

    def generate_narrative_structure(self, story_idea, genre, duration_length="Short Film", characters_list=None, project_id=None):
        """Generates Act 1, 2, 3 narrative structure."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        if not characters_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                chars_doc = firebase_service.get_document("characters", project_id)
                if chars_doc and "characters" in chars_doc:
                    characters_list = chars_doc["characters"]
            except Exception:
                pass
                
        chars_json = json.dumps({"characters": characters_list or []}, indent=2)
        
        formatted_prompt = NARRATIVE_STRUCTURE_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_analysis=parsed_idea["story_analysis"],
            characters_json=chars_json,
            genre=genre,
            duration_length=duration_length
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1200)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "act_1" in parsed:
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_narrative_structure(story_idea, genre, duration_length, characters_list))

    def generate_characters(self, story_idea, genre, project_id=None):
        """Generates 3-4 detailed character profiles."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        formatted_prompt = CHARACTER_GENERATOR_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_analysis=parsed_idea["story_analysis"],
            story_idea=parsed_idea["pitch"],
            genre=genre
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1500)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "characters" in parsed:
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_characters(story_idea, genre))

    def generate_scenes(self, story_idea, genre, duration_length="Short Film", characters_list=None, project_id=None):
        """Generates core scene breakdowns."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        if not characters_list and project_id:
            try:
                from backend.services.firebase_service import firebase_service
                chars_doc = firebase_service.get_document("characters", project_id)
                if chars_doc and "characters" in chars_doc:
                    characters_list = chars_doc["characters"]
            except Exception:
                pass
                
        chars_json = json.dumps({"characters": characters_list or []}, indent=2)
        
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
            
        formatted_prompt = SCENE_BREAKDOWN_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_analysis=parsed_idea["story_analysis"],
            narrative_structure=narrative_structure_str,
            characters_json=chars_json,
            duration_length=duration_length
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1500)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "scenes" in parsed:
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_scenes(story_idea, genre, duration_length, characters_list))

    def generate_storyboard(self, story_idea, scenes_list, project_id=None):
        """Generates camera angle, mood, lighting, and prompt for storyboard frames."""
        parsed_idea = parse_combined_story_idea(story_idea)
        
        characters_list = []
        if project_id:
            try:
                from backend.services.firebase_service import firebase_service
                chars_doc = firebase_service.get_document("characters", project_id)
                if chars_doc and "characters" in chars_doc:
                    characters_list = chars_doc["characters"]
            except Exception:
                pass
        chars_json = json.dumps({"characters": characters_list}, indent=2)
        scenes_json = json.dumps({"scenes": scenes_list}, indent=2)
        
        formatted_prompt = STORYBOARD_PROMPT.format(
            global_rules=GLOBAL_RULES,
            story_idea=parsed_idea["pitch"],
            characters_json=chars_json,
            scenes_json=scenes_json
        )
        
        # 1. Try Groq
        response_text = self._generate_groq(formatted_prompt, max_tokens=1500)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(formatted_prompt)
            
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "storyboards" in parsed:
                return clean_prose_data(parsed)
                
        # Mock Fallback
        return clean_prose_data(self._mock_storyboard(story_idea, scenes_list))

    def chat_with_copilot(self, project_context, history, user_message):
        """Processes copilot chat interactions with project context awareness."""
        # Build prompt
        prompt = f"{project_context}\n\n"
        prompt += "CONVERSATION HISTORY:\n"
        for msg in history:
            role = "User" if msg.get("role") == "user" else "Copilot"
            prompt += f"{role}: {msg.get('content')}\n"
            
        prompt += f"User: {user_message}\n"
        prompt += "Copilot: "
        
        system_message = "You are CineForge Copilot, a master screenwriter and creative film producer. You assist the user with brainstorming and pre-production. Provide clean, engaging prose. Keep responses supportive and concise."
        
        # 1. Try Groq
        response_text = self._generate_groq(prompt, max_tokens=1024, system_message=system_message)
        
        # 2. Try Gemini
        if not response_text:
            response_text = self._generate(prompt)
            
        if response_text:
            return response_text.strip()
            
        # Fallback
        return "I'm having trouble connecting to my creative database right now, but I'm here to help brainstorm your story once connection is restored!"


    # --- MOCK GENERATION FALLBACKS ---
    def _mock_story_analysis(self, story_idea, genre, target_audience, duration_length="Short Film"):
        res = generate_mock_story(
            story_idea=story_idea,
            genre=genre,
            target_audience=target_audience,
            duration_length=duration_length
        )["story_analysis"]
        defaults = {
            "tone": "Suspenseful" if genre == "Thriller" else "Dramatic",
            "rating": "PG-13",
            "comparable_films": [],
            "festival_potential": "Strong potential for indie film festivals.",
            "streaming_audience_fit": "Excellent fit for SVOD streaming platforms."
        }
        for k, v in defaults.items():
            if k not in res:
                res[k] = v
        return res

    def _mock_narrative_structure(self, story_idea, genre, duration_length="Short Film", characters_list=None):
        return generate_mock_story(
            story_idea=story_idea,
            genre=genre,
            duration_length=duration_length,
            characters_list=characters_list
        )["narrative_structure"]

    def _mock_characters(self, story_idea, genre):
        return generate_mock_story(
            story_idea=story_idea,
            genre=genre
        )["characters"]

    def _mock_scenes(self, story_idea, genre, duration_length="Short Film", characters_list=None):
        return generate_mock_story(
            story_idea=story_idea,
            genre=genre,
            duration_length=duration_length,
            characters_list=characters_list
        )["scene_breakdown"]

    def _mock_storyboard(self, story_idea, scenes_list):
        storyboards = []
        angles = ["Wide shot", "Close-up", "Low-angle medium shot", "Establishing overhead shot", "Two-shot tracking"]
        lightings = ["Low-key dramatic lighting with harsh shadows", "Cold blue neon fill light", "Warm golden hour backlight", "High-contrast chiaroscuro", "Diffused misty morning light"]
        moods = ["Tense and suspenseful", "Melancholic and quiet", "Action-packed and energetic", "Ominous and threatening", "Hopeful and resolute"]
        
        for i, scene in enumerate(scenes_list):
            num = scene.get("scene_number", i + 1)
            loc = scene.get("location", "INT. SCENE - DAY")
            chars = scene.get("characters", "Characters")
            
            angle = angles[i % len(angles)]
            lighting = lightings[i % len(lightings)]
            mood = moods[i % len(moods)]
            
            prompt = f"Cinematic storyboard frame, {loc.lower()}, featuring {chars.lower()}, {angle.lower()}, {lighting.lower()}, film concept art style, highly detailed composition."
            
            storyboards.append({
                "scene_number": num,
                "prompt": prompt,
                "camera_angle": angle,
                "lighting": lighting,
                "mood": mood
            })
            
        return {"storyboards": storyboards}

# Instantiate service singleton
gemini_service = GeminiService()
