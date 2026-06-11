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
    is_sports = any(w in idea_lower for w in ["cricket", "football", "soccer", "sports", "athlete", "player", "game", "tournament", "team", "play", "match", "athletics", "stadium", "pitch", "ground", "gym", "coach", "train", "selection", "practice"]) or any(w in genre_lower for w in ["sports", "athletic", "game", "cricket"])
    is_horror = any(w in idea_lower for w in ["horror", "ghost", "haunted", "spirit", "demon", "scary", "creepy", "witch", "monster", "paranormal", "vampire", "zombie", "dark"]) or "horror" in genre_lower
    is_comedy = any(w in idea_lower for w in ["comedy", "funny", "hilarious", "joke", "prank", "laugh"]) or "comedy" in genre_lower
    is_action = any(w in idea_lower for w in ["action", "fight", "chase", "escape", "adventure", "danger", "mission", "weapon", "warrior", "battle", "soldier"]) or any(w in genre_lower for w in ["action", "adventure", "thriller"])

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
    elif is_sports:
        char1_name = "Arjun"
        char2_name = "Coach Kabir"
        char3_name = "Selector Sharma"
    elif is_horror:
        char1_name = "Vikram"
        char2_name = "Neha"
        char3_name = "Panditji"
    elif is_comedy:
        char1_name = "Raju"
        char2_name = "Baburao"
        char3_name = "Shyam"
    elif is_action:
        char1_name = "Agent Vikram"
        char2_name = "Zoya"
        char3_name = "Chief Malik"
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
    loc_mid = "INT. ENTRANCE HALLWAYS - DAY" # default fallback
    
    if len(unique_locs) >= 2:
        loc_main = f"INT. {unique_locs[0].upper()} - DAY"
        loc_action = f"EXT. {unique_locs[1].upper()} STREETS - DUSK"
        loc_climax = f"INT. {unique_locs[0].upper()} - NIGHT"
        loc_mid = f"INT. {unique_locs[0].upper()} CORRIDOR - DAY"
    elif len(unique_locs) == 1:
        loc_name = unique_locs[0].upper()
        if loc_name in ["GOA", "MUMBAI", "DELHI", "BANGALORE", "LONDON", "PARIS", "SPACE"]:
            loc_main = f"INT. APARTMENT IN {loc_name} - DAY"
            loc_action = f"EXT. {loc_name.title()} STREETS - DAY"
            loc_climax = f"INT. APARTMENT IN {loc_name} - NIGHT"
            loc_mid = f"INT. APARTMENT IN {loc_name} HALLWAY - DAY"
        else:
            loc_main = f"INT. {loc_name} - DAY"
            loc_action = f"EXT. {loc_name} ENTRANCE - DUSK"
            loc_climax = f"INT. {loc_name} - NIGHT"
            loc_mid = f"INT. {loc_name} HALLWAY - DAY"
    else:
        if is_space:
            loc_main = "INT. SPACESHIP BRIDGE - DAY"
            loc_action = "EXT. PLANETARY SURFACE - DAY"
            loc_climax = "INT. SPACESHIP REACTOR ROOM - NIGHT"
            loc_mid = "INT. SPACESHIP CORRIDOR - DAY"
        elif is_scifi:
            loc_main = "INT. FUTURISTIC LABORATORY - DAY"
            loc_action = "EXT. FUTURISTIC CITY STREETS - NIGHT"
            loc_climax = "INT. FUTURISTIC LABORATORY - NIGHT"
            loc_mid = "INT. LABORATORY CORRIDOR - DAY"
        elif is_detective:
            loc_main = "INT. DIMLY LIT OFFICE - NIGHT"
            loc_action = "EXT. RAIN-SLICKED ALLEY - NIGHT"
            loc_climax = "INT. ABANDONED WAREHOUSE - NIGHT"
            loc_mid = "INT. POLICE STATION CORRIDOR - DAY"
        elif is_chef:
            loc_main = "INT. RESTAURANT KITCHEN - DAY"
            loc_action = "EXT. OUTDOOR PATIO - DUSK"
            loc_climax = "INT. DINING ROOM - NIGHT"
            loc_mid = "INT. RESTAURANT PANTRY - DAY"
        elif is_school:
            loc_main = "INT. HIGH SCHOOL CLASSROOM - DAY"
            loc_action = "EXT. SCHOOL PLAYGROUND - DAY"
            loc_climax = "INT. HIGH SCHOOL CLASSROOM - NIGHT"
            loc_mid = "INT. SCHOOL HALLWAY - DAY"
        elif is_college:
            loc_main = "INT. UNIVERSITY LIBRARY - DAY"
            loc_action = "EXT. CAMPUS QUAD - DAY"
            loc_climax = "INT. COLLEGE AUDITORIUM - NIGHT"
            loc_mid = "INT. COLLEGE CORRIDOR - DAY"
        elif is_sports:
            loc_main = "INT. SPORTS ACADEMY LOCKER ROOM - DAY"
            loc_action = "EXT. PRACTICE PITCH GROUND - DAY"
            loc_climax = "EXT. SELECTION MATCH STADIUM - NIGHT"
            loc_mid = "INT. STADIUM HALLWAY - DAY"
        elif is_horror:
            loc_main = "INT. HAUNTED HOUSE LIVING ROOM - NIGHT"
            loc_action = "EXT. FOGGY FOREST PATH - NIGHT"
            loc_climax = "INT. HAUNTED HOUSE BASEMENT - NIGHT"
            loc_mid = "INT. HAUNTED HOUSE HALLWAY - NIGHT"
        elif is_comedy:
            loc_main = "INT. BUSY CAFE - DAY"
            loc_action = "EXT. NEIGHBORHOOD STREETS - DAY"
            loc_climax = "INT. BUSY CAFE - NIGHT"
            loc_mid = "INT. CAFE ENTRANCE - DAY"
        elif is_action:
            loc_main = "INT. CONTROL ROOM - DAY"
            loc_action = "EXT. RUGGED MOUNTAIN PASS - DAY"
            loc_climax = "EXT. ROOFTOP HELIPAD - NIGHT"
            loc_mid = "INT. BASEMENT CORRIDOR - DAY"
        elif is_married or is_romance:
            loc_main = "INT. COZY APARTMENT - DAY"
            loc_action = "EXT. SCENIC PARK - DUSK"
            loc_climax = "INT. COZY APARTMENT - NIGHT"
            loc_mid = "INT. APARTMENT LOBBY - DAY"
        else:
            loc_main = "INT. COZY OFFICE - DAY"
            loc_action = "EXT. NEIGHBORHOOD STREETS - DAY"
            loc_climax = "INT. COZY OFFICE - NIGHT"
            loc_mid = "INT. ENTRANCE HALLWAYS - DAY"

    loc_main_header = loc_main
    loc_action_header = loc_action
    loc_climax_header = loc_climax
    loc_mid_header = loc_mid

    loc_main = clean_location_for_prose(loc_main)
    loc_action = clean_location_for_prose(loc_action)
    loc_climax = clean_location_for_prose(loc_climax)
    loc_mid = clean_location_for_prose(loc_mid)

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
        scene_1_obj = f"Introduce Captain {char1_name} and navigator {char2_name} planning the interstellar journey for {story_summary_lc}."
        scene_2_obj = f"Commander {char3_name} enters the ship corridor to demand compliance with critical galactic protocols."
        scene_3_obj = f"A high-stakes scene on the planet surface where {char1_name} and {char2_name} face harsh atmospheric conditions."
        scene_4_obj = f"Commander {char3_name} reveals a classified telemetry report, pointing out a safer path for the ship."
        scene_5_obj = f"The emotional climax: stabilizing the reactor core to successfully execute {story_summary_lc}."
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
        scene_1_obj = f"Introduce {char1_name} and {char2_name} inside the lab preparing the technological setup for {story_summary_lc}."
        scene_2_obj = f"{char3_name} checks the laboratory corridor, warning about high energy leakage risks."
        scene_3_obj = f"A tense scene in the futuristic city streets where they run field tests for {story_summary_lc}."
        scene_4_obj = f"{char3_name} shares a code override key, allowing them to bypass system restrictions."
        scene_5_obj = f"The climax: preventing a critical database wipe to secure {story_summary_lc}."
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
        scene_1_obj = f"Detective {char1_name} and partner {char2_name} review the secret files to start investigating {story_summary_lc}."
        scene_2_obj = f"Inspector {char3_name} confronts them in the corridor, warning them to back off the case."
        scene_3_obj = f"A suspenseful night stakeout in the rain-slicked alley to trace a suspect linked to {story_summary_lc}."
        scene_4_obj = f"{char3_name} delivers a crucial forensics tip that unlocks a hidden connection."
        scene_5_obj = f"The high-stakes climax: cornering the suspect at the warehouse and solving the case of {story_summary_lc}."
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
        scene_1_obj = f"Chef {char1_name} and partner {char2_name} prep the kitchen and debate menu designs for {story_summary_lc}."
        scene_2_obj = f"Food critic {char3_name} inspects the pantry, expressing skepticism about their culinary concept."
        scene_3_obj = f"A hectic, high-pressure dinner service where {char1_name} and {char2_name} clash over cooking times."
        scene_4_obj = f"{char3_name} points out a secret local ingredient, inspiring {char2_name} to revise the main dish."
        scene_5_obj = f"The culinary climax: serving the final signature dish to save the reputation of {story_summary_lc}."
    elif is_school:
        logline = f"Determined to succeed, students {char1_name} and {char2_name} navigate classroom challenges and deadlines to achieve {story_summary_lc}, under the strict supervision of teacher {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where classmates {char1_name} and {char2_name} start brainstorming ideas for {story_summary_lc}. "
            f"Their initial plans face setbacks when their teacher {char3_name} warns them about a strict evaluation criteria.\n\n"
            f"During the second act at {loc_action}, pressure mounts. A major disagreement on how to present {story_summary_lc} leads to a falling out, putting their grades in jeopardy.\n\n"
            f"In the dramatic climax at {loc_climax}, a sudden deadline change forces them to coordinate. "
            f"Combining their skills, they deliver a brilliant presentation, securing the approval of {char3_name}."
        )
        theme = f"Learning, team spirit, and overcoming doubts to bring {story_summary_lc} to life."
        genre_analysis = f"The story operates as a school drama. It integrates genre conventions by placing characters in a setting ({loc_main}) that tests their academic ability. The target audience of {target_audience} will connect with the schoolyard stakes, while the transitions between {loc_main} and {loc_action} offer visual contrast."
        audience_insights = f"Highly appealing to family and teenage demographics. Skewing towards {target_audience}, viewers will appreciate the relatable peer pressures surrounding {story_summary_lc}."
        tagline = f"Big dreams start in small classrooms. CineForge presents a fresh story of {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} work together in {loc_main} as they plan {story_summary_lc}. They set their resources and schedules, but a small misunderstanding threatens their partnership."
        act_2_desc = f"Setbacks arise as they test their ideas at {loc_action}. A clash of views on safety versus risk leads to a temporary split between the students."
        act_3_desc = f"A deadline emergency regarding {story_summary_lc} forces them to reunite at {loc_climax}. Combining practical and creative skills, they deliver a successful presentation."
        backstory1 = f"An enthusiastic student eager to show their capability in mastering {story_summary_lc}."
        backstory2 = f"A creative classmate who brings unique ideas and design aesthetics to {story_summary_lc}."
        backstory3 = f"A strict but caring teacher who wants to guide the students to excel in {story_summary_lc}."
        scene_1_obj = f"Introduce students {char1_name} and {char2_name} as they start planning their project for {story_summary_lc}."
        scene_2_obj = f"Teacher {char3_name} catches them in the hallway, warning about project deadlines."
        scene_3_obj = f"A funny and chaotic scene on the school playground testing their prototype for {story_summary_lc}."
        scene_4_obj = f"Teacher {char3_name} provides extra materials, helping {char2_name} resolve a design flaw."
        scene_5_obj = f"The final classroom presentation: successfully demonstrating {story_summary_lc} under pressure."
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
        scene_1_obj = f"Introduce classmates {char1_name} and {char2_name} preparing their thesis presentation on {story_summary_lc}."
        scene_2_obj = f"Professor {char3_name} stops them in the corridor, criticizing their research methodology."
        scene_3_obj = f"A high-stakes campus campaign or test run where they try to gather data for {story_summary_lc}."
        scene_4_obj = f"Professor {char3_name} offers a rare reference book, helping {char2_name} resolve the theoretical equation."
        scene_5_obj = f"The dramatic presentation in the auditorium: securing approval and funding for {story_summary_lc}."
    elif is_sports:
        logline = f"Against all odds, aspiring athlete {char1_name} and Coach {char2_name} battle rigorous training and selector skepticism to qualify for {story_summary_lc}, facing critical pressure from Selector {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} undergoes intense conditioning under the supervision of Coach {char2_name} to qualify for {story_summary_lc}. "
            f"However, early visits from Selector {char3_name} warn that only top-tier performances will secure selection.\n\n"
            f"During the second act at {loc_action}, physical fatigue and differences in training methods lead to a dispute between athlete and coach, endangering their target of {story_summary_lc}.\n\n"
            f"In the dramatic climax at {loc_climax}, during a high-stakes selection match, {char1_name} plays through minor injury, working in sync with Coach {char2_name}'s game plan. "
            f"A heroic performance wins the match, securing selection and achieving their dream of {story_summary_lc}."
        )
        theme = f"Discipline, grit, and the mentor-student bond required to qualify for {story_summary_lc}."
        genre_analysis = f"The story operates as a classic Sports drama. It places characters in competitive settings ({loc_main} and {loc_climax}) to highlight physical and psychological limits. The target audience of {target_audience} will be thrilled by the training sequences and the ultimate match climax."
        audience_insights = f"Highly appealing to sports fans and inspirational drama lovers. Skewing towards {target_audience}, viewers will connect with the physical struggle and emotional release of qualifying for {story_summary_lc}."
        tagline = f"Gold is refined in fire, champions are built in sweat. CineForge presents an inspiring story of {story_summary_lc}."
        act_1_desc = f"{char1_name} and Coach {char2_name} outline the training schedule in {loc_main} to prepare for {story_summary_lc}. They establish their strategy, but early selector pressure tests their resolve."
        act_2_desc = f"The pressure mounts at {loc_action} during practice games. A dispute on whether to focus on speed or tactical safety leads to a brief split between athlete and coach."
        act_3_desc = f"At the selection match at {loc_climax}, a critical game situation forces them to reunite. Using Coach {char2_name}'s tactics, {char1_name} delivers a winning play to establish their eligibility."
        backstory1 = f"A determined and passionate athlete who has dedicated years of training to get selected for {story_summary_lc}."
        backstory2 = f"A veteran coach who sees raw potential in the athlete and wants to guide them to master {story_summary_lc}."
        backstory3 = f"A strict selector who evaluates performance indicators and demands absolute excellence for {story_summary_lc}."
        scene_1_obj = f"Introduce athlete {char1_name} and Coach {char2_name} planning the training schedule for {story_summary_lc}."
        scene_2_obj = f"Selector {char3_name} visits the locker room, warning them that only peak performance gets selection."
        scene_3_obj = f"A grueling and high-energy practice session on the pitch testing {char1_name}'s stamina and skills."
        scene_4_obj = f"Selector {char3_name} shares feedback on the rivals' weak points, helping Coach {char2_name} adjust tactics."
        scene_5_obj = f"The final match climax: {char1_name} playing under intense pressure to secure selection for {story_summary_lc}."
    elif is_horror:
        logline = f"Trapped in a haunted house, {char1_name} and {char2_name} must decipher a terrifying history to survive, while receiving mysterious warnings from Panditji {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} seek refuge or conduct research on {story_summary_lc}. "
            f"They face immediate paranormal activity, when Panditji {char3_name} warns them about a vengeful spirit haunting the location.\n\n"
            f"During the second act at {loc_action}, their attempt to escape the area leads them through a foggy forest, where the entity splits them apart, magnifying their fear.\n\n"
            f"In the dramatic climax at {loc_climax}, cornered in the basement, they combine their wits to decipher the spirit's origin. "
            f"Using a ritual item provided earlier, they banish the spirit, achieving safety and completing their goal of {story_summary_lc}."
        )
        theme = f"Fear, psychological resilience, and trusting one another to survive the paranormal while achieving {story_summary_lc}."
        genre_analysis = f"The story operates as a classic Horror/Mystery. It integrates genre conventions like isolated settings ({loc_main}) and supernatural threats. The target audience of {target_audience} will connect with the suspense, jump scares, and atmospheric tension."
        audience_insights = f"Highly appealing to horror fans and supernatural thriller enthusiasts. Demographics skewing towards {target_audience} will enjoy the dread and puzzle-solving elements related to {story_summary_lc}."
        tagline = f"Some doors should never be opened. CineForge presents a chilling nightmare about {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} settle into {loc_main} to work on {story_summary_lc}, but strange occurrences disrupt their setup."
        act_2_desc = f"As they flee or investigate at {loc_action}, the entity targets them, creating a rift of fear and leading to a temporary split between the survivors."
        act_3_desc = f"Trapped at {loc_climax}, they must unite to face the entity. They combine their clues to banish the spirit, resulting in survival."
        backstory1 = f"A skeptical investigator who tries to find rational explanations for the anomalies while pursuing {story_summary_lc}."
        backstory2 = f"A sensitive investigator who senses the paranormal energies and seeks to pacify the spirits."
        backstory3 = f"An eccentric local priest who holds the key to the estate's dark past and the solution to {story_summary_lc}."
        scene_1_obj = f"Introduce {char1_name} and {char2_name} entering the haunted living room, attempting to research {story_summary_lc}."
        scene_2_obj = f"Panditji {char3_name} warns them in the dark hallway about the malevolent spirits occupying the house."
        scene_3_obj = f"A terrifying sequence along the foggy forest path as they flee from an unexplained presence."
        scene_4_obj = f"{char3_name} reveals the history of the curse, giving {char2_name} a protective ward or clue."
        scene_5_obj = f"The basement showdown: banishing the entity to successfully survive and achieve {story_summary_lc}."
    elif is_comedy:
        logline = f"Two absolute misfits, {char1_name} and {char2_name}, concoct a ridiculous scheme to accomplish {story_summary_lc}, constantly chased by the suspicious {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} outline their absurd plan for {story_summary_lc}. "
            f"Their discussion is interrupted by the nosey neighbor {char3_name}, who suspects they are up to no good.\n\n"
            f"During the second act at {loc_action}, a chaotic mix-up on the streets ruins their primary prop, leading to a hilarious argument and a split between the two buddies.\n\n"
            f"In the dramatic climax at {loc_climax}, a comedy of errors traps them inside the venue. "
            f"They combine their silly tactics, accidentally pull off the scheme, and achieve their goal of {story_summary_lc} to everyone's shock."
        )
        theme = f"Friendship, laughter, and the unexpected success of absurd plans for {story_summary_lc}."
        genre_analysis = f"The story operates as a classic buddy comedy. It relies on situational irony, banter, and slapstick elements. The target audience of {target_audience} will enjoy the fast pacing, comical misunderstandings, and funny character quirks."
        audience_insights = f"Highly appealing to comedy lovers seeking lighthearted entertainment. Demographics skewing towards {target_audience} will enjoy the funny mistakes around {story_summary_lc}."
        tagline = f"Failing their way to the top. CineForge presents a hilarious look at {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} brainstorm their hilarious strategy in {loc_main}. However, a silly misunderstanding about funds threatens to cancel the project."
        act_2_desc = f"Setbacks peak at {loc_action} when their plans run wild. A clash of ridiculous ideas leads to a temporary split between the two collaborators."
        act_3_desc = f"A comedic emergency at {loc_climax} forces them to team up again. They pull off an accidental success, realizing their dream of {story_summary_lc}."
        backstory1 = f"A fast-talking schemer who believes they are a genius at coordinating {story_summary_lc}."
        backstory2 = f"A naive helper who brings hilarious literalism and unexpected luck to the project."
        backstory3 = f"A nosey inspector or local figure who keeps running into them, trying to figure out their plans."
        scene_1_obj = f"Introduce {char1_name} and {char2_name} discussing a hilarious scheme to pull off {story_summary_lc}."
        scene_2_obj = f"{char3_name} encounters them at the entrance, questioning their bizarre behavior and plans."
        scene_3_obj = f"A chaotic and funny chase down the neighborhood streets as their plans for {story_summary_lc} go wild."
        scene_4_obj = f"{char3_name} accidentally reveals a ridiculous shortcut, solving {char2_name}'s immediate dilemma."
        scene_5_obj = f"The final comedic showdown: pulling off the plan for {story_summary_lc} in the most unexpected way possible."
    elif is_action:
        logline = f"In a race against time, tactical agent {char1_name} and technician {char2_name} must secure a critical asset to achieve {story_summary_lc}, while dodging hostile forces led by {char3_name}."
        synopsis = (
            f"The film opens in {loc_main} where {char1_name} and {char2_name} formulate an extraction plan for {story_summary_lc}. "
            f"Their briefing is cut short when Chief {char3_name} warns of a hostile unit closing in on their position.\n\n"
            f"During the second act at {loc_action}, an intense vehicle chase and shootout on the mountain pass splits them up, forcing {char1_name} to engage solo to protect {story_summary_lc}.\n\n"
            f"In the dramatic climax at {loc_climax}, cornered on the rooftop, they coordinate air support with {char3_name}. "
            f"They defeat the hostile leader and secure the assets, successfully completing the mission for {story_summary_lc}."
        )
        theme = f"Duty, courage, and high-tech coordination required to complete the mission for {story_summary_lc}."
        genre_analysis = f"The story operates as an Action thriller. It uses high-energy set pieces like mountain chases ({loc_action}) and rooftop showdowns ({loc_climax}). The target audience of {target_audience} will be hooked by the stunts and fast-paced tension."
        audience_insights = f"Highly appealing to action, spy, and thriller fans. Skewing towards {target_audience}, viewers will appreciate the tactical details and high stakes surrounding {story_summary_lc}."
        tagline = f"Mission accepted. CineForge presents a high-octane ride for {story_summary_lc}."
        act_1_desc = f"{char1_name} and {char2_name} analyze the data coordinates in {loc_main} to plan {story_summary_lc}, but security breach alerts disrupt their setup."
        act_2_desc = f"The conflict peaks at {loc_action} during an escape run. A disagreement on tactical retreat versus engagement causes a split between the agents."
        act_3_desc = f"Cornered by hostiles at {loc_climax}, they reunite. Combining combat prowess and tech hacking, they complete the extraction."
        backstory1 = f"A highly decorated tactical agent specialized in high-risk operations for {story_summary_lc}."
        backstory2 = f"A brilliant tech expert who manages communications and systems hacking for {story_summary_lc}."
        backstory3 = f"A senior agency director who monitors the field operatives and provides support for {story_summary_lc}."
        scene_1_obj = f"Agent {char1_name} and partner {char2_name} study the tactical map in the control room to plan {story_summary_lc}."
        scene_2_obj = f"Chief {char3_name} warns them in the basement corridor that a hostile team is close to intercepting them."
        scene_3_obj = f"A high-octane chase and combat sequence through the rugged mountain pass to protect {story_summary_lc}."
        scene_4_obj = f"Chief {char3_name} coordinates air support, sending {char2_name} the GPS escape coordinates."
        scene_5_obj = f"The rooftop showdown: defeating the hostile leader and successfully completing the mission for {story_summary_lc}."
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
        scene_1_obj = f"Introduce {char1_name} and {char2_name} in their cozy apartment, sharing their shared dream of {story_summary_lc}."
        scene_2_obj = f"Family member {char3_name} drops by the lobby, raising doubts and highlighting setup costs."
        scene_3_obj = f"An emotional, high-stakes conversation in the park as they face early financial setbacks."
        scene_4_obj = f"{char3_name} offers a family heirloom or savings tip, helping {char2_name} overcome a budget limit."
        scene_5_obj = f"The heartwarming climax: celebrating their breakthrough together and achieving {story_summary_lc}."
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
        scene_1_obj = f"Introduce {char1_name} and {char2_name} planning the details of {story_summary_lc} and discussing setup hurdles."
        scene_2_obj = f"{char3_name} visits the hallway, warning them about local hurdles in achieving {story_summary_lc}."
        scene_3_obj = f"A tense, high-stakes scene showing characters working to establish {story_summary_lc}."
        scene_4_obj = f"{char3_name} shares a helpful tip, helping {char2_name} resolve a critical logistics issue."
        scene_5_obj = f"The emotional climax: resolving the final emergency to save their dream of {story_summary_lc}."

    # Scenes Breakdown
    scenes = [
        {
            "scene_number": 1,
            "location": loc_main_header,
            "characters": f"{char1_name}, {char2_name}",
            "objective": scene_1_obj,
            "duration": "3 mins"
        },
        {
            "scene_number": 2,
            "location": loc_mid_header,
            "characters": f"{char1_name}, {char3_name}",
            "objective": scene_2_obj,
            "duration": "2 mins"
        },
        {
            "scene_number": 3,
            "location": loc_action_header,
            "characters": f"{char1_name}, {char2_name}",
            "objective": scene_3_obj,
            "duration": "4 mins"
        },
        {
            "scene_number": 4,
            "location": loc_main_header,
            "characters": f"{char2_name}, {char3_name}",
            "objective": scene_4_obj,
            "duration": "3 mins"
        },
        {
            "scene_number": 5,
            "location": loc_climax_header,
            "characters": f"{char1_name}, {char2_name}",
            "objective": scene_5_obj,
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
    elif is_sports:
        action_item = "our training schedule and selection preparation"
        details_line = "The selection trials are tomorrow morning, and my muscles are still sore from the drills."
        funny_line = "If I have to run another lap, I might turn into a track hurdle."
        parenthetical = "wiping sweat from his forehead"
    elif is_horror:
        action_item = "our cursed house research"
        details_line = "The flashlight batteries are dying, and the room temperature just dropped to zero."
        funny_line = "Next time, we research a nice, bright beach. Deal?"
        parenthetical = "shivering, checking the door"
    elif is_comedy:
        action_item = "our hilarious scheme plan"
        details_line = "We've got the costumes ready, but we forgot to secure the donuts for the guard."
        funny_line = "I was expecting a smooth operation, not wearing a giant chicken suit."
        parenthetical = "grinning, holding a feather"
    elif is_action:
        action_item = "our tactical extraction map"
        details_line = "The hostile team has bypassed our firewall. We have less than five minutes before they arrive."
        funny_line = "I was promised a quiet office job, not a rooftop sniper duel."
        parenthetical = "reloading the sidearm"
    elif is_school:
        action_item = "our classroom presentation drafts"
        details_line = "The presentation starts in ten minutes, and our prototype slide is blank."
        funny_line = "I thought school was about homework, not building a functional rocket model."
        parenthetical = "hurriedly erasing the whiteboard"

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
            "tagline": tagline,
            "tone": "Suspenseful" if genre == "Thriller" else "Dramatic",
            "rating": "PG-13",
            "comparable_films": [],
            "festival_potential": "Strong potential for indie film festivals.",
            "streaming_audience_fit": "Excellent fit for SVOD streaming platforms."
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
    
    idea_lower = (story_idea or "").lower()
    genre_lower = (genre or "").lower()

    is_space = any(w in idea_lower for w in ["space", "ship", "star", "cosmic", "alien", "astronaut", "spaceship", "galaxy", "orbit", "planet", "mars", "moon"])
    is_scifi = any(w in idea_lower for w in ["robot", "robo", "chitti", "android", "ai", "machine", "futuristic", "technology", "sci-fi", "science", "laboratory", "lab", "nuclear", "physics"]) or is_space
    is_detective = any(w in idea_lower for w in ["detective", "spy", "murder", "agent", "investigation", "crime", "police"])
    is_chef = any(w in idea_lower for w in ["chef", "cooking", "food", "restaurant", "kitchen", "bakery", "cafe", "bake"])
    is_school = any(w in idea_lower for w in ["school", "teen", "kid", "child", "children", "classroom", "classmate", "high school", "middle school", "elementary", "primary school", "schoolboy", "schoolgirl", "schoolchild"])
    is_college = any(w in idea_lower for w in ["college", "university", "student", "class", "library"])
    is_married = any(w in idea_lower for w in ["married", "marriage", "couple", "wife", "husband", "wedding", "spouse", "newlywed"])
    is_romance = any(w in idea_lower for w in ["love", "romance", "romantic", "lover", "girlfriend", "boyfriend", "heart"]) or "romance" in genre_lower
    is_sports = any(w in idea_lower for w in ["cricket", "football", "soccer", "sports", "athlete", "player", "game", "tournament", "team", "play", "match", "athletics", "stadium", "pitch", "ground", "gym", "coach", "train", "selection", "practice"]) or any(w in genre_lower for w in ["sports", "athletic", "game", "cricket"])
    is_horror = any(w in idea_lower for w in ["horror", "ghost", "haunted", "spirit", "demon", "scary", "creepy", "witch", "monster", "paranormal", "vampire", "zombie", "dark"]) or "horror" in genre_lower
    is_comedy = any(w in idea_lower for w in ["comedy", "funny", "hilarious", "joke", "prank", "laugh"]) or "comedy" in genre_lower
    is_action = any(w in idea_lower for w in ["action", "fight", "chase", "escape", "adventure", "danger", "mission", "weapon", "warrior", "battle", "soldier"]) or any(w in genre_lower for w in ["action", "adventure", "thriller"])

    if s_num_str == "1":
        if is_space:
            intro_action = f"The low thrum of the ion engine vibrates through the deck. Holographic starmaps flicker above the metallic dashboard, casting a cool blue glow."
            c1_action = f"{c1.upper()} stands at the console, typing telemetry coordinates and looking tense. {c2.upper()} enters carrying a thermal flask, observing him."
            c2_parenthetical = "placing the flask on the console, smiling"
            c2_line_1 = f"You've been monitoring these charts for hours, {c1}. Take a moment."
            c1_line_1 = f"Thanks, {c2}. But with the orbital window closing, we have to stay on target. Initiating our dream of {story_summary_lc} is exciting but risky."
            c2_line_2 = f"It is a massive journey. But we have a clear objective: to establish the foundation of {story_summary_lc}. If we take it sector by sector, we can make it a reality."
            c1_line_2 = f"You are right. Let's stay focused. We have about {duration} to stabilize the telemetry."
        elif is_sports:
            intro_action = f"The smell of leather and liniment fills the locker room. Whiteboards on the walls are covered in play diagrams and selection schedules."
            c1_action = f"{c1.upper()} sits on the bench, wrapping tape around a sports shoe, looking anxious. {c2.upper()} enters holding a stopwatch, tapping it."
            c2_parenthetical = "tapping the clipboard, encouraging"
            c2_line_1 = f"Still running drills in your head, {c1}? You need to rest before the trial."
            c1_line_1 = f"I can't, {c2}. Getting selected to play for {story_summary_lc} has been my life's goal. It's exciting but daunting."
            c2_line_2 = f"Daunting is fine, but focus is better. Our clear objective is to show the selectors your technique for {story_summary_lc}. Trust your drills."
            c1_line_2 = f"You are right. Let's stay focused. We have about {duration} to review the tactical game plan."
        elif is_horror:
            intro_action = f"Dust motes dance in the beam of a single flashlight. The walls of the room are peeling, and the floorboards creak with every step."
            c1_action = f"{c1.upper()} stands in the center of the haunted room, checking a compass and looking tense. {c2.upper()} enters carrying an old book, shivering."
            c2_parenthetical = "hugging the book, looking around anxiously"
            c2_line_1 = f"This place is freezing, {c1}. We shouldn't stay here after dark."
            c1_line_1 = f"We have to, {c2}. The answers we need to complete {story_summary_lc} are hidden in these rooms. It's terrifying but necessary."
            c2_line_2 = f"It is. But we must have a clear objective: establish the safe zone and find the records of {story_summary_lc}. We stay together, always."
            c1_line_2 = f"Agreed. Let's stay focused. We have about {duration} to scan this floor before the light fades."
        elif is_detective:
            intro_action = f"Rain beats a steady rhythm against the windowpane. Shadows stretch across the floor from a dimly lit lamp, illuminating a pile of folders."
            c1_action = f"{c1.upper()} stands near the corkboard, pinning suspect photos and looking overwhelmed. {c2.upper()} enters carrying case files, pausing."
            c2_parenthetical = "setting the files down, serious"
            c2_line_1 = f"You've been staring at that board for hours, {c1}. Take a break."
            c1_line_1 = f"Thanks, {c2}. But I can't stop thinking about it. Solving the case of {story_summary_lc} is the biggest mystery of our careers."
            c2_line_2 = f"It is a complex case. But we have a clear objective: to establish the timeline of {story_summary_lc}. We analyze the clues one by one."
            c1_line_2 = f"You are right. Let's stay focused. We have about {duration} to cross-reference these logs."
        elif is_chef:
            intro_action = f"Stainless steel counters gleam under bright lights. The sound of exhaust fans hums in the background, and fresh herbs sit on a wooden table."
            c1_action = f"{c1.upper()} stands at the prep table, slicing ingredients and looking stressed. {c2.upper()} enters carrying a recipe notebook, looking at him."
            c2_parenthetical = "adjusting her apron, smiling"
            c2_line_1 = f"You've been prepping since dawn, {c1}. Here, taste this."
            c1_line_1 = f"Thanks, {c2}. But with the opening tomorrow, I can't slow down. Preparing our menu for {story_summary_lc} is a huge challenge."
            c2_line_2 = f"It's a big step. But we have a clear objective: to establish our signature dish for {story_summary_lc}. If we focus on quality, we'll win."
            c1_line_2 = f"You are right. Let's stay focused. We have about {duration} to finalize the first course."
        elif is_college:
            intro_action = f"Fluorescent lights illuminate rows of library books. Quiet chatter hums in the background, and study guides are scattered on a table."
            c1_action = f"{c1.upper()} stands by the whiteboard, writing equations and looking overwhelmed. {c2.upper()} enters carrying reference books."
            c2_parenthetical = "dropping the books quietly, smiling"
            c2_line_1 = f"You've been sketching out this presentation for hours, {c1}. Take a breath."
            c1_line_1 = f"Thanks, {c2}. But I'm stressed. Presenting our thesis on {story_summary_lc} is our ticket to graduation."
            c2_line_2 = f"It is a big deal. But we have a clear objective: to establish the key arguments for {story_summary_lc}. Step by step, we will nail it."
            c1_line_2 = f"You are right. Let's stay focused. We have about {duration} to run through the opening slides."
        elif is_action:
            intro_action = f"The glow of computer monitors lights up the dark control room. Cyber maps show tracking points across a grid map."
            c1_action = f"{c1.upper()} stands at the terminal, loading mission layouts and looking focused. {c2.upper()} enters carrying a tactical gear pack."
            c2_parenthetical = "securing the pack, determined"
            c2_line_1 = f"You've been studying the target routes for hours, {c1}. We need to gear up."
            c1_line_1 = f"Understood, {c2}. But the intelligence reports are dense. Completing the mission for {story_summary_lc} is highly dangerous."
            c2_line_2 = f"It is high-risk. But we have a clear objective: to establish the perimeter for {story_summary_lc}. We stick to the tactical plan."
            c1_line_2 = f"Agreed. Let's stay focused. We have about {duration} to calibrate our frequencies."
        elif is_comedy:
            intro_action = f"Bright cafe lights highlight a table piled high with index cards and half-eaten pastries. A blueprint is upside down."
            c1_action = f"{c1.upper()} stands in the center of the room, holding a plastic prop and looking confused. {c2.upper()} enters carrying a funny costume."
            c2_parenthetical = "holding up the costume, grinning"
            c2_line_1 = f"I found the disguise, {c1}! Tell me you've figured out the layout."
            c1_line_1 = f"Barely, {c2}. This scheme to pull off {story_summary_lc} is turning into a complete circus."
            c2_line_2 = f"Circus or not, we have a clear objective: to launch {story_summary_lc} and get rich! We just need to follow my simple instructions."
            c1_line_2 = f"Simple? We have about {duration} before everything goes hilariously wrong!"
        else: # Drama / default
            intro_action = f"Shafts of natural light illuminate the room. Standard materials are scattered across a wooden table."
            c1_action = f"{c1.upper()} stands in the center of the room, holding a notepad and looking overwhelmed. {c2.upper()} enters carrying a box, looking at him."
            c2_parenthetical = "setting down the box, smiling"
            c2_line_1 = f"You have been working on this setup for hours, {c1}. Here, take a break."
            c1_line_1 = f"Thank you, {c2}. But I can't stop thinking about it. We are finally initiating our dream of {story_summary_lc}. It's exciting but daunting."
            c2_line_2 = f"It is a big step. But we have a clear objective: to establish the foundation of {story_summary_lc}. If we take it step by step, we can make it a reality."
            c1_line_2 = f"You are right. Let's stay focused. We have about {duration} to map out the next steps."

        script = f"""FADE IN:

{location.upper()}

{intro_action}

{c1_action}

{c2.upper()}
({c2_parenthetical})
          {c2_line_1}

{c1.upper()}
(taking it, sighing)
          {c1_line_1}

{c2.upper()}
          {c2_line_2}

{c1.upper()}
(nods, feeling motivated)
          {c1_line_2}

{c2.upper()}
          Exactly. Let's get to work.
"""
    elif s_num_str == "2":
        if is_space:
            c2_action = f"when {c2.upper()} enters the ship corridor, looking stern and checking a digital datapad."
            c2_line_1 = f"I reviewed your fuel consumption charts for {story_summary_lc}. This is an unauthorized trajectory, {c1}."
            c1_line = f"We are adjusting vectors to optimize safety, Commander. We are fully committed to {story_summary_lc}."
            c2_line_2 = f"Commitment doesn't override galactic regulation. Space is unforgiving. You have exactly {duration} to recalibrate, or I will lock down the reactor."
        elif is_sports:
            c2_action = f"when {c2.upper()} enters the locker room hallway, wearing an official blazer and looking skeptical."
            c2_line_1 = f"I saw your performance records for {story_summary_lc}. It is a very ambitious goal you have set, {c1}."
            c1_line = f"We are training harder than ever, Selector. I am dedicating everything to get selected."
            c2_line_2 = f"Desire is fine, but results matter. The selection trials are tomorrow. You have about {duration} to prove your stamina, or you won't make the team."
        elif is_horror:
            c2_action = f"when {c2.upper()} enters the dark hallway, holding a brass oil lamp and looking warningly."
            c2_line_1 = f"I saw you setting up your equipment for {story_summary_lc}. You do not know what forces you are disturbing here, {c1}."
            c1_line = f"We are just trying to research the truth, Panditji. We have to finish this."
            c2_line_2 = f"The truth here is covered in blood. You have about {duration} before the midnight hour. Get out of this house, or you will join the spirits."
        elif is_detective:
            c2_action = f"when {c2.upper()} enters the police station corridor, drinking coffee and looking warningly."
            c2_line_1 = f"I saw the suspect board you set up for {story_summary_lc}. You are crossing lines and looking in the wrong places, {c1}."
            c1_line = f"We are just following the clues, Inspector. This investigation is valid."
            c2_line_2 = f"This investigation is hitting nerves in high offices. You have about {duration} to back off the case, or I'll take your badge."
        elif is_chef:
            c2_action = f"when {c2.upper()} enters the pantry hallway, holding a pen and looking highly critical."
            c2_line_1 = f"I inspected your menu plans for {story_summary_lc}. It lacks culinary sophistication, {c1}."
            c1_line = f"We are aiming for bold, local flavors, Sir. We believe the customers will love it."
            c2_line_2 = f"Boldness is often just cover for bad technique. The opening is tomorrow. You have about {duration} to refine the menu, or I will write a scathing review."
        elif is_college:
            c2_action = f"when {c2.upper()} enters the department hallway, looking strict and holding a lecture binder."
            c2_line_1 = f"I reviewed your thesis outline for {story_summary_lc}. The methodology is extremely weak, {c1}."
            c1_line = f"We are compiling the survey data now, Professor. We are confident in the results."
            c2_line_2 = f"Confidence is not an academic citation. The presentation is tomorrow. You have about {duration} to fix the references, or you will fail this course."
        elif is_action:
            c2_action = f"when {c2.upper()} enters the corridor, wearing a tactical headset and looking highly alert."
            c2_line_1 = f"I detected an anomaly on the grid map for {story_summary_lc}. Hostile forces have intercepted our feed, {c1}."
            c1_line = f"We are encrypting the database now, Chief. We are holding the line."
            c2_line_2 = f"Encryption won't stop a bullet. You have about {duration} to evacuate the sector, or the enemy team will overrun our position."
        elif is_comedy:
            c2_action = f"when {c2.upper()} enters the cafe hallway, wearing oversized glasses and looking highly suspicious."
            c2_line_1 = f"I heard your loud talking about {story_summary_lc}. What kind of funny business are you planning here, {c1}?"
            c1_line = f"It's just a normal project, Sir. Nothing suspicious at all, I promise."
            c2_line_2 = f"I've got my eyes on you. You have about {duration} to clear out of this hallway, or I am calling the building manager."
        else: # Default drama / other
            c2_action = f"when {c2.upper()} enters the hallway, looking skeptical and crossing arms."
            c2_line_1 = f"I saw the blueprints you laid out for {story_summary_lc}. It is a very ambitious plan, {c1}."
            c1_line = f"Thank you, {c2}. We are dedicating everything to make it work."
            c2_line_2 = f"Ambition is good, but reality is harsh. The local regulations and resource limits here are very strict. You have about {duration} to prove you have a stable setup, or the local committee will halt your project."

        script = f"""{location.upper()}

The atmosphere is quiet. {c1.upper()} is double-checking plans, {c2_action}

{c2.upper()}
(crossing arms)
          {c2_line_1}

{c1.upper()}
(determined)
          {c1_line}

{c2.upper()}
          {c2_line_2}

{c1.upper()}
          I understand the stakes. We will double our efforts to comply with all rules.
"""
    elif s_num_str == "3":
        if is_space:
            intro_action = f"Alarms beep intermittently on the backup panels. The viewport shows the empty expanse of space, stars streaking by."
            c1_line_1 = f"If we vent the backup thrusters now, we can clear orbit and finalize {story_summary_lc} tonight!"
            c2_line_1 = f"No, {c1}! That is reckless. If the grid fails, we lose life support. We must stick to the commander's protocols."
            c1_line_2 = f"Commander's protocols will trap us in this sector! We must take this risk to succeed."
            c2_line_2 = f"There's a difference between bravery and suicide! I won't let you risk our crew for your dream of {story_summary_lc}."
            c1_line_3 = f"Maybe you care more about rules than our mission!"
        elif is_sports:
            intro_action = f"The stadium lights glare down on the empty practice pitch. Rain begins to fall, slicking the grass."
            c1_line_1 = f"If I run the aggressive offense drill now, I can prove I'm ready to dominate {story_summary_lc}!"
            c2_line_1 = f"No, {c1}! That's too risky on this wet pitch. You'll blow out your knee. We must stick to the defensive strategy."
            c1_line_2 = f"Defensive strategy is too passive! The selectors want to see action. I have to take this risk."
            c2_line_2 = f"An injured player is useless to any team! I won't let you ruin your athletic career for {story_summary_lc} because you are impatient."
            c1_line_3 = f"Maybe you've lost the drive to win, Coach!"
        elif is_horror:
            intro_action = f"A cold wind howls through the trees along the foggy path. The flashlight beam flickers, casting long shadows."
            c1_line_1 = f"If we split up and search the woods now, we can find the relic to finish {story_summary_lc}!"
            c2_line_1 = f"Are you crazy, {c1}? That's suicide. The entity is waiting for us in the dark. We must stick together."
            c1_line_2 = f"Staying here makes us sitting ducks! We need to search the woods to find answers."
            c2_line_2 = f"I won't let you drag me into the dark. I want to survive this night, not get killed for {story_summary_lc}!"
            c1_line_3 = f"Maybe you're letting fear cloud your judgment!"
        elif is_detective:
            intro_action = f"A rain-slicked alleyway, illuminated only by a distant streetlight. Steam rises from the sewer grates."
            c1_line_1 = f"If we break into the suspect's apartment now, we can retrieve the ledger for {story_summary_lc}!"
            c2_line_1 = f"No, {c1}! That is illegal entry. We don't have a warrant. We must follow standard police procedures."
            c1_line_2 = f"Standard procedures will let the suspect destroy the evidence! We have to cross lines to solve this case."
            c2_line_2 = f"We are officers of the law, not criminals! I won't let you compromise our integrity for {story_summary_lc}."
            c1_line_3 = f"Maybe you've forgotten what justice actually means!"
        elif is_chef:
            intro_action = f"The kitchen heat is intense. The sound of boiling pots and sizzling oil creates a loud hum."
            c1_line_1 = f"If we change the recipe to use this hot sauce, we can surprise the critic and elevate {story_summary_lc}!"
            c2_line_1 = f"No, {c1}! That will ruin the balance of the dish. It's too spicy. We must stick to the tested menu."
            c1_line_2 = f"Tested menu is boring! We need to make a statement. I have to cook this way."
            c2_line_2 = f"I manage the design and budget of this restaurant, and I won't let you burn our customer base for {story_summary_lc}!"
            c1_line_3 = f"Maybe you don't have the culinary vision to understand!"
        elif is_college:
            intro_action = f"The campus quad is quiet. A cool evening breeze rustles the leaves of the old oak trees."
            c1_line_1 = f"If we rewrite the core argument of our thesis now, we can shock the panel and win {story_summary_lc}!"
            c2_line_1 = f"Are you kidding, {c1}? That is too risky. If they reject it, we fail. We must stick to the professor's notes."
            c1_line_2 = f"Professor's notes are generic! We need to stand out. I'm willing to take this risk."
            c2_line_2 = f"I spent weeks compiling this research, and I won't let you ruin our graduation for {story_summary_lc}!"
            c1_line_3 = f"Maybe you care more about safety than academic excellence!"
        elif is_action:
            intro_action = f"A rugged mountain pass under a dark sky. Distant thunder rolls, and the wind whips dust across the trail."
            c1_line_1 = f"If we assault their camp now, we can retrieve the files and secure {story_summary_lc}!"
            c2_line_1 = f"No, {c1}! That is a tactical error. They outnumber us ten to one. We must wait for Chief's backup."
            c1_line_2 = f"Backup is twenty minutes out! By then, the targets will be gone. We have to act now."
            c2_line_2 = f"I won't let you lead us into an ambush! I'm responsible for our tactical survival, not just {story_summary_lc}!"
            c1_line_3 = f"Maybe you're letting caution paralyze you!"
        elif is_comedy:
            intro_action = f"A crowded street sidewalk. People push past, and car horns honk loudly. A giant inflatable mascot stands nearby."
            c1_line_1 = f"If we wear these ridiculous giant mascot suits, we can sneak in and get {story_summary_lc}!"
            c2_line_1 = f"No, {c1}! That is the dumbest idea ever. Everyone will notice us. We must use the back door."
            c1_line_2 = f"The back door is locked! This is our only chance. Trust the mascot suits!"
            c2_line_2 = f"I won't dress up like a giant chicken for your crazy dream of {story_summary_lc}!"
            c1_line_3 = f"Maybe you just don't have a sense of fashion!"
        else: # Default drama / other
            intro_action = f"The air is thick with tension as {c1.upper()} and {c2.upper()} stand near the control desk. They have been working non-stop on {story_summary_lc}."
            c1_line_1 = f"If we take this shortcut, we can bypass the delays and finalize {story_summary_lc} tonight!"
            c2_line_1 = f"No, {c1}! That is too risky. If it fails, we lose everything. We must follow the traditional safety guidelines."
            c1_line_2 = f"Traditional guidelines will delay us by weeks! We need to take this risk to succeed."
            c2_line_2 = f"There is a difference between a calculated risk and reckless behavior! I won't let you ruin our dream of {story_summary_lc} because you are impatient."
            c1_line_3 = f"Maybe you don't believe in {story_summary_lc} as much as I do!"

        script = f"""{location.upper()}

{intro_action}

{c1.upper()}
(pointing at the plans)
          {c1_line_1}

{c2.upper()}
(shaking head, defensive)
          {c2_line_1}

{c1.upper()}
          {c1_line_2}

{c2.upper()}
(raising voice)
          {c2_line_2}

{c1.upper()}
          {c1_line_3}

{c2.upper()}
(hurt, backing away)
          How can you say that? If you cannot trust my judgment, then maybe we shouldn't be doing this together.

{c2.upper()} walks out, slamming the door. {c1.upper()} stands alone, staring at the blueprints.
"""
    elif s_num_str == "4":
        if is_space:
            intro_action = f"The lighting is soft inside the observation dome. {c1.upper()} is analyzing starmaps, looking frustrated. {c2.upper()} walks over, observing her work."
            c2_parenthetical = f"observing, holding a datapad"
            c2_line_1 = f"Still struggling with the reactor coordinates for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. It seems we've hit a roadblock. We cannot bypass the safety rules, but we don't have the time to take the standard flight path."
            c2_line_2 = f"You young officers are always in a rush. Sometimes, you need local system experience. Here is a tip: there is a secondary wormhole vector that is bypassed in standard charts."
            c1_line_2 = f"Really? I didn't see that in the official fleet navigation files."
            c2_line_3 = f"It is an unlisted patrol route. If you navigate through there, you can secure the clearance in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, Commander {c2}. I must go share this with the captain and get {story_summary_lc} back on track."
        elif is_sports:
            intro_action = f"The gym is quiet. The distant echo of bouncing basketballs hums. {c1.upper()} is checking training logs, looking disappointed. {c2.upper()} walks over, observing her."
            c2_parenthetical = f"holding a whistle, smiling"
            c2_line_1 = f"Still worried about the team selection for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. The athlete is exhausted and our offensive strategy is blocked. We don't have time to rebuild our stamina."
            c2_line_2 = f"You coaches are always looking at stats. Here is a tip: the opponent defenders always leave their left side open in the third quarter."
            c1_line_2 = f"Really? I didn't catch that in the game recordings."
            c2_line_3 = f"It's a habit from their junior tournament days. If you play there, you can secure the winning goal in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, Selector {c2}. I must go share this with the player and get {story_summary_lc} back on track."
        elif is_horror:
            intro_action = f"The dust-covered study is dimly lit. {c1.upper()} is checking old maps of the mansion, looking frightened. {c2.upper()} enters, holding a sacred talisman."
            c2_parenthetical = f"holding the talisman, whispering"
            c2_line_1 = f"Still searching for a way to complete {story_summary_lc} in this cursed place?"
            c1_line_1 = f"Yes, {c2}. The ghost is blocking the exit, and we cannot survive the night if we don't find the ritual words."
            c2_line_2 = f"Fear blinds the mind. Here is a tip: the spirit is bound to the old mirror in the basement. If you shatter it, you break the curse."
            c1_line_2 = f"Really? The local myths said it was bound to the forest."
            c2_line_3 = f"The myths were written to mislead. If you destroy the mirror, you can banish the entity in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, Panditji {c2}. I must go tell the others and get {story_summary_lc} finished safely."
        elif is_detective:
            intro_action = f"The precinct desk is cluttered with case files and cold coffee cups. {c1.upper()} is reviewing witness statements. {c2.upper()} walks over, holding a confidential file."
            c2_parenthetical = f"tapping the file, lowering voice"
            c2_line_1 = f"Still hitting a wall with the suspect list for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. We cannot link the financial records to the main suspect, and the inspector is threatening to close the case."
            c2_line_2 = f"You rookie investigators rely too much on databases. Here is a tip: the suspect runs an off-shore account listed under his mother's maiden name."
            c1_line_2 = f"Really? That didn't show up in our bank searches."
            c2_line_3 = f"It's a classified transaction ledger. If you pull these files, you can secure the arrest warrant in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, Inspector {c2}. I must go share this with my partner and get {story_summary_lc} resolved."
        elif is_chef:
            intro_action = f"The dining room is empty, chairs stacked on tables. {c1.upper()} is looking at the recipe list, sighing. {c2.upper()} walks over, tasting a sauce."
            c2_parenthetical = f"wiping his mouth, looking thoughtful"
            c2_line_1 = f"Still struggling with the critics' expectations for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. The kitchen is disorganized and the recipes lack that special touch to win the review."
            c2_line_2 = f"You young chefs focus too much on presentation. Here is a tip: add a pinch of star anise to the sauce. It brings out the local flavor instantly."
            c1_line_2 = f"Really? Star anise? I didn't see that in any standard recipe."
            c2_line_3 = f"It is a secret family technique. If you add it now, you can elevate the dish in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, Chef {c2}. I must go share this with the kitchen and get {story_summary_lc} ready."
        elif is_college:
            intro_action = f"The professor's office is filled with old journals and a green banker's lamp. {c1.upper()} is reviewing the thesis slides. {c2.upper()} walks in, looking over his spectacles."
            c2_parenthetical = f"adjusting his glasses, speaking gently"
            c2_line_1 = f"Still struggling with the citation structure for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. The research notes are scattered and we don't have the data to prove our main conclusion."
            c2_line_2 = f"You students rely too much on internet searches. Here is a tip: there is a 1984 study in the archives that has the exact mathematical proofs you need."
            c1_line_2 = f"Really? I didn't find that in the digital university library."
            c2_line_3 = f"It is only available in the physical archives. If you cite it, you can secure your project approval in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, Professor {c2}. I must go tell my research partner and get {story_summary_lc} completed."
        elif is_action:
            intro_action = f"The tactical command center is hummed with radio static. {c1.upper()} is checking the grid maps. {c2.upper()} enters, checking the satellite link."
            c2_parenthetical = f"pointing at the screen, serious"
            c2_line_1 = f"Still locked out of the decryption grid for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. The code is too complex, and the hostile forces are closing in. We have no escape route."
            c2_line_2 = f"You tech operators forget basic signal routing. Here is a tip: bypass the main server and patch directly into the local analog relay."
            c1_line_2 = f"Really? That route is unmonitored?"
            c2_line_3 = f"Completely off the grid. If you upload the files there, you can secure the backup in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, Chief {c2}. I must go tell the team and get {story_summary_lc} completed."
        elif is_comedy:
            intro_action = f"Inside a messy supply closet. {c1.upper()} is sorting through props. {c2.upper()} enters, wearing a security guard hat."
            c2_parenthetical = f"adjusting the hat, laughing"
            c2_line_1 = f"Still trying to figure out how to sneak the props in for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. The main doors are guarded, and we can't get our comedy set in without being caught."
            c2_line_2 = f"You kids make things too complicated. Here is a tip: the security guard at the side gate is my cousin. Tell him I sent you."
            c1_line_2 = f"Really? He'll just let us walk in?"
            c2_line_3 = f"Just give him a box of donuts. He'll open the gate in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, {c2}. I must go tell my partner and get {story_summary_lc} moving."
        else: # Default drama / other
            intro_action = f"The lighting is soft. {c1.upper()} is analyzing the files, looking frustrated. {c2.upper()} walks over, observing the work."
            c2_parenthetical = f"observing, holding a notepad"
            c2_line_1 = f"Still struggling with the resource layout for {story_summary_lc}?"
            c1_line_1 = f"Yes, {c2}. It seems we've hit a roadblock. We cannot bypass the safety rules, but we don't have the time to go the long way."
            c2_line_2 = f"You young folks are always in a rush. Sometimes, you need local experience. Here is a tip: there is a secondary permit office that handles expedited requests for community projects."
            c1_line_2 = f"Really? I didn't see that in the official guidelines."
            c2_line_3 = f"It is an unlisted protocol. If you apply there, you can secure the clearance in {duration}."
            c1_line_3 = f"This is exactly what we need! Thank you, {c2}. I must go share this with the team and get {story_summary_lc} back on track."

        script = f"""{location.upper()}

{intro_action}

{c2.upper()}
({c2_parenthetical})
          {c2_line_1}

{c1.upper()}
(sighing)
          {c1_line_1}

{c2.upper()}
          {c2_line_2}

{c1.upper()}
(looking up, surprised)
          {c1_line_2}

{c2.upper()}
          {c2_line_3}

{c1.upper()}
(smiling, relieved)
          {c1_line_3}
"""
    else:
        if is_space:
            intro_action = f"Alarms blare loudly as steam vents from the overhead pipes. The central console flashes warning indicators."
            c1_line_1 = f"The system temperature is fluctuating! We need to stabilize the power grid!"
            c2_line_1 = f"I have the bypass line ready! Trigger the system restart on my mark!"
            c1_line_2 = f"It's too much pressure on the connection! Can you hold it?"
            c2_line_2 = f"I won't let go! For our dream of {story_summary_lc}! Mark!"
            hum_action = f"A brilliant green status light illuminates. The alarms stop, replaced by a steady, peaceful hum of the engines."
            c1_line_3 = f"It worked. The system is stable."
            c2_line_3 = f"We actually did it. The goal of {story_summary_lc} is real."
        elif is_sports:
            intro_action = f"The scoreboard shows five seconds left. The crowd is deafening. The match is on the line."
            c1_line_1 = f"The defenders are closing in on my left side! Coach's tactic is our only chance!"
            c2_line_1 = f"I've got the assist pass ready! Make the run to the open space now!"
            c1_line_2 = f"The angle is too tight! I have to shoot now!"
            c2_line_2 = f"Trust the training! Execute the final play for {story_summary_lc}! Now!"
            hum_action = f"The ball arcs beautifully through the air, hitting the back of the net. The buzzer sounds, and the crowd goes wild."
            c1_line_3 = f"It worked. We won the game."
            c2_line_3 = f"We actually did it. The selection for {story_summary_lc} is ours."
        elif is_horror:
            intro_action = f"The basement is pitch black, illuminated only by a flickering flashlight. A dark shadow towers in the corner."
            c1_line_1 = f"The spirit is rising! The basement door is locked!"
            c2_line_1 = f"I have the ancient ritual amulet! Stand back and shield the light!"
            c1_line_2 = f"It's casting a shadow towards us! Can you chant the words?"
            c2_line_2 = f"I will hold the line! For our survival and {story_summary_lc}! Now!"
            hum_action = f"A bright light erupts from the amulet, banishing the shadow. The oppressive weight lifts, replaced by quiet morning light."
            c1_line_3 = f"It worked. The entity is gone."
            c2_line_3 = f"We actually survived. The nightmare is over, and {story_summary_lc} is safe."
        elif is_detective:
            intro_action = f"Inside the warehouse, dust hangs in the air. The suspect stands cornered near the shipping crates, raising his hands."
            c1_line_1 = f"Drop the weapon! The warehouse is surrounded!"
            c2_line_1 = f"I have the exit doors locked and the cuffs ready! Don't let him escape!"
            c1_line_2 = f"He's reaching for his belt! Watch out!"
            c2_line_2 = f"I've got him covered! Secure the evidence ledger for {story_summary_lc}! Now!"
            hum_action = f"The suspect is brought down to the floor, metal handcuffs clicking loudly. The sirens echo outside."
            c1_line_3 = f"It worked. The suspect is in custody."
            c2_line_3 = f"We actually did it. The case of {story_summary_lc} is solved."
        elif is_chef:
            intro_action = f"The restaurant kitchen is in full activity. Ticket orders are printing rapidly. Plates are stacked ready."
            c1_line_1 = f"The final table order is ready, but the critic is waiting for the signature dish!"
            c2_line_1 = f"I have the special star anise sauce plated! Take it to the pass!"
            c1_line_2 = f"The presentation must be perfect! Are we ready?"
            c2_line_2 = f"It is perfect! For the culinary dream of {story_summary_lc}! Go!"
            hum_action = f"The server carries the plate to the dining room. A round of applause echoes from the customers."
            c1_line_3 = f"It worked. The critic is smiling."
            c2_line_3 = f"We actually did it. The culinary success of {story_summary_lc} is real."
        elif is_college:
            intro_action = f"Inside the auditorium, the judges look at their scoring sheets. The projector shows the final slide."
            c1_line_1 = f"The presentation timer is flashing zero! We need to conclude the thesis!"
            c2_line_1 = f"I have the final research reference ready! Present the key proof!"
            c1_line_2 = f"The judges look highly skeptical! Can we convince them?"
            c2_line_2 = f"We have the truth on our side! For our graduation and {story_summary_lc}! Mark!"
            hum_action = f"A silence falls over the auditorium, followed by a loud applause from the academic panel."
            c1_line_3 = f"It worked. The presentation is approved."
            c2_line_3 = f"We actually did it. The academic dream of {story_summary_lc} is certified."
        elif is_action:
            intro_action = f"The rooftop helipad is whipped by wind. Rain falls as the helicopter engines drone loudly."
            c1_line_1 = f"The hostile leader is boarding the chopper! We need to retrieve the hard drive!"
            c2_line_1 = f"I have the magnetic grapple ready! Fire the hook on my mark!"
            c1_line_2 = f"The wind is too strong! Can you lock the signal?"
            c2_line_2 = f"I won't let go! For the mission and {story_summary_lc}! Mark!"
            hum_action = f"The grapple hooks the hard drive case, pulling it free. The chopper flies away empty. The area goes quiet."
            c1_line_3 = f"It worked. We secured the data."
            c2_line_3 = f"We actually did it. The mission for {story_summary_lc} is complete."
        elif is_comedy:
            intro_action = f"Inside the auditorium, the giant mascot chicken costume is caught on a ropes rig, swinging."
            c1_line_1 = f"The rope is slipping! We're going to crash onto the stage!"
            c2_line_1 = f"I have the landing pad set! Jump on my mark!"
            c1_line_2 = f"I'm wearing a giant chicken suit! I can't jump!"
            c2_line_2 = f"Just trust the landing! For the funny dream of {story_summary_lc}! Mark!"
            hum_action = f"The mascot costume lands perfectly on the soft cushion. The audience breaks into hysterics and wild applause."
            c1_line_3 = f"It worked. They think it's part of the act."
            c2_line_3 = f"We actually did it. The launch of {story_summary_lc} is a massive success."
        else: # Default drama / other
            intro_action = f"Alarms beep softly in the background. {c1.upper()} is typing at the control panel, while {c2.upper()} is holding a critical cable connection."
            c1_line_1 = f"The system temperature is fluctuating! We need to stabilize the power grid!"
            c2_line_1 = f"I have the bypass line ready! Trigger the system restart on my mark!"
            c1_line_2 = f"It's too much pressure on the connection! Can you hold it?"
            c2_line_2 = f"I won't let go! For our dream of {story_summary_lc}! Mark!"
            hum_action = f"A brilliant green status light illuminates. The alarms stop, replaced by a steady, peaceful hum."
            c1_line_3 = f"It worked. The system is stable."
            c2_line_3 = f"We actually did it. The goal of {story_summary_lc} is real."

        script = f"""{location.upper()}

{intro_action}

{c1.upper()}
(shouting)
          {c1_line_1}

{c2.upper()}
(determined)
          {c2_line_1}

{c1.upper()}
          {c1_line_2}

{c2.upper()}
          {c2_line_2}

{hum_action}

{c1.upper()}
(letting out a breath)
          {c1_line_3}

{c2.upper()}
          {c2_line_3}

{c1.upper()} walks over and embraces her.

{c1.upper()}
          We did it together.

FADE OUT.
"""
        
    return script

