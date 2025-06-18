# ERMES.py

# ─── IMPORTS ─────────────────────────────────────
import numpy as np
import xarray as xr
import cdsapi
import warnings
import tempfile
import pandas as pd, numpy as np
from pyproj import Transformer
warnings.filterwarnings("ignore")
from scipy.interpolate import RegularGridInterpolator
import xyzservices.providers as xyz
import datetime
from scipy.stats import linregress

from bokeh.plotting import figure
from bokeh.palettes import viridis, inferno, plasma, cividis, magma, turbo
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource, DatePicker, Slider, Button,
    LinearColorMapper, ColorBar, Div,
    TextInput, Button, InlineStyleSheet,GlobalInlineStyleSheet,
    Select,HoverTool,TapTool,MultiChoice, RadioButtonGroup,WheelZoomTool, TextAreaInput

)

# ─── SOME INITIALS ─────────────────────────────────────
curdoc().theme = 'dark_minimal'

era5_variables = [
    ("10m_u_component_of_wind", "10m U Wind"),
    ("10m_v_component_of_wind", "10m V Wind"),
    ("2m_dewpoint_temperature", "2m Dewpoint Temperature"),
    ("2m_temperature", "2m Temperature"),
    ("mean_sea_level_pressure", "Mean Sea Level Pressure"),
    ("mean_wave_direction", "Mean Wave Direction"),
    ("sea_surface_temperature", "Sea Surface Temperature"),
    ("surface_pressure", "Surface Pressure"),
    ("total_precipitation", "Total Precipitation"),
    ("surface_net_solar_radiation", "Surface Net Solar Radiation"),
    ("surface_solar_radiation_downwards", "Surface Solar Radiation Downwards"),
    ("total_cloud_cover", "Total Cloud Cover"),
    ("evaporation", "Evaporation"),
    ("snowfall", "Snowfall"),
    ("k_index", "K Index"),
    ("sea_ice_cover", "Sea Ice Cover"),
]

variable_netcdf_map = {
    "10m_u_component_of_wind": "u10",
    "10m_v_component_of_wind": "v10",
    "2m_dewpoint_temperature": "d2m",
    "2m_temperature": "t2m",
    "mean_sea_level_pressure": "msl",
    "mean_wave_direction": "mwd",
    "sea_surface_temperature": "sst",
    "surface_pressure": "sp",
    "total_precipitation": "tp",
    "surface_net_solar_radiation": "ssr",
    "surface_solar_radiation_downwards": "ssrd",
    "total_cloud_cover": "tcc",
    "evaporation": "e",
    "snowfall": "sf",
    "k_index": "kx",
    "sea_ice_cover": "siconc"
}

variable_units_map = {
    "10m_u_component_of_wind": "m/s",
    "10m_v_component_of_wind": "m/s",
    "2m_dewpoint_temperature": "°C",
    "2m_temperature": "°C",
    "mean_sea_level_pressure": "Pa",
    "mean_wave_direction": "°",
    "sea_surface_temperature": "°C",
    "surface_pressure": "Pa",
    "total_precipitation": "mm",
    "surface_net_solar_radiation": "J/m²",
    "surface_solar_radiation_downwards": "J/m²",
    "total_cloud_cover": "(0-1)",
    "evaporation": "m",
    "snowfall": "m",
    "k_index": "K",
    "sea_ice_cover": "0|1"
}

minmax_auto_set = {'value': True}   # dict for mutability in Bokeh callbacks
is_playing = {'value': False}
callback_id = {'value': None}

# ─── CSS ─────────────────────────────────────

