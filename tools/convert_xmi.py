#!/usr/bin/env python3
"""
XMI music format converter for Oregon Trail files.
Converts XMI files to standard MIDI format.

Format details:
- Miles Sound System format
- Multiple songs per file (FORM:XDIR + CAT:XMID)
- 60 PPQN timing in source
- Note On events include duration
- Delays are summed 7-bit values
"""

import logging
from pathlib import Path
import struct
from typing import Optional

import sys


def hex_dump(data: bytes, offset: int = 0, length: Optional[int] = None) -> str:
    """Create hex dump of data for debugging"""
    if length is None:
        length = len(data)
    result = []
    for i in range(0, length, 16):
        chunk = data[i : i + 16]
        hex_values = " ".join(f"{b:02x}" for b in chunk)
        hex_values = f"{hex_values:<48}"
        ascii_values = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        result.append(f"{offset + i:04x}: {hex_values} {ascii_values}")
    return "\n".join(result)


# Configure logging to stderr
logging.basicConfig(
    level=logging.DEBUG, format="%(levelname).1s %(message)s", stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Force debug level
logger.setLevel(logging.DEBUG)


def read_xmi_duration(data: bytes, pos: int) -> tuple[int, int]:
    """Read XMI duration value (concatenated bits format like standard MIDI)"""
    if pos >= len(data):
        return 0, pos

    value = 0

    # Read first byte
    if pos >= len(data):
        return 0, pos
    byte = data[pos]
    pos += 1

    # Check if this is an event byte
    if byte & 0x80:
        pos -= 1  # Rewind to reread as event
        return 0, pos

    # Add first byte's value
    value = byte & 0x7F

    # Read additional bytes if needed
    while byte == 0x7F:
        if pos >= len(data):
            break

        byte = data[pos]
        pos += 1

        # Check if this is an event byte
        if byte & 0x80:
            pos -= 1  # Rewind to reread as event
            break

        # Add this byte's value
        value = (value << 7) | (byte & 0x7F)

    return value, pos


def read_xmi_delay(data: bytes, pos: int) -> tuple[int, int]:
    """Read XMI delay value (summed 7-bit values)"""
    if pos >= len(data):
        return 0, pos

    value = 0

    # Read first byte
    if pos >= len(data):
        return 0, pos
    byte = data[pos]
    pos += 1

    # Check if this is an event byte
    if byte & 0x80:
        pos -= 1  # Rewind to reread as event
        return 0, pos

    # Add first byte's value
    value = byte & 0x7F

    # Read additional bytes if needed
    while byte == 0x7F:
        if pos >= len(data):
            break

        byte = data[pos]
        pos += 1

        # Check if this is an event byte
        if byte & 0x80:
            pos -= 1  # Rewind to reread as event
            break

        # Add this byte's value
        value += byte & 0x7F

    return value, pos


def write_variable_length(value: int) -> bytes:
    """Write standard MIDI variable length value"""
    result = bytearray()
    while value >= 0x80:
        result.append(0x80 | (value & 0x7F))
        value >>= 7
    result.append(value)
    return bytes(result)


def parse_xmi_song(
    data: bytes, start_pos: int, filename: str = ""
) -> tuple[list[tuple[int, int]], bytes, Optional[list[tuple[int, int]]]]:
    """Parse a single FORM:XMID song

    Args:
        data: Raw file data
        start_pos: Starting position in data
        filename: Original filename for debug output

    Returns:
        tuple: (instruments list, EVNT data, branch points list or None)
    """
    # Find FORM:XMID chunk
    form_pos = data.find(b"FORM", start_pos)
    if form_pos == -1:
        raise ValueError("Missing FORM:XMID chunk")

    # Get FORM size and verify XMID type
    xmid_size = struct.unpack(">L", data[form_pos + 4 : form_pos + 8])[0]
    if data[form_pos + 8 : form_pos + 12] != b"XMID":
        raise ValueError("Not a FORM:XMID chunk")

    # Find chunks within XMID section
    pos = form_pos + 12  # Skip FORM + size + XMID
    xmid_end = form_pos + 8 + xmid_size
    logger.debug(f"XMID section: {pos} to {xmid_end}")

    timb_data = None
    evnt_data = None
    rbrn_data = None

    while pos < xmid_end - 8:
        chunk_type = data[pos : pos + 4]
        chunk_size = struct.unpack(">L", data[pos + 4 : pos + 8])[0]
        logger.debug(f"Found chunk {chunk_type} size {chunk_size} at {pos}")

        if pos + 8 + chunk_size > xmid_end:
            raise ValueError(f"Chunk extends beyond XMID section: {chunk_type}")

        chunk_data = data[pos + 8 : pos + 8 + chunk_size]

        if chunk_type == b"TIMB":
            timb_data = chunk_data
        elif chunk_type == b"EVNT":
            evnt_data = chunk_data
        elif chunk_type == b"RBRN":
            rbrn_data = chunk_data

        pos += 8 + chunk_size
        if chunk_size % 2:  # Skip padding
            pos += 1

    if not timb_data or not evnt_data:
        raise ValueError("Missing required chunks")

    # Parse TIMB data
    if len(timb_data) < 2:
        raise ValueError(f"TIMB chunk too small: {len(timb_data)} bytes")

    num_timbres = struct.unpack("<H", timb_data[0:2])[0]  # Little endian
    logger.debug(f"TIMB contains {num_timbres} instruments")

    # Verify reasonable number of instruments
    if num_timbres > 256:
        logger.debug(f"Suspiciously large instrument count: {num_timbres}")
        num_timbres = struct.unpack(">H", timb_data[0:2])[0]  # Try big endian
        logger.debug(f"Big endian count: {num_timbres}")
        if num_timbres > 256:
            raise ValueError(f"Invalid instrument count: {num_timbres}")

    # Parse instruments
    instruments = []
    pos = 2
    for i in range(num_timbres):
        if pos + 2 > len(timb_data):
            raise ValueError(f"Truncated TIMB data at instrument {i}")
        patch = timb_data[pos]
        bank = timb_data[pos + 1]
        logger.debug(f"Instrument {i}: patch={patch} bank={bank}")
        instruments.append((patch, bank))
        pos += 2

    # Parse RBRN data if present
    branch_points = None
    if rbrn_data:
        branch_points = []
        pos = 0
        while pos + 6 <= len(rbrn_data):
            branch_id = struct.unpack("<H", rbrn_data[pos : pos + 2])[0]
            dest = struct.unpack("<L", rbrn_data[pos + 2 : pos + 6])[0]
            branch_points.append((branch_id, dest))
            pos += 6

    return instruments, evnt_data, branch_points


def convert_xmi(filepath: Path, output_dir: Path) -> bool:
    """Convert XMI to standard MIDI"""
    try:
        if not filepath.name.upper().endswith(".XMI"):
            return False

        # Read XMI file
        with open(filepath, "rb") as f:
            data = f.read()

        # Find FORM:XDIR chunk
        form_pos = data.find(b"FORM")
        if form_pos == -1:
            logger.error("Missing FORM:XDIR chunk")
            raise ValueError("Missing FORM:XDIR chunk")

        if data[form_pos + 8 : form_pos + 12] != b"XDIR":
            logger.error(
                f"Invalid XDIR section at {form_pos + 8}: {data[form_pos + 8 : form_pos + 12]}"
            )
            raise ValueError("Missing XDIR section")

        # Get number of songs
        info_pos = form_pos + 12
        if data[info_pos : info_pos + 4] != b"INFO":
            logger.error(
                f"Invalid INFO chunk at {info_pos}: {data[info_pos : info_pos + 4]}"
            )
            raise ValueError("Missing INFO chunk")

        num_songs = struct.unpack("<H", data[info_pos + 8 : info_pos + 10])[0]
        logger.debug(f"XMI contains {num_songs} songs")
        if num_songs == 0:
            logger.error("No songs found in XMI file")
            raise ValueError("No songs found")

        # Find CAT:XMID chunk
        cat_pos = data.find(b"CAT ", info_pos + 10)
        if cat_pos == -1:
            raise ValueError("Missing CAT:XMID chunk")

        if data[cat_pos + 8 : cat_pos + 12] != b"XMID":
            raise ValueError("Missing XMID section")

        # Process each song
        pos = cat_pos + 12
        for song_num in range(num_songs):
            # Parse song data
            instruments, evnt_data, branch_points = parse_xmi_song(
                data, pos, filepath.name
            )

            # Create output path
            stem = filepath.stem
            if num_songs > 1:
                stem = f"{stem}_{song_num + 1}"
            output_path = output_dir / "music" / f"{stem}.mid"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                output_path.unlink()

            # Create tracks
            tracks = []

            # Track 0: Tempo and setup
            setup_events = []

            # Add initial tempo (200 BPM = 300,000 microseconds per quarter note)
            tempo_bytes = struct.pack(">L", 300000)[1:]  # 3 bytes
            setup_events.append((0, bytes([0xFF, 0x51, 0x03]) + tempo_bytes))

            tracks.append(setup_events)

            # Track 1: Music data
            main_events = []

            # MT-32 initialization
            for channel in range(16):
                # Reset all controllers
                main_events.append(
                    (0, bytes([0xB0 | channel, 121, 0]))
                )  # Reset all controllers
                main_events.append(
                    (0, bytes([0xB0 | channel, 0, 0]))
                )  # Bank select MSB
                main_events.append(
                    (0, bytes([0xB0 | channel, 32, 0]))
                )  # Bank select LSB

                # MT-32 reverb settings
                main_events.append((0, bytes([0xB0 | channel, 91, 50])))  # Reverb level
                main_events.append((0, bytes([0xB0 | channel, 93, 30])))  # Chorus level

            # Map GM patches to MT-32 equivalents
            mt32_patches = {
                52: 17,  # Choir -> MT-32 Organ 1
                59: 58,  # Tuba -> MT-32 Horn
                64: 49,  # Soprano Sax -> MT-32 Strings
            }

            # Add program changes for instruments
            for channel, (patch, bank) in enumerate(instruments):
                # Force MT-32 mode
                main_events.append(
                    (0, bytes([0xB0 | channel, 114, 0x7F]))
                )  # AIL bank = MT-32
                # Map GM patch to MT-32 equivalent
                mt32_patch = mt32_patches.get(patch, patch)
                main_events.append((0, bytes([0xC0 | channel, mt32_patch])))

            # Process EVNT chunk
            pos = 0
            event_type = None
            current_time = 0

            try:
                while pos < len(evnt_data):
                    # Read delta time
                    if pos < len(evnt_data) and not (evnt_data[pos] & 0x80):
                        delta_time, pos = read_xmi_delay(evnt_data, pos)
                        # Keep original timing (no scaling)
                        current_time += delta_time

                    if pos >= len(evnt_data):
                        break

                    # Read event
                    byte = evnt_data[pos]
                    pos += 1

                    if byte == 0xFF:  # Meta event
                        if pos + 2 > len(evnt_data):
                            break
                        meta_type = evnt_data[pos]
                        pos += 1
                        length = evnt_data[pos]
                        pos += 1
                        if pos + length > len(evnt_data):
                            break
                        data = evnt_data[pos : pos + length]
                        pos += length

                        event_data = bytearray([0xFF, meta_type, length])
                        event_data.extend(data)
                        main_events.append((current_time, bytes(event_data)))

                    elif byte & 0x80:  # Status byte
                        event_type = byte

                    elif event_type is None:
                        break

                    else:  # Data byte with running status
                        pos -= 1  # Rewind to reread data byte

                    if event_type is not None and event_type >= 0x80:  # MIDI event
                        if event_type >= 0x90 and event_type <= 0x9F:  # Note On
                            if pos + 2 > len(evnt_data):
                                break
                            note = evnt_data[pos]
                            velocity = evnt_data[pos + 1]
                            pos += 2

                            # Read duration
                            raw_duration, pos = read_xmi_duration(evnt_data, pos)

                            # Keep original duration (no scaling)
                            duration = raw_duration if raw_duration > 0 else 24

                            # Write Note On
                            event_data = bytearray([event_type, note, velocity])
                            main_events.append((current_time, bytes(event_data)))

                            # Schedule Note Off
                            event_data = bytearray(
                                [0x80 | (event_type & 0x0F), note, 0x40]
                            )
                            main_events.append(
                                (current_time + duration, bytes(event_data))
                            )

                            if filepath.name == "DEATH.XMI":
                                logger.debug(
                                    f"Note: ch={event_type & 0x0F} note={note} vel={velocity} raw_dur={raw_duration} dur={duration} time={current_time}"
                                )

                        elif (
                            event_type >= 0xC0 and event_type <= 0xDF
                        ):  # Program change, Channel pressure
                            if pos + 1 > len(evnt_data):
                                break
                            data = evnt_data[pos : pos + 1]
                            pos += 1
                            event_data = bytearray([event_type])
                            event_data.extend(data)
                            main_events.append((current_time, bytes(event_data)))

                        else:  # Other voice messages
                            if pos + 2 > len(evnt_data):
                                break
                            data = evnt_data[pos : pos + 2]
                            pos += 2
                            event_data = bytearray([event_type])
                            event_data.extend(data)
                            main_events.append((current_time, bytes(event_data)))
            except Exception as e:
                logger.error(f"Error parsing EVNT data at pos {pos}: {str(e)}")
                raise

            tracks.append(main_events)

            # Write MIDI file
            midi_data = bytearray()

            # Write header
            midi_data.extend(
                struct.pack(
                    ">4sLHHH",
                    b"MThd",  # Header magic
                    6,  # Header size
                    1,  # Format 1 (multiple tracks)
                    len(tracks),  # Number of tracks
                    60,  # Original XMI PPQN
                )
            )

            # Write tracks
            for track_num, track_events in enumerate(tracks):
                track_events.sort(key=lambda x: x[0])  # Sort by time

                track_data = bytearray()

                # Add track name
                track_name = f"Track {track_num}"
                track_data.extend([0x00, 0xFF, 0x03, len(track_name)])
                track_data.extend(track_name.encode("ascii"))

                # Add events
                last_time = 0
                for abs_time, event in track_events:
                    delta_time = abs_time - last_time
                    if delta_time < 0:
                        logger.warning(
                            f"Negative delta time in track {track_num}: {delta_time}"
                        )
                        delta_time = 0
                    track_data.extend(write_variable_length(delta_time))
                    track_data.extend(event)
                    last_time = abs_time

                # End of track
                track_data.extend([0x00, 0xFF, 0x2F, 0x00])

                # Add MTrk header
                track_header = struct.pack(">4sL", b"MTrk", len(track_data))
                midi_data.extend(track_header + track_data)

            with open(output_path, "wb") as f:
                f.write(midi_data)

            logger.info(
                f"Converted song {song_num + 1} of {filepath.name} to {output_path.name}"
            )

            # Find next song
            form_pos = data.find(b"FORM", pos)
            if form_pos == -1:
                break
            pos = form_pos

        return True

    except Exception as e:
        logger.error(f"Error converting {filepath.name}: {str(e)}")
        return False
