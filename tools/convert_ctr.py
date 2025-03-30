#!/usr/bin/env python3
"""
CTR control format converter for Oregon Trail files.
Converts CTR files to structured JSON format.

Format details:
- CTR: Control/script files for UI layout and game interaction
- Contains commands for positioning, text, buttons, and other UI elements
- Defines screens, dialogs, and interactive components
"""

import json
import logging
import re
from pathlib import Path
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)

# Command type mapping for better readability
COMMAND_TYPES = {
    1: "image_count",
    4: "set_x",
    5: "set_y",
    6: "position_x",
    7: "position_y",
    8: "button_properties",
    10: "text_content",
    11: "input_field",
    12: "set_color",
    17: "comment",
    18: "text_style",
    19: "vertical_spacing",
    20: "horizontal_spacing",
}

# Button states mapping
BUTTON_STATES = {0: "normal", 1: "disabled", 28: "enabled"}

# Common action mappings
ACTION_MAPPINGS = {
    1: "confirm",
    2: "cancel",
    3: "back",
    5001: "close",
    32000: "index",
    32001: "ok",
    32002: "cancel",
    32003: "page_forward",
    32004: "page_backward",
    99: "apply",
}

# Text style mappings
FONT_SIZES = {1: "small", 2: "medium", 3: "large"}

TEXT_STYLES = {0: "normal", 1: "bold", 2: "italic"}

TEXT_ALIGNMENTS = {0: "left", 1: "center", 2: "right"}

# Color mappings
COLOR_NAMES = {0: "black", 6: "gold", 7: "white"}