gstyle = GlobalInlineStyleSheet(css=""" html, body, .bk, .bk-root {background-color: #343838; margin: 0; padding: 0; height: 100%; color: white; font-family: 'Consolas', 'Courier New', monospace; } .bk { color: white; } .bk-input, .bk-btn, .bk-select, .bk-slider-title, .bk-headers, .bk-label, .bk-title, .bk-legend, .bk-axis-label { color: white !important; } .bk-input::placeholder { color: #aaaaaa !important; } """)
style = InlineStyleSheet(css=""" .bk-btn { background-color: #00ffe0; color: #1e1e2e; font-weight: bold; border: 10px solid #00ffe0; border-radius: 6px; transform: rotate(0deg); box-shadow: none; transition: all 0.3s ease-in-out; } /* 🟦 Hover: #1e1e2e + rotate */ .bk-btn:hover { background-color: #1e1e2e; border-color: #1e1e2e; color: #00ffe0; transform: rotate(3deg); box-shadow: 0 0 15px 3px #00ffe0; } /* 🔴 Active (click hold): red + stronger rotate */ .bk-btn:active { background-color: red; border-color: red; transform: rotate(6deg); box-shadow: 0 0 15px 3px red; } """)
style2 = InlineStyleSheet(css=""" .bk-input { background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1px solid #3c3c3c; border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } /* Input Hover */ .bk-input:hover { background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1.5px solid #ff3232;        /* Red border */ box-shadow: 0 0 9px 2px #ff3232cc;  /* Red glow */ border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } /* Input Focus */ .bk-input:focus { background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1.5px solid #ff3232; box-shadow: 0 0 11px 3px #ff3232dd; border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } .bk-input:active { outline: none; background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1.5px solid #ff3232; box-shadow: 0 0 14px 3px #ff3232; border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } .bk-input:-webkit-autofill { background-color: #1e1e1e !important; color: #d4d4d4 !important; -webkit-box-shadow: 0 0 0px 1000px #1e1e1e inset !important; -webkit-text-fill-color: #d4d4d4 !important; } """)
style3 = InlineStyleSheet(css=""" .bk-btn { background-color: #00ffe0; color: #1e1e2e; font-weight: bold; border: none; border-radius: 8px; box-shadow: 0 2px 14px 0 #00ffe055; padding: 10px 26px; font-size: 1em; transition: background 0.18s, color 0.18s, box-shadow 0.2s; outline: none; cursor: pointer; } .bk-btn:hover { background: #22293b; color: #00ffe0; box-shadow: 0 0 20px 4px #00ffe0cc; } .bk-btn:active { background: #ff3131; color: #fff; box-shadow: 0 0 18px 3px #ff3131bb; } """)
slider_style = InlineStyleSheet(css=""" /* Host slider container */ :host { background: none !important; } /* Full track: set dark grey, but filled part will override with .noUi-connect */ :host .noUi-base, :host .noUi-target { background: #bfbfbf !important; } /* Highlighted portion of track */ :host .noUi-connect { background: #00ffe0; } /* Slider handle */ :host .noUi-handle { background: #343838; border: 2px solid #00ffe0; border-radius: 50%; width: 20px; height: 20px; } /* Handle hover/focus */ :host .noUi-handle:hover, :host .noUi-handle:focus { border-color: #ff2a68; box-shadow: 0 0 10px #ff2a6890; } /* Tooltip stepping value */ :host .noUi-tooltip { background: #343838; color: #00ffe0; font-family: 'Consolas', monospace; border-radius: 6px; border: 1px solid #00ffe0; } /* Filled (active) slider track */ :host .noUi-connect { background: linear-gradient(90deg, #00ffe0 20%, #d810f7 100%) !important; /* greenish-cyan fade */ box-shadow: 0 0 10px #00ffe099 !important; } """)
multi_style = InlineStyleSheet(css=""" :host { /* CSS Custom Properties for easy theming */ --primary-color: #8b5cf6; --secondary-color: #06b6d4; --background-color: #1f2937; --surface-color: #343838; --text-color: #f9fafb; --accent-color: #f59e0b; --danger-color: #ef4444; background: none !important; } :host .choices__list--dropdown { background: var(--surface-color) !important; border: 1px solid var(--secondary-color) !important; border-radius: 8px !important; box-shadow: 0 10px 25px rgba(0,0,0,0.3) !important; } :host .choices__item--choice { color: var(--text-color) !important; padding: 12px 16px !important; border-bottom: 1px solid rgba(139, 92, 246, 0.2) !important; transition: all 0.2s ease !important; } :host .choices__item--choice:hover { background: var(--primary-color) !important; color: var(--background-color) !important; } :host .choices__item--selectable { background: linear-gradient(90deg, #ffb028 20%, #ff4f4f 100%) !important; color: var(--background-color) !important; border-radius: 6px !important; padding: 6px 12px !important; margin: 3px !important; font-weight: 600 !important; } :host .choices__inner { background: none !important; color: var(--text-color) !important; border: 1px solid lime !important; font-size: 14px !important; } """)

# ─── LOADING SPINNER HTML ─────────────────────────────────────
wait_html = """ <div class="spin-wrapper"> <img src="https://raw.githubusercontent.com/mixstam1821/bokeh_showcases/refs/heads/main/assets0/2784386.png" class="spinner-img"> <p class="loader-msg">⏳ Loading... Stand by.</p> </div> <style> .spin-wrapper { height: 300px; display: flex; flex-direction: column; align-items: center; justify-content: center; } .spinner-img { width: 160px; height: 160px; animation: spin-fast 1.8s linear infinite; filter: drop-shadow(0 0 6px #1a73e8); } @keyframes spin-fast { 0%   { transform: rotate(0deg); } 100% { transform: rotate(360deg); } } .loader-msg { margin-top: 16px; font-size: 18px; color: #ccc; font-family: 'Segoe UI', sans-serif; } </style> """

