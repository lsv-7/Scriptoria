import random
import re

COMMON_WORDS = {"the", "a", "an", "this", "that", "he", "she", "it", "they", "i", "you", "we", "in", "on", "at", 
                "to", "for", "with", "by", "of", "and", "but", "or", "so", "if", "when", "while", "as", "is", 
                "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "not", "who", 
                "which", "whose", "where", "about"}

SENTENCE_STARTERS = {
    "In", "On", "At", "To", "For", "With", "By", "Of", "And", "But", "Or", "So", "If", "When", "While", 
    "As", "Is", "Are", "Was", "Were", "He", "She", "It", "They", "We", "I", "You", "Our", "Their", "His", 
    "Her", "The", "A", "An", "This", "That", "These", "Those", "Then", "There", "Here", "Now", "After", 
    "Before", "During", "Under", "Over", "Between", "Through", "Throughout", "Into", "Out", "Off", 
    "Up", "Down", "Back", "Once", "First", "Second", "Third", "Finally", "Next", "Also", "However", 
    "Although", "Even", "Though", "But", "Yet", "Still", "Therefore", "Thus", "Hence", "Meanwhile", 
    "Otherwise", "Instead", "Indeed", "Certainly", "Possibly", "Probably", "Maybe", "Perhaps", "Almost", 
    "Most", "Many", "Some", "Any", "Every", "Each", "All", "Both", "Either", "Neither", "One", "Two", 
    "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Driven", "Despite", "Act", "Scene"
}

IGNORE_CAPITALIZED = {
    "GOA", "MUMBAI", "DELHI", "BANGALORE", "LONDON", "PARIS", "ROBOT", "HUMAN", "CINEFORGE", "AI",
    "PITCH", "LOGLINE", "SYNOPSIS", "THEME", "PARAGRAPH", "DESCRIPTION", "GENRE", "ANALYSIS", "AUDIENCE", 
    "INSIGHTS", "TAGLINE", "ACT", "SCENE", "SPACE", "BAKERY", "KITCHEN", "OFFICE", "LIBRARY", 
    "COLLEGE", "SCHOOL", "HOSPITAL", "JUNGLE", "FOREST", "BEACH", "APARTMENT", "HOUSE", "RESTAURANT", 
    "CAFE", "HOTEL", "CABIN", "STATION", "SHOP", "STORE", "INDIAN", "ENGLISH", "AMERICAN", "HOLLYWOOD", 
    "BOLLYWOOD", "SHORT", "FILM", "FEATURE", "SERIES", "EPISODE", "SEASON", "DIRECTOR", "WRITER", 
    "PRODUCER", "ACTOR", "CHARACTER", "PROTAGONIST", "ANTAGONIST", "PROJECT",
    "DR", "MR", "MS", "MRS", "PROF", "SIR", "MADAM", "DOCTOR", "PROFESSOR",
    "INT", "EXT", "DAY", "NIGHT", "DUSK", "DAWN", "FADE", "IN", "OUT", "CUT", "TO", "SCENE",
    "INTEXT", "EXTINT", "IE", "CHARACTER", "PITCH", "LOGLINE", "SYNOPSIS", "THEME",
    "ACT", "SCENE", "SHOT", "PAN", "ZOOM", "TILT", "TRACK", "CAMERA", "ANGLE", "VIEW", 
    "FADEIN", "FADEOUT", "CUTTO",
    "DORM", "ROOM", "HALLWAY", "HALLWAYS", "STREET", "STREETS", "BACKSTAGE", "STAGE", 
    "BEDROOM", "LIVING", "BATHROOM", "ROOFTOP", "BALCONY", "GARDEN", "PARKING", "LOT", 
    "CAR", "TRUCK", "VEHICLE", "AIRPORT", "BAR", "CLUB", "MALL", "CLINIC", "LAB", "LABORATORY",
    "ESTABLISH", "SHOW", "INTRODUCE", "CREATE", "DEPICT", "HIGHLIGHT", "REVEAL", "EXPLORE", 
    "FOCUS", "ILLUSTRATE", "DEMONSTRATE", "FOLLOW", "PRESENT", "DISPLAY"
}

def is_invalid_character_name(name):
    if not name:
        return True
    name_strip = name.strip()
    name_upper = name_strip.upper()
    if name_upper.startswith("INT.") or name_upper.startswith("EXT.") or name_upper.startswith("INT ") or name_upper.startswith("EXT ") or name_upper.startswith("INT/") or name_upper.startswith("EXT/"):
        return True
    # Remove standard punctuation and make uppercase
    cleaned = "".join(c for c in name_strip.upper() if c.isalpha())
    if cleaned in IGNORE_CAPITALIZED:
        return True
    if name_strip.lower() in COMMON_WORDS or cleaned.lower() in COMMON_WORDS:
        return True
    if name_strip in SENTENCE_STARTERS or cleaned in SENTENCE_STARTERS:
        return True
    return False

def extract_characters_from_idea(story_idea):
    extracted = []
    lines = [line.strip() for line in (story_idea or "").split('\n') if line.strip()]
    
    # Check if there is any INT. or EXT. in the text to identify structured scene lists
    has_scenes = any("INT." in line.upper() or "EXT." in line.upper() for line in lines)
    
    if has_scenes:
        for line in lines:
            # 1. Clean line of scene number
            line_clean = re.sub(r'#\d+', '', line)
            
            # 2. Clean line of location headers
            loc_pattern = r'\b(?:INT\b|EXT\b|INT\./EXT\.|EXT\./INT\.)\s+[^-\t\n\r]+(?:\s*-\s*(?:DAY|NIGHT|DUSK|DAWN|LATER|CONTINUOUS|SAME TIME))?'
            line_clean = re.sub(loc_pattern, '', line_clean, flags=re.IGNORECASE)
            
            # 3. Clean line of duration headers
            dur_pattern = r'\b\d+(?:\.\d+)?\s*(?:mins|min|minutes|minute)\b'
            line_clean = re.sub(dur_pattern, '', line_clean, flags=re.IGNORECASE)
            
            # Split line by tabs or multiple spaces
            parts = []
            if '\t' in line_clean:
                parts = [p.strip() for p in line_clean.split('\t') if p.strip()]
            else:
                parts = [p.strip() for p in re.split(r'\s{2,}', line_clean) if p.strip()]
                
            for part in parts:
                part_len = len(part)
                if part_len > 60 or part_len < 2:
                    continue
                
                # Check capitalization ratio
                words_in_part = [w for w in part.split() if w]
                if not words_in_part:
                    continue
                
                meaningful_words = []
                cap_meaningful = []
                for w in words_in_part:
                    w_clean = "".join(c for c in w if c.isalpha())
                    if not w_clean:
                        continue
                    if w_clean.lower() in {"and", "or", "with", "of", "the", "minor", "extra"}:
                        continue
                    meaningful_words.append(w_clean)
                    if w_clean[0].isupper():
                        cap_meaningful.append(w_clean)
                        
                if not meaningful_words:
                    continue
                ratio = len(cap_meaningful) / len(meaningful_words)
                if ratio < 0.75:
                    continue
                
                # Clean up parenthetical comments like (minor extra)
                clean_part = re.sub(r'\(.*?\)', '', part)
                # Replace ' and ' with comma
                clean_part = re.sub(r'\band\b', ',', clean_part, flags=re.IGNORECASE)
                
                # Split by commas or semicolons
                name_candidates = [n.strip() for n in re.split(r'[,;]', clean_part) if n.strip()]
                for candidate in name_candidates:
                    words = candidate.split()
                    if not words:
                        continue
                    first_word = words[0]
                    first_word_clean = "".join(c for c in first_word if c.isalpha())
                    if first_word_clean and first_word_clean[0].isupper():
                        if not is_invalid_character_name(first_word_clean):
                            if first_word_clean not in extracted:
                                extracted.append(first_word_clean)
                                
    # Fallback to standard word-by-word extraction
    if not extracted:
        char_search_text = (story_idea or "").strip()
        loc_pattern = r'\b(?:INT\b|EXT\b|INT\./EXT\.|EXT\./INT\.)\s+[^-\t\n\r]+(?:\s*-\s*(?:DAY|NIGHT|DUSK|DAWN|LATER|CONTINUOUS|SAME TIME))?'
        char_search_text = re.sub(loc_pattern, '', char_search_text, flags=re.IGNORECASE)
        
        labels = ["pitch", "logline", "synopsis", "description", "theme", "paragraph1", "paragraph2", "paragraph3", "paragraph", 
                  "genre analysis", "audience insights", "tagline", "key tropes", "unique twists", "genre fit", 
                  "target audience", "marketing hooks", "competitive landscape", "act 1", "act 2", "act 3"]
        for label in labels:
            char_search_text = re.sub(rf'\b{label}\b\s*:?', '', char_search_text, flags=re.IGNORECASE)

        words = char_search_text.split()
        for w in words:
            w_clean = re.sub(r"'[sS]\b", "", w)
            cleaned = "".join(c for c in w_clean if c.isalpha())
            if cleaned and not is_invalid_character_name(cleaned):
                if cleaned.lower().endswith("ing"):
                    continue
                if cleaned[0].isupper():
                    # Check if the lowercase version appears as a lowercase word in the text (to filter out common nouns starting a sentence)
                    pattern = rf'\b{re.escape(cleaned.lower())}\b'
                    if re.search(pattern, char_search_text):
                        continue
                    if cleaned not in extracted:
                        extracted.append(cleaned)
                        
    return extracted

