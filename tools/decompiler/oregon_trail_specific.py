"""
Oregon Trail specific data structures and constants for the decompiler.
"""

import re
from typing import Dict, List, Set, Optional, Tuple, Any

# Oregon Trail game states
GAME_STATES = {
    0: "GAME_STATE_MENU",
    1: "GAME_STATE_SETUP",
    2: "GAME_STATE_TRAVELING",
    3: "GAME_STATE_HUNTING",
    4: "GAME_STATE_TRADING",
    5: "GAME_STATE_RIVER_CROSSING",
    6: "GAME_STATE_EVENT",
    7: "GAME_STATE_LANDMARK",
    8: "GAME_STATE_DEATH",
    9: "GAME_STATE_END_GAME",
    10: "GAME_STATE_SAVE_GAME",
    11: "GAME_STATE_LOAD_GAME",
}

# Oregon Trail professions
PROFESSIONS = {
    0: "PROFESSION_BANKER",
    1: "PROFESSION_CARPENTER",
    2: "PROFESSION_FARMER",
}

# Oregon Trail weather conditions
WEATHER_CONDITIONS = {
    0: "WEATHER_GOOD",
    1: "WEATHER_FAIR",
    2: "WEATHER_POOR",
    3: "WEATHER_VERY_POOR",
    4: "WEATHER_RAIN",
    5: "WEATHER_HEAVY_RAIN",
    6: "WEATHER_SNOW",
    7: "WEATHER_BLIZZARD",
}

# Oregon Trail pace settings
PACE_SETTINGS = {
    0: "PACE_STOPPED",
    1: "PACE_SLOW",
    2: "PACE_NORMAL",
    3: "PACE_FAST",
    4: "PACE_GRUELING",
}

# Oregon Trail ration settings
RATION_SETTINGS = {
    0: "RATIONS_BARE_BONES",
    1: "RATIONS_MEAGER",
    2: "RATIONS_NORMAL",
    3: "RATIONS_WELL_FED",
}

# Oregon Trail river crossing methods
RIVER_CROSSING_METHODS = {
    0: "RIVER_FORD",
    1: "RIVER_CAULK",
    2: "RIVER_FERRY",
    3: "RIVER_WAIT",
}

# Oregon Trail landmarks
LANDMARKS = {
    0: "LANDMARK_INDEPENDENCE",
    1: "LANDMARK_KANSAS_RIVER",
    2: "LANDMARK_BIG_BLUE_RIVER",
    3: "LANDMARK_FORT_KEARNEY",
    4: "LANDMARK_CHIMNEY_ROCK",
    5: "LANDMARK_FORT_LARAMIE",
    6: "LANDMARK_INDEPENDENCE_ROCK",
    7: "LANDMARK_SOUTH_PASS",
    8: "LANDMARK_FORT_BRIDGER",
    9: "LANDMARK_GREEN_RIVER",
    10: "LANDMARK_SODA_SPRINGS",
    11: "LANDMARK_FORT_HALL",
    12: "LANDMARK_SNAKE_RIVER",
    13: "LANDMARK_FORT_BOISE",
    14: "LANDMARK_BLUE_MOUNTAINS",
    15: "LANDMARK_FORT_WALLA_WALLA",
    16: "LANDMARK_THE_DALLES",
    17: "LANDMARK_WILLAMETTE_VALLEY",
}

# Oregon Trail events
EVENTS = {
    0: "EVENT_NONE",
    1: "EVENT_ILLNESS",
    2: "EVENT_OXEN_INJURY",
    3: "EVENT_WAGON_BREAK",
    4: "EVENT_BAD_WATER",
    5: "EVENT_LITTLE_FOOD",
    6: "EVENT_EXHAUSTION",
    7: "EVENT_THIEF",
    8: "EVENT_FIRE",
    9: "EVENT_HEAVY_FOG",
    10: "EVENT_HAIL",
    11: "EVENT_HELPFUL_INDIANS",
    12: "EVENT_WILD_FRUIT",
    13: "EVENT_ABANDONED_WAGON",
}

# Oregon Trail illnesses
ILLNESSES = {
    0: "ILLNESS_NONE",
    1: "ILLNESS_EXHAUSTION",
    2: "ILLNESS_TYPHOID",
    3: "ILLNESS_CHOLERA",
    4: "ILLNESS_MEASLES",
    5: "ILLNESS_DYSENTERY",
    6: "ILLNESS_FEVER",
    7: "ILLNESS_BROKEN_LIMB",
    8: "ILLNESS_SNAKEBITE",
}