button_style = InlineStyleSheet(css=""" .bk-btn { background: linear-gradient(90deg, #4545a7 60%, #27293b 100%); color: #fff7cc; font-family: Consolas, monospace; font-size: 1.07em; border-radius: 11px; box-shadow: 0 2px 12px #00ffe055; border: none; padding: 10px 20px; font-weight: 700; } """)
radio_style = InlineStyleSheet(css=""" /* Outer container */ :host { background: #181824 !important; border-radius: 16px !important; padding: 22px 22px 18px 22px !important; box-shadow: 0 4px 18px #0008 !important; max-width: 600px !important; } /* Title */ :host .bk-input-group label, :host .bk-radiobuttongroup-title { color: #f59e0b !important; font-size: 1.16em !important; font-family: 'Fira Code', monospace; font-weight: bold !important; margin-bottom: 16px !important; text-shadow: 0 2px 10px #f59e0b99; letter-spacing: 0.5px; } /* Button group: wrap on small screens */ :host .bk-btn-group { display: flex !important; gap: 18px !important; flex-wrap: wrap !important; justify-content: flex-start; margin-bottom: 6px; } /* Each radio button - pill shape, full text, no ellipsis */ :host button.bk-btn { background: #23233c !important; color: #f9fafb !important; border: 2.5px solid #f59e0b !important; border-radius: 999px !important; padding: 0.7em 2.2em !important; min-width: 120px !important; font-size: 1.09em !important; font-family: 'Fira Code', monospace; font-weight: 600 !important; transition: border 0.13s, box-shadow 0.14s, color 0.12s, background 0.13s; box-shadow: 0 2px 10px #0002 !important; cursor: pointer !important; outline: none !important; white-space: nowrap !important; overflow: visible !important; text-overflow: unset !important; } /* Orange glow on hover */ :host button.bk-btn:hover:not(.bk-active) { border-color: #ffa733 !important; color: #ffa733 !important; box-shadow: 0 0 0 2px #ffa73399, 0 0 13px #ffa73388 !important; background: #2e2937 !important; } /* Red glow on active/focus */ :host button.bk-btn:focus, :host button.bk-btn.bk-active { border-color: #ff3049 !important; color: #ff3049 !important; background: #322d36 !important; box-shadow: 0 0 0 2px #ff304999, 0 0 19px #ff304988 !important; } /* Remove focus outline */ :host button.bk-btn:focus { outline: none !important; } """)
base_variables = """ :host { /* CSS Custom Properties for easy theming */ --primary-color: #8b5cf6; --secondary-color: #06b6d4; --background-color: #1f2937; --surface-color: #343838; --text-color: #f9fafb; --accent-color: #f59e0b; --danger-color: #ef4444; --success-color: #10b981; --border-color: #4b5563; --hover-color: #6366f1; background: none !important; } """
textarea_style  = InlineStyleSheet(css=base_variables + """ :host textarea { background: var(--surface-color) !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; border-radius: 6px !important; padding: 10px 12px !important; font-size: 14px !important; font-family: inherit !important; transition: all 0.2s ease !important; resize: vertical !important; } :host textarea:focus { outline: none !important; border-color: var(--primary-color) !important; box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important; } :host textarea::placeholder { color: #9ca3af !important; opacity: 0.7 !important; } """)
fancy_div_style = InlineStyleSheet(css=""" :host  { background: linear-gradient(90deg, #232b33 80%, #25224c 100%); color: #f1faee; font-family: Consolas, monospace; font-size: 1.13em; padding: 13px 16px; border-radius: 14px; box-shadow: 0 3px 16px #00ffe033; margin-bottom: 8px; margin-top: 7px; text-align: center; letter-spacing: 0.6px; font-weight: bold; line-height: 1.4; } """)

# ─── FUNCTIONS ─────────────────────────────────────