class CommandSequence:
    """Track and analyze sequences of commands"""

    def __init__(self):
        self.commands = []
        self.current_element = None
        self.elements = []
        self.metadata = {"images": [], "comments": []}

    def add_command(self, command: dict[str, Any]) -> None:
        """Add a command to the sequence and update tracking"""
        self.commands.append(command)

        # Process command based on type
        cmd_type = command.get("type")

        if cmd_type == "comment":
            comment_text = command.get("text", "")
            self.metadata["comments"].append(comment_text)

            # Check for section markers
            if "icon buttons" in comment_text.lower():
                self._finish_current_element()
                self.current_element = {"type": "button_section", "buttons": []}
            elif "load the images" in comment_text.lower():
                self._finish_current_element()
                self.current_element = {"type": "image_section", "images": []}
            elif "text" in comment_text.lower():
                self._finish_current_element()
                self.current_element = {"type": "text_section", "blocks": []}

        elif cmd_type == "image_count":
            if self.current_element and self.current_element["type"] == "image_section":
                self.current_element["count"] = command.get("count", 1)

        elif cmd_type == "text_content":
            text = command.get("text", "")
            if text and self.current_element:
                if self.current_element["type"] == "text_block":
                    self.current_element["content"] = text
                    self._finish_current_element()

                elif self.current_element["type"] == "text_section":
                    # Create a new text block
                    self._finish_current_element()
                    self.current_element = {"type": "text_block", "content": text}

                    # Get previous style if available
                    for cmd in reversed(self.commands[:-1]):
                        if cmd.get("type") == "text_style":
                            self.current_element["style"] = cmd.get("style", {})
                            break

                    # Get previous position if available
                    position = {}
                    for cmd in reversed(self.commands[:-1]):
                        if cmd.get("type") == "position_x":
                            position["x"] = cmd.get("x")
                        elif cmd.get("type") == "position_y":
                            position["y"] = cmd.get("y")

                    if position:
                        self.current_element["position"] = position

        elif cmd_type == "button_properties":
            properties = command.get("properties", {})
            position = {}

            # Get most recent X position
            for cmd in reversed(self.commands[:-1]):
                if cmd.get("type") == "position_x":
                    position["x"] = cmd.get("x")
                    break

            # Get most recent Y section and offset
            y_section = None
            y_offset = None
            for cmd in reversed(self.commands[:-1]):
                if cmd.get("type") == "set_y" and y_section is None:
                    y_section = cmd.get("y")
                elif cmd.get("type") == "position_y" and y_offset is None:
                    y_offset = cmd.get("y")

            if y_section is not None and y_offset is not None:
                position["y"] = y_offset
                position["y_section"] = y_section
            elif y_offset is not None:
                position["y"] = y_offset

            # Create button element
            button = {"type": "button", "properties": properties, "position": position}

            # Add to buttons section or as standalone
            if (
                self.current_element
                and self.current_element["type"] == "button_section"
            ):
                self.current_element["buttons"].append(button)
            else:
                self._finish_current_element()
                self.current_element = button

        elif cmd_type == "text_style":
            style = command.get("style", {})

            if self.current_element:
                if self.current_element["type"] == "text_block":
                    self.current_element["style"] = style
                elif self.current_element["type"] == "text_section":
                    # Store for next text block
                    pass
            else:
                self.current_element = {"type": "text_block", "style": style}

        elif cmd_type == "set_color":
            colors = command.get("colors", {})

            # Find what this color applies to
            # Look for recent position/dimension commands
            has_position = False
            for cmd in reversed(self.commands[:-1]):
                if cmd.get("type") in ["set_x", "set_y", "position_x", "position_y"]:
                    has_position = True
                    break

            if has_position:
                # This is likely a dialog or panel
                if self.current_element and self.current_element["type"] not in [
                    "image_section",
                    "button_section",
                    "text_section",
                ]:
                    self.current_element["colors"] = colors
                else:
                    self._finish_current_element()
                    self.current_element = {"type": "panel", "colors": colors}

                    # Get dimensions if available
                    dimensions = {}
                    position = {}
                    for cmd in reversed(self.commands[:-1]):
                        if cmd.get("type") == "set_x":
                            dimensions["width"] = cmd.get("x")
                        elif cmd.get("type") == "set_y":
                            dimensions["height"] = cmd.get("y")
                        elif cmd.get("type") == "position_x":
                            position["x"] = cmd.get("x")
                        elif cmd.get("type") == "position_y":
                            position["y"] = cmd.get("y")

                    if dimensions:
                        self.current_element["dimensions"] = dimensions
                    if position:
                        self.current_element["position"] = position
            else:
                # This is probably a color for text or other element
                if self.current_element:
                    self.current_element["colors"] = colors

        elif cmd_type == "input_field":
            field = command.get("field", {})
            position = {}

            # Get most recent position
            for cmd in reversed(self.commands[:-1]):
                if cmd.get("type") == "position_x":
                    position["x"] = cmd.get("x")
                elif cmd.get("type") == "position_y":
                    position["y"] = cmd.get("y")

            # Create input field element
            self._finish_current_element()
            self.current_element = {
                "type": "input_field",
                "field": field,
                "position": position,
            }

    def _finish_current_element(self) -> None:
        """Finish the current element and add it to elements list"""
        if self.current_element:
            # Don't add empty containers
            if not (
                (
                    self.current_element["type"] == "image_section"
                    and not self.current_element.get("images")
                )
                or (
                    self.current_element["type"] == "button_section"
                    and not self.current_element.get("buttons")
                )
                or (
                    self.current_element["type"] == "text_section"
                    and not self.current_element.get("blocks")
                )
            ):
                self.elements.append(self.current_element)
            self.current_element = None

    def get_result(self) -> dict[str, Any]:
        """Get the final processed result"""
        self._finish_current_element()

        # Organize elements by type
        result = {"metadata": self.metadata, "ui_elements": []}

        # Add all non-container elements
        for element in self.elements:
            element_type = element.get("type")

            # Handle special containers
            if element_type == "image_section":
                result["metadata"]["images"] = element.get("images", [])
            elif element_type == "button_section":
                result["ui_elements"].extend(element.get("buttons", []))
            elif element_type == "text_section":
                result["ui_elements"].extend(element.get("blocks", []))
            else:
                result["ui_elements"].append(element)

        return result


def split_commands(line: str) -> list[str]:
    """Split a line that might contain multiple commands

    Args:
        line: Line potentially containing multiple commands

    Returns:
        list of individual command strings
    """
    # Handle special case of comment
    if line.startswith("17,"):
        return [line]

    # Handle lines with command numbers separated by spaces
    commands = []
    parts = line.split()
    current_cmd = ""

    for part in parts:
        # If it starts with a number and looks like a command
        if part and part[0].isdigit() and (part[1:2] == "," or part.isdigit()):
            # If we have a previous command, add it
            if current_cmd:
                commands.append(current_cmd)

            # Start a new command
            current_cmd = part
        elif current_cmd:
            # Add to current command if it exists
            current_cmd += " " + part

    # Add the final command if any
    if current_cmd:
        commands.append(current_cmd)

    # If nothing was found but line isn't empty, return the whole line
    if not commands and line:
        return [line]

    return commands


