"""
Oregon Trail specific data structures and constants for the decompiler.
"""

import re
from typing import List, Optional

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
    # Try to infer context from value if not provided
    if not context:
        # Check all constant dictionaries
        for context_name, constant_dict in [
            ("game_state", GAME_STATES),
            ("profession", PROFESSIONS),
            ("weather", WEATHER_CONDITIONS),
            ("pace", PACE_SETTINGS),
            ("rations", RATION_SETTINGS),
            ("river_crossing", RIVER_CROSSING_METHODS),
            ("landmark", LANDMARKS),
            ("event", EVENTS),
            ("illness", ILLNESSES),
            ("month", MONTHS),
            ("item", ITEM_TYPES),
        ]:
            if value in constant_dict:
                return constant_dict[value]
    
    # If context is provided, use it for more specific lookup
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
    return None


def identify_memory_address(address: int) -> Optional[str]:
    """
    Identify a memory address based on known game memory locations.

    Args:
        address: The memory address

    Returns:
        A string describing the memory location, or None if not recognized
    """
    # Direct address match
    if address in MEMORY_ADDRESSES:
        return MEMORY_ADDRESSES[address]
    elif address in GRAPHICS_ADDRESSES:
        return GRAPHICS_ADDRESSES[address]
    elif address in SOUND_ADDRESSES:
        return SOUND_ADDRESSES[address]
    elif address in INPUT_ADDRESSES:
        return INPUT_ADDRESSES[address]

    # Check for array accesses with more flexible offset range
    for base_addr, name in MEMORY_ADDRESSES.items():
        if address >= base_addr and address < base_addr + 0x40:  # Increased range for array detection
            offset = address - base_addr
            # Check if this might be a player array
            if name == "player_names_offset" and offset < 0x30:
                return f"player_name[{offset // 6}][{offset % 6}]"
            elif name == "player_health_offset" and offset < 0x10:
                return f"player_health[{offset // 2}]"
            else:
                return f"{name}[{offset}]"
    
    # Check for approximate matches (addresses that are close to known addresses)
    closest_addr = None
    closest_name = None
    closest_distance = 0x20  # Maximum distance to consider
    
    for addr_dict in [MEMORY_ADDRESSES, GRAPHICS_ADDRESSES, SOUND_ADDRESSES, INPUT_ADDRESSES]:
        for addr, name in addr_dict.items():
            distance = abs(address - addr)
            if distance < closest_distance:
                closest_distance = distance
                closest_addr = addr
                closest_name = name
    
    if closest_name:
        offset = address - closest_addr
        if offset > 0:
            return f"{closest_name}+{offset}"
        else:
            return f"{closest_name}{offset}"  # Negative offset will include the minus sign

    return None


