"""
Constants for the Oregon Trail decompiler.

This module contains game-specific constants, memory addresses, and patterns
that are used by various analyzers to improve the decompilation output.
"""

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