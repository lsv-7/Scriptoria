# System and template prompts for the CineForge AI generation services

STORY_ANALYSIS_PROMPT = """
You are an expert film analyst and producer.
Analyze the following story idea and generate a comprehensive story analysis.
Your response MUST be a valid JSON object ONLY. Do not wrap the JSON in Markdown code blocks (like ```json), and do not include any other text.

Story Idea: {story_idea}
Genre: {genre}
Target Audience: {target_audience}

Expected JSON structure:
{{
  "genre_analysis": "Detailed analysis of how the story fits the chosen genre, key tropes used, and unique twists.",
  "theme": "The core thematic message and underlying meaning of the story.",
  "logline": "A compelling 1-2 sentence hook describing the main protagonist, conflict, and goal.",
  "synopsis": "A detailed 3-paragraph synopsis of the plot.",
  "audience_insights": "Analysis of the target audience appeal, marketing hooks, and competitive landscape.",
  "tagline": "A catchy marketing tagline for the film poster."
}}
"""

NARRATIVE_STRUCTURE_PROMPT = """
You are an expert screenwriter and script consultant.
Generate a structured 3-Act narrative breakdown for the following story idea.
Your response MUST be a valid JSON object ONLY. Do not wrap the JSON in Markdown code blocks, and do not include any other text.

Story Idea: {story_idea}
Genre: {genre}

Expected JSON structure:
{{
  "act_1": {{
    "title": "Act 1: Setup",
    "description": "Establish the status quo, inciting incident, and the first major plot point.",
    "conflict": "The initial central conflict introduced.",
    "rising_action": "How the characters are pushed out of their comfort zones."
  }},
  "act_2": {{
    "title": "Act 2: Confrontation & Midpoint",
    "description": "The rising stakes, midpoint twist, and descent into the 'all is lost' moment.",
    "rising_action": "Subplots, obstacles, and compounding problems.",
    "climax": "The peak tension leading to the end of Act 2."
  }},
  "act_3": {{
    "title": "Act 3: Resolution",
    "description": "The climax of the film and final resolution.",
    "climax": "The final showdown or confrontation resolving the main conflict.",
    "resolution": "The new status quo and character realizations."
  }}
}}
"""

CHARACTER_GENERATOR_PROMPT = """
You are an expert character designer.
Generate 3-4 distinct character profiles for a film based on the story idea below.
Your response MUST be a valid JSON object ONLY. Do not wrap the JSON in Markdown code blocks, and do not include any other text.

Story Idea: {story_idea}
Genre: {genre}

Expected JSON structure:
{{
  "characters": [
    {{
      "name": "Character Name",
      "age": "Age (e.g. 30)",
      "backstory": "Detailed backstory and history.",
      "personality": "Personality traits, temperament.",
      "goals": "Core motivation and goal in the story.",
      "strengths": "Key abilities or traits that help them.",
      "weaknesses": "Flaws or obstacles in their personality.",
      "arc": "How the character changes from start to finish."
    }}
  ]
}}
"""

SCENE_BREAKDOWN_PROMPT = """
You are a film director and assistant director.
Break down the story idea into 5-6 core scenes for a screenplay.
Your response MUST be a valid JSON object ONLY. Do not wrap the JSON in Markdown code blocks, and do not include any other text.

Story Idea: {story_idea}
Genre: {genre}

Expected JSON structure:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "location": "INT. LOCATION - TIME (e.g. INT. COFFEE SHOP - DAY)",
      "characters": "List of character names in the scene",
      "objective": "What is the dramatic goal of this scene?",
      "duration": "Estimated duration in minutes (e.g., 2 mins)"
    }}
  ]
}}
"""

STORYBOARD_PROMPT = """
You are a visual storyboard artist and cinematographer.
For each scene in the provided list, generate visual details and a specific text-to-image prompt to generate a storyboard panel.
Your response MUST be a valid JSON object ONLY. Do not wrap the JSON in Markdown code blocks, and do not include any other text.

Story Idea: {story_idea}
Scenes:
{scenes_json}

Expected JSON structure:
{{
  "storyboards": [
    {{
      "scene_number": 1,
      "prompt": "Detailed cinematic text-to-image prompt (e.g. 'Cinematic storyboard frame, dark office at night, detective examining evidence, dramatic lighting, wide shot, film concept art.')",
      "camera_angle": "Camera shot type and angle (e.g. Close-up, Low-angle wide shot, Medium tracking shot)",
      "lighting": "Description of lighting (e.g. High-contrast noir lighting, warm golden hour, cold neon glow)",
      "mood": "Emotional tone of the scene (e.g. Tense, Melancholic, Mystical, Thrilling)"
    }}
  ]
}}
"""

SCREENPLAY_PROMPT = """
You are an award-winning screenwriter.
Generate a professional screenplay excerpt (approximately 2-3 scenes) based on the following story idea and character list.
Write in standard screenplay format (use uppercase for Scene Headings, Character Names, and Transitions). 
Write dialogs and action descriptions clearly.
Do not write JSON, do not include markdown code block formats unless you are returning standard text. Return the raw screenplay script.

Story Idea: {story_idea}
Genre: {genre}
Characters: {characters_list}

Example screenplay format to follow:
INT. OFFICE - NIGHT

RAHUL enters the room.

RAHUL
What is this device?

He picks up a small brass box, glowing with a soft purple light.

Now, write the screenplay script:
"""

SOUND_DESIGN_PROMPT = """
You are a professional film sound designer and composer.
Generate a comprehensive sound design blueprint for a film based on the story idea below.
Your response MUST be a valid JSON object ONLY. Do not wrap the JSON in Markdown code blocks, and do not include any other text.

Story Idea: {story_idea}
Genre: {genre}

Expected JSON structure:
{{
  "background_music": "Theme style, orchestration, tempo, emotional cue descriptions.",
  "ambience": "Environmental background sounds for key scenes.",
  "foley_effects": "Specific character actions requiring distinct foley sounds (footsteps, fabric, objects).",
  "dialogue_treatment": "Vocal effects, filters, or specific dialogue styles (reverb, echoing, voiceovers).",
  "scene_sound_notes": "A sequence of sound notes mapping major moments to sound design cues."
}}
"""

PRODUCTION_PLAN_PROMPT = """
You are an experienced line producer and unit production manager.
Generate a realistic production plan and breakdown for a low-to-medium budget shoot of the story idea below.
Your response MUST be a valid JSON object ONLY. Do not wrap the JSON in Markdown code blocks, and do not include any other text.

Story Idea: {story_idea}
Genre: {genre}

Expected JSON structure:
{{
  "shooting_locations": "List of locations, description, and difficulty of obtaining access/permits.",
  "required_props": "Crucial props needed to tell the story.",
  "equipment": "Camera, lens package, lighting rigs, audio package suggested.",
  "crew_suggestions": "Crucial crew roles needed for this project (e.g. Director of Photography, Gaffer, Sound Recordist).",
  "estimated_shoot_days": "Total estimated shoot days (e.g. 5 days) with a brief justification."
}}
"""
