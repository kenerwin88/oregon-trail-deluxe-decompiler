# Oregon Trail (DOS) Executable Analysis

## Basic Information
- Filename: OREGON.EXE
- Size: 273,648 bytes
- Format: MS-DOS MZ executable
- Compiler: Borland C++ (1991)

## MZ Header Analysis
First 32 bytes of the executable contain the MZ header:

```
00000000: 4d 5a 70 01 28 01 63 06  c0 01 00 00 ff ff 2f 23  |MZp.(.c......./#|
00000010: 80 00 00 00 00 00 00 00  3e 00 00 00 01 00 fb 50  |........>......P|
```

### Header Breakdown
- 0x0000: "MZ" signature (4D 5A)
- 0x0002: Bytes on last page (0x0170)
- 0x0004: Pages in file (0x0128)
- 0x0006: Relocation entries (0x0663)
- 0x0008: Header size in paragraphs (0x01C0)
- 0x000A: Minimum extra paragraphs (0x0000)
- 0x000C: Maximum extra paragraphs (0xFFFF)
- 0x000E: Initial SS value (0x232F)
- 0x0010: Initial SP value (0x0080)
- 0x0012: Checksum (0x0000)
- 0x0014: Initial IP value (0x0000)
- 0x0016: Initial CS value (0x003E)
- 0x0018: Relocation table offset (0x0001)
- 0x001A: Overlay number (0x50FB)

## Resource Files
The executable references several external resource files:

### Graphics
- OREGON.GXL - Main graphics library
- SPLASH.PC8/PC4 - Splash screen images
- TITLEANI.PCC - Title animation
- MOUNTAIN.PCC - Background graphics
- LEGENDS.PCC - Legend/help screens

### Sound
- GUNSHOT.SND - Sound effect
- HITCRITT.SND - Sound effect
- SPLASH.XMI - Music file

### Sound Drivers
- ADLIB.COM - AdLib sound card driver
- IBMSND.COM - IBM PC speaker driver
- MIDPAK.COM - MIDI music driver
- SBLASTER.COM - Sound Blaster driver

### Configuration
- OT.CNF - Configuration file
- PRODUCT.PF - Product information
- LEGENDS.LST - Legend data

## Memory Requirements
- Minimum: 475K free memory
- With sound: 515K free memory

## Command Line Options
- /CONFIGURE - Launch configuration utility
- -16 - Force 16-color VGA mode

## Next Steps
1. Detailed analysis of code segments
2. Identification of main functions
3. Resource file format analysis
4. Creation of extraction tools for each resource type