def clean_location_for_prose(loc_str):
    if not loc_str:
        return "the location"
    # Remove INT. or EXT. or INT/EXT. prefix
    s = re.sub(r'^(INT\.\s*|EXT\.\s*|INT/EXT\.\s*|INT\s+|EXT\s+)', '', loc_str, flags=re.IGNORECASE).strip()
    # Remove suffix like - DAY, - NIGHT, - DUSK, - DAWN
    s = re.sub(r'\s*-\s*(DAY|NIGHT|DUSK|DAWN)\b.*$', '', s, flags=re.IGNORECASE).strip()
    s = s.lower()
    
    # Prepend a/the where appropriate for natural prose
    if any(w in s for w in ["school", "college", "university", "library", "office", "kitchen", "apartment", "restaurant", "cafe", "hotel", "cabin", "station", "shop", "store", "lab", "laboratory", "park", "garden", "city", "studio", "workshop", "spaceship", "bridge", "reactor", "house", "beach", "jungle", "forest"]):
        if not s.startswith("the ") and not s.startswith("a ") and not s.startswith("an "):
            return f"the {s}"
    return s

def extract_raw_pitch(story_idea):
    if not story_idea:
        return "our project"
    s = story_idea.strip()
    
    # 1. Look for Pitch: case-insensitively
    match_pitch = re.search(r'(?i)\bPitch\s*:\s*(.*?)(?:\r?\n\s*\b(?:Logline|Synopsis|Theme|Characters|Scenes|Scene|Act)\b\s*:|$)', s, re.DOTALL)
    if match_pitch:
        return match_pitch.group(1).strip()
        
    # 2. Look for Logline: case-insensitively
    match_log = re.search(r'(?i)\bLogline\s*:\s*(.*?)(?:\r?\n\s*\b(?:Synopsis|Theme|Characters|Scenes|Scene|Act)\b\s*:|$)', s, re.DOTALL)
    if match_log:
        log_text = match_log.group(1).strip()
        # If the logline has "driven by the dream of ...", try to extract just the dream
        dream_match = re.search(r'(?i)Driven by the dream of\s+(.*?)(?:,\s+[A-Za-z0-9\s]+\s+and\s+[A-Za-z0-9\s]+\s+(?:navigate|face|go|work|cooperate|explore|strive|fight|embark|run)|,\s+[^,]+?\s+navigate|,\s+[^,]+?\s+face|$)', log_text, re.DOTALL)
        if dream_match:
            return dream_match.group(1).strip()
        return log_text
        
    # 3. Handle multi-line blocks with headers
    lines = [line.strip() for line in s.split('\n') if line.strip()]
    for line in lines:
        if not any(line.lower().startswith(h) for h in ["pitch:", "logline:", "synopsis:", "theme:", "characters:", "scenes:", "scene:", "act:"]):
            return line
            
    # 4. Remove labels and clean it up as fallback
    idea_clean = s
    labels = ["pitch", "logline", "synopsis", "description", "theme", "paragraph1", "paragraph2", "paragraph3", "paragraph", 
              "genre analysis", "audience insights", "tagline", "key tropes", "unique twists", "genre fit", 
              "target audience", "marketing hooks", "competitive landscape", "act 1", "act 2", "act 3"]
    for label in labels:
        idea_clean = re.sub(rf'\b{label}\b\s*:?', '', idea_clean, flags=re.IGNORECASE)
    idea_clean = idea_clean.strip()
    
    # Strip phrases like "a story about"
    strip_phrases = ["a story about", "a film about", "write a story about", "write a screenplay about", "a screenplay about", "story about", "film about", "about"]
    for phrase in strip_phrases:
        if idea_clean.lower().startswith(phrase):
            idea_clean = idea_clean[len(phrase):].strip()
            break
            
    return idea_clean

