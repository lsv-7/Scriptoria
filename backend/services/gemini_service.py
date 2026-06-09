import os
import json
import random
from backend.config import Config
from backend.utils.prompts import (
    STORY_ANALYSIS_PROMPT,
    NARRATIVE_STRUCTURE_PROMPT,
    CHARACTER_GENERATOR_PROMPT,
    SCENE_BREAKDOWN_PROMPT,
    STORYBOARD_PROMPT
)
from backend.utils.helpers import clean_json_response

# Try to import google-generativeai. If missing, we fall back to mock generation.
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.initialized = False
        self.initialize_client()

    def initialize_client(self):
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
                print(">>> Google Gemini API configured successfully.")
            except Exception as e:
                print(f">>> Failed to configure Gemini Client: {e}")
                self.initialized = False
        else:
            print(">>> Gemini API key not found. Using local mock generator for Gemini modules.")
            self.initialized = False

    def _generate(self, prompt):
        """Internal helper to call Gemini API."""
        if not self.initialized:
            return None
            
        try:
            # Using the fast and reliable gemini-1.5-flash model
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None

    def generate_story_analysis(self, story_idea, genre, target_audience):
        """Generates genre analysis, theme, logline, synopsis, audience insights, tagline."""
        formatted_prompt = STORY_ANALYSIS_PROMPT.format(
            story_idea=story_idea,
            genre=genre,
            target_audience=target_audience
        )
        
        response_text = self._generate(formatted_prompt)
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "genre_analysis" in parsed:
                return parsed
                
        # Mock Fallback
        return self._mock_story_analysis(story_idea, genre, target_audience)

    def generate_narrative_structure(self, story_idea, genre):
        """Generates Act 1, 2, 3 narrative structure."""
        formatted_prompt = NARRATIVE_STRUCTURE_PROMPT.format(
            story_idea=story_idea,
            genre=genre
        )
        
        response_text = self._generate(formatted_prompt)
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "act_1" in parsed:
                return parsed
                
        # Mock Fallback
        return self._mock_narrative_structure(story_idea, genre)

    def generate_characters(self, story_idea, genre):
        """Generates 3-4 detailed character profiles."""
        formatted_prompt = CHARACTER_GENERATOR_PROMPT.format(
            story_idea=story_idea,
            genre=genre
        )
        
        response_text = self._generate(formatted_prompt)
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "characters" in parsed:
                return parsed
                
        # Mock Fallback
        return self._mock_characters(story_idea, genre)

    def generate_scenes(self, story_idea, genre):
        """Generates 5-6 core scene breakdowns."""
        formatted_prompt = SCENE_BREAKDOWN_PROMPT.format(
            story_idea=story_idea,
            genre=genre
        )
        
        response_text = self._generate(formatted_prompt)
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "scenes" in parsed:
                return parsed
                
        # Mock Fallback
        return self._mock_scenes(story_idea, genre)

    def generate_storyboard(self, story_idea, scenes_list):
        """Generates camera angle, mood, lighting, and prompt for storyboard frames."""
        scenes_json = json.dumps({"scenes": scenes_list}, indent=2)
        formatted_prompt = STORYBOARD_PROMPT.format(
            story_idea=story_idea,
            scenes_json=scenes_json
        )
        
        response_text = self._generate(formatted_prompt)
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "storyboards" in parsed:
                return parsed
                
        # Mock Fallback
        return self._mock_storyboard(story_idea, scenes_list)

    # --- MOCK GENERATION FALLBACKS ---
    def _mock_story_analysis(self, story_idea, genre, target_audience):
        logline_hooks = [
            f"When a mysterious event disrupts their quiet life, a determined protagonist must confront their deepest fears to save what remains of their world.",
            f"In a race against time, an unlikely hero is forced to team up with an enigmatic stranger to uncover a truth that could alter history.",
            f"After discovering a long-lost secret, an ordinary person finds themselves hunted by a powerful organization and must learn to survive."
        ]
        
        return {
            "genre_analysis": f"The story operates as a classic {genre}. It integrates major genre conventions, using the protagonist's normal environment as a contrast to the inciting incident. The target audience of {target_audience} will connect with the high stakes and the relatable emotional journey, while the setting provides excellent cinematic opportunities.",
            "theme": "The struggle for identity in a changing world, and the sacrifices required to protect one's freedom and family.",
            "logline": random.choice(logline_hooks) + f" (Tailored for: {story_idea[:60]}...)",
            "synopsis": f"The film opens in a detailed environment that reflects the protagonist's daily routine and core emotional wound. Soon, a sudden crisis forces them to make a difficult choice, kicking off a series of complications. As they delve deeper into the conflict, they form key alliances and face intense opposition.\n\nDuring the second act, the stakes escalate significantly. The protagonist learns a shocking truth that redefines their mission. After a major setback where all hope seems lost, they find the inner strength to mount a final plan.\n\nIn the dramatic climax, the protagonist confronts the main antagonist/force in an intense showdown. Through wit and sacrifice, they emerge transformed, establishing a new and wiser status quo.",
            "audience_insights": f"Highly appealing to fans of contemporary {genre} films. The concept offers strong visual set pieces suitable for trailers and social media teasers. Demographics skewing towards {target_audience} will appreciate the depth of character development alongside active plot progression.",
            "tagline": f"Some secrets can never be buried. CineForge presents a gripping new vision in {genre}."
        }

    def _mock_narrative_structure(self, story_idea, genre):
        return {
            "act_1": {
                "title": "Act 1: Setup & Inciting Incident",
                "description": f"We are introduced to the protagonist and their world. Soon, a major event disrupts this balance, forcing them to take action.",
                "conflict": "The protagonist must decide whether to step out of their comfort zone or let the crisis consume their life.",
                "rising_action": "Accepting the challenge, the protagonist takes the first step into the unknown, leaving their old world behind."
            },
            "act_2": {
                "title": "Act 2: Confrontation & Midpoint Escalation",
                "description": "The protagonist encounters a series of physical and emotional obstacles, meeting key allies and adversaries.",
                "rising_action": "Stakes are raised. The antagonist's plans accelerate, leading to a major twist at the midpoint that makes turning back impossible.",
                "climax": "A devastating loss or setback occurs, leaving the characters in their 'dark night of the soul' moment."
            },
            "act_3": {
                "title": "Act 3: Climax & Resolution",
                "description": "Armed with new insights and resolve, the protagonist plans a final confrontation.",
                "climax": "The final showdown. The protagonist uses everything they have learned to overcome the central antagonist or obstacle.",
                "resolution": "The conflict is resolved. The protagonist returns to a new normalcy, forever changed by their experience."
            }
        }

    def _mock_characters(self, story_idea, genre):
        names = ["Vikram", "Anya", "Marcus", "Kofi", "Elena", "Leo"]
        random.shuffle(names)
        
        return {
            "characters": [
                {
                    "name": names[0],
                    "age": "28",
                    "backstory": "Grew up in the outskirts. A former specialist who left the field after a critical mission went sideways, seeking a quiet life.",
                    "personality": "Stoic, analytical, fiercely loyal, but harbors deep trust issues.",
                    "goals": "To protect their community and find redemption for past failures.",
                    "strengths": "Tactical thinking, resourceful, calm under extreme pressure.",
                    "weaknesses": "Reluctance to ask for help, haunted by guilt, prone to isolation.",
                    "arc": "Learns to rely on others and accept that past mistakes do not define their future value."
                },
                {
                    "name": names[1],
                    "age": "34",
                    "backstory": "A brilliant academic or technician whose controversial research was shut down by major corporations.",
                    "personality": "Eccentric, passionate, highly verbal, often overlooks physical danger for intellectual curiosity.",
                    "goals": "To expose the truth behind a hidden conspiracy, no matter the cost.",
                    "strengths": "Exceptional intellect, technological expertise, out-of-the-box problem solving.",
                    "weaknesses": "Obsessive focus, physically vulnerable, overly trusting of data.",
                    "arc": "Realizes that emotional intelligence and human connections are as critical as raw logic."
                },
                {
                    "name": names[2],
                    "age": "45",
                    "backstory": "An influential local leader who has compromised their ideals over the years to maintain a fragile peace.",
                    "personality": "Charismatic, pragmatic, world-weary, conflicted.",
                    "goals": "To maintain order and prevent chaos, even if it requires difficult compromises.",
                    "strengths": "Political influence, negotiation skills, deep understanding of the system.",
                    "weaknesses": "Fear of radical change, vulnerable to blackmail, morally compromised.",
                    "arc": "Rediscovers their original ideals and risks everything to support the protagonist at a critical juncture."
                }
            ]
        }

    def _mock_scenes(self, story_idea, genre):
        return {
            "scenes": [
                {
                    "scene_number": 1,
                    "location": "INT. ABANDONED WAREHOUSE - NIGHT",
                    "characters": "Vikram, Anya",
                    "objective": "Establish the stakes and introduce the mysterious device/secret that starts the plot.",
                    "duration": "3 mins"
                },
                {
                    "scene_number": 2,
                    "location": "EXT. CITY STREETS - DAY",
                    "characters": "Vikram, Pursuers",
                    "objective": "A tense chase sequence establishing the danger and opposition Vikram faces.",
                    "duration": "2 mins"
                },
                {
                    "scene_number": 3,
                    "location": "INT. SAFEhouse - NIGHT",
                    "characters": "Vikram, Anya, Marcus",
                    "objective": "Characters form a temporary alliance and debate the moral consequences of their discovery.",
                    "duration": "4 mins"
                },
                {
                    "scene_number": 4,
                    "location": "INT. ANTAGONIST HEADQUARTERS - DAY",
                    "characters": "Marcus, The Antagonist",
                    "objective": "Reveal the antagonist's motivations and raise the stakes by showing the betrayal of Marcus.",
                    "duration": "3 mins"
                },
                {
                    "scene_number": 5,
                    "location": "EXT. WATERFRONT DOCKS - NIGHT",
                    "characters": "Vikram, Anya, The Antagonist",
                    "objective": "The dramatic climax: Vikram confronts the antagonist to stop the device from activating.",
                    "duration": "5 mins"
                }
            ]
        }

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
