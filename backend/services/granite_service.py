import os
import json
import requests
from backend.config import Config
from backend.utils.prompts import (
    SCREENPLAY_PROMPT,
    SOUND_DESIGN_PROMPT,
    PRODUCTION_PLAN_PROMPT
)
from backend.utils.helpers import clean_json_response

class GraniteService:
    def __init__(self):
        self.api_key = Config.WATSONX_API_KEY
        self.project_id = Config.WATSONX_PROJECT_ID
        self.url = Config.WATSONX_URL
        self.model_id = Config.WATSONX_MODEL_ID
        self._token = None
        self.initialized = bool(self.api_key and self.project_id)
        if self.initialized:
            print(">>> IBM Watsonx API credentials configured.")
        else:
            print(">>> IBM Watsonx credentials incomplete. Using local mock generator for Granite modules.")

    def _get_token(self):
        """Exchange IAM API key for IBM Cloud OAuth token."""
        if not self.api_key:
            return None
            
        # If token is cached, we could return it, but for simplicity/robustness we request it.
        if self._token:
            return self._token
            
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key
            }
            response = requests.post("https://iam.cloud.ibm.com/identity/token", headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                self._token = res_data.get("access_token")
                return self._token
            else:
                print(f"Failed to get IBM Cloud Token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching IBM Cloud Token: {e}")
            return None

    def _generate(self, prompt, max_tokens=1024):
        """Internal helper to call Watsonx Text Generation API."""
        if not self.initialized:
            return None
            
        token = self._get_token()
        if not token:
            return None
            
        try:
            endpoint = f"{self.url.rstrip('/')}/ml/v1/text/generation?version=2023-05-29"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            payload = {
                "model_id": self.model_id,
                "input": prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "min_new_tokens": 1,
                    "repetition_penalty": 1.1
                },
                "project_id": self.project_id
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                results = res_json.get("results", [])
                if results:
                    return results[0].get("generated_text", "")
            else:
                print(f"Watsonx API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception calling Watsonx API: {e}")
            
        return None

    def generate_screenplay(self, story_idea, genre, characters_list):
        """Generates a professional screenplay script."""
        chars_str = ", ".join([c.get("name", "") for c in characters_list]) if isinstance(characters_list, list) else str(characters_list)
        formatted_prompt = SCREENPLAY_PROMPT.format(
            story_idea=story_idea,
            genre=genre,
            characters_list=chars_str
        )
        
        response_text = self._generate(formatted_prompt, max_tokens=1500)
        if response_text:
            return response_text.strip()
            
        # Mock Fallback
        return self._mock_screenplay(story_idea, genre, characters_list)

    def generate_sound_design(self, story_idea, genre):
        """Generates background music, ambience, foley, vocal treatment, sound notes."""
        formatted_prompt = SOUND_DESIGN_PROMPT.format(
            story_idea=story_idea,
            genre=genre
        )
        
        response_text = self._generate(formatted_prompt, max_tokens=1024)
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "background_music" in parsed:
                return parsed
                
        # Mock Fallback
        return self._mock_sound_design(story_idea, genre)

    def generate_production_plan(self, story_idea, genre):
        """Generates shooting locations, props, equipment, crew, and estimated shoot days."""
        formatted_prompt = PRODUCTION_PLAN_PROMPT.format(
            story_idea=story_idea,
            genre=genre
        )
        
        response_text = self._generate(formatted_prompt, max_tokens=1024)
        if response_text:
            parsed = clean_json_response(response_text)
            if parsed and "shooting_locations" in parsed:
                return parsed
                
        # Mock Fallback
        return self._mock_production_plan(story_idea, genre)

    # --- MOCK GENERATION FALLBACKS ---
    def _mock_screenplay(self, story_idea, genre, characters_list):
        char1 = "VIKRAM"
        char2 = "ANYA"
        if isinstance(characters_list, list) and len(characters_list) >= 2:
            char1 = characters_list[0].get("name", "VIKRAM").upper()
            char2 = characters_list[1].get("name", "ANYA").upper()
            
        return f"""FADE IN:

INT. ABANDONED WAREHOUSE - NIGHT

Dust particles dance in the pale light of a single swinging bulb. The ambient hum of the city vibrates through the rusted metal walls. 

{char1} paces back and forth, holding a cellular phone, his expression tight with anxiety. {char2} sits on a stack of wooden crates, carefully tapping a wireframe device on her lap.

{char1}
(stops pacing)
He's not answering. It's been two hours since the drop time.

{char2}
He's smart. If they caught on, he would have dumped the drives and gone dark.

{char1}
And what about the files on this device? If we don't upload them in twenty minutes, the override locks down.

{char2} looking up from her device. Her eyes show a mixture of fear and absolute resolve.

{char2}
Then we don't wait for him. We initialize the broadcast ourselves.

{char1}
Without the access codes? Anya, it'll trigger the local alarm grid. We'll be trapped in here.

{char2}
We are already trapped, Vikram. Look around. This is the only chance we have.

She hits a final key. The device emits a soft, escalating chime. A purple glow reflects in her eyes.

FADE OUT.
"""

    def _mock_sound_design(self, story_idea, genre):
        return {
            "background_music": f"An atmospheric, synth-heavy score with slow, brooding cello movements for tension. The tempo starts at 80 BPM, building to a frantic electronic heartbeat of 130 BPM during chase sequences. Motif uses a low, repeating minor-fifth piano key to signify impending discovery.",
            "ambience": "Distant industrial drone, rhythmic water droplets, muffled city sirens bouncing off concrete, and wind whistling through thin metal vents.",
            "foley_effects": "Heavy leather boots dragging on concrete, rustling canvas jackets, crisp metallic clicks of hard drive bay locks, keys rattling, and the heavy breathing of characters trapped in enclosed spaces.",
            "dialogue_treatment": "Clean, dry dialogue for close-ups, with subtle, dark room-reverb added in the warehouse. Brief radio distortion and low-pass filter on phone-transmitted voices.",
            "scene_sound_notes": "Scene 1: Silence broken only by wet footsteps. Sound of a match striking. Scene 2: High-pitch electronic feedback building as the device activates. Scene 3: Hard cut to silence at the blackout, ending with a low-frequency hum."
        }

    def _mock_production_plan(self, story_idea, genre):
        return {
            "shooting_locations": "1. Industrial Warehouse: Authentic, distressed interior with power access. Requires fire safety permit. 2. Back Alleys: Tense chase setting. Requires evening street closure and city permit for dynamic lighting setup.",
            "required_props": "1. The CineForge Device: Custom mock-up glowing purple box with internal LED lights. 2. Tactical backpack, rugged laptop, fake security access cards, and handheld flashlight.",
            "equipment": "Camera: RED V-Raptor or Sony FX6 for low-light performance. Lenses: anamorphic primes for a cinematic widescreen look. G&E: Astera tubes (for colored purple glow), 1x1 LED panels, and a haze machine.",
            "crew_suggestions": "Director, Director of Photography, Gaffer/Key Grip, Production Sound Mixer, Art Director/Prop Master, and Hair/Makeup Artist.",
            "estimated_shoot_days": "3 days (Day 1: Warehouse dialogues, Day 2: Alleyway chases, Day 3: Intimate close-ups and pickup shots)."
        }

# Instantiate service singleton
granite_service = GraniteService()
