def safe_float(value):
    try:
        num = float(str(value).replace(",", "."))
        return round(num, 2) if num > 0 else None
    except:
        return 0.0

import re

def linestring_to_coordinates(linestring):
    match = re.search(r'LINESTRING\s*\(([^)]+)\)', linestring)
    if not match:
        return []
    coord_pairs = match.group(1).split(',')
    coords = []
    for pair in coord_pairs:
        parts = pair.strip().replace('(', '').replace(')', '').split()
        if len(parts) == 2:
            try:
                lon = float(parts[0].replace(",", "."))
                lat = float(parts[1].replace(",", "."))
                coords.append([lon, lat])
            except Exception:
                continue
    return coords