def update_image(attr, old, new):
    if not hasattr(doc, "_ds"):
        return
    ds = doc._ds.sortby('latitude')
    print(ds)
    variable = variable_select.value

    hr = hour_slider.value
    # select the appropriate time slice
    time_str = pd.to_datetime(hr, unit='ms')
    display_str = time_str.strftime("%A, %Y-%m-%d %H:%M UTC")
    mode = mode_radio.active
    if mode == 1:
        # Monthly: format as "YYYY-MM"
        display_str = time_str.strftime("%B %Y")
    else:
        display_str = time_str.strftime("%A, %Y-%m-%d %H:%M UTC")
    date_time_display.text = f"{display_str}"

    # In update_image(), after calculating time_str, add:
    if mode == 1:
        time_str_short = time_str.strftime("%Y-%m")
    else:
        time_str_short = time_str.strftime("%Y-%m-%d %H:%M")
    if date_multichoice.value != [time_str_short]:
        date_multichoice.value = [time_str_short]


    print('---',time_str)

    # varname = "tp" if variable == "total_precipitation" else "t2m"
    variable = variable_select.value
    varname = variable_netcdf_map.get(variable, variable)
    da = ds.sel(valid_time=time_str, method="nearest")[varname]
    # da = ds.sel(valid_time=time_str, method="nearest")[varname]
    print(da.max())
    # da = da.where(da != 0)
    color_bar.title = f"{variable} [{variable_units_map.get(variable)}]"

    # Precipitation: mask zeros, use mm
    if variable == "total_precipitation":
        varname = "tp"
        da = ds.sel(valid_time=time_str, method="nearest")[varname]
        da = da.where(da > 0.00001) * 1000  # Convert to mm, mask near-zero
        arr = da.values
        color_bar.title = "Precipitation (mm)"
    elif varname in ['t2m','d2m','sst']:
        # varname = "t2m"
        da = ds.sel(valid_time=time_str, method="nearest")[varname]
        da = da - 273.15           # Kelvin to Celsius
        arr = da.values
        color_bar.title = f"{variable} [{variable_units_map.get(variable)}]"
    
    else:
        print('')

    arr = da.values
    n_lat, n_lon = arr.shape
    lats = da.latitude.values  
    lons = da.longitude.values  

    print(f"Data shape: {arr.shape}")
    print(f"Latitude range: {lats[0]:.3f} to {lats[-1]:.3f}")
    print(f"Longitude range: {lons[0]:.3f} to {lons[-1]:.3f}")

    # Web Mercator projection functions (corrected)
    def latlon_to_mercator(lon, lat):
        """Convert lat/lon to Web Mercator coordinates"""
        R = 6378137.0
        x = np.deg2rad(lon) * R
        y = np.log(np.tan(np.pi/4 + np.deg2rad(lat)/2)) * R
        return x, y

    def mercator_to_latlon(x, y):
        """Convert Web Mercator back to lat/lon"""
        R = 6378137.0
        lon = np.rad2deg(x / R)
        lat = np.rad2deg(2 * np.arctan(np.exp(y / R)) - np.pi/2)
        return lon, lat

    # Calculate Web Mercator bounds
    # Determine proper lat/lon order
    lat1, lat2 = lats[0], lats[-1]
    lon1, lon2 = lons[0], lons[-1]

    lat_bottom = min(lat1, lat2)
    lat_top    = max(lat1, lat2)
    lon_left   = min(lon1, lon2)
    lon_right  = max(lon1, lon2)

    x_min, y_min = latlon_to_mercator(lon_left, lat_bottom)
    x_max, y_max = latlon_to_mercator(lon_right, lat_top)

    print(f"Web Mercator bounds: x=({x_min:.0f}, {x_max:.0f}), y=({y_min:.0f}, {y_max:.0f})")
    interp = RegularGridInterpolator((lats, lons), arr, bounds_error=False, fill_value=np.nan)

    # Get your data coverage
    lat_span = lats[-1] - lats[0]  # total latitude coverage
    lon_span = lons[-1] - lons[0]  # total longitude coverage
    # This maintains aspect ratio and provides good detail
    aspect_ratio = lon_span / lat_span
    base_height = 600  # Choose base height
    target_height_scaled = base_height
    target_width_scaled = int(base_height * aspect_ratio)

    target_width = target_width_scaled
    target_height = target_height_scaled

    # Create uniform grid in Web Mercator space
    xs = np.linspace(x_min, x_max, target_width)
    ys = np.linspace(y_min, y_max, target_height)
    xm, ym = np.meshgrid(xs, ys)

    # Convert Web Mercator grid back to lat/lon for interpolation
    lonm, latm = mercator_to_latlon(xm, ym)

    # Create points for interpolation (lat, lon order)
    points = np.column_stack([latm.ravel(), lonm.ravel()])

    # Interpolate your data to the Web Mercator grid
    temp_merc = interp(points).reshape((target_height, target_width))

    # # If lats are in decreasing order, flip the result vertically
    if lats[0] > lats[-1]:
        temp_merc = np.flipud(temp_merc)

    # Create image data source
    image_src.data = dict(
        image=[temp_merc],
        x=[x_min], 
        y=[y_min],
        dw=[x_max - x_min], 
        dh=[y_max - y_min]
    )

    # === KEEP COLORMAP & RANGE IN SYNC WITH WIDGETS ===
    # Only auto-fill min/max once per load
    if minmax_auto_set['value']:
        arr_flat = arr.flatten()
        arr_nz = arr_flat[~np.isnan(arr_flat)]
        if arr_nz.size > 0:
            arr_min = float(arr_nz.min())
            arr_max = float(arr_nz.max())
            min_input.value = f"{arr_min:.4g}"
            max_input.value = f"{arr_max:.4g}"
        else:
            arr_min = 0
            arr_max = 1
            min_input.value = "0"
            max_input.value = "1"
        minmax_auto_set['value'] = False  # Prevent further auto-fills

    # === KEEP COLORMAP & RANGE IN SYNC WITH WIDGETS ===
    color_mapper.palette = palette_dict[palette_select.value]
    try:
        color_mapper.low = float(min_input.value)
    except ValueError:
        color_mapper.low = arr_min if 'arr_min' in locals() else 0
    try:
        color_mapper.high = float(max_input.value)
    except ValueError:
        color_mapper.high = arr_max if 'arr_max' in locals() else 1


    # === UPDATE STATS DIV ===
    arr_flat = arr.flatten()
    arr_nz = arr_flat[~np.isnan(arr_flat)]
    if arr_nz.size > 0:
        arr_min = arr_nz.min()
        arr_max = arr_nz.max()
        arr_mean = arr_nz.mean()
        stats_div.text = f"Min: {arr_min:.3f} <br> Max: {arr_max:.3f} <br> Mean: {arr_mean:.3f}"
    else:
        stats_div.text = " "

    # === SYNC THE MULTICHOICE (OPTIONAL) ===
    # This ensures the MultiChoice selection matches the slider date
    if mode == 1:
        time_str_short = time_str.strftime("%Y-%m")
    else:
        time_str_short = time_str.strftime("%Y-%m-%d %H:%M")
    if date_multichoice.value != [time_str_short]:
        date_multichoice.value = [time_str_short]


def update_slider_range(attr, old, new):
    mode = mode_radio.active  # 0 = hourly, 1 = monthly
    dt0 = datetime.datetime.fromisoformat(start_picker.value).replace(tzinfo=datetime.timezone.utc)
    dt1 = datetime.datetime.fromisoformat(end_picker.value).replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(days=1)
    if mode == 1:  # Monthly
        month_starts = get_month_starts(start_picker.value, end_picker.value)
        if not month_starts:
            month_starts = [int(dt0.timestamp()*1000)]
        hour_slider.start = month_starts[0]
        hour_slider.end = month_starts[-1]
        hour_slider.value = month_starts[0]
        # For monthly mode, step = 1 month in ms (just pick diff between first two if >1 month)
        if len(month_starts) > 1:
            hour_slider.step = month_starts[1] - month_starts[0]
        else:
            hour_slider.step = 30*24*3600*1000  # fallback: 30 days
    else:  # Hourly
        start_ms = int(dt0.timestamp() * 1000)
        end_ms   = int(dt1.timestamp() * 1000)
        hour_slider.start = start_ms
        hour_slider.end   = end_ms
        hour_slider.value = start_ms
        hour_slider.step = 3600*1000  # 1 hour in ms