# Oregon Trail months
MONTHS = {
    1: "MONTH_JANUARY",
    2: "MONTH_FEBRUARY",
    3: "MONTH_MARCH",
    4: "MONTH_APRIL",
    5: "MONTH_MAY",
    6: "MONTH_JUNE",
    7: "MONTH_JULY",
    8: "MONTH_AUGUST",
    9: "MONTH_SEPTEMBER",
    10: "MONTH_OCTOBER",
    11: "MONTH_NOVEMBER",
    12: "MONTH_DECEMBER",
}

# Oregon Trail item types
ITEM_TYPES = {
    0: "ITEM_FOOD",
    1: "ITEM_OXEN",
    2: "ITEM_CLOTHING",
    3: "ITEM_AMMUNITION",
    4: "ITEM_WHEEL",
    5: "ITEM_AXLE",
    6: "ITEM_TONGUE",
    7: "ITEM_MEDICAL_KIT",
}

# Common memory addresses and their meanings
MEMORY_ADDRESSES = {
    0x5C00: "game_state",
    0x5C02: "current_month",
    0x5C04: "current_day",
    0x5C06: "current_year",
    0x5C08: "total_miles_traveled",
    0x5C0A: "miles_to_next_landmark",
    0x5C0C: "current_weather",
    0x5C0E: "current_health",
    0x5C10: "current_pace",
    0x5C12: "current_rations",
    0x5C14: "food_remaining",
    0x5C16: "money_remaining",
    0x5C18: "oxen_count",
    0x5C1A: "clothing_count",
    0x5C1C: "ammunition_count",
    0x5C1E: "spare_parts_count",
    0x5C20: "medical_kits_count",
    0x5C22: "player_count",
    0x5C24: "player_names_offset",
    0x5C26: "player_health_offset",
    0x5C28: "current_landmark_index",
    0x5C2A: "river_depth",
    0x5C2C: "river_width",
    0x5C2E: "next_event_miles",
    0x5C30: "next_event_type",
    0x5C32: "random_seed",
    0x5C34: "profession_type",
    0x5C36: "starting_month",
}

# Graphics-related memory addresses
GRAPHICS_ADDRESSES = {
    0x6000: "screen_buffer",
    0x6002: "current_palette",
    0x6004: "sprite_table",
    0x6006: "animation_state",
    0x6008: "current_background",
    0x600A: "text_color",
    0x600C: "background_color",
}

# Sound-related memory addresses
SOUND_ADDRESSES = {
    0x6100: "sound_enabled",
    0x6102: "current_music",
    0x6104: "sound_effect_playing",
    0x6106: "music_tempo",
}

# Input-related memory addresses
INPUT_ADDRESSES = {
    0x6200: "key_pressed",
    0x6202: "mouse_x",
    0x6204: "mouse_y",
    0x6206: "mouse_buttons",
}

# Common code patterns in Oregon Trail
OREGON_TRAIL_PATTERNS = {
    # Travel routine
    r"mov\s+word\s+ptr\s+\[0x5c08\],\s*.+\s*add\s+word\s+ptr\s+\[0x5c08\],": "Update miles traveled",
    
    # Health calculation
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c0e\].*sub\s+ax,": "Update player health",
    
    # Food consumption
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c14\].*sub\s+ax,": "Consume food",
    
    # Money transaction
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c16\].*sub\s+ax,": "Spend money",
    
    # Random number generation
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c32\].*mul": "Generate random number",
    
    # Weather change
    r"mov\s+word\s+ptr\s+\[0x5c0c\],": "Change weather condition",
    
    # River crossing
    r"cmp\s+word\s+ptr\s+\[0x5c2a\],": "Check river depth",
    
    # Event trigger
    r"mov\s+word\s+ptr\s+\[0x5c30\],": "Trigger game event",
    
    # Landmark arrival
    r"inc\s+word\s+ptr\s+\[0x5c28\]": "Arrive at new landmark",
}

def identify_game_constant(value: int, context: str) -> Optional[str]:
    """
    Identify a game constant based on its value and context.
    
    Args:
        value: The constant value
        context: The context in which the constant is used (e.g., "game_state", "weather", etc.)
        
    Returns:
        A string describing the constant, or None if not recognized
    """
    if context == "game_state" and value in GAME_STATES:
        return GAME_STATES[value]
    elif context == "profession" and value in PROFESSIONS:
        return PROFESSIONS[value]
    elif context == "weather" and value in WEATHER_CONDITIONS:
        return WEATHER_CONDITIONS[value]
    elif context == "pace" and value in PACE_SETTINGS:
        return PACE_SETTINGS[value]
    elif context == "rations" and value in RATION_SETTINGS:
        return RATION_SETTINGS[value]
    elif context == "river_crossing" and value in RIVER_CROSSING_METHODS:
        return RIVER_CROSSING_METHODS[value]
    elif context == "landmark" and value in LANDMARKS:
        return LANDMARKS[value]
    elif context == "event" and value in EVENTS:
        return EVENTS[value]
    elif context == "illness" and value in ILLNESSES:
        return ILLNESSES[value]
    elif context == "month" and value in MONTHS:
        return MONTHS[value]
    elif context == "item" and value in ITEM_TYPES:
        return ITEM_TYPES[value]
    
    return None

