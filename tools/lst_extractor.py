#!/usr/bin/env python3
"""
Extract names from LEGENDS.LST file
"""


def looks_like_name(data):
    """Check if bytes look like a valid name"""
    # Must be ASCII letters, spaces, or periods
    return all(b == 32 or b == 46 or (65 <= b <= 90) or (97 <= b <= 122) for b in data)


def parse_entry_data(data, pos):
    """Parse the bytes after a name"""
    try:
        # Skip initial null byte
        if pos < len(data) and data[pos] == 0:
            pos += 1

        bytes_data = data[pos : pos + 7]  # Get 7 bytes after null
        result = {
            "raw_bytes": " ".join(f"{b:02x}" for b in bytes_data),
            "bytes": bytes_data,
            "values": [],
        }

        # First try bytes 5-6 (where we found some exact matches)
        if len(bytes_data) >= 6:
            score_bytes = bytes_data[5:7]
            if len(score_bytes) == 2:
                le_val = int.from_bytes(score_bytes, byteorder="little")
                be_val = int.from_bytes(score_bytes, byteorder="big")
                result["values"].append(
                    {
                        "offset": 5,
                        "size": 2,
                        "le_value": le_val,
                        "be_value": be_val,
                        "bytes": score_bytes,
                        "priority": "high",  # Mark these as high priority
                    }
                )

        # Then try all other combinations
        for i in range(len(bytes_data) - 1):
            if i == 5:  # Skip the bytes we already tried
                continue

            bytes_pair = bytes_data[i : i + 2]
            if len(bytes_pair) == 2:
                le_val = int.from_bytes(bytes_pair, byteorder="little")
                be_val = int.from_bytes(bytes_pair, byteorder="big")
                result["values"].append(
                    {
                        "offset": i,
                        "size": 2,
                        "le_value": le_val,
                        "be_value": be_val,
                        "bytes": bytes_pair,
                        "priority": "normal",
                    }
                )

                # Try scaling for normal priority only
                result["values"].append(
                    {
                        "offset": i,
                        "size": 2,
                        "le_value": le_val * 10,
                        "be_value": be_val * 10,
                        "bytes": bytes_pair,
                        "scaled": True,
                        "priority": "normal",
                    }
                )

        return result
    except Exception as e:
        print(f"Error parsing entry data: {e}")
        return None


def find_score_match(values_dict, target_scores):
    """Find values that closely match target scores"""
    if not values_dict:
        return None

    for value_type, values in values_dict.items():
        for value in values:
            if any(abs(value - score) < 10 for score in target_scores):
                return value
    return None


def find_names(data):
    """Find sequences that look like names in the data"""
    names = []
    pos = 0
    while pos < len(data):
        # Look for capital letter that might start a name
        if 65 <= data[pos] <= 90:  # ASCII uppercase A-Z
            # Look ahead for a space and more text
            end = pos + 1
            while end < len(data) and (
                data[end] == 32 or (65 <= data[end] <= 90) or (97 <= data[end] <= 122)
            ):
                end += 1

            # If we found what looks like a name (at least 2 chars with a space)
            potential_name = data[pos:end]
            if (
                len(potential_name) >= 4
                and b" " in potential_name
                and looks_like_name(potential_name)
            ):
                names.append((pos, end, potential_name))
                pos = end
            else:
                pos += 1
        else:
            pos += 1
    return names


def extract_legends(filename):
    """Extract names and scores from LEGENDS.LST file"""
    entries = []
    with open(filename, "rb") as f:
        data = f.read()

    print(f"File size: {len(data)} bytes")

    # Find all potential names
    names = find_names(data)
    print(f"Found {len(names)} potential names")

    # Process each name and its following data
    for i, (start, end, name_bytes) in enumerate(names):
        name = name_bytes.decode("ascii")
        print(f"\nName {i + 1}: {name} at position {start}")

        # Get the 8 bytes after the name
        data_pos = end
        entry_data = parse_entry_data(data, data_pos)

        if entry_data:
            entry = {
                "name": name,
                "start_offset": start,
                "values": entry_data["values"],
                "raw_bytes": entry_data["raw_bytes"],
                "bytes": entry_data["bytes"],
            }
            entries.append(entry)
            print(f"Added entry with {len(entry_data['values'])} values")

    return entries