def on_map_tap(event):
    if not hasattr(doc, "_ds"):
        return

    # Convert Web Mercator tap coordinates to lon, lat
    lon, lat = transformer.transform(event.x, event.y, direction='INVERSE')

    ds = doc._ds
    lons = ds.longitude.values
    lats = ds.latitude.values

    # Check if the tap is within the data extent
    lat_min = np.min(lats)
    lat_max = np.max(lats)
    lon_min = np.min(lons)
    lon_max = np.max(lons)

    # Only proceed if within bounds
    if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
        return  # Don't show timeseries if outside data

    # Find nearest index in data grid
    i = np.abs(lats - lat).argmin()
    j = np.abs(lons - lon).argmin()

    variable = variable_select.value
    # varname = "tp" if variable == "total_precipitation" else "t2m"
    # get the API variable
    variable = variable_select.value
    # get the NetCDF/xarray variable name, fallback to API name if missing
    varname = variable_netcdf_map.get(variable, variable)


    da = ds[varname][:, i, j]  # assumes (time, lat, lon) order

    ylabel = f"{variable_units_map.get(variable)}"
    values = da.values
    times = ds['valid_time'].values
    times = pd.to_datetime(times)
    timeseries_src.data = dict(time=times, value=values)
    timeseries_plot.yaxis.axis_label = ylabel

    # # After you update timeseries_src.data:
    times = timeseries_src.data['time']
    values = timeseries_src.data['value']

    if len(times) > 0 and len(values) > 0:
        # Convert to numeric if needed (for pandas Timestamps etc)
        x_min = np.nanmin(times)
        x_max = np.nanmax(times)
        y_min = np.nanmin(values)
        y_max = np.nanmax(values)
        # Add some padding so lines aren't at the very edge
        y_pad = (y_max - y_min) * 0.05 if y_max != y_min else 1.0
        timeseries_plot.x_range.start = x_min
        timeseries_plot.x_range.end = x_max
        timeseries_plot.y_range.start = y_min - y_pad
        timeseries_plot.y_range.end = y_max + y_pad

    # --- Fill info_div ---
    lat_disp = f"{lat:.4f}"
    lon_disp = f"{lon:.4f}"
    mask = np.isfinite(values)
    if np.sum(mask) > 2:
        y = values[mask]
        x = np.arange(len(y))
        result = linregress(x, y)
        slope = f"{result.slope:.4g}"
        pval = f"{result.pvalue:.3g}"
    else:
        slope = "--"
        pval = "--"

    info_div.text = (
        f"Lat: <b>{lat_disp}</b> &nbsp;&nbsp; Lon: <b>{lon_disp}</b> "
        f" &nbsp;&nbsp; Slope: <b>{slope}</b> &nbsp;&nbsp; p-value: <b>{pval}</b>"
    )


def on_click():
    div.text = wait_html
    layout.children[2] = column( column(Div(text="", width=0, height=0),styles = {'margin-top': '20px'}),button,column(div, styles = {'margin-left':'45px'}))
    for p in plots:
        p.visible = False
    curdoc().add_timeout_callback(poll_job_status, 1)

def play():
    if not is_playing['value']:
        is_playing['value'] = True
        play_button.label = "Pause ⏸️"
        run_animation()
    else:
        is_playing['value'] = False
        play_button.label = "Play ▶️"
        if callback_id['value'] is not None:
            curdoc().remove_timeout_callback(callback_id['value'])

def run_animation():
    if not is_playing['value']:
        return
    next_value = hour_slider.value + hour_slider.step
    if next_value > hour_slider.end:
        next_value = hour_slider.start
    hour_slider.value = next_value
    callback_id['value'] = curdoc().add_timeout_callback(run_animation, 350) 

def on_variable_change(attr, old, new):
    # Show spinner immediately
    div.text = wait_html
    layout.children[2] = column(button, column(div, styles = {'margin-left':'45px'}))

    for p in plots:
        p.visible = False
    # Schedule the polling, which fetches data after UI refresh
    minmax_auto_set['value'] = True


    curdoc().add_timeout_callback(poll_job_status, 1)

def on_palette_change(attr, old, new):
    color_mapper.palette = palette_dict[new]

def on_min_change(attr, old, new):
    try:
        color_mapper.low = float(new)
    except ValueError:
        pass

def on_max_change(attr, old, new):
    try:
        color_mapper.high = float(new)
    except ValueError:
        pass

def on_date_multichoice_change(attr, old, new):
    if not new:
        return
    # Only take first selected date (enforced by max_items=1)
    selected_str = new[0]
    import pandas as pd
    dt = pd.to_datetime(selected_str)
    hour_slider.value = int(dt.timestamp() * 1000)
def datepicker_str_to_utc_ts(date_str):
    # This returns UTC timestamp at 00:00 of date_str
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)  # milliseconds

def datepicker_str_to_utc_ts_end_of_day(date_str):
    # This returns UTC timestamp at 23:00 of date_str
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    dt = dt.replace(hour=23, minute=0, second=0, tzinfo=datetime.timezone.utc)
    return int(dt.timestamp() * 1000)


# ─── Helper to fetch ERA5 into memory ───────────────────────────────────────────
def fetch_era5(start_date, end_date, variable, min_lat, max_lat, min_lon, max_lon):
    """
    Retrieve hourly dust export flux from ERA5 for the Med region,
    into an in-memory xarray.Dataset, using exactly your cdsapi.Client() snippet.
    """
    # client = cdsapi.Client()
    client = cdsapi.Client(
    url="https://cds.climate.copernicus.eu/api",
    key="73c6526b-1f98-4d5e-80e2-7ce7c393ff20",
    verify=0
)
    # Choose dataset and request parameters based on mode
    mode = mode_radio.active  # 0=Hourly, 1=Monthly

    if mode == 1:  # Monthly
        dataset = "reanalysis-era5-single-levels-monthly-means"

        # Convert start_date, end_date to years and months lists
        import pandas as pd
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        months_range = pd.date_range(start, end, freq='MS')
        years = sorted({str(d.year) for d in months_range})
        months = sorted({f"{d.month:02d}" for d in months_range})

        request = {
            'format': 'netcdf',
            'product_type': 'monthly_averaged_reanalysis',
            'variable': [variable],
            'year': years,
            'month': months,
            'time': '00:00',
            'area': [float(max_lat), float(min_lon), float(min_lat), float(max_lon)],  # [N, W, S, E]
        }

    else:  # Hourly
        dataset = "reanalysis-era5-single-levels"
        request = {
            'product_type': 'reanalysis',
            'variable': [variable],
            'date': f'{start_date}/{end_date}',
            'time': [f'{h:02d}:00' for h in range(24)],
            'area': [float(max_lat), float(min_lon), float(min_lat), float(max_lon)],
            'format': 'netcdf',
        }

    with tempfile.NamedTemporaryFile(suffix='.nc') as tmp:
        client.retrieve(dataset, request, tmp.name)
        ds = xr.open_dataset(tmp.name)
    return ds