def identify_game_pattern(code: str) -> Optional[str]:
    """
    Identify a game-specific code pattern.

    Args:
        code: The code to analyze

    Returns:
        A string describing the pattern, or None if not recognized
    """
    # First check for exact pattern matches
    for pattern, description in OREGON_TRAIL_PATTERNS.items():
        if re.search(pattern, code, re.IGNORECASE):
            return description
    
    # Then check for more general patterns
    
    # Travel-related patterns
    if re.search(r"mov\s+.+\[0x5c08\]|add\s+.+\[0x5c08\]", code, re.IGNORECASE):
        return "Update travel distance"
    
    # Health-related patterns
    if re.search(r"mov\s+.+\[0x5c0e\]|sub\s+.+\[0x5c0e\]", code, re.IGNORECASE):
        return "Update player health"
    
    # Food-related patterns
    if re.search(r"mov\s+.+\[0x5c14\]|sub\s+.+\[0x5c14\]", code, re.IGNORECASE):
        return "Update food supplies"
    
    # Money-related patterns
    if re.search(r"mov\s+.+\[0x5c16\]|sub\s+.+\[0x5c16\]", code, re.IGNORECASE):
        return "Update money"
    
    # Weather-related patterns
    if re.search(r"mov\s+.+\[0x5c0c\]", code, re.IGNORECASE):
        return "Update weather conditions"
    
    # River crossing patterns
    if re.search(r"cmp\s+.+\[0x5c2a\]|cmp\s+.+\[0x5c2c\]", code, re.IGNORECASE):
        return "Handle river crossing"
    
    # Event-related patterns
    if re.search(r"mov\s+.+\[0x5c30\]", code, re.IGNORECASE):
        return "Handle game event"
    
    # Landmark-related patterns
    if re.search(r"inc\s+.+\[0x5c28\]|mov\s+.+\[0x5c28\]", code, re.IGNORECASE):
        return "Handle landmark arrival"
    
    # Hunting-related patterns
    if re.search(r"mov\s+.+\[0x5c1c\]|sub\s+.+\[0x5c1c\]", code, re.IGNORECASE):
        return "Handle hunting"
    
    # Trading-related patterns
    if re.search(r"mov\s+.+\[0x5c16\]|add\s+.+\[0x5c16\]", code, re.IGNORECASE):
        return "Handle trading"

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

    # Add a header with more specific information
    header = "// Enhanced Pseudocode for Oregon Trail with Game-Specific Knowledge\n"
    header += "// Generated with Oregon Trail Decompiler\n\n"
    
    if enhanced.startswith("// Enhanced Pseudocode for OREGON.EXE"):
        # Replace the existing header
        enhanced = re.sub(r"// Enhanced Pseudocode for OREGON\.EXE.*?\n\n", header, enhanced, flags=re.DOTALL)
    else:
        # Add the header at the beginning
        enhanced = header + enhanced
    
    # Replace memory addresses with meaningful names - more robust pattern matching
    for addr, name in MEMORY_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        # Match both uppercase and lowercase hex, with and without brackets
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)

    # Replace graphics addresses
    for addr, name in GRAPHICS_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)

    # Replace sound addresses
    for addr, name in SOUND_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)

    # Replace input addresses
    for addr, name in INPUT_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", f"{name}", enhanced, flags=re.IGNORECASE)

    # Replace game state constants
    for value, name in GAME_STATES.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[game_state\],\s*" + str(value) + r"\b",
            f"cmp word ptr [game_state], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[game_state\],\s*" + str(value) + r"\b",
            f"mov word ptr [game_state], {name} // {value}",
            enhanced,
        )

    # Replace profession constants
    for value, name in PROFESSIONS.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[profession_type\],\s*" + str(value) + r"\b",
            f"cmp word ptr [profession_type], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[profession_type\],\s*" + str(value) + r"\b",
            f"mov word ptr [profession_type], {name} // {value}",
            enhanced,
        )

    # Replace weather constants
    for value, name in WEATHER_CONDITIONS.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[current_weather\],\s*" + str(value) + r"\b",
            f"cmp word ptr [current_weather], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[current_weather\],\s*" + str(value) + r"\b",
            f"mov word ptr [current_weather], {name} // {value}",
            enhanced,
        )

    # Replace pace constants
    for value, name in PACE_SETTINGS.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[current_pace\],\s*" + str(value) + r"\b",
            f"cmp word ptr [current_pace], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[current_pace\],\s*" + str(value) + r"\b",
            f"mov word ptr [current_pace], {name} // {value}",
            enhanced,
        )

    # Replace ration constants
    for value, name in RATION_SETTINGS.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[current_rations\],\s*" + str(value) + r"\b",
            f"cmp word ptr [current_rations], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[current_rations\],\s*" + str(value) + r"\b",
            f"mov word ptr [current_rations], {name} // {value}",
            enhanced,
        )

    # Replace landmark constants
    for value, name in LANDMARKS.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[current_landmark_index\],\s*" + str(value) + r"\b",
            f"cmp word ptr [current_landmark_index], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[current_landmark_index\],\s*" + str(value) + r"\b",
            f"mov word ptr [current_landmark_index], {name} // {value}",
            enhanced,
        )

    # Replace event constants
    for value, name in EVENTS.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[next_event_type\],\s*" + str(value) + r"\b",
            f"cmp word ptr [next_event_type], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[next_event_type\],\s*" + str(value) + r"\b",
            f"mov word ptr [next_event_type], {name} // {value}",
            enhanced,
        )

    return enhanced