def get_difficulty_level(bytes_data):
    """Try to determine difficulty level from byte pattern"""
    # Look at first few bytes for potential difficulty indicator
    if len(bytes_data) >= 2:
        first_byte = bytes_data[0]
        if first_byte == 0x02:  # Stephen Meek pattern
            return "Trail Guide"
        elif first_byte == 0xDC:  # David Hastings pattern
            return "Adventurer"
        elif first_byte == 0xBF:  # Andrew Sublette pattern
            return "Adventurer"
        else:
            return "Greenhorn"  # Most entries are Greenhorn
    return "Unknown"


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} LEGENDS.LST")
        sys.exit(1)

    # Known scores and difficulties
    expected_entries = [
        ("Stephen Meek", "Trail Guide", 7650),
        ("David Hastings", "Adventurer", 5694),
        ("Andrew Sublette", "Adventurer", 4138),
        ("Celinda Hines", "Greenhorn", 2945),
        ("Ezra Meeker", "Greenhorn", 2052),
        ("William Vaughn", "Greenhorn", 1401),
        ("Mary Bartlett", "Greenhorn", 937),
        ("William Wiggins", "Greenhorn", 615),
        ("Charles Hopper", "Greenhorn", 396),
        ("Elijah White", "Greenhorn", 250),
    ]

    target_scores = [entry[2] for entry in expected_entries]

    entries = extract_legends(sys.argv[1])
    print("\nAnalyzing High Scores:")
    print("(Looking for scores:", ", ".join(map(str, target_scores)), ")")

    # First pass: Look for exact matches at offset 5
    exact_matches = []
    for i, entry in enumerate(entries, 1):
        # Look for high priority matches first (offset 5)
        high_priority = [v for v in entry["values"] if v.get("priority") == "high"]
        for value_info in high_priority:
            for target in target_scores:
                # Check LE value first (since we found exact matches there)
                if value_info["le_value"] == target:
                    exact_matches.append((i, entry["name"], target))
                    break

    if exact_matches:
        print("\nExact matches found:")
        for i, name, score in exact_matches:
            print(f"{i}. {name}: {score}")

    print("\nDetailed Analysis:")
    for i, entry in enumerate(entries, 1):
        expected = expected_entries[i - 1]
        print(f"\n{i}. {entry['name']}")
        print(f"  Expected: {expected[1]}, {expected[2]} points")
        print(f"  Data bytes: {entry['raw_bytes']}")

        # Determine difficulty from byte pattern
        bytes_data = bytes.fromhex(entry["raw_bytes"].replace(" ", ""))
        difficulty = get_difficulty_level(bytes_data)
        print(f"  Detected difficulty: {difficulty}")

        # Track best score match
        best_match = None
        best_diff = float("inf")

        # Process values by priority
        for priority in ["high", "normal"]:
            values = [
                v for v in entry["values"] if v.get("priority", "normal") == priority
            ]
            for value_info in values:
                offset = value_info["offset"]
                bytes_hex = " ".join(f"{b:02x}" for b in value_info["bytes"])
                scaled = value_info.get("scaled", False)

                # Check both LE and BE values against expected score
                expected_score = expected[2]

                # Check LE value
                diff = abs(value_info["le_value"] - expected_score)
                # Use percentage-based threshold for smaller scores
                threshold = max(
                    min(expected_score * 0.1, 50), 10
                )  # 10% of score or 50, minimum 10
                if diff < threshold:
                    desc = f"{value_info['le_value']} (LE{' scaled' if scaled else ''} at offset {offset})"
                    if priority == "high":
                        print(f"  *High priority score match: {desc}")
                    else:
                        print(f"    Possible score: {desc}")
                    print(
                        f"      Bytes: [{bytes_hex}] (diff from expected {expected_score}: {diff})"
                    )
                    if diff < best_diff:
                        best_match = (
                            expected_score,
                            value_info["le_value"],
                            diff,
                            "LE",
                            scaled,
                            priority,
                        )
                        best_diff = diff

                # Check BE value
                diff = abs(value_info["be_value"] - expected_score)
                # Use same percentage-based threshold
                if diff < threshold:
                    desc = f"{value_info['be_value']} (BE{' scaled' if scaled else ''} at offset {offset})"
                    if priority == "high":
                        print(f"  *High priority score match: {desc}")
                    else:
                        print(f"    Possible score: {desc}")
                    print(
                        f"      Bytes: [{bytes_hex}] (diff from expected {expected_score}: {diff})"
                    )
                    if diff < best_diff:
                        best_match = (
                            expected_score,
                            value_info["be_value"],
                            diff,
                            "BE",
                            scaled,
                            priority,
                        )
                        best_diff = diff

        if best_match:
            expected_score, value, diff, endian, scaled, priority = best_match
            priority_str = " (HIGH PRIORITY)" if priority == "high" else ""
            print(
                f"  Best match{priority_str}: {value} ({endian}{' scaled' if scaled else ''}) -> {expected_score} (diff: {diff})"
            )
