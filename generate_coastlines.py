"""
Generate a simple GeoJSON FeatureCollection of coastlines by extracting
a contour at land=0.5 from our synthetic mask. Uses matplotlib's
contour for marching squares since cartopy isn't available.

This produces visually plausible coastlines that match the continents
encoded in the synthetic data. Replace this with real Natural Earth
coastlines for a published version.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

# Mirror the same land mask construction
N_LAT = 72
N_LON = 144
lats = np.linspace(-87.5, 87.5, N_LAT)
lons = np.linspace(-178.75, 178.75, N_LON)

LON, LAT = np.meshgrid(lons, lats)
mask = np.zeros_like(LON)
continents = [
    (-100, 45, 30, 18, 1.0),
    (-90, 30, 25, 15, 0.9),
    (-60, -15, 12, 25, 1.0),
    (15, 50, 25, 12, 0.95),
    (20, 5, 20, 25, 1.0),
    (90, 45, 40, 22, 1.0),
    (110, 25, 25, 18, 0.95),
    (135, -25, 18, 12, 1.0),
    (-40, 72, 12, 8, 0.9),
    (0, -82, 180, 8, 1.0),
    (100, 65, 40, 12, 1.0),
    (115, 0, 12, 8, 0.7),
]
for clon, clat, slon, slat, w in continents:
    d2 = ((LON - clon)/slon)**2 + ((LAT - clat)/slat)**2
    mask += w * np.exp(-d2)
mask = np.clip(mask, 0, 1)

# Use matplotlib contour to extract land contours at multiple levels
# for finer continent edges. We use level 0.3 for "land+coastal" extent.
fig, ax = plt.subplots()
cs = ax.contour(LON, LAT, mask, levels=[0.3, 0.55])

# Extract the contour paths from both levels
features = []
for level_idx in range(len(cs.allsegs)):
    for path in cs.allsegs[level_idx]:
        if len(path) < 6:
            continue
        coords = path.tolist()
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        features.append({
            'type': 'Feature',
            'properties': {'level': float(cs.levels[level_idx])},
            'geometry': {
                'type': 'Polygon',
                'coordinates': [coords],
            }
        })

plt.close(fig)

geojson = {
    'type': 'FeatureCollection',
    'features': features,
}

out_path = os.path.join(os.path.dirname(__file__), 'data', 'coastlines.json')
with open(out_path, 'w') as f:
    json.dump(geojson, f)

sz = os.path.getsize(out_path) / 1024
print(f"Wrote {len(features)} coastline features ({sz:.1f} KB) to {out_path}")