def parse_command(cmd_str: str) -> Optional[dict[str, Any]]:
    """Parse a single CTR command

    Args:
        cmd_str: Command string to parse

    Returns:
        dict containing parsed command data, or None if invalid
    """
    # Skip empty strings
    cmd_str = cmd_str.strip()
    if not cmd_str:
        return None

    # Basic command format: ID,param1,param2,...
    parts = cmd_str.split(",", 1)
    if len(parts) == 0:
        return None

    try:
        # Get command ID and remaining parameters
        cmd_id = int(parts[0].strip())

        # Get command type
        cmd_type = COMMAND_TYPES.get(cmd_id, f"command_{cmd_id}")

        # Basic command info
        command = {"command": cmd_id, "type": cmd_type}

        # Add parameters based on command type
        if len(parts) > 1:
            params = parts[1].strip()
            # Remove trailing comma if present
            if params.endswith(","):
                params = params[:-1]

            if cmd_id == 1:  # Image count
                command["count"] = int(params)

            elif cmd_id in [4, 5, 6, 7]:  # Coordinates
                command["x" if cmd_id in [4, 6] else "y"] = int(params)

            elif cmd_id == 8:  # Button properties
                props = [int(p.strip()) for p in params.split(",")]
                if len(props) >= 4:
                    # Map properties to meaningful names
                    action_id = props[2]
                    action_name = ACTION_MAPPINGS.get(action_id, f"action_{action_id}")
                    state_value = props[3]
                    state_name = BUTTON_STATES.get(state_value, f"state_{state_value}")

                    command["properties"] = {
                        "group": props[0],
                        "index": props[1],
                        "action": {"id": action_id, "name": action_name},
                        "state": {"value": state_value, "name": state_name},
                    }

            elif cmd_id == 10:  # Text content
                command["text"] = params

            elif cmd_id == 11:  # Input field
                field_props = [int(p.strip()) for p in params.split(",")]
                if len(field_props) >= 3:
                    command["field"] = {
                        "width": field_props[0],
                        "type": field_props[1],
                        "id": field_props[2],
                    }

            elif cmd_id == 12:  # Color
                color_props = [int(p.strip()) for p in params.split(",")]
                if len(color_props) >= 2:
                    # Map colors to names where known
                    bg_name = COLOR_NAMES.get(color_props[0], f"color_{color_props[0]}")
                    fg_name = (
                        COLOR_NAMES.get(color_props[1], f"color_{color_props[1]}")
                        if len(color_props) > 1
                        else None
                    )

                    command["colors"] = {
                        "background": {"value": color_props[0], "name": bg_name}
                    }

                    if fg_name:
                        command["colors"]["foreground"] = {
                            "value": color_props[1],
                            "name": fg_name,
                        }

            elif cmd_id == 17:  # Comment
                command["text"] = params

            elif cmd_id == 18:  # Text style
                style_props = [int(p.strip()) for p in params.split(",")]
                if len(style_props) >= 5:
                    # Map style values to names
                    font_name = FONT_SIZES.get(style_props[0], f"font_{style_props[0]}")
                    style_name = TEXT_STYLES.get(
                        style_props[1], f"style_{style_props[1]}"
                    )
                    bg_name = COLOR_NAMES.get(style_props[2], f"color_{style_props[2]}")
                    fg_name = COLOR_NAMES.get(style_props[3], f"color_{style_props[3]}")
                    align_name = TEXT_ALIGNMENTS.get(
                        style_props[4], f"align_{style_props[4]}"
                    )

                    command["style"] = {
                        "font": {"value": style_props[0], "name": font_name},
                        "style": {"value": style_props[1], "name": style_name},
                        "background": {"value": style_props[2], "name": bg_name},
                        "foreground": {"value": style_props[3], "name": fg_name},
                        "alignment": {"value": style_props[4], "name": align_name},
                    }

            elif cmd_id in [19, 20]:  # Spacing
                command["spacing"] = int(params)

            else:
                # For unknown commands, store raw params
                command["params"] = params

        return command

    except (ValueError, IndexError) as e:
        logger.warning(f"Error parsing command: {cmd_str} - {str(e)}")
        return None


