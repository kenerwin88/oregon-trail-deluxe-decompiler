# Oregon Trail CTR Format Analysis

## Overview

CTR files are control/script files used in The Oregon Trail to define UI layouts, actions, text, and interactive elements. They contain a sequence of numeric commands with parameters that describe how screens and dialogs should be rendered and behave.

## Command Structure

Each command starts with a numeric identifier, followed by comma-separated parameters:
```
COMMAND_ID, param1, param2, ...
```

Most commands occupy a single line, but some (particularly text and UI elements) work in conjunction with subsequent commands to define a complete element.

## Command Types

| Command | Description | Parameters | Example |
|---------|-------------|------------|---------|
| 1 | Image count | Number of images (n) | `1,1` |
| 4 | Set X coordinate | X value | `4,200` |
| 5 | Set Y coordinate | Y value | `5,350` |
| 6 | Set position X | X value | `6,135` |
| 7 | Set position Y | Y value | `7,120` |
| 8 | Button properties | [group, index, action_id, state] | `8,0,0,1,28` |
| 10 | Text content | Text string | `10,This is text content` |
| 11 | Input field | [width, type, id] | `11,4,1,2` |
| 12 | Set color | [background, foreground] | `12,0,6` |
| 17 | Comment/Section | Comment text | `17, let's load the images` |
| 18 | Text style | [font, style, bg, fg, alignment] | `18,2,0,6,1` |
| 19 | Vertical spacing | Pixels to move down | `19,32` |
| 20 | Horizontal spacing | Pixels to move right | `20,24` |

## Command Relationships

### UI Elements

UI elements are defined by sequences of commands:

1. **Dialog Boxes**:
   ```
   4,x_pos 5,y_pos        # Position
   6,width 7,height       # Dimensions
   12,bg_color,fg_color   # Colors
   ```

2. **Text Blocks**:
   ```
   18,font,style,bg,fg,align   # Text style
   6,x_pos 7,y_pos            # Position
   10,Text content            # Content
   20,spacing                 # Optional horizontal spacing
   ```

3. **Buttons**:
   ```
   4,x_section 5,y_section    # Section position
   7,y_offset                 # Y position offset
   6,x_pos 8,params           # X position and button properties
   ```

4. **Input Fields**:
   ```
   6,x_pos 7,y_pos            # Position
   11,width,type,id           # Input field properties
   ```

## Button Properties

Button properties (command 8) use the format `8,group,index,action_id,state`:

- **group**: UI group the button belongs to (0 for main UI)
- **index**: Button index within the group
- **action_id**: Function ID to call when pressed
- **state**: Visual state (28 = enabled, 0 = normal, 1 = disabled)

## Text Styles

Text style (command 18) uses the format `18,font,style,bg,fg,align`:

- **font**: Font ID (1 = small, 2 = medium, 3 = large)
- **style**: Text style (0 = normal, 1 = bold, 2 = italic)
- **bg**: Background color
- **fg**: Foreground color
- **align**: Alignment (0 = left, 1 = center, 2 = right)

## Color Values

Common color values:
- 0: Black
- 6: Gold/Yellow (common background)
- 7: White

## Common Action IDs

Observed action mappings:
- 1: OK/Confirm
- 2: Cancel
- 3: Back
- 5001: Close/Exit

## File Structure Pattern

Most CTR files follow this general structure:
1. Image loading section
   ```
   17, let's load the images
   1,n                  # Number of images
   [Image filenames]    # One per line
   ```

2. UI layout section
   ```
   [Dialog position and dimensions]
   [Color settings]
   ```

3. Content section
   ```
   [Text styles]
   [Text content]
   [Spacing commands]
   ```

4. Controls section
   ```
   17, icon buttons
   [Button definitions]
   [Input fields]