def generate_mock_story(story_idea, genre, target_audience="General", duration_length="Short Film", characters_list=None):
    # Extract names from the full story_idea BEFORE trimming to the logline, to avoid throwing away characters in the synopsis
    extracted_names = extract_characters_from_idea(story_idea)

    # Now trim idea_clean to just the logline text for structural placeholders and backstories
    idea_clean = extract_raw_pitch(story_idea)
    idea_lower = idea_clean.lower()
    genre_lower = (genre or "").lower()

    # Fallback lists of names
    female_names = ["Priya", "Ananya", "Diya", "Kavya", "Meera", "Neha", "Riya", "Shreya", "Tanvi", "Aditi", "Anjali"]
    male_names = ["Rohan", "Aarav", "Arjun", "Dev", "Kabir", "Siddharth", "Vihaan", "Aditya", "Kunal", "Raj"]
    supporting_names = ["Sharmaji", "Vermaji", "Suresh", "Mehta Uncle", "Kapoor Aunt", "Guptaji"]
    
    # Determine base defaults from prompt keywords
    is_space = any(w in idea_lower for w in ["space", "ship", "star", "cosmic", "alien", "astronaut", "spaceship", "galaxy", "orbit", "planet", "mars", "moon"])
    is_scifi = any(w in idea_lower for w in ["robot", "robo", "chitti", "android", "ai", "machine", "futuristic", "technology", "sci-fi", "science", "laboratory", "lab", "nuclear", "physics"]) or is_space
    is_detective = any(w in idea_lower for w in ["detective", "spy", "murder", "agent", "investigation", "crime", "police"])
    is_chef = any(w in idea_lower for w in ["chef", "cooking", "food", "restaurant", "kitchen", "bakery", "cafe", "bake"])
    is_school = any(w in idea_lower for w in ["school", "teen", "kid", "child", "children", "classroom", "classmate", "high school", "middle school", "elementary", "primary school", "schoolboy", "schoolgirl", "schoolchild"])
    is_college = any(w in idea_lower for w in ["college", "university", "student", "class", "library"])
    is_married = any(w in idea_lower for w in ["married", "marriage", "couple", "wife", "husband", "wedding", "spouse", "newlywed"])
    is_romance = any(w in idea_lower for w in ["love", "romance", "romantic", "lover", "girlfriend", "boyfriend", "heart"]) or "romance" in genre_lower

    if is_space:
        char1_name = "Captain Dev"
        char2_name = "Aria"
        char3_name = "Commander Kapoor"
    elif is_scifi:
        char1_name = "Chitti"
        char2_name = "Aishu"
        char3_name = "Vaseegaran"
    elif is_detective:
        char1_name = "Inspector Kabir"
        char2_name = "Neha"
        char3_name = "Guptaji"
    elif is_chef:
        char1_name = "Chef Rohan"
        char2_name = "Priya"
        char3_name = "Sharmaji"
    elif is_school:
        char1_name = "Rohan"
        char2_name = "Diya"
        char3_name = "Sharmaji"
    elif is_college:
        char1_name = "Aarav"
        char2_name = "Ananya"
        char3_name = "Siddharth"
    elif is_married or is_romance:
        char1_name = "Rohan"
        char2_name = "Priya"
        char3_name = "Kapoor Aunt"
    else:
        char1_name = "Aarav"
        char2_name = "Ananya"
        char3_name = "Vermaji"
        
    # Apply override from characters_list if provided
    char1_age = None
    char2_age = None
    char3_age = None
    if characters_list and isinstance(characters_list, list):
        names = []
        for c in characters_list:
            if isinstance(c, dict):
                names.append(c.get("name", ""))
            elif isinstance(c, str):
                names.append(c)
        names = [n for n in names if n]
        if len(names) >= 1:
            char1_name = names[0]
            if isinstance(characters_list[0], dict) and "age" in characters_list[0]:
                char1_age = characters_list[0]["age"]
        if len(names) >= 2:
            char2_name = names[1]
            if isinstance(characters_list[1], dict) and "age" in characters_list[1]:
                char2_age = characters_list[1]["age"]
        if len(names) >= 3:
            char3_name = names[2]
            if isinstance(characters_list[2], dict) and "age" in characters_list[2]:
                char3_age = characters_list[2]["age"]
    else:
        # Otherwise apply override from extracted_names if available
        if len(extracted_names) >= 1:
            char1_name = extracted_names[0]
        if len(extracted_names) >= 2:
            char2_name = extracted_names[1]
        if len(extracted_names) >= 3:
            char3_name = extracted_names[2]

    # Resolve dynamic ages based on prompt categories
    if not char1_age:
        if is_school:
            char1_age = "15"
        elif is_college:
            char1_age = "20"
        elif is_scifi or is_space or is_detective or is_chef:
            char1_age = "28"
        else:
            char1_age = "27"
            
    if not char2_age:
        if is_school:
            char2_age = "15"
        elif is_college:
            char2_age = "21"
        elif is_scifi or is_space or is_detective or is_chef:
            char2_age = "26"
        else:
            char2_age = "25"
            
    if not char3_age:
        if is_school:
            char3_age = "42"
        elif is_college:
            char3_age = "52"
        elif is_scifi or is_space or is_detective or is_chef:
            char3_age = "54"
        else:
            char3_age = "52"

    c1 = char1_name.upper()
    c2 = char2_name.upper()
    c3 = char3_name.upper()

    # 2. DYNAMIC LOCATION EXTRACTION
    locations_list = ["goa", "mumbai", "delhi", "bangalore", "london", "paris", "space", "bakery", "kitchen", "office", "library", "college", "school", "hospital", "jungle", "forest", "beach", "apartment", "house", "restaurant", "cafe", "hotel", "cabin", "station", "shop", "store", "lab", "laboratory", "park", "garden", "city", "studio", "workshop"]
    found_locations = []
    
    for loc in locations_list:
        if loc in idea_lower:
            start_idx = idea_lower.find(loc)
            found_locations.append(idea_clean[start_idx:start_idx+len(loc)])
            
    matches = re.findall(r'\b(in|at|to|near)\s+([A-Z][a-zA-Z]+)', idea_clean)
    for m in matches:
        if m[1] not in found_locations and m[1].lower() not in COMMON_WORDS:
            found_locations.append(m[1])
            
    unique_locs = []
    for l in found_locations:
        if l.lower() not in [u.lower() for u in unique_locs]:
            unique_locs.append(l)
            
    if len(unique_locs) >= 2:
        loc_main = f"INT. {unique_locs[0].upper()} - DAY"
        loc_action = f"EXT. {unique_locs[1].upper()} STREETS - DUSK"
        loc_climax = f"INT. {unique_locs[0].upper()} - NIGHT"
    elif len(unique_locs) == 1:
        loc_name = unique_locs[0].upper()
        if loc_name in ["GOA", "MUMBAI", "DELHI", "BANGALORE", "LONDON", "PARIS", "SPACE"]:
            loc_main = f"INT. APARTMENT IN {loc_name} - DAY"
            loc_action = f"EXT. {loc_name.title()} STREETS - DAY"
            loc_climax = f"INT. APARTMENT IN {loc_name} - NIGHT"
        else:
            loc_main = f"INT. {loc_name} - DAY"
            loc_action = f"EXT. {loc_name} ENTRANCE - DUSK"
            loc_climax = f"INT. {loc_name} - NIGHT"
    else:
        if is_space:
            loc_main = "INT. SPACESHIP BRIDGE - DAY"
            loc_action = "EXT. PLANETARY SURFACE - DAY"
            loc_climax = "INT. SPACESHIP REACTOR ROOM - NIGHT"
        elif is_scifi:
            loc_main = "INT. FUTURISTIC LABORATORY - DAY"
            loc_action = "EXT. FUTURISTIC CITY STREETS - NIGHT"
            loc_climax = "INT. FUTURISTIC LABORATORY - NIGHT"
        elif is_detective:
            loc_main = "INT. DIMLY LIT OFFICE - NIGHT"
            loc_action = "EXT. RAIN-SLICKED ALLEY - NIGHT"
            loc_climax = "INT. ABANDONED WAREHOUSE - NIGHT"
        elif is_chef:
            loc_main = "INT. RESTAURANT KITCHEN - DAY"
            loc_action = "EXT. OUTDOOR PATIO - DUSK"
            loc_climax = "INT. DINING ROOM - NIGHT"
        elif is_college:
            loc_main = "INT. UNIVERSITY LIBRARY - DAY"
            loc_action = "EXT. CAMPUS QUAD - DAY"
            loc_climax = "INT. COLLEGE AUDITORIUM - NIGHT"
        elif is_married or is_romance:
            loc_main = "INT. COZY APARTMENT - DAY"
            loc_action = "EXT. SCENIC PARK - DUSK"
            loc_climax = "INT. COZY APARTMENT - NIGHT"
        else:
            loc_main = "INT. COZY OFFICE - DAY"
            loc_action = "EXT. NEIGHBORHOOD STREETS - DAY"
            loc_climax = "INT. COZY OFFICE - NIGHT"

    loc_main_header = loc_main
    loc_action_header = loc_action
    loc_climax_header = loc_climax

    loc_main = clean_location_for_prose(loc_main)
    loc_action = clean_location_for_prose(loc_action)
    loc_climax = clean_location_for_prose(loc_climax)

    # 3. DYNAMIC STORY PHRASE EXTRACTION
    story_summary = idea_clean
    
    # If the story_summary contains a logline, let's extract the actual dream/core idea.
    logline_match = re.search(r'(?i)Driven by the dream of\s+(.*?)(?:,\s+[A-Za-z0-9\s]+\s+and\s+[A-Za-z0-9\s]+\s+(?:navigate|face|go|work|cooperate|explore|strive|fight|embark|run)|,\s+[^,]+?\s+navigate|,\s+[^,]+?\s+face|$)', story_summary, re.DOTALL)
    if logline_match:
        story_summary = logline_match.group(1).strip()
    elif "driven by the dream of" in story_summary.lower():
        idx = story_summary.lower().find("driven by the dream of")
        sub = story_summary[idx + len("driven by the dream of"):].strip()
        comma_parts = sub.split(",")
        if len(comma_parts) > 1:
            story_summary = comma_parts[0].strip()
        else:
            story_summary = sub

    strip_phrases = ["a story about", "a film about", "write a story about", "write a screenplay about", "a screenplay about", "story about", "film about", "about"]
    for phrase in strip_phrases:
        if story_summary.lower().startswith(phrase):
            story_summary = story_summary[len(phrase):].strip()
            break
            
    # Clean up tail punctuation
    if story_summary.endswith("."):
        story_summary = story_summary[:-1].strip()

    story_summary_lc = story_summary[0].lower() + story_summary[1:] if story_summary else "our project"
    story_summary_cap = story_summary[0].upper() + story_summary[1:] if story_summary else "Our project"

    # 4. COMPOSING THE PRE-PRODUCTION PACKAGE
    
    # Story Analysis Details
    if is_space:
        logline = f"Lost in the depths of the galaxy, Captain {char1_name} and navigator {char2_name} must overcome mechanical failures and crew conflicts to achieve their dream of {story_summary_lc}, while facing strict orders from Commander {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} monitor cosmic telemetry for {story_summary_lc}. "
            f"An unexpected solar flare compromises their orbit, raising the stakes immediately, while {char3_name} demands strict adherence to military protocols.\n\n"
            f"During the second act at {loc_action}, survival becomes a struggle. A major disagreement over venting the fuel grids to finalize {story_summary_lc} causes a split, leaving them isolated on the planet surface.\n\n"
            f"In the dramatic climax at {loc_climax}, a reactor meltdown threatens to incinerate the spaceship. "
            f"Combining mechanical genius and navigation skills, they stabilize the core and achieve {story_summary_lc}, cementing their status as pioneers."
        )
        theme = f"Survival, trust, and the human spirit's drive to explore and achieve {story_summary_lc} across the stars."
        genre_analysis = f"The story operates as a classic Space Sci-Fi. It integrates major genre conventions by placing the main characters in a setting ({loc_main}) that challenges their ability to achieve their goal of {story_summary_lc}. The target audience of {target_audience} will connect with the relatable emotional stakes, while the transitions between {loc_main} and {loc_action} provide excellent cinematic opportunities."
        audience_insights = f"Highly appealing to fans of contemporary Space Sci-Fi and futuristic films. Demographics skewing towards {target_audience} will appreciate the depth of character development as the protagonist pushes forward with {story_summary_lc}."
        tagline = f"A journey of a thousand lightyears begins with one bold dream. CineForge presents a gripping new vision of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} to establish the plans for {story_summary_lc}. They establish their partnership, resources, and schedule, but a minor disagreement over resources and scheduling escalates, threatening to derail their plans."
        act_2_desc = f"The stakes escalate as {char1_name} and {char2_name} face critical setbacks and hurdles at {loc_action}. {char1_name} wants to take a safe, traditional route, whereas {char2_name} insists on taking a creative risk, leading to a clash of ideologies and a temporary split between the two collaborators."
        act_3_desc = f"A sudden emergency related to their dream of {story_summary_lc} forces {char1_name} and {char2_name} to set aside their differences and work together at {loc_climax}. They combine their skills to resolve the crisis, leading to a heartwarming resolution and the successful establishment of their goal."
        backstory1 = f"A seasoned astronaut captain who has dedicated their life to the exploration and development of {story_summary_lc}."
        backstory2 = f"A brilliant spaceship navigator who believes that {story_summary_lc} is the key to humanity's survival."
        backstory3 = f"A stern, by-the-book commander who fears that the mission for {story_summary_lc} is too risky."
    elif is_scifi:
        logline = f"In a futuristic world, {char1_name} and {char2_name} must navigate the boundaries of technology and emotion to achieve their dream of {story_summary_lc}, facing opposition from {char3_name}."
        synopsis = (
            f"The story begins in {loc_main} where {char1_name} and {char2_name} are working intensely on {story_summary_lc}. "
            f"As their connection deepens, they face sudden technical errors and societal barriers, while {char3_name} watches their every move with caution.\n\n"
            f"During the second act at {loc_action}, the stakes escalate. {char1_name} pushes for a dangerous upgrade or risk to achieve {story_summary_lc}, "
            f"whereas {char2_name} insists on taking a safer path. This ideological clash leads to a temporary split between the two collaborators.\n\n"
            f"In the dramatic climax at {loc_climax}, a critical system failure threatens to destroy {story_summary_lc} completely. "
            f"Setting aside their differences, they unite their strengths to stabilize the core. The story ends in a heartwarming resolution, proving that connection can transcend any boundary."
        )
        theme = f"The power of humanity and connection to transcend artificial boundaries and achieve {story_summary_lc}."
        genre_analysis = f"The story operates as a classic Sci-Fi. It integrates major genre conventions by placing the main characters in a setting ({loc_main}) that challenges their ability to achieve their goal of {story_summary_lc}. The target audience of {target_audience} will connect with the relatable emotional stakes, while the transitions between {loc_main} and {loc_action} provide excellent cinematic opportunities."
        audience_insights = f"Highly appealing to fans of contemporary Sci-Fi films. Demographics skewing towards {target_audience} will appreciate the depth of character development as the protagonist pushes forward with {story_summary_lc}."
        tagline = f"A journey of a thousand steps begins with one bold dream. CineForge presents a gripping new vision of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} to establish the plans for {story_summary_lc}. They establish their partnership, resources, and schedule, but a minor disagreement over resources and scheduling escalates, threatening to derail their plans."
        act_2_desc = f"The stakes escalate as {char1_name} and {char2_name} face critical setbacks and hurdles at {loc_action}. {char1_name} wants to take a safe, traditional route, whereas {char2_name} insists on taking a creative risk, leading to a clash of ideologies and a temporary split between the two collaborators."
        act_3_desc = f"A sudden emergency related to their dream of {story_summary_lc} forces {char1_name} and {char2_name} to set aside their differences and work together at {loc_climax}. They combine their skills to resolve the crisis, leading to a heartwarming resolution and the successful establishment of their goal."
        backstory1 = f"A focused professional who has invested everything into the dream of {story_summary_lc}."
        backstory2 = f"An imaginative creator who brings the passion and design vision to their goal of {story_summary_lc}."
        backstory3 = f"An experienced local figure who is highly skeptical about their plans for {story_summary_lc} but offers critical advice."
    elif is_detective:
        logline = f"In a city filled with secrets, detective {char1_name} and partner {char2_name} race against time to solve {story_summary_lc}, while staying one step ahead of the mysterious {char3_name}."
        synopsis = (
            f"The story opens in {loc_main} where {char1_name} and {char2_name} gather critical clues regarding {story_summary_lc}. "
            f"However, they quickly realize they are dealing with a larger conspiracy. The intervention of {char3_name} adds immediate danger.\n\n"
            f"During the second act at {loc_action}, the investigation reaches a boiling point. A disagreement on whether to follow the law or cross lines to solve {story_summary_lc} leads to a split between the partners.\n\n"
            f"In the dramatic climax at {loc_climax}, a trap set by the antagonist forces them to coordinate their tactics. "
            f"Working in perfect sync, they capture the culprit and secure the evidence, successfully solving the mystery of {story_summary_lc}."
        )
        theme = f"Justice, truth, and the trust needed between partners to solve {story_summary_lc}."
        genre_analysis = f"The story operates as a classic Detective mystery. It integrates major genre conventions by placing the main characters in a setting ({loc_main}) that challenges their ability to achieve their goal of {story_summary_lc}. The target audience of {target_audience} will connect with the relatable emotional stakes, while the transitions between {loc_main} and {loc_action} provide excellent cinematic opportunities."
        audience_insights = f"Highly appealing to fans of classic mystery and crime thrillers. Demographics skewing towards {target_audience} will appreciate the puzzle-solving nature of {story_summary_lc}."
        tagline = f"Every clue counts. CineForge presents a gripping new vision of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} to gather critical clues regarding {story_summary_lc}. They establish their partnership, resources, and schedule, but a minor disagreement over resources and scheduling escalates, threatening to derail their plans."
        act_2_desc = f"The stakes escalate as {char1_name} and {char2_name} face critical setbacks and hurdles at {loc_action}. {char1_name} wants to take a safe, traditional route, whereas {char2_name} insists on taking a creative risk, leading to a clash of ideologies and a temporary split between the two collaborators."
        act_3_desc = f"A sudden emergency related to their dream of {story_summary_lc} forces {char1_name} and {char2_name} to set aside their differences and work together at {loc_climax}. They combine their skills to resolve the crisis, leading to a heartwarming resolution and the successful establishment of their goal."
        backstory1 = f"A seasoned detective with a sharp mind who has dedicated their career to solving {story_summary_lc}."
        backstory2 = f"A meticulous partner who balances the detective's instincts with solid data and research on {story_summary_lc}."
        backstory3 = f"A senior inspector who holds key files and coordinates local intelligence for {story_summary_lc}."
    elif is_chef:
        logline = f"Aspiring chef {char1_name} and designer {char2_name} clash and cooperate to launch their culinary dream of {story_summary_lc}, facing critical reviews from food critic {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} prepare for the opening of their dream {story_summary_lc}. "
            f"They face immediate pressure when local food critic {char3_name} drops by unexpectedly.\n\n"
            f"During the second act at {loc_action}, the kitchen heat rises. A major recipe failure or supply delay causes a heated argument between the two partners, leading to a temporary split.\n\n"
            f"In the dramatic climax at {loc_climax}, a sudden rush of customers forces them to coordinate. "
            f"They combine culinary expertise and elegant design to deliver an unforgettable dining experience, securing the success of {story_summary_lc}."
        )
        theme = f"Passion, creativity, and the perfect recipe of partnership required to achieve {story_summary_lc}."
        genre_analysis = f"The story operates as a classic culinary drama/comedy. It integrates major genre conventions by placing the main characters in a setting ({loc_main}) that challenges their ability to achieve their goal of {story_summary_lc}. The target audience of {target_audience} will connect with the relatable emotional stakes, while the transitions between {loc_main} and {loc_action} provide excellent cinematic opportunities."
        audience_insights = f"Highly appealing to fans of culinary and passion-driven character stories. Demographics skewing towards {target_audience} will appreciate the sensory details as they strive for {story_summary_lc}."
        tagline = f"Cooked with passion, served with love. CineForge presents a gripping new vision of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} as they make preparation for {story_summary_lc}. They establish their partnership, resources, and schedule, but a minor disagreement over resources and scheduling escalates, threatening to derail their plans."
        act_2_desc = f"The stakes escalate as {char1_name} and {char2_name} face critical setbacks and hurdles at {loc_action}. {char1_name} wants to take a safe, traditional route, whereas {char2_name} insists on taking a creative risk, leading to a clash of ideologies and a temporary split between the two collaborators."
        act_3_desc = f"A sudden emergency related to their dream of {story_summary_lc} forces {char1_name} and {char2_name} to set aside their differences and work together at {loc_climax}. They combine their skills to resolve the crisis, leading to a heartwarming resolution and the successful establishment of their goal."
        backstory1 = f"A talented chef whose dream has always been to master {story_summary_lc}."
        backstory2 = f"An energetic partner who manages the restaurant and brings creative design to {story_summary_lc}."
        backstory3 = f"A demanding food critic whose opinions can make or break their dream of {story_summary_lc}."
    elif is_college:
        logline = f"Determined to make their mark, students {char1_name} and {char2_name} navigate campus politics and academic pressure to achieve {story_summary_lc}, under the watchful eyes of professor {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} are preparing their final presentation for {story_summary_lc}. "
            f"Their initial plans are disrupted by professor {char3_name}'s tough feedback and strict guidelines.\n\n"
            f"During the second act at {loc_action}, the competition intensifies. A clash of ideas on how to execute their presentation leads to a falling out, leaving their grades and future in jeopardy.\n\n"
            f"In the dramatic climax at {loc_climax}, a sudden deadline change forces them to combine their efforts. "
            f"They deliver a brilliant, unified presentation on {story_summary_lc}, earning praise and establishing their future path."
        )
        theme = f"Growth, collaboration, and finding one's voice through the journey of {story_summary_lc}."
        genre_analysis = f"The story operates as a classic coming-of-age campus drama. It integrates major genre conventions by placing the main characters in a setting ({loc_main}) that challenges their ability to achieve their goal of {story_summary_lc}. The target audience of {target_audience} will connect with the relatable emotional stakes, while the transitions between {loc_main} and {loc_action} provide excellent cinematic opportunities."
        audience_insights = f"Highly appealing to students and young adults. Demographics skewing towards {target_audience} will appreciate the relatable peer pressures and academic struggles around {story_summary_lc}."
        tagline = f"Learning the hard way, succeeding together. CineForge presents a gripping new vision of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} as they make preparation for {story_summary_lc}. They establish their partnership, resources, and schedule, but a minor disagreement over resources and scheduling escalates, threatening to derail their plans."
        act_2_desc = f"The stakes escalate as {char1_name} and {char2_name} face critical setbacks and hurdles at {loc_action}. {char1_name} wants to take a safe, traditional route, whereas {char2_name} insists on taking a creative risk, leading to a clash of ideologies and a temporary split between the two collaborators."
        act_3_desc = f"A sudden emergency related to their dream of {story_summary_lc} forces {char1_name} and {char2_name} to set aside their differences and work together at {loc_climax}. They combine their skills to resolve the crisis, leading to a heartwarming resolution and the successful establishment of their goal."
        backstory1 = f"An ambitious student trying to balance academics with the project of {story_summary_lc}."
        backstory2 = f"A supportive classmate who brings technical skills and focus to their goal of {story_summary_lc}."
        backstory3 = f"A strict professor who pushes them to excel and demands compliance for {story_summary_lc}."
    elif is_married or is_romance:
        logline = f"Driven by their deep connection, {char1_name} and {char2_name} fight to build their life together and achieve {story_summary_lc}, overcoming personal doubts and the skepticism of {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} are focusing on their dream of {story_summary_lc}. "
            f"However, they quickly realize that the path forward is filled with complications, especially with {char3_name} questioning their readiness and adding pressure.\n\n"
            f"During the second act at {loc_action}, the stakes escalate. Financial and emotional hurdles test the core of their partnership. "
            f"A heated argument about resource management leads to a temporary split, threatening their future together.\n\n"
            f"In the dramatic climax at {loc_climax}, a sudden personal emergency forces them to reunite. "
            f"Working together, they combine their strengths to overcome the crisis, achieving their goal of {story_summary_lc} and reinforcing their unbreakable bond."
        )
        theme = f"The power of trust, compromise, and mutual support required to achieve {story_summary_lc}."
        genre_analysis = f"The story operates as a classic Romance/Drama. It integrates major genre conventions by placing the main characters in a setting ({loc_main}) that challenges their ability to achieve their goal of {story_summary_lc}. The target audience of {target_audience} will connect with the relatable emotional stakes, while the transitions between {loc_main} and {loc_action} provide excellent cinematic opportunities."
        audience_insights = f"Highly appealing to couples and drama lovers. Demographics skewing towards {target_audience} will appreciate the relationship dynamics and core struggle of {story_summary_lc}."
        tagline = f"In love and life, partnership is everything. CineForge presents a gripping new vision of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} as they make preparation for {story_summary_lc}. They establish their partnership, resources, and schedule, but a minor disagreement over resources and scheduling escalates, threatening to derail their plans."
        act_2_desc = f"The stakes escalate as {char1_name} and {char2_name} face critical setbacks and hurdles at {loc_action}. {char1_name} wants to take a safe, traditional route, whereas {char2_name} insists on taking a creative risk, leading to a clash of ideologies and a temporary split between the two collaborators."
        act_3_desc = f"A sudden emergency related to their dream of {story_summary_lc} forces {char1_name} and {char2_name} to set aside their differences and work together at {loc_climax}. They combine their skills to resolve the crisis, leading to a heartwarming resolution and the successful establishment of their goal."
        backstory1 = f"A dedicated partner who has committed all their effort to building their joint dream of {story_summary_lc}."
        backstory2 = f"A loving spouse who provides the creative spark and emotional anchor for {story_summary_lc}."
        backstory3 = f"A senior family member or neighbor who offers traditional wisdom and occasional warnings about {story_summary_lc}."
    else:
        logline = f"Driven by the dream of {story_summary_lc}, {char1_name} and {char2_name} navigate unexpected personal and environmental complications in {loc_main.split(' - ')[0]}, facing crucial tests under the watchful eyes of {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} are dedicating all their energy "
            f"towards {story_summary_lc}. However, they quickly realize that the path forward is filled with complications. "
            f"A minor disagreement over resources and scheduling escalates, threatening to derail their plans, while "
            f"the unexpected intervention of {char3_name} adds significant localized pressure.\n\n"
            f"During the second act at {loc_action}, the stakes escalate. They face critical setbacks and hurdles "
            f"that test the core of their partnership. {char1_name} wants to take a safe, traditional route, whereas "
            f"{char2_name} insists on taking a creative risk to finalize their goals. This clash of ideologies reaches "
            f"a boiling point, leading to a temporary split between the two collaborators.\n\n"
            f"In the dramatic climax at {loc_climax}, a sudden emergency directly related to their dream of "
            f"{story_summary_lc} forces them to set aside their differences. Working together, they combine "
            f"{char1_name}'s practical skills and {char2_name}'s creative passion to resolve the crisis. The story "
            f"ends in a heartwarming resolution, showcasing the successful establishment of their goal."
        )
        theme = f"The power of cooperation, perseverance, and compromise required to bring the dream of {story_summary_lc} to life."
        genre_analysis = f"The story operates as a classic Drama. It integrates major genre conventions by placing the main characters in a setting ({loc_main}) that challenges their ability to achieve their goal of {story_summary_lc}. The target audience of {target_audience} will connect with the relatable emotional stakes, while the transitions between {loc_main} and {loc_action} provide excellent cinematic opportunities."
        audience_insights = f"Highly appealing to general drama fans. Demographics skewing towards {target_audience} will appreciate the relatable emotional stakes as they strive for {story_summary_lc}."
        tagline = f"A journey of a thousand steps begins with one bold dream. CineForge presents a gripping new vision of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} as they make preparation for {story_summary_lc}. They establish their partnership, resources, and schedule, but a minor disagreement over resources and scheduling escalates, threatening to derail their plans."
        act_2_desc = f"The stakes escalate as {char1_name} and {char2_name} face critical setbacks and hurdles at {loc_action}. {char1_name} wants to take a safe, traditional route, whereas {char2_name} insists on taking a creative risk, leading to a clash of ideologies and a temporary split between the two collaborators."
        act_3_desc = f"A sudden emergency related to their dream of {story_summary_lc} forces {char1_name} and {char2_name} to set aside their differences and work together at {loc_climax}. They combine their skills to resolve the crisis, leading to a heartwarming resolution and the successful establishment of their goal."
        backstory1 = f"A focused professional who has invested everything into the dream of {story_summary_lc}."
        backstory2 = f"An imaginative creator who brings the passion and design vision to their goal of {story_summary_lc}."
        backstory3 = f"An experienced local figure who is highly skeptical about their plans for {story_summary_lc} but offers critical advice."

    # Scenes Breakdown
    scenes = [
        {
            "scene_number": 1,
            "location": loc_main_header,
            "characters": f"{char1_name}, {char2_name}",
            "objective": f"Establish the launch of their plan for {story_summary_lc} and show initial setup hurdles.",
            "duration": "3 mins"
        },
        {
            "scene_number": 2,
            "location": f"INT. ENTRANCE HALLWAYS - DAY",
            "characters": f"{char1_name}, {char3_name}",
            "objective": f"{char3_name} drops in unexpectedly, warning them about local challenges in achieving {story_summary_lc}.",
            "duration": "2 mins"
        },
        {
            "scene_number": 3,
            "location": loc_action_header,
            "characters": f"{char1_name}, {char2_name}",
            "objective": f"A funny, high-stakes scene showing the characters working directly on {story_summary_lc}.",
            "duration": "4 mins"
        },
        {
            "scene_number": 4,
            "location": loc_main_header,
            "characters": f"{char2_name}, {char3_name}",
            "objective": f"{char3_name} offers a surprising local tip, helping {char2_name} set up a critical solution.",
            "duration": "3 mins"
        },
        {
            "scene_number": 5,
            "location": loc_climax_header,
            "characters": f"{char1_name}, {char2_name}",
            "objective": f"The emotional climax: resolving the final emergency to save their dream of {story_summary_lc}.",
            "duration": "4 mins"
        }
    ]

    # Determine roles for storyboard prompt descriptions
    if is_married:
        char1_role = "a young husband"
        char2_role = "a young wife"
        char3_role = "an elderly neighbor woman"
    elif is_college:
        char1_role = "a young male student"
        char2_role = "a young female student"
        char3_role = "a college friend"
    elif is_space:
        char1_role = "an astronaut captain"
        char2_role = "a female spaceship navigator"
        char3_role = "a stern spaceship commander"
    elif is_chef:
        char1_role = "a professional chef"
        char2_role = "a young woman assistant"
        char3_role = "an elderly food critic"
    elif is_detective:
        char1_role = "a detective in a trench coat"
        char2_role = "a female forensic investigator"
        char3_role = "a senior police officer"
    else:
        char1_role = "a young man"
        char2_role = "a young woman"
        char3_role = "a supporting character"

    # Storyboard Prompts
    storyboards = []
    angles = ["Wide shot", "Close-up", "Low-angle medium shot", "Establishing overhead shot", "Two-shot tracking"]
    lightings = ["Low-key dramatic lighting", "Warm morning sunlight", "Golden hour backlight", "Cozy interior light", "Soft lamp lighting"]
    moods = ["Suspenseful", "Heartwarming", "Energetic", "Tense", "Joyful"]
    
    for i, scene in enumerate(scenes):
        num = scene["scene_number"]
        loc = scene["location"]
        chars = scene["characters"]
        
        # Replace proper names with roles to prevent AI confusion
        chars_cleaned = chars
        chars_cleaned = chars_cleaned.replace(char1_name, char1_role)
        chars_cleaned = chars_cleaned.replace(char2_name, char2_role)
        chars_cleaned = chars_cleaned.replace(char3_name, char3_role)
        chars_cleaned = chars_cleaned.replace(char1_name.lower(), char1_role)
        chars_cleaned = chars_cleaned.replace(char2_name.lower(), char2_role)
        chars_cleaned = chars_cleaned.replace(char3_name.lower(), char3_role)
        
        angle = angles[i % len(angles)]
        lighting = lightings[i % len(lightings)]
        mood = moods[i % len(moods)]
        
        prompt = f"Cinematic film storyboard panel sketch, charcoal pencil drawing, {loc.lower()}, featuring {chars_cleaned.lower()}, {angle.lower()}, {lighting.lower()}, film concept art style, highly detailed composition."
        
        storyboards.append({
            "scene_number": num,
            "prompt": prompt,
            "camera_angle": angle,
            "lighting": lighting,
            "mood": mood
        })

    # Screenplay Dialogue Selection
    action_item = "this project"
    details_line = "We need to get the planning, permits, and resources sorted out."
    funny_line = "I thought this would be a simple execution, not a full-time logistics puzzle."
    parenthetical = "wearily"
    
    if is_married:
        action_item = "our new life setup"
        details_line = "We've only been married for two weeks, and we're already arguing about where to place the boxes."
        funny_line = "Next time, we order tea and samosas from the corner stall. Deal?"
        parenthetical = "smiling"
    elif is_chef:
        action_item = "the kitchen setup and recipe testing"
        details_line = "The ovens are warming up, but the recipe still needs tweaking to get the local flavor right."
        funny_line = "I followed the recipe, but it looks like charcoal instead of a gourmet dish."
        parenthetical = "tasting from a spoon"
    elif is_college:
        action_item = "our finals research notes"
        details_line = "The seminar is tomorrow morning. We've got the main themes, but the analysis is missing."
        funny_line = "I only get inspired when I'm under extreme pressure."
        parenthetical = "whispering in the library"
    elif is_detective:
        action_item = "the suspect case files"
        details_line = "The timestamps from the security footage don't match up. Someone edited the logs."
        funny_line = "This is the third cup of black coffee, and the clues are still spinning."
        parenthetical = "lighting a cigarette"
    elif is_space:
        action_item = "the starship reactor core diagnostics"
        details_line = "The core temperature is fluctuating. We have less than ten minutes to stabilize the grid."
        funny_line = "I was promised a scenic view of the galaxy, not a reactor meltdown."
        parenthetical = "monitoring the console"

    screenplay_text = f"""FADE IN:

{loc_main_header.upper()}

Shafts of natural light illuminate the room. Standard materials are scattered across a wooden table. 

{c1} stands in the center of the room, holding a notepad and looking overwhelmed. {c2} enters, carrying a box, and stops to look at him.

{c1}
(sighing, pointing at the plans)
          We've been working on this for days, {char2_name}. The plan to start {story_summary_lc} is harder than it looked on paper.

{c2}
(setting down the box, smiling)
          {char1_name}, of course it is. But we didn't start this because it was easy. We started it because we believed in it.

{c1}
          I know, but look at this. {details_line}

{c2} walks over, looking at the notepad. She taps a line gently.

{c2}
          We can adjust. We are a team now.

{c1}
({parenthetical})
          {funny_line}

{c2}
(laughs)
          Deal. Now let's get back to work on {story_summary_lc}. We have a dream to build.

FADE OUT.
"""

    # Sound Design
    foley = "Footsteps, papers rustling, opening boxes, keys turning in locks."
    if is_chef:
        foley = "Spatula scraping a pan, tea boiling, ovens timer pinging, flour bags rustling, plates clinking."
    elif is_space:
        foley = "Console buttons clicking, computerized alarm beep, hum of ventilation fans, metal hatch sealing."
    elif is_detective:
        foley = "Rain tapping on window, camera shutter clicking, drawers sliding, metallic click of lockpicks."
    elif is_college:
        foley = "Books sliding on tables, pages rustling, whispers, heavy backpack zipper opening."

    sound_design = {
        "background_music": f"A dynamic score fitting a {genre} style. The music begins with a soft, hopeful acoustic melody (84 BPM) representing the startup of {story_summary_lc}, shifting to high-contrast strings during the climax, and ending with a warm, resolving orchestration.",
        "ambience": f"Environmental sounds matching {loc_main.split(' - ')[0].lower()}, with distant chatter, soft wind, and localized sound effects corresponding to {story_summary_lc}.",
        "foley_effects": foley,
        "dialogue_treatment": f"Crisp, clean dialogue for {char1_name} and {char2_name} with natural room acoustic reverb. Close-mic proximity for emotional moments.",
        "scene_sound_notes": f"Scene 1: Ambient hum of {loc_main.lower()} fades as {char1_name} and {char2_name} discuss {story_summary_lc}. Scene 3: Fast-tempo music rises during action. Scene 5: Warm resolution motif."
    }

    # Production Plan
    props = ["Notebooks", "folders", "a communication device", "planning board"]
    if is_chef:
        props = ["Flour bags", "baking pans", "ovens", "chef aprons", "pastry display cases"]
    elif is_space:
        props = ["Spacesuits", "control console panels", "glowing canisters", "scanners"]
    elif is_detective:
        props = ["Evidence bags", "magnifying glass", "old case files", "badge", "camera"]
        
    production_plan = {
        "shooting_locations": f"1. {loc_main.replace('INT. ', '').title()}: Chosen setting to represent the headquarters for {story_summary_lc}. 2. {loc_action.replace('EXT. ', '').title()}: Outdoor settings to show the characters active in their environment.",
        "required_props": ", ".join(props) + f", personal items for {char1_name} and {char2_name}",
        "equipment": "Camera: Sony FX3 or RED Komodo for dynamic, mobile shooting. Lenses: 24-70mm zoom and 50mm prime. G&E: Portable LED mats (Amaran) and reflector boards.",
        "crew_suggestions": "Director, Director of Photography, Gaffer, Sound Recordist, Art Director (to set up the location details), and Production Assistant.",
        "estimated_shoot_days": f"3 days (Day 1: Setup and interior dialogs between {char1_name} and {char2_name}, Day 2: Exterior action on the streets, Day 3: Climax resolution)."
    }

    # Budget Plan (Dynamic INR calculation)
    scale_factor = 1.0
    if "space" in idea_lower or "sci-fi" in genre_lower or "action" in genre_lower or "thriller" in genre_lower:
        scale_factor = 2.0
    if "feature" in duration_length.lower():
        scale_factor *= 5.0
    elif "series" in duration_length.lower():
        scale_factor *= 8.0
        
    pre_val = int(150000 * scale_factor)
    prod_val = int(550000 * scale_factor)
    post_val = int(250000 * scale_factor)
    total_val = pre_val + prod_val + post_val
    
    def format_rupees(val):
        s = str(val)
        if len(s) <= 3:
            return f"₹{s}"
        elif len(s) <= 5:
            return f"₹{s[:-3]},{s[-3:]}"
        else:
            return f"₹{s[:-5]},{s[-5:-3]},{s[-3:]}"
            
    pre_cost = format_rupees(pre_val)
    prod_cost = format_rupees(prod_val)
    post_cost = format_rupees(post_val)
    total_budget = f"{format_rupees(total_val)} (INR)"
    
    cost_saving_tips = (
        f"1. Shoot in real locations matching {loc_main.split(' - ')[0].lower()} to save on studio construction fees.\n"
        f"2. Use local catering and crew from nearby regions to eliminate travel and lodging expenses.\n"
        f"3. Utilize natural daylight panels rather than heavy G&E generator setups.\n"
        f"4. Leverage local actors or student talent who want to build their portfolios for {story_summary_lc}."
    )

    return {
        "story_analysis": {
            "genre_analysis": genre_analysis,
            "theme": theme,
            "logline": logline,
            "synopsis": synopsis,
            "audience_insights": audience_insights,
            "tagline": tagline
        },
        "narrative_structure": {
            "act_1": {
                "title": "Act 1: Setting the Goal",
                "description": act_1_desc,
                "conflict": f"Initial doubts and external advice from {char3_name} make them question their plans.",
                "rising_action": f"Taking the first big step, they head to the location to secure their resources."
            },
            "act_2": {
                "title": "Act 2: Rising Complications",
                "description": act_2_desc,
                "rising_action": f"A major misunderstanding or setback occurs, escalating tension between {char1_name} and {char2_name}.",
                "climax": f"A heated argument at {loc_action.split(' - ')[0]} leads to a fallout, leaving their project in jeopardy."
            },
            "act_3": {
                "title": "Act 3: Climax & Success",
                "description": act_3_desc,
                "climax": f"They confront the ultimate challenge at {loc_climax}, resolving their conflict through teamwork.",
                "resolution": f"With the goal achieved, {char1_name} and {char2_name} establish a stronger bond, celebrating their success."
            }
        },
        "characters": {
            "characters": [
                {
                    "name": char1_name,
                    "age": char1_age,
                    "backstory": backstory1,
                    "personality": "Pragmatic, structured, detail-oriented, but gets easily stressed.",
                    "goals": f"To successfully achieve their goal of {story_summary_lc}.",
                    "strengths": "Planning, analytical thinking, resourcefulness.",
                    "weaknesses": "Fear of failure, struggles to adapt to sudden changes.",
                    "arc": "Learns to trust their partner and value creativity over rigid rules."
                },
                {
                    "name": char2_name,
                    "age": char2_age,
                    "backstory": backstory2,
                    "personality": "Creative, expressive, optimistic, and highly intuitive.",
                    "goals": f"To prove that their creative vision for {story_summary_lc} can succeed.",
                    "strengths": "Out-of-the-box thinking, communication, artistic design.",
                    "weaknesses": "Impulsive, easily distracted, avoids logistics.",
                    "arc": "Learns the value of organization, planning, and compromise."
                },
                {
                    "name": char3_name,
                    "age": char3_age,
                    "backstory": backstory3,
                    "personality": "Nosey, opinionated, authoritative, but deep down wants to help.",
                    "goals": "To advise the main characters, often creating minor complications.",
                    "strengths": "Deep local knowledge, connections, life experience.",
                    "weaknesses": "Stubborn, lacks personal boundaries, talks too much.",
                    "arc": "Learns to step back and trust the younger generation to succeed."
                }
            ]
        },
        "scene_breakdown": {"scenes": scenes},
        "storyboard": {"storyboards": storyboards},
        "screenplay": screenplay_text,
        "sound_design": sound_design,
        "production_plan": production_plan,
        "budget_plan": {
            "pre_production": {
                "cost": pre_cost,
                "details": f"Script prep & editing for {story_summary_lc}, scouting location fees, permits & casting sessions for {char1_name} and {char2_name}."
            },
            "production": {
                "cost": prod_cost,
                "details": f"Camera Sony FX3 rental, crew day-rates, actor day-rates for {char1_name} and {char2_name}, props, catering & transport for shooting {story_summary_lc}."
            },
            "post_production": {
                "cost": post_cost,
                "details": f"Editing labor, sound mixing, color grading sessions, original score composition, backups & licensing."
            },
            "total_budget": total_budget,
            "cost_saving_tips": cost_saving_tips
        }
    }