def on_timeseries_tap(event):
    # Find nearest x in timeseries_src
    x_click = event.x  # this is in ms-since-epoch
    xs = timeseries_src.data['time']
    # xs are pandas Timestamp or np.datetime64, need ms
    import pandas as pd
    xs_ms = pd.to_datetime(xs).astype(np.int64) // 10**6
    idx = np.abs(xs_ms - x_click).argmin()
    hr_ms = xs_ms[idx]
    hour_slider.value = int(hr_ms)  # this triggers heatmap update



    # Helper functions for Mercator transforms

def lonlat_to_mercator(lon, lat):
    """Convert lon,lat in degrees to Web Mercator (meters)."""
    k = 6378137
    x = lon * (k * np.pi/180.0)
    y = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
    return x, y

def fill_date_multichoice():
    if not hasattr(doc, "_ds"):
        print("No dataset yet.")
        return
    times = doc._ds['valid_time'].values
    import pandas as pd
    mode = mode_radio.active
    if mode == 1:
        # Monthly: Only show YYYY-MM unique
        time_strs = list(pd.to_datetime(times).strftime("%Y-%m"))
    else:
        time_strs = [str(s) for s in pd.to_datetime(times).strftime("%Y-%m-%d %H:%M")]
    date_multichoice.options = time_strs
    print("MultiChoice options filled:", date_multichoice.options[:5], "...")


# store the dataset on the document
def is_job_done():
    sd, ed = start_picker.value, end_picker.value
    variable = variable_select.value

    min_lat = min_lat_input.value
    max_lat = max_lat_input.value
    min_lon = min_lon_input.value
    max_lon = max_lon_input.value

    ds = fetch_era5(sd, ed, variable, min_lat, max_lat, min_lon, max_lon)

    # ds = fetch_era5(sd, ed, variable)
    doc._ds = ds
    fill_date_multichoice()   # <<<--- CALL IT HERE!

    update_image(None, None, None)
    minmax_auto_set['value'] = True

    return 1

# ─── JOB POLLING LOGIC ────────────────────────────────────────
def poll_job_status():
    if is_job_done() == 1:
        for p in plots:
            p.visible = True
        layout.children[2] = column(column(Div(text="", width=0, height=0),styles = {'margin-top': '20px'}),button, plots[0], info_div, timeseries_plot,
                                    )
    else:
        curdoc().add_timeout_callback(poll_job_status, 1)

def on_mode_change(attr, old, new):
    minmax_auto_set['value'] = True
    update_slider_range(None, None, None)  # << Add this!

    on_click()  # triggers data reload via poll_job_status


def get_month_starts(start_date, end_date):
    # start_date, end_date: "YYYY-MM-DD"
    from datetime import datetime
    import pandas as pd
    start = pd.to_datetime(start_date).replace(day=1)
    end = pd.to_datetime(end_date).replace(day=1)
    months = pd.date_range(start, end, freq='MS')  # Month start
    return [int(m.timestamp()*1000) for m in months]  # as ms since epoch



# ─── WIDGETS ─────────────────────────────────────