def identify_game_function(
    function_name: str, instructions: List[str]
) -> Optional[str]:
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
    
    # Check for entry point function
    if function_name == "entry":
        return "Main game entry point - initializes game state and starts the game"
    
    # Check for specific function names that might indicate purpose
    if "travel" in function_name.lower():
        return "Handles travel mechanics"
    elif "health" in function_name.lower():
        return "Manages player health"
    elif "food" in function_name.lower():
        return "Manages food supplies"
    elif "money" in function_name.lower() or "cash" in function_name.lower():
        return "Handles money transactions"
    elif "weather" in function_name.lower():
        return "Controls weather conditions"
    elif "river" in function_name.lower():
        return "Handles river crossing events"
    elif "event" in function_name.lower():
        return "Manages random events"
    elif "landmark" in function_name.lower():
        return "Handles landmark arrivals"
    elif "hunt" in function_name.lower():
        return "Controls hunting mini-game"
    elif "trade" in function_name.lower():
        return "Manages trading with merchants"
    elif "save" in function_name.lower() or "load" in function_name.lower():
        return "Handles game saving/loading"
    elif "menu" in function_name.lower():
        return "Controls game menus"
    elif "input" in function_name.lower() or "key" in function_name.lower():
        return "Processes user input"
    elif "draw" in function_name.lower() or "render" in function_name.lower():
        return "Renders game graphics"
    elif "sound" in function_name.lower() or "music" in function_name.lower():
        return "Controls game audio"

    # Check for travel-related functions - more flexible pattern matching
    if (re.search(r"\[0x5c08\]|\[total_miles_traveled\]", code, re.IGNORECASE) and
        (re.search(r"add|inc", code, re.IGNORECASE))):
        return "Update travel distance"

    # Check for health-related functions
    if (re.search(r"\[0x5c0e\]|\[current_health\]", code, re.IGNORECASE) and
        (re.search(r"sub|dec", code, re.IGNORECASE) or re.search(r"add|inc", code, re.IGNORECASE))):
        return "Update player health"

    # Check for food-related functions
    if (re.search(r"\[0x5c14\]|\[food_remaining\]", code, re.IGNORECASE) and
        (re.search(r"sub|dec", code, re.IGNORECASE) or re.search(r"add|inc", code, re.IGNORECASE))):
        return "Update food supplies"

    # Check for money-related functions
    if (re.search(r"\[0x5c16\]|\[money_remaining\]", code, re.IGNORECASE) and
        (re.search(r"sub|dec", code, re.IGNORECASE) or re.search(r"add|inc", code, re.IGNORECASE))):
        return "Update money"

    # Check for random number generation
    if re.search(r"\[0x5c32\]|\[random_seed\]", code, re.IGNORECASE) and re.search(r"mul", code, re.IGNORECASE):
        return "Generate random number"

    # Check for weather-related functions
    if re.search(r"\[0x5c0c\]|\[current_weather\]", code, re.IGNORECASE):
        return "Update weather conditions"

    # Check for river crossing functions
    if (re.search(r"\[0x5c2a\]|\[river_depth\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c2c\]|\[river_width\]", code, re.IGNORECASE)):
        return "Handle river crossing"

    # Check for event-related functions
    if re.search(r"\[0x5c30\]|\[next_event_type\]", code, re.IGNORECASE):
        return "Handle game event"

    # Check for landmark-related functions
    if re.search(r"\[0x5c28\]|\[current_landmark_index\]", code, re.IGNORECASE):
        return "Handle landmark arrival"

    # Check for hunting-related functions
    if (re.search(r"\[0x5c1c\]|\[ammunition_count\]", code, re.IGNORECASE) and
        (re.search(r"sub|dec", code, re.IGNORECASE) or re.search(r"add|inc", code, re.IGNORECASE))):
        return "Handle hunting"

    # Check for trading-related functions
    if (re.search(r"\[0x5c16\]|\[money_remaining\]", code, re.IGNORECASE) and
        re.search(r"add|inc", code, re.IGNORECASE)):
        return "Handle trading"

    # Check for date/time-related functions
    if (re.search(r"\[0x5c04\]|\[current_day\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c02\]|\[current_month\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c06\]|\[current_year\]", code, re.IGNORECASE)):
        return "Update game date"

    # Check for graphics-related functions
    if (re.search(r"mov\s+ax,\s*0x13", code, re.IGNORECASE) and re.search(r"int\s+0x10", code, re.IGNORECASE)) or \
       re.search(r"\[0x6000\]|\[screen_buffer\]", code, re.IGNORECASE):
        return "Set graphics mode or update display"

    # Check for sound-related functions
    if (re.search(r"\[0x6102\]|\[current_music\]", code, re.IGNORECASE) or
        re.search(r"\[0x6104\]|\[sound_effect_playing\]", code, re.IGNORECASE)):
        return "Play sound or music"

    # Check for input-related functions
    if (re.search(r"int\s+0x16", code, re.IGNORECASE) or
        re.search(r"\[0x6200\]|\[key_pressed\]", code, re.IGNORECASE) or
        re.search(r"\[0x6202\]|\[mouse_x\]", code, re.IGNORECASE) or
        re.search(r"\[0x6204\]|\[mouse_y\]", code, re.IGNORECASE)):
        return "Handle keyboard or mouse input"

    # Check for save/load functions
    if (re.search(r"mov\s+ah,\s*0x3c", code, re.IGNORECASE) or
        re.search(r"mov\s+ah,\s*0x3d", code, re.IGNORECASE) or
        re.search(r"mov\s+ah,\s*0x3e", code, re.IGNORECASE) or
        re.search(r"mov\s+ah,\s*0x3f", code, re.IGNORECASE)):
        return "Save or load game data"
        
    # Check for game state changes
    if re.search(r"\[0x5c00\]|\[game_state\]", code, re.IGNORECASE):
        return "Change game state or mode"
        
    # Check for player-related functions
    if (re.search(r"\[0x5c24\]|\[player_names_offset\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c26\]|\[player_health_offset\]", code, re.IGNORECASE)):
        return "Update player information"
        
    # Check for inventory-related functions
    if (re.search(r"\[0x5c18\]|\[oxen_count\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c1a\]|\[clothing_count\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c1c\]|\[ammunition_count\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c1e\]|\[spare_parts_count\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c20\]|\[medical_kits_count\]", code, re.IGNORECASE)):
        return "Update inventory items"

    # Check for pace/ration setting functions
    if (re.search(r"\[0x5c10\]|\[current_pace\]", code, re.IGNORECASE) or
        re.search(r"\[0x5c12\]|\[current_rations\]", code, re.IGNORECASE)):
        return "Update travel pace or ration settings"

    return None