def generate_mock_scene_script(story_idea, genre, scene_number, location, scene_characters, objective, duration, characters_list=None):
    char_names = []
    if characters_list:
        for c in characters_list:
            name = ""
            if isinstance(c, dict):
                name = c.get("name", "")
            elif isinstance(c, str):
                name = c
            if name and not is_invalid_character_name(name):
                char_names.append(name)
    
    # Try to extract names from story_idea if characters_list doesn't have names
    if not char_names:
        char_names = extract_characters_from_idea(story_idea)
                    
    if not char_names:
        char_names = ["Rohan", "Priya", "Sharmaji"]
        
    chars = [c.strip() for c in (scene_characters or "").split(",") if c.strip()]
    speaking_chars = []
    for c in chars:
        if c and not is_invalid_character_name(c):
            if c not in speaking_chars:
                speaking_chars.append(c)
            
    for c in char_names:
        if c not in speaking_chars:
            speaking_chars.append(c)
            
    while len(speaking_chars) < 3:
        speaking_chars.append(f"CHARACTER {len(speaking_chars) + 1}")
        
    c1 = speaking_chars[0]
    c2 = speaking_chars[1]
    c3 = speaking_chars[2]

    # Extract dynamic story phrase from story_idea
    idea_trimmed = extract_raw_pitch(story_idea)
    story_summary_lc = idea_trimmed[0].lower() + idea_trimmed[1:] if idea_trimmed else "our project"

    s_num_str = str(scene_number)
    
    if s_num_str == "1":
        script = f"""FADE IN:

{location.upper()}

The morning sun streams into the room, illuminating sheets of drafts and project layouts scattered across a large table. 

{c1.upper()} stands in the center of the room, looking overwhelmed by the initial setup. {c2.upper()} enters carrying a warm beverage, taking in the scene.

{c2.upper()}
(smiling, holding out the cup)
          You have been working on this setup for hours, {c1}. Here, take a break.

{c1.upper()}
(taking it, sighing)
          Thank you, {c2}. But I can't stop thinking about it. We are finally initiating our dream of {story_summary_lc}. It's exciting but daunting.

{c2.upper()}
          It is a big step. But we have a clear objective: to establish the foundation of {story_summary_lc}. If we take it step by step, we can make it a reality.

{c1.upper()}
(nods, feeling motivated)
          You are right. Let's stay focused. We have about {duration} to map out the next steps.

{c2.upper()}
          Exactly. Let's get to work.
"""
    elif s_num_str == "2":
        script = f"""{location.upper()}

The atmosphere is quiet. {c1.upper()} is double-checking plans, when {c2.upper()} enters the hallway, looking skeptical.

{c2.upper()}
(crossing arms)
          I saw the blueprints you laid out for {story_summary_lc}. It is a very ambitious plan, {c1}.

{c1.upper()}
          Thank you, {c2}. We are dedicating everything to make it work.

{c2.upper()}
          Ambition is good, but reality is harsh. The local regulations and resource limits here are very strict. You are going to face massive roadblocks.

{c1.upper()}
(determined)
          We have anticipated some challenges. But we believe in this dream.

{c2.upper()}
          Believing is not enough. You have about {duration} to prove you have a stable setup, or the local committee will halt your project.

{c1.upper()}
          I understand the stakes. We will double our efforts to comply with all rules.
"""
    elif s_num_str == "3":
        script = f"""{location.upper()}

The air is thick with tension as {c1.upper()} and {c2.upper()} stand near the control desk. They have been working non-stop on {story_summary_lc}.

{c1.upper()}
(pointing at the plans)
          If we take this shortcut, we can bypass the delays and finalize {story_summary_lc} tonight!

{c2.upper()}
(shaking head, defensive)
          No, {c1}! That is too risky. If it fails, we lose everything. We must follow the traditional safety guidelines.

{c1.upper()}
          Traditional guidelines will delay us by weeks! We need to take this risk to succeed.

{c2.upper()}
(raising voice)
          There is a difference between a calculated risk and reckless behavior! I won't let you ruin our dream of {story_summary_lc} because you are impatient.

{c1.upper()}
          Maybe you don't believe in {story_summary_lc} as much as I do!

{c2.upper()}
(hurt, backing away)
          How can you say that? If you cannot trust my judgment, then maybe we shouldn't be doing this together.

{c2.upper()} walks out, slamming the door. {c1.upper()} stands alone, staring at the blueprints.
"""
    elif s_num_str == "4":
        script = f"""{location.upper()}

The lighting is soft. {c1.upper()} is analyzing the files, looking frustrated. {c2.upper()} walks over, observing the work.

{c2.upper()}
(observing, holding a notepad)
          Still struggling with the resource layout for {story_summary_lc}?

{c1.upper()}
(sighing)
          Yes, {c2}. It seems we've hit a roadblock. We cannot bypass the safety rules, but we don't have the time to go the long way.

{c2.upper()}
(smiling)
          You young folks are always in a rush. Sometimes, you need local experience. Here is a tip: there is a secondary permit office that handles expedited requests for community projects.

{c1.upper()}
(looking up, surprised)
          Really? I didn't see that in the official guidelines.

{c2.upper()}
          It is an unlisted protocol. If you apply there, you can secure the clearance in {duration}.

{c1.upper()}
(smiling, relieved)
          This is exactly what we need! Thank you, {c2}. I must go share this with the team and get {story_summary_lc} back on track.
"""
    else:
        script = f"""{location.upper()}

Alarms beep softly in the background. {c1.upper()} is typing at the control panel, while {c2.upper()} is holding a critical cable connection.

{c1.upper()}
(shouting)
          The system temperature is fluctuating! We need to stabilize the power grid!

{c2.upper()}
(determined)
          I have the bypass line ready! Trigger the system restart on my mark!

{c1.upper()}
          It's too much pressure on the connection! Can you hold it?

{c2.upper()}
          I won't let go! For our dream of {story_summary_lc}! Mark!

{c1.upper()} hits the switch. A brilliant green status light illuminates. The alarms stop, replaced by a steady, peaceful hum.

{c1.upper()}
(letting out a breath)
          It worked. The system is stable.

{c2.upper()}
          We actually did it. The goal of {story_summary_lc} is real.

{c1.upper()} walks over and embraces her.

{c1.upper()}
          We did it together.

FADE OUT.
"""
        
    return script