date_time_display = Div(text="", width=340, height=32, stylesheets=[fancy_div_style])
stats_div = Div(text="Min: --<br>Max: --<br>Mean: --", width=260, height=48,)
mode_radio = RadioButtonGroup( labels=["Hourly", "Monthly"], active=0, width=240, stylesheets=[radio_style],styles={"margin-top": "20px", "margin-bottom": "10px"} )
notes_textarea = TextAreaInput( title="Notes / Comments", value="", width=860, height=260, stylesheets=[textarea_style] )
logo_url = "https://raw.githubusercontent.com/mixstam1821/bokeh_showcases/refs/heads/main/assets0/ermes.png"  # <-- set your actual path
logo_div = Div( text=f'<img src="{logo_url}" style="width:200px; margin-bottom:10px;  border-radius:12px; box-shadow:0 2px 14px #00ffe055;">', width=200, height=150, styles={"display": "flex", "justify-content": "center"} )
about_div = Div( text=""" <div style="text-align:center; color:#00ffe0; font-size:1.07em; font-family:Consolas, monospace;"> Developed with <span style="color:#ff4c4c;">&#10084;&#65039;</span> by <a href="https://github.com/mixstam1821" target="_blank" style="color:#ffb031; font-weight:bold; text-decoration:none;"> mixstam1821 </a> </div> """, width=420, height=38, styles={"margin-top": "10px"} )
era5_div = Div( text=""" <div style="text-align:center; font-size:1.06em; color:#a5e7ff; font-family: Consolas, monospace;"> Powered by <a href="https://bokeh.org" target="_blank" style="color:#00ffe0; font-weight:bold; text-decoration:underline;">Bokeh</a> <span style="margin:0 6px;">and data from</span> <a href="https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels" target="_blank" style="color:#00ffe0; font-weight:bold; text-decoration:underline;"> ERA5 Reanalysis (Copernicus CDS) </a> </div> """, width=440, height=38, styles={"margin-top": "2px", 'margin-left': '-30px'} )
# ts_xarray_div = Div( text="<pre>--</pre>", width=520, height=220, styles={ "background": "#141417", "color": "#f8fbff", "font-size": "1.06em", "margin-top": "15px", "padding": "8px 18px", "border-radius": "12px", "box-shadow": "0 2px 18px #00ffe055", "font-family": "Consolas, 'Fira Mono', 'monospace'" } )
palette_dict = { "viridis": viridis(256), "inferno": inferno(256), "plasma": plasma(256), "cividis": cividis(256), "magma": magma(256) , "turbo": turbo(256) }
min_lat_input = TextInput(title="Min Lat", value="30", width=100, stylesheets=[style2])
max_lat_input = TextInput(title="Max Lat", value="46", width=100, stylesheets=[style2])
min_lon_input = TextInput(title="Min Lon", value="-6", width=100, stylesheets=[style2])
max_lon_input = TextInput(title="Max Lon", value="36", width=100, stylesheets=[style2])
div = Div(text="", width=600, height=320)
div2 = Div(text="", width=180, height=320)
palette_select = Select( title="Colormap", value="viridis", options=["viridis", "inferno", "plasma", "cividis", "magma", "turbo"], width=100,stylesheets=[style2] )
min_input = TextInput(title="min", value="0", width=80,stylesheets=[style2])
max_input = TextInput(title="max", value="1", width=80,stylesheets=[style2])
stats_div = Div(text=" ", width=300, height=65, styles={"font-size": "1.2em", "color": "#00ffe0"},stylesheets=[style2])
info_div = Div( text="Lat: --  Lon: --  Slope: --  p-value: --", width=850, height=30, styles={"font-size": "1.9em", "color": "#00ffe0", "margin": "4px"} )
variable_select = Select( title="Variable", value="total_precipitation", options=era5_variables, stylesheets=[style2] )
play_button = Button(label="Play ▶️", button_type="primary", width=100, stylesheets=[style3])
date_time_display = Div(text="", width=420, height=30, styles = {"font-size": "20px", "font-family": "Consolas, 'Courier New', monospace", "color": "#00ffe0",})
start_picker = DatePicker(title="Start Date", value="2025-04-08", min_date="1984-01-01",stylesheets=[style2],width=130)
end_picker   = DatePicker(title="End Date",   value="2025-04-09", min_date="1984-01-01",stylesheets=[style2],width=130)
start_ts = datepicker_str_to_utc_ts(start_picker.value)
end_ts = datepicker_str_to_utc_ts_end_of_day(end_picker.value)
hour_slider = Slider( title="Date & Time", start=int(start_ts), end=int(end_ts+ 24*60*60*1000), value=int(start_ts), step=3600*1000, stylesheets=[slider_style] )
button = Button(label="▶️ Load ERA5 data", button_type="success", width=260,stylesheets=[style])
date_multichoice = MultiChoice( title="Select Date/Time (UTC)", options=[], value=[], width=260, max_items=1, stylesheets=[multi_style] )


# ─── PLOTS ─────────────────────────────────────

# 1.
timeseries_src = ColumnDataSource(data=dict(time=[], value=[]))
timeseries_plot = figure(tools="pan,reset,box_zoom,save",
    x_axis_type='datetime',
    width=1600, height=250,
    title="Timeseries at selected location",
    background_fill_color="#343838",
    border_fill_color="#343838", styles = {'margin-left': '-340px',},
)
timeseries_plot.line('time', 'value', source=timeseries_src, line_width=2, color="orange")
timeseries_plot.xaxis.axis_label = 'Time'
timeseries_plot.yaxis.axis_label = 'Value'
timeseries_plot.xgrid.grid_line_color = "#3c3c3c"
timeseries_plot.ygrid.grid_line_color = "#3c3c3c"
custom_tooltip = """ <div style="background-color: #fff0eb; padding: 5px; border-radius: 5px; box-shadow: 0px 0px 5px rgba(0,0,0,0.3);"> <font size="3" style="background-color: #fff0eb; padding: 5px; border-radius: 5px;"> 🕒 @time{%F %H:%M} <br> <b>Value:</b> @value{0.000} </font> </div> <style> :host { --tooltip-border: transparent;  /* Same border color used everywhere */ --tooltip-color: transparent; --tooltip-text: #2f2f2f; } </style> """
timeseries_plot.add_tools(HoverTool( tooltips=custom_tooltip, formatters={'@time': 'datetime'}, mode='vline', point_policy='snap_to_data' ))
scatter_renderer = timeseries_plot.scatter('time', 'value', source=timeseries_src, size=9, line_color = 'black', color="orange", alpha=0.85)
scatter_taptool = TapTool(renderers=[scatter_renderer])
timeseries_plot.add_tools(scatter_taptool)
wheel_zoom_x = WheelZoomTool(dimensions='width')
timeseries_plot.add_tools(wheel_zoom_x)
timeseries_plot.toolbar.active_scroll = wheel_zoom_x



# 2.
# ─── Set up Web-Mercator projection for Med region ──────────────────────────────
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
# approximate bounding box of Med: lon [-6→36], lat [30→46]
x0, y0 = transformer.transform(-6, 30)
x1, y1 = transformer.transform(36, 46)