def parse_image_lines(lines: list[str], start_idx: int) -> Tuple[list[str], int]:
    """Parse image filename lines after image count command

    Args:
        lines: list of all lines
        start_idx: Starting index after image count

    Returns:
        Tuple of (image_list, next_index)
    """
    image_count = 1  # Default

    # Get image count from previous line
    if start_idx > 0:
        count_match = re.match(r"1,(\d+)", lines[start_idx - 1])
        if count_match:
            image_count = int(count_match.group(1))

    images = []
    idx = start_idx

    # Read the specified number of image lines
    for _ in range(image_count):
        if idx >= len(lines):
            break

        line = lines[idx].strip()
        if line and not line[0].isdigit():  # If it's not a command
            images.append(line)
            idx += 1
        else:
            break

    return images, idx


def clean_text(text: str) -> str:
    """Clean text by removing special control characters and normalizing whitespace

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove control characters and normalize whitespace
    cleaned = "".join(char for char in text if char.isprintable() or char.isspace())
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned


def parse_ctr_file(filepath: Path) -> dict[str, Any]:
    """Parse a CTR file into structured data

    Args:
        filepath: Path to CTR file

    Returns:
        dict containing structured data
    """
    # Read the file
    with open(filepath, "r", encoding="ascii", errors="replace") as f:
        content = f.read()

    # Split into lines and remove empty lines
    lines = [line.strip() for line in content.split("\n")]
    lines = [line for line in lines if line]

    # Initialize sequence tracker
    sequence = CommandSequence()

    # Process lines
    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip empty lines or lines that only contain control characters
        if not line or not clean_text(line):
            i += 1
            continue

        # Handle image count and filenames special case
        if line.startswith("1,"):
            command = parse_command(line)
            if command and command["type"] == "image_count":
                # Process image filenames
                images, next_idx = parse_image_lines(lines, i + 1)
                sequence.metadata["images"] = [
                    clean_text(img) for img in images if clean_text(img)
                ]
                sequence.add_command(command)
                i = next_idx
                continue

        # Handle special case for text content - usually a whole line
        if line.startswith("10,"):
            command = parse_command(line)
            if command:
                if "text" in command:
                    cleaned_text = clean_text(command["text"])
                    if cleaned_text:
                        command["text"] = cleaned_text
                        sequence.add_command(command)
                i += 1
                continue

        # Handle comment lines - keep the whole line as one command
        if line.startswith("17,"):
            command = parse_command(line)
            if command:
                if "text" in command:
                    cleaned_text = clean_text(command["text"])
                    if cleaned_text:
                        command["text"] = cleaned_text
                        sequence.add_command(command)
                i += 1
                continue

        # For other lines, try to split into commands only if they contain command-like patterns
        if any(cmd_pattern in line for cmd_pattern in [",", " "]) and any(
            str(i) + "," in line for i in range(1, 21)
        ):
            # Split line into individual commands and process each one
            commands = line.split()
            for cmd_str in commands:
                # Only try to parse if it looks like a command (starts with number followed by comma)
                if cmd_str and cmd_str[0].isdigit() and "," in cmd_str:
                    command = parse_command(cmd_str)
                    if command:
                        sequence.add_command(command)
        else:
            # If it's not a command line, it might be an image filename or other content
            if i > 0 and lines[i - 1].startswith("1,"):
                # This is likely an image filename after image count
                cleaned_line = clean_text(line)
                if cleaned_line:
                    sequence.metadata["images"].append(cleaned_line)
            elif not line[0].isdigit():
                # This might be a continuation of a text field or other content
                cleaned_line = clean_text(line)
                if cleaned_line:
                    text_appended = False
                    for cmd in reversed(sequence.commands):
                        if cmd.get("type") == "text_content":
                            # Append to the previous text content
                            cmd["text"] += " " + cleaned_line
                            text_appended = True
                            break

                    # If we didn't append to existing text, treat it as a comment
                    if not text_appended:
                        sequence.add_command(
                            {"command": 17, "type": "comment", "text": cleaned_line}
                        )

        i += 1

    # Get final result
    result = sequence.get_result()

    # Add file metadata
    result["filename"] = filepath.name

    return result


def convert_ctr(filepath: Path, output_dir: Path) -> bool:
    """Convert CTR to JSON

    Args:
        filepath: Path to CTR file
        output_dir: Output directory for converted files

    Returns:
        bool: True if conversion successful
    """
    try:
        if not filepath.name.upper().endswith(".CTR"):
            return False

        output_path = output_dir / "controls" / f"{filepath.stem}.json"
        if output_path.exists():
            logger.debug(f"Skipping {filepath.name} - already converted")
            return True

        # Parse the CTR file
        data = parse_ctr_file(filepath)

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Converted {filepath.name} to JSON")
        return True

    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
