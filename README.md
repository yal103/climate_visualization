# When does the world cross 2°C?

An interactive D3 visualization of CMIP6 climate-model temperature projections,
showing when each region of the world crosses critical warming thresholds
(1.5°C, 2°C, 3°C, 4°C) under three emissions scenarios (SSP1-2.6, SSP2-4.5,
SSP5-8.5).

**DSC 106 · Project 3 · Spring 2026**

## Live demo

Once deployed, the site lives at `https://<your-org>.github.io/<your-repo>/`.

## Repo layout

```
project3/
├── index.html              # the page
├── css/style.css           # all styles
├── js/
│   ├── lib/d3.min.js       # D3 v7 (vendored — replace with CDN if preferred)
│   └── app.js              # all viz logic, ~700 lines
├── data/
│   ├── grid.json           # lat/lon arrays, year array, scenarios, thresholds
│   ├── crossings.json      # first-crossing-year maps (per scenario × threshold)
│   ├── timeseries.bin      # binary int16-encoded full anomaly grid
│   ├── global_means.json   # global-mean anomaly per scenario per year
│   ├── regional_means.json # regional area-weighted means
│   └── coastlines.json     # GeoJSON outline of continents
├── generate_data.py        # rebuild the synthetic data files
├── generate_coastlines.py  # rebuild the coastline GeoJSON
└── README.md
```

## Running locally

```bash
cd project3
python3 -m http.server 8000
# then open http://localhost:8000
```

Any static file server works — there is no build step.

## Deploying to GitHub Pages

1. Make the repo **public**.
2. In repo Settings → Pages, set the source to `main` (root) or `/docs`.
3. Wait ~30 seconds, then visit `https://<your-username>.github.io/<your-repo>/`.

The vendored `d3.min.js` works offline. If you'd rather use the CDN, swap the
`<script>` tag in `index.html`:

```html
<!-- Local (default) -->
<script src="js/lib/d3.min.js"></script>

<!-- Or CDN -->
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
```

## Swapping in real CMIP6 data

The current data is **synthetic but physically calibrated** — it follows the
same warming patterns CESM2 produces (Arctic amplification ~3×, land/ocean
contrast ~1.4×, and global means matching the IPCC AR6 ranges of ~1.8°C /
~2.7°C / ~5°C in 2100 for SSP1-2.6 / SSP2-4.5 / SSP5-8.5). To replace it
with output from your own notebook:

1. In your CMIP6 notebook, for each scenario `sc` in `('ssp126','ssp245','ssp585')`:

   ```python
   import numpy as np
   subset = catalog.query(
       f"variable_id == 'tas' and table_id == 'Amon' and "
       f"experiment_id == '{sc}' and source_id == 'CESM2'"
   )
   ds = xr.open_zarr(gcs.get_mapper(subset.iloc[0]['zstore']), consolidated=True)
   tas_c = ds['tas'] - 273.15
   yearly = tas_c.groupby('time.year').mean('time')
   baseline = yearly.sel(year=slice(2015, 2034)).mean('year')  # or pre-industrial!
   anomaly = yearly - baseline

   # Save as a single npy
   np.save(f'anomaly_{sc}.npy', anomaly.values)  # shape (years, lat, lon)
   np.save('lats.npy', yearly.lat.values)
   np.save('lons.npy', yearly.lon.values)
   np.save('years.npy', yearly.year.values)
   ```

2. Replace the body of `generate_data.py` after the imports with:

   ```python
   anom_by_sc = {
       'ssp126': np.load('anomaly_ssp126.npy'),
       'ssp245': np.load('anomaly_ssp245.npy'),
       'ssp585': np.load('anomaly_ssp585.npy'),
   }
   lats = np.load('lats.npy')
   lons = np.load('lons.npy')
   years = np.load('years.npy')
   ```

   …and let the rest of the script run (it computes crossings, regional
   means, the global mean, and writes the same JSON / binary files).

3. Re-run `python3 generate_data.py`. Done — no JS changes needed.

For higher-quality coastlines, replace `data/coastlines.json` with
[Natural Earth](https://github.com/topojson/world-atlas) `land-110m`:

```html
<!-- in app.js, replace the loadData fetch -->
const topo = await d3.json('https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json');
data.worldGeo = topojson.feature(topo, topo.objects.land);
```

You'll also need to add a `<script>` tag for `topojson-client`:

```html
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3"></script>
```

## How the viz is structured

State is one object that holds the current scenario / threshold / mode / year /
selected cell. Five components (`map`, `legend`, `globalChart`, `cellChart`,
`histogram`) each expose `init()` and `update()`. Every control change funnels
through `render()`, which calls all five `update()` functions. There's no
component-to-component coupling — adding a new view means writing one module
and one line in `render()`.

The map projects each grid cell as a 4-corner polygon manually (rather than
using `d3.geoPath`) to avoid an antimeridian-clipping artifact in `d3-geo`
where small polygons get drawn with the entire sphere outline appended.

The 5 MB `timeseries.bin` is a single `int16` array (×100 fixed-point
anomaly °C). It loads in one fetch and gets parsed in the browser via
`DataView` + `Int16Array`. Indexing by year is simple offset arithmetic. JSON
encoding the same data would be ~4× larger and ~10× slower to parse.

## Credits

Built for DSC 106 (Spring 2026). Data structure inspired by Pangeo's CMIP6
ARCO catalog. No charting library used — pure D3 v7.
