#!/usr/bin/env python3
"""
Format converter for Oregon Trail files.
Converts extracted GXL files to modern formats.
"""

import logging
from pathlib import Path
from PIL import Image
import struct
import wave

from ..src.core.rle import decompress_rle

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname).1s %(message)s")
logger = logging.getLogger(__name__)


def set_debug(enabled: bool):
    """Enable or disable debug logging"""
    logger.setLevel(logging.DEBUG if enabled else logging.INFO)


class FormatConverter:
    """Handles conversion of various Oregon Trail file formats"""

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

    def convert_pc8_pc4(self, filepath: Path) -> bool:
        """Convert PC8/PC4 image to PNG

        Args:
            filepath: Path to PC8/PC4 file

        Returns:
            bool: True if conversion successful
        """
        try:
            # Skip if already processed
            if not filepath.name.upper().endswith((".PC8", ".PC4")):
                return False

            output_path = self.output_dir / "images" / f"{filepath.stem}.png"
            # Always convert XMI files
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                output_path.unlink()

            # Read raw image data
            with open(filepath, "rb") as f:
                data = f.read()

            # Parse header
            if len(data) < 12:
                logger.warning(f"Invalid header in {filepath.name}")
                return False

            # Check if this is a file table entry
            if data.startswith(b"ght ") or data.startswith(b"pyri"):
                logger.debug(f"Skipping file table entry {filepath.name}")
                return False

            # Ensure we have enough data
            if len(data) < 780:  # At least header (12) + palette (768)
                logger.warning(f"Not enough image data in {filepath.name}")
                return False

            # Check metadata
            metadata = data[:4]
            if metadata[0] != 0x0A or metadata[1] != 0x05 or metadata[2] != 0x01:
                logger.warning(f"Invalid metadata in {filepath.name}")
                return False

            is_8bit = metadata[3] == 0x08

            # Get dimensions
            width = height = 0
            for offset in [4, 8]:
                w, h = struct.unpack("<HH", data[offset : offset + 4])
                if 0 < w <= 320 and 0 < h <= 240:
                    width, height = w, h
                    break

            if not width or not height:
                logger.warning(f"Invalid dimensions in {filepath.name}")
                return False

            # Read palette
            palette_offset = 12
            palette_data = data[palette_offset : palette_offset + 768]
            if len(palette_data) != 768:
                logger.warning(f"Invalid palette in {filepath.name}")
                return False

            # Convert palette to PIL format
            palette = []
            for i in range(0, 768, 3):
                r = (palette_data[i] << 2) | (palette_data[i] >> 4)
                g = (palette_data[i + 1] << 2) | (palette_data[i + 1] >> 4)
                b = (palette_data[i + 2] << 2) | (palette_data[i + 2] >> 4)
                palette.extend([r, g, b])

            # Read and decompress pixel data
            compressed_data = data[palette_offset + 768 :]
            try:
                expected_size = width * height
                if not is_8bit:
                    expected_size = (expected_size + 1) // 2  # Round up for 4-bit

                # Decompress RLE data
                pixel_data, _ = decompress_rle(compressed_data, expected_size)

                if is_8bit:
                    img = Image.frombytes("P", (width, height), pixel_data)
                else:
                    # Expand 4-bit to 8-bit
                    expanded = bytearray()
                    pixels_needed = width * height
                    for byte in pixel_data:
                        if len(expanded) < pixels_needed:
                            expanded.append((byte >> 4) & 0x0F)  # High nibble
                        if len(expanded) < pixels_needed:
                            expanded.append(byte & 0x0F)  # Low nibble
                    img = Image.frombytes(
                        "P", (width, height), bytes(expanded[:pixels_needed])
                    )
            except Exception as e:
                logger.error(
                    f"Error processing pixel data for {filepath.name}: {str(e)}"
                )
                return False

            # Apply palette
            img.putpalette(palette)

            # Save as PNG
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG")
            logger.info(f"Converted {filepath.name} to PNG")
            return True

        except Exception as e:
            logger.error(f"Error converting {filepath.name}: {str(e)}")
            return False

    def convert_xmi(self, filepath: Path) -> bool:
        """Convert XMI to standard MIDI

        Args:
            filepath: Path to XMI file

        Returns:
            bool: True if conversion successful
        """
        try:
            if not filepath.name.upper().endswith(".XMI"):
                return False

            output_path = self.output_dir / "music" / f"{filepath.stem}.mid"
            if output_path.exists():
                logger.debug(f"Skipping {filepath.name} - already converted")
                return True

            def parse_xmi_file(filepath: Path) -> tuple[list[tuple[int, int]], bytes]:
                """Parse XMI file and extract TIMB and EVNT data

                Args:
                    filepath: Path to XMI file

                Returns:
                    tuple: (instruments list, EVNT chunk data)
                """
                # Read XMI file
                with open(filepath, "rb") as f:
                    data = f.read()

                # Find first FORM chunk
                form_pos = data.find(b"FORM")
                if form_pos == -1:
                    raise ValueError("Missing FORM chunk")

                # Skip FORM XDIR section
                if data[form_pos + 8 : form_pos + 12] != b"XDIR":
                    raise ValueError("Missing XDIR section")

                # Find FORM XMID section
                form_pos = data.find(b"FORM", form_pos + 8)
                if form_pos == -1:
                    raise ValueError("Missing FORM XMID section")
                if data[form_pos : form_pos + 4] != b"FORM":
                    raise ValueError("Missing FORM after XDIR")

                # Get XMID section size
                xmid_size = struct.unpack(">L", data[form_pos + 4 : form_pos + 8])[0]
                logger.debug(f"XMID size: {xmid_size}")

                # Verify XMID marker
                if data[form_pos + 8 : form_pos + 12] != b"XMID":
                    raise ValueError("Not an XMID file")

                # Find chunks within XMID section
                pos = form_pos + 12  # Skip FORM + size + XMID
                xmid_end = form_pos + 8 + xmid_size
                logger.debug(f"XMID section: {pos} to {xmid_end}")

                timb_data = None
                evnt_data = None

                while pos < xmid_end - 8:  # Need at least 8 bytes for chunk header
                    chunk_type = data[pos : pos + 4]
                    chunk_size = struct.unpack(">L", data[pos + 4 : pos + 8])[0]
                    logger.debug(f"Found chunk {chunk_type} size {chunk_size} at {pos}")

                    if pos + 8 + chunk_size > xmid_end:
                        raise ValueError(
                            f"Chunk extends beyond XMID section: {chunk_type}"
                        )

                    chunk_data = data[pos + 8 : pos + 8 + chunk_size]

                    if chunk_type == b"TIMB":
                        timb_data = chunk_data
                    elif chunk_type == b"EVNT":
                        evnt_data = chunk_data

                    pos += 8 + chunk_size
                    if chunk_size % 2:  # Skip padding
                        pos += 1

                if not timb_data or not evnt_data:
                    raise ValueError("Missing required chunks")

                # Parse TIMB data
                num_timbres = struct.unpack(">H", timb_data[0:2])[0]
                instruments = []
                pos = 2
                for _ in range(num_timbres):
                    patch = timb_data[pos]
                    bank = timb_data[pos + 1]
                    instruments.append((patch, bank))
                    pos += 2

                return instruments, evnt_data

            # Parse XMI file
            try:
                instruments, evnt_data = parse_xmi_file(filepath)
            except ValueError as e:
                logger.error(f"Error parsing {filepath.name}: {str(e)}")
                return False

            def write_variable_length(value: int) -> bytes:
                """Write a variable length value

                Args:
                    value: Integer value to write

                Returns:
                    bytes: Variable length encoded value
                """
                result = bytearray()
                while value >= 0x80:
                    result.append(0x80 | (value & 0x7F))
                    value >>= 7
                result.append(value)
                return bytes(result)

            def write_track(events: list[tuple[int, bytes]]) -> bytes:
                """Write a MIDI track

                Args:
                    events: list of (delta_time, event_data) tuples

                Returns:
                    bytes: Complete track data with header
                """
                track_data = bytearray()
                for delta_time, event in events:
                    track_data.extend(write_variable_length(delta_time))
                    track_data.extend(event)
                track_data.extend([0x00, 0xFF, 0x2F, 0x00])  # End of track

                header = struct.pack(">4sL", b"MTrk", len(track_data))
                return header + track_data

            # Create instrument tracks
            tracks = []
            for i, (patch, bank) in enumerate(instruments):
                events = [
                    (0, bytes([0xB0 | i, 0x00, bank])),  # Bank select MSB
                    (0, bytes([0xB0 | i, 0x20, 0x00])),  # Bank select LSB
                    (0, bytes([0xC0 | i, patch])),  # Program change
                ]
                tracks.append(write_track(events))

            # Process EVNT chunk into events
            main_events = []
            pos = 0
            event_type = None  # Initialize running status
            try:
                while pos < len(evnt_data):
                    # Read delta time (if present)
                    delta_time = 0
                    if pos < len(evnt_data) and not (evnt_data[pos] & 0x80):
                        # Sum delay bytes until a value less than 0x7F is found
                        while pos < len(evnt_data):
                            byte = evnt_data[pos]
                            pos += 1
                            if byte & 0x80:  # Not a delay byte
                                pos -= 1  # Rewind to reread as event
                                break
                            delta_time += byte
                            if byte != 0x7F:  # Last delay byte
                                break
                        logger.debug(f"Delta time: {delta_time} at {pos}")
                        # Convert 60 PPQN to 96 PPQN
                        delta_time = (delta_time * 96) // 60

                    if pos >= len(evnt_data):
                        logger.debug("End of EVNT data")
                        break

                    # Read event
                    try:
                        byte = evnt_data[pos]
                        pos += 1
                        logger.debug(f"Event byte: {hex(byte)} at {pos - 1}")

                        if byte == 0xFF:  # Meta event
                            if pos + 2 > len(evnt_data):
                                logger.debug("Truncated meta event")
                                break
                            meta_type = evnt_data[pos]
                            pos += 1
                            length = evnt_data[pos]
                            pos += 1
                            logger.debug(
                                f"Meta event: type={hex(meta_type)} length={length} at {pos - 2}"
                            )
                            if pos + length > len(evnt_data):
                                logger.debug("Truncated meta data")
                                break
                            data = evnt_data[pos : pos + length]
                            pos += length

                            # Handle meta events
                            if meta_type == 0x51:  # Tempo
                                # Convert tempo from microseconds per quarter note to BPM
                                tempo = (data[0] << 16) | (data[1] << 8) | data[2]
                                bpm = int(60000000 / tempo)
                                logger.debug(f"Tempo: {bpm} BPM")
                            elif meta_type == 0x58:  # Time signature
                                numerator = data[0]
                                denominator = 1 << data[1]
                                logger.debug(
                                    f"Time signature: {numerator}/{denominator}"
                                )
                            elif meta_type == 0x54:  # SMPTE offset
                                logger.debug("SMPTE offset")

                            event_data = bytearray([0xFF, meta_type, length])
                            event_data.extend(data)
                            main_events.append((delta_time, bytes(event_data)))

                        elif byte & 0x80:  # Status byte
                            event_type = byte
                            logger.debug(f"New status: {hex(event_type)} at {pos - 1}")

                        # Handle MIDI event (either new status or running status)
                        if event_type is None:
                            logger.debug("No running status")
                            break

                        if not (byte & 0x80):  # Data byte
                            pos -= 1  # Rewind to reread the data byte

                        if event_type >= 0xF0:  # System message
                            if pos + 1 > len(evnt_data):
                                logger.debug("Truncated system message")
                                break
                            length = evnt_data[pos]
                            pos += 1
                            logger.debug(
                                f"System message: length={length} at {pos - 1}"
                            )
                            if pos + length > len(evnt_data):
                                logger.debug("Truncated system data")
                                break
                            data = evnt_data[pos : pos + length]
                            pos += length
                            event_data = bytearray([event_type, length])
                            event_data.extend(data)
                            main_events.append((delta_time, bytes(event_data)))
                        else:  # Voice message
                            if event_type >= 0x90 and event_type <= 0x9F:  # Note On
                                if pos + 2 > len(evnt_data):  # Need note, velocity
                                    logger.debug("Truncated Note On")
                                    break
                                note = evnt_data[pos]
                                velocity = evnt_data[pos + 1]
                                pos += 2
                                logger.debug(
                                    f"Note On: note={note} vel={velocity} at {pos}"
                                )

                                # Read duration (variable length)
                                duration = 0
                                try:
                                    # Read first duration byte
                                    if pos >= len(evnt_data):
                                        logger.debug("Missing duration")
                                        break
                                    byte = evnt_data[pos]
                                    pos += 1
                                    if byte & 0x80:  # Not a duration byte
                                        logger.debug(
                                            f"Invalid duration byte: {hex(byte)}"
                                        )
                                        pos -= 1  # Rewind to reread as event
                                        break
                                    duration = byte

                                    # Read additional duration bytes if needed
                                    while byte == 0x7F and pos < len(evnt_data):
                                        byte = evnt_data[pos]
                                        pos += 1
                                        if byte & 0x80:  # Not a duration byte
                                            logger.debug(
                                                f"Invalid duration byte: {hex(byte)}"
                                            )
                                            pos -= 1  # Rewind to reread as event
                                            break
                                        duration += byte
                                    logger.debug(f"Note duration: {duration} at {pos}")

                                    # Convert duration to 96 PPQN
                                    duration = (duration * 96) // 60

                                    # Write Note On
                                    event_data = bytearray([event_type, note, velocity])
                                    main_events.append((delta_time, bytes(event_data)))

                                    # Schedule Note Off
                                    event_data = bytearray(
                                        [0x80 | (event_type & 0x0F), note, 0x40]
                                    )
                                    main_events.append((duration, bytes(event_data)))
                                except IndexError:
                                    logger.debug("Truncated duration")
                                    break

                            elif (
                                event_type >= 0xC0 and event_type <= 0xDF
                            ):  # Program change, Channel pressure
                                length = 1
                                if pos + length > len(evnt_data):
                                    logger.debug("Truncated voice message")
                                    break
                                data = evnt_data[pos : pos + length]
                                pos += length
                                event_data = bytearray([event_type])
                                event_data.extend(data)
                                main_events.append((delta_time, bytes(event_data)))

                            else:  # Other voice messages
                                length = 2
                                if pos + length > len(evnt_data):
                                    logger.debug("Truncated voice message")
                                    break
                                data = evnt_data[pos : pos + length]
                                pos += length
                                event_data = bytearray([event_type])
                                event_data.extend(data)
                                main_events.append((delta_time, bytes(event_data)))

                            # Only read next delta time if we have a complete event
                            if pos < len(evnt_data):
                                if not (byte & 0x80):  # Current byte was data
                                    # Read next delta time
                                    delta_time = 0
                                    try:
                                        # Read first delay byte
                                        if pos >= len(evnt_data):
                                            logger.debug("Missing delay")
                                            break
                                        byte = evnt_data[pos]
                                        pos += 1
                                        if byte & 0x80:  # Not a delay byte
                                            logger.debug(
                                                f"Invalid delay byte: {hex(byte)}"
                                            )
                                            pos -= 1  # Rewind to reread as event
                                            break
                                        delta_time = byte

                                        # Read additional delay bytes if needed
                                        while byte == 0x7F and pos < len(evnt_data):
                                            byte = evnt_data[pos]
                                            pos += 1
                                            if byte & 0x80:  # Not a delay byte
                                                logger.debug(
                                                    f"Invalid delay byte: {hex(byte)}"
                                                )
                                                pos -= 1  # Rewind to reread as event
                                                break
                                            delta_time += byte
                                        logger.debug(
                                            f"Next delta time: {delta_time} at {pos}"
                                        )
                                        # Convert 60 PPQN to 96 PPQN
                                        delta_time = (delta_time * 96) // 60
                                    except IndexError:
                                        logger.debug("Truncated delay")
                                        break
                                else:  # Current byte was status
                                    # Use it for next event
                                    event_type = byte
                                    logger.debug(
                                        f"New running status: {hex(event_type)}"
                                    )
                                    pos -= 1
                            else:
                                logger.debug("End of EVNT data")
                                break

                    except IndexError:
                        logger.error(f"Index error at pos {pos} of {len(evnt_data)}")
                        raise
            except Exception as e:
                logger.error(f"Error parsing EVNT data: {str(e)}")
                return False

            # Add main track
            tracks.append(write_track(main_events))

            # Create output directory and remove existing file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                output_path.unlink()

            # Build MIDI data
            midi_data = bytearray()

            # Write header
            midi_data.extend(
                struct.pack(
                    ">4sLHHH",
                    b"MThd",  # Header magic
                    6,  # Header size
                    1,  # Format 1 (multiple tracks)
                    len(tracks),  # Number of tracks
                    96,  # Ticks per quarter note
                )
            )

            # Write tracks
            for track in tracks:
                midi_data.extend(track)

            # Write MIDI file
            with open(output_path, "wb") as f:
                f.write(midi_data)

            logger.info(f"Converted {filepath.name} to MIDI")
            return True

        except Exception as e:
            logger.error(f"Error converting {filepath.name}: {str(e)}")
            return False

    def convert_snd(self, filepath: Path) -> bool:
        """Convert SND to WAV

        Args:
            filepath: Path to SND file

        Returns:
            bool: True if conversion successful
        """
        try:
            if not filepath.name.upper().endswith(".SND"):
                return False

            output_path = self.output_dir / "sounds" / f"{filepath.stem}.wav"
            if output_path.exists():
                logger.debug(f"Skipping {filepath.name} - already converted")
                return True

            # Read raw audio data
            with open(filepath, "rb") as f:
                data = f.read()

            # Create WAV file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), "wb") as wav:
                wav.setnchannels(1)  # Mono
                wav.setsampwidth(1)  # 8-bit
                wav.setframerate(11025)  # Standard PC speaker rate
                wav.writeframes(data)

            logger.info(f"Converted {filepath.name} to WAV")
            return True

        except Exception as e:
            logger.error(f"Error converting {filepath.name}: {str(e)}")
            return False

    def convert_text(self, filepath: Path) -> bool:
        """Convert text files to UTF-8

        Args:
            filepath: Path to text file

        Returns:
            bool: True if conversion successful
        """
        try:
            if not filepath.name.upper().endswith((".CTR", ".TXT")):
                return False

            output_path = self.output_dir / "text" / f"{filepath.stem}.txt"
            if output_path.exists():
                logger.debug(f"Skipping {filepath.name} - already converted")
                return True

            # Read as ASCII and convert to UTF-8
            with open(filepath, "r", encoding="ascii") as f:
                text = f.read()

            # Save as UTF-8
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            logger.info(f"Converted {filepath.name} to UTF-8")
            return True

        except Exception as e:
            logger.error(f"Error converting {filepath.name}: {str(e)}")
            return False

    def convert_all(self) -> bool:
        """Convert all files in input directory

        Returns:
            bool: True if all conversions successful
        """
        success = True
        for filepath in self.input_dir.rglob("*"):
            if filepath.is_file():
                # Try each converter
                if not any(
                    [
                        self.convert_pc8_pc4(filepath),
                        self.convert_xmi(filepath),
                        self.convert_snd(filepath),
                        self.convert_text(filepath),
                    ]
                ):
                    logger.debug(f"Skipped {filepath.name} - unknown format")

        return success