# ─── Bokeh figure with a tile provider ──────────────────────────────────────────
p = figure(
    x_axis_type="mercator", y_axis_type="mercator",
    x_range=(x0, x1), y_range=(y0, y1),
    width=1600, height=500,
    title="ERA5",
    tools="pan,wheel_zoom,reset",active_scroll="wheel_zoom",background_fill_color="#343838",border_fill_color="#343838",styles = {'margin-left': '-330px'}
)
p.title.text_color = "white"
p.add_tile(xyz.OpenStreetMap.Mapnik)
image_src = ColumnDataSource(dict(image=[np.zeros((1,1))], 
                                  x=[x0], y=[y0], dw=[x1-x0], dh=[y1-y0]))

plots = []
for i in range(1):
    p.visible = False
    plots.append(p)


color_mapper = LinearColorMapper(
    palette=inferno(256), 
    low=0.000001,       # Replacing 0 with 1 as per your request
    high=0.001,   # You might want to check that high/low order; usually low < high!
    nan_color="rgba(0,0,0,0)"
)
p.image(
    image="image", x="x", y="y", dw="dw", dh="dh",
    source=image_src, color_mapper=color_mapper,alpha=0.6
)
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, border_line_color=None,background_fill_color=None, location=(0,0))
p.add_layout(color_bar, 'right')
p.background_fill_color = None
p.border_fill_color = None
p.grid.visible = False
p.add_tools(TapTool())
image_renderer = p.image(
    image="image", x="x", y="y", dw="dw", dh="dh",
    source=image_src, color_mapper=color_mapper, alpha=0.6
)
# custom_tooltip2 = """ <div style="background-color: #fff0eb; padding: 5px; border-radius: 5px; box-shadow: 0px 0px 5px rgba(0,0,0,0.3);"> <font size="3" style="background-color: #fff0eb; padding: 5px; border-radius: 5px;"> <b>Lat</b> $y <br> <b>Lon</b> $x <br> <b>Value:</b> @image{0.000} </font> </div> <style> :host { --tooltip-border: transparent;  /* Same border color used everywhere */ --tooltip-color: transparent; --tooltip-text: #2f2f2f; } </style> """
# p.add_tools(HoverTool( tooltips=custom_tooltip2,point_policy='snap_to_data' ))


from bokeh.models import HoverTool, CustomJSHover

# Web Mercator to Longitude
merc_x_to_lon = CustomJSHover(code="""
    // Web Mercator to Longitude (rounded to 2 decimals)
    var lon = (value / 6378137.0) * 180.0 / Math.PI;
    return Math.round(lon * 100) / 100;
""")

# Web Mercator to Latitude
merc_y_to_lat = CustomJSHover(code="""
    // Web Mercator to Latitude (rounded to 2 decimals)
    var a = value / 6378137.0;
    var lat = (2 * Math.atan(Math.exp(a)) - (Math.PI / 2)) * 180.0 / Math.PI;
    return Math.round(lat * 100) / 100;
""")

custom_tooltip2 = """ <div style="background-color: #fff0eb; padding: 5px; border-radius: 5px; box-shadow: 0px 0px 5px rgba(0,0,0,0.3);"> <font size="3" style="background-color: #fff0eb; padding: 5px; border-radius: 5px;"> <b>Lat</b> $y{custom} <br> <b>Lon</b> $x{custom} <br> <b>Value:</b> @image{0.000000} </font> </div> <style> :host { --tooltip-border: transparent;  /* Same border color used everywhere */ --tooltip-color: transparent; --tooltip-text: #2f2f2f; } </style> """

hover = HoverTool(
    tooltips=custom_tooltip2,
    formatters={
        "$x": merc_x_to_lon,
        "$y": merc_y_to_lat,
    },
    point_policy='snap_to_data'
)
p.add_tools(hover)


# ─── CALLBACKS ─────────────────────────────────────
mode_radio.on_change('active', on_mode_change)

timeseries_plot.on_event('tap', on_timeseries_tap)
button.on_click(on_click)
start_picker.on_change("value", update_slider_range)
end_picker.on_change("value",   update_slider_range)
hour_slider.on_change("value", update_image)
play_button.on_click(play)
variable_select.on_change("value", on_variable_change)
p.on_event('tap', on_map_tap)
palette_select.on_change("value", on_palette_change)
min_input.on_change("value", on_min_change)
max_input.on_change("value", on_max_change)
date_multichoice.on_change("value", on_date_multichoice_change)


# ─── LAYOUT ─────────────────────────────────────



controls_inner = column(
    row(min_lat_input, max_lat_input, stylesheets=[gstyle]),
    row(min_lon_input, max_lon_input, stylesheets=[gstyle]),
    row(start_picker, end_picker), variable_select, row(palette_select,
    row(min_input, max_input)),
    play_button, hour_slider, date_multichoice, #date_time_display, stats_div,
    sizing_mode="stretch_width", stylesheets=[gstyle]
)

controls = column(

    Div(text="", width=370, height=950, styles={
        "background": "linear-gradient(135deg, #212325 60%, #27293b 100%)",
        "box-shadow": "0 8px 36px #00ffe055",
        "border-radius": "18px", "position": "absolute",
        "z-index": "0", "margin": "-10px", "padding": "28px",'margin-right': '20px'
    }),
    controls_inner,styles = {'margin-left': '20px', 'margin-top': '30px', 'margin-bottom': '5px', 'width': '350px', 'height': '500px', 'position': 'relative', 'z-index': '1'},
    stylesheets=[gstyle]
)

layout = row(column(column(row(logo_div,column(date_time_display, stats_div)), mode_radio),controls),div2,column(button,styles = {'margin-top': '30px'}),stylesheets=[gstyle])
doc = curdoc()
doc.title = "ERMES"
doc.add_root(column( layout, row(column(about_div, era5_div),notes_textarea), stylesheets=[gstyle] ))
update_slider_range(None, None, None)