def identify_memory_address(address: int) -> Optional[str]:
    """
    Identify a memory address based on known game memory locations.
    
    Args:
        address: The memory address
        
    Returns:
        A string describing the memory location, or None if not recognized
    """
    if address in MEMORY_ADDRESSES:
        return MEMORY_ADDRESSES[address]
    elif address in GRAPHICS_ADDRESSES:
        return GRAPHICS_ADDRESSES[address]
    elif address in SOUND_ADDRESSES:
        return SOUND_ADDRESSES[address]
    elif address in INPUT_ADDRESSES:
        return INPUT_ADDRESSES[address]
    
    # Check for array accesses
    for base_addr, name in MEMORY_ADDRESSES.items():
        if address >= base_addr and address < base_addr + 0x20:
            offset = address - base_addr
            return f"{name}[{offset}]"
    
    return None

def identify_game_pattern(code: str) -> Optional[str]:
    """
    Identify a game-specific code pattern.
    
    Args:
        code: The code to analyze
        
    Returns:
        A string describing the pattern, or None if not recognized
    """
    for pattern, description in OREGON_TRAIL_PATTERNS.items():
        if re.search(pattern, code, re.IGNORECASE):
            return description
    
    return None

def enhance_with_game_knowledge(pseudocode: str) -> str:
    """
    Enhance pseudocode with Oregon Trail specific knowledge.
    
    Args:
        pseudocode: The pseudocode to enhance
        
    Returns:
        Enhanced pseudocode with game-specific information
    """
    enhanced = pseudocode
    
    # Replace memory addresses with meaningful names
    for addr, name in MEMORY_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r'\[' + addr_str + r'\]', f"[{name}]", enhanced)
        enhanced = re.sub(r'\[' + addr_str.lower() + r'\]', f"[{name}]", enhanced)
    
    # Replace graphics addresses
    for addr, name in GRAPHICS_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r'\[' + addr_str + r'\]', f"[{name}]", enhanced)
        enhanced = re.sub(r'\[' + addr_str.lower() + r'\]', f"[{name}]", enhanced)
    
    # Replace sound addresses
    for addr, name in SOUND_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r'\[' + addr_str + r'\]', f"[{name}]", enhanced)
        enhanced = re.sub(r'\[' + addr_str.lower() + r'\]', f"[{name}]", enhanced)
    
    # Replace input addresses
    for addr, name in INPUT_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r'\[' + addr_str + r'\]', f"[{name}]", enhanced)
        enhanced = re.sub(r'\[' + addr_str.lower() + r'\]', f"[{name}]", enhanced)
    
    # Replace game state constants
    for value, name in GAME_STATES.items():
        enhanced = re.sub(r'cmp\s+word\s+ptr\s+\[game_state\],\s*' + str(value) + r'\b', f"cmp word ptr [game_state], {name} // {value}", enhanced)
        enhanced = re.sub(r'mov\s+word\s+ptr\s+\[game_state\],\s*' + str(value) + r'\b', f"mov word ptr [game_state], {name} // {value}", enhanced)
    
    # Replace profession constants
    for value, name in PROFESSIONS.items():
        enhanced = re.sub(r'cmp\s+word\s+ptr\s+\[profession_type\],\s*' + str(value) + r'\b', f"cmp word ptr [profession_type], {name} // {value}", enhanced)
        enhanced = re.sub(r'mov\s+word\s+ptr\s+\[profession_type\],\s*' + str(value) + r'\b', f"mov word ptr [profession_type], {name} // {value}", enhanced)
    
    # Replace weather constants
    for value, name in WEATHER_CONDITIONS.items():
        enhanced = re.sub(r'cmp\s+word\s+ptr\s+\[current_weather\],\s*' + str(value) + r'\b', f"cmp word ptr [current_weather], {name} // {value}", enhanced)
        enhanced = re.sub(r'mov\s+word\s+ptr\s+\[current_weather\],\s*' + str(value) + r'\b', f"mov word ptr [current_weather], {name} // {value}", enhanced)
    
    # Replace pace constants
    for value, name in PACE_SETTINGS.items():
        enhanced = re.sub(r'cmp\s+word\s+ptr\s+\[current_pace\],\s*' + str(value) + r'\b', f"cmp word ptr [current_pace], {name} // {value}", enhanced)
        enhanced = re.sub(r'mov\s+word\s+ptr\s+\[current_pace\],\s*' + str(value) + r'\b', f"mov word ptr [current_pace], {name} // {value}", enhanced)
    
    # Replace ration constants
    for value, name in RATION_SETTINGS.items():
        enhanced = re.sub(r'cmp\s+word\s+ptr\s+\[current_rations\],\s*' + str(value) + r'\b', f"cmp word ptr [current_rations], {name} // {value}", enhanced)
        enhanced = re.sub(r'mov\s+word\s+ptr\s+\[current_rations\],\s*' + str(value) + r'\b', f"mov word ptr [current_rations], {name} // {value}", enhanced)
    
    # Replace landmark constants
    for value, name in LANDMARKS.items():
        enhanced = re.sub(r'cmp\s+word\s+ptr\s+\[current_landmark_index\],\s*' + str(value) + r'\b', f"cmp word ptr [current_landmark_index], {name} // {value}", enhanced)
        enhanced = re.sub(r'mov\s+word\s+ptr\s+\[current_landmark_index\],\s*' + str(value) + r'\b', f"mov word ptr [current_landmark_index], {name} // {value}", enhanced)
    
    # Replace event constants
    for value, name in EVENTS.items():
        enhanced = re.sub(r'cmp\s+word\s+ptr\s+\[next_event_type\],\s*' + str(value) + r'\b', f"cmp word ptr [next_event_type], {name} // {value}", enhanced)
        enhanced = re.sub(r'mov\s+word\s+ptr\s+\[next_event_type\],\s*' + str(value) + r'\b', f"mov word ptr [next_event_type], {name} // {value}", enhanced)
    
    return enhanced

def identify_game_function(function_name: str, instructions: List[str]) -> Optional[str]:
    """
    Identify the purpose of a function based on game-specific knowledge.
    
    Args:
        function_name: The name of the function
        instructions: The instructions in the function
        
    Returns:
        A string describing the function's purpose, or None if not recognized
    """
    # Convert instructions to a single string for pattern matching
    code = "\n".join(instructions)
    
    # Check for travel-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c08\]', code) and re.search(r'add\s+word\s+ptr\s+\[0x5c08\]', code):
        return "Update travel distance"
    
    # Check for health-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c0e\]', code) and re.search(r'sub\s+word\s+ptr\s+\[0x5c0e\]', code):
        return "Update player health"
    
    # Check for food-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c14\]', code) and re.search(r'sub\s+word\s+ptr\s+\[0x5c14\]', code):
        return "Update food supplies"
    
    # Check for money-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c16\]', code) and re.search(r'sub\s+word\s+ptr\s+\[0x5c16\]', code):
        return "Update money"
    
    # Check for random number generation
    if re.search(r'mov\s+ax,\s*word\s+ptr\s+\[0x5c32\]', code) and re.search(r'mul', code):
        return "Generate random number"
    
    # Check for weather-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c0c\]', code):
        return "Update weather conditions"
    
    # Check for river crossing functions
    if re.search(r'cmp\s+word\s+ptr\s+\[0x5c2a\]', code) and re.search(r'cmp\s+word\s+ptr\s+\[0x5c2c\]', code):
        return "Handle river crossing"
    
    # Check for event-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c30\]', code):
        return "Handle game event"
    
    # Check for landmark-related functions
    if re.search(r'inc\s+word\s+ptr\s+\[0x5c28\]', code) or re.search(r'mov\s+word\s+ptr\s+\[0x5c28\]', code):
        return "Handle landmark arrival"
    
    # Check for hunting-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c1c\]', code) and re.search(r'sub\s+word\s+ptr\s+\[0x5c1c\]', code):
        return "Handle hunting"
    
    # Check for trading-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x5c16\]', code) and re.search(r'add\s+word\s+ptr\s+\[0x5c16\]', code):
        return "Handle trading"
    
    # Check for date/time-related functions
    if re.search(r'inc\s+word\s+ptr\s+\[0x5c04\]', code) or re.search(r'mov\s+word\s+ptr\s+\[0x5c04\]', code):
        return "Update game date"
    
    # Check for graphics-related functions
    if re.search(r'mov\s+ax,\s*0x13', code) and re.search(r'int\s+0x10', code):
        return "Set graphics mode"
    
    # Check for sound-related functions
    if re.search(r'mov\s+word\s+ptr\s+\[0x6102\]', code) or re.search(r'mov\s+word\s+ptr\s+\[0x6104\]', code):
        return "Play sound or music"
    
    # Check for input-related functions
    if re.search(r'int\s+0x16', code) and re.search(r'mov\s+word\s+ptr\s+\[0x6200\]', code):
        return "Handle keyboard input"
    
    # Check for save/load functions
    if re.search(r'mov\s+ah,\s*0x3c', code) or re.search(r'mov\s+ah,\s*0x3d', code):
        return "Save or load game"
    
    return None