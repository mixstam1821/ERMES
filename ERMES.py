# ERMES.py
# PLEASE USE YOUR API KEY!!

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
    Select,HoverTool,TapTool,MultiChoice, RadioButtonGroup,WheelZoomTool, TextAreaInput,Range1d, CustomJSHover,CustomJS,BoxEditTool
)

# ─── SOME INITIALS ─────────────────────────────────────
curdoc().theme = 'dark_minimal'

def cusj():
    num=1
    return CustomJSHover(code=f"""
    special_vars.indices = special_vars.indices.slice(0,{num})
    return special_vars.indices.includes(special_vars.index) ? " " : " hidden "
    """)
def hovfun(tltl):
    return """<div @hidden{custom} style="background-color: #efffeb; padding: 5px; border-radius: 5px; box-shadow: 0px 0px 5px rgba(0,0,0,0.3);">        <font size="3" style="background-color: #efffeb; padding: 5px; border-radius: 5px;"> """+tltl+""" <br> </font> </div> <style> :host { --tooltip-border: transparent;  /* Same border color used everywhere */ --tooltip-color: transparent; --tooltip-text: #2f2f2f;} </style> """

month_colors = [
    "blue",      # Jan
    "gray",   # Feb
    "pink",   # Mar
    "lime",    # Apr
    "green",     # May
    "yellow",   # Jun
    "orange",     # Jul
    "red",  # Aug
    "deepskyblue",     # Sep
    "brown",    # Oct
    "steelblue",     # Nov
    "purple",    # Dec
]

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

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
era5_variables += [
    ("high_cloud_cover", "High Cloud Cover"),
    ("medium_cloud_cover", "Medium Cloud Cover"),
    ("low_cloud_cover", "Low Cloud Cover"),
    ("lake_cover", "Lake Cover"),
    ("lake_depth", "Lake Depth"),
    ("snow_depth", "Snow Depth"),
    ("snowmelt", "Snowmelt"),
    ("soil_temperature_level_1", "Soil Temperature Level 1"),
    ("soil_temperature_level_2", "Soil Temperature Level 2"),
    ("maximum_individual_wave_height", "Maximum Individual Wave Height"),
    ("mean_period_of_total_swell", "Mean Period of Total Swell"),
    ("total_column_ozone", "Total Column Ozone"),
    ("total_column_water_vapour", "Total Column Water Vapour"),
    ("total_totals_index", "Total Totals Index"),
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

variable_netcdf_map.update({
    "high_cloud_cover": "hcc",
    "medium_cloud_cover": "mcc",
    "low_cloud_cover": "lcc",
    "lake_cover": "cl",           
    "lake_depth": "dl",
    "snow_depth": "sd",
    "snowmelt": "smlt",
    "soil_temperature_level_1": "stl1",
    "soil_temperature_level_2": "stl2",
    "maximum_individual_wave_height": "hmax",
    "mean_period_of_total_swell": "mpts",

    "total_column_ozone": "tco3",
    "total_column_water_vapour": "tcwv",
    "total_totals_index": "totalx",
})


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
    "sea_ice_cover": "0|1",

    "high_cloud_cover": "(0-1)",
    "medium_cloud_cover": "(0-1)",
    "low_cloud_cover": "(0-1)",
    "lake_cover": "(0-1)",
    "lake_depth": "m",
    "snow_depth": "m",
    "snowmelt": "m",
    "soil_temperature_level_1": "°C",
    "soil_temperature_level_2": "°C",
    "maximum_individual_wave_height": "m",
    "mean_period_of_total_swell": "s",
    "total_column_ozone": "kg/m²",
    "total_column_water_vapour": "kg/m²",
    "total_totals_index": "°C", 


}

minmax_auto_set = {'value': True}   # dict for mutability in Bokeh callbacks
is_playing = {'value': False}
callback_id = {'value': None}
hour_labels = [f"{h:02d}:00" for h in range(24)]
hour_colors = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33",
    "#a65628", "#f781bf", "#999999", "#66c2a5", "#fc8d62", "#8da0cb",
    "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3", "#1b9e77",
    "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d"
]

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
fancy_div_style2 = InlineStyleSheet(css=""" :host { position: relative; background: #343838; color: #fff; border-radius: 16px; padding: 18px 28px; text-align: center; overflow: hidden; box-shadow: 0 6px 18px red; margin: 28px auto; } """)

# ─── FUNCTIONS ─────────────────────────────────────


def update_image(attr, old, new):
    if not hasattr(doc, "_ds"):
        return
    ds = doc._ds.sortby('latitude')
    # print(ds)
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


    # print('---',time_str)

    # varname = "tp" if variable == "total_precipitation" else "t2m"
    variable = variable_select.value
    varname = variable_netcdf_map.get(variable, variable)
    da = ds.sel(valid_time=time_str, method="nearest")[varname]
    # da = ds.sel(valid_time=time_str, method="nearest")[varname]
    # print(da.max())
    # da = da.where(da != 0)
    color_bar.title = f"{variable} [{variable_units_map.get(variable)}]"

    # Precipitation: mask zeros, use mm
    if variable == "total_precipitation":
        varname = "tp"
        da = ds.sel(valid_time=time_str, method="nearest")[varname]
        da = da.where(da > 0.00001*1000) #* 1000  # Convert to mm, mask near-zero
        arr = da.values
        color_bar.title = "Precipitation (mm)"
    # elif varname in ['t2m','d2m','sst']:
    #     # varname = "t2m"
    #     da = ds.sel(valid_time=time_str, method="nearest")[varname]
    #     da = da - 273.15           # Kelvin to Celsius
    #     arr = da.values
    #     color_bar.title = f"{variable} [{variable_units_map.get(variable)}]"
    
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


    months = times.month
    colors = [month_colors[m-1] for m in months]



    
    timeseries_src.data = dict(
        time=times,
        value=values,
        hidden=[False]*len(times),
        month=[month_names[m-1] for m in months],
        color=[month_colors[m-1] for m in months],
    )
    for i, name in enumerate(month_names):
        boolean_filters[i].booleans = [m == name for m in timeseries_src.data['month']]
        
    
    avg_ts = da

    series = pd.Series(avg_ts, index=pd.to_datetime(times))
    monthly_means = series.groupby(series.index.month).mean()
    # print(monthly_means)
    # print('series', series)
    months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    timeseries_plot.yaxis.axis_label = ylabel
    x_min = times.min()
    x_max = times.max()
    # After updating timeseries_src.data and after calculating y_min/y_max:
    if len(values) > 0 and np.any(np.isfinite(values)):
        y_min = np.nanmin(values)
        y_max = np.nanmax(values)
        y_pad = (y_max - y_min) * 0.05 if y_max != y_min else 1.0
        timeseries_plot.y_range = Range1d(start=y_min - y_pad, end=y_max + y_pad)
        timeseries_plot.x_range = Range1d(start=x_min, end=x_max)

    else:
        timeseries_plot.y_range = Range1d(start=0, end=1)
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
        f"Lat: <b>{lat_disp}</b> <br>Lon: <b>{lon_disp}</b><br>"
        f"Slope: <b>{slope}</b> <br>p-value: <b>{pval}</b>"
    )

    download_info.data = dict(
        variable=[variable_select.value],
        lat=[f"{lat:.3f}"],
        lon=[f"{lon:.3f}"],
    )
    box_bounds_div.text = f"point,{lat},{lon}"


    # --- CYCLE PLOT AND TRENDBAR LOGIC ---
    mode = mode_radio.active  # 0=hourly, 1=monthly

    dt = pd.to_datetime(times)
    avg_series = pd.Series(values, index=dt)

    if mode == 1:  # Monthly
        groupby_vals = dt.month
        group_labels = months_names
        group_colors = month_colors
        group_range = range(0, 12)
    else:
        groupby_vals = dt.hour
        group_labels = hour_labels
        group_colors = hour_colors
        group_range = range(24)

    # -- cycle (mean per group)
    means = []
    for g in group_range:
        vals = avg_series[groupby_vals == g if mode == 0 else (groupby_vals == g+1)]
        means.append(np.nanmean(vals) if np.any(~np.isnan(vals)) else np.nan)
    cycleplot_src.data = dict(time=group_labels, value=means)
    cycleplot.x_range.factors = group_labels

    mmin = np.nanmin(means)
    mmax = np.nanmax(means)
    cycleplot.y_range = Range1d(start=mmin, end=mmax)

    # -- trend (slope per group)
    trends = []
    for g in group_range:
        vals = avg_series[groupby_vals == g if mode == 0 else (groupby_vals == g+1)]
        if len(vals) < 2 or np.all(np.isnan(vals)):
            trends.append(np.nan)
            continue
        valid = ~np.isnan(vals)
        if np.sum(valid) < 2:
            trends.append(np.nan)
            continue
        t_sel = vals.index[valid]
        t_num = t_sel.view('int64') / (24 * 60 * 60 * 1e9)
        y_sel = vals.values[valid]
        slope, *_ = linregress(t_num, y_sel)
        trends.append(slope)

    colorss = ['purple' if v >= 0 else 'orange' for v in trends]
    trendbar_src.data = dict(time=group_labels, value=trends,colors=colorss)
    trendbar.y_range.factors = group_labels[::-1]
    mm = np.nanmax(np.abs(trends))
    trendbar.x_range = Range1d(start=-mm-mm*0.01, end=mm+mm*0.01)
    trendbar.title.text = f"Trend for the {len(group_labels)} {'hours' if mode == 0 else 'months'}"

    cross_source.data = dict(x=[event.x], y=[event.y])




def on_click():
    data_error_div.text = ""  # No error!

    div.text = wait_html
    layout.children[2] = column( column(Div(text="", width=0, height=0),styles = {'margin-top': '20px'}),button,column(div, styles = {'margin-left':'10px'}))
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
    layout.children[2] = column(Div(text="",height = 2),button, column(div, styles = {'margin-left':'10px'}))

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

def on_timeseries_tap2(event):
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

    try:
        ds = fetch_era5(sd, ed, variable, min_lat, max_lat, min_lon, max_lon)
        # Kelvin to Celsius conversion for temp variables, only if selected/requested
        temp_vars = ['t2m', 'd2m', 'sst','stl1','stl2','totalx']
        selected_var = variable_netcdf_map.get(variable, variable)
        if selected_var in temp_vars and selected_var in ds.variables:
            ds[selected_var] = ds[selected_var] - 273.15
            ds[selected_var].attrs['units'] = '°C'


        if selected_var == 'tp':
            # Convert total_precipitation from m to mm
            ds[selected_var] = ds[selected_var] * 1000  # Convert to mm
            ds[selected_var].attrs['units'] = 'mm'
        # ds = fetch_era5(sd, ed, variable)
        doc._ds = ds
        data_error_div.text = ""  # No error!
        fill_date_multichoice()   # <<<--- CALL IT HERE!
        update_image(None, None, None)
        minmax_auto_set['value'] = True
    except Exception as e:
        msg = str(e)
        # Optionally, only show error if it's a data-related one:
        data_error_div.text = f"Data error: <br>{msg}"
    return 1

# ─── JOB POLLING LOGIC ────────────────────────────────────────
def poll_job_status():
    if is_job_done() == 1:
        for p in plots:
            p.visible = True
        layout.children[2] = column(column(Div(text="", width=0, height=0),styles = {'margin-top': '20px'}),button, row(column(plots[0], stylesheets=[fancy_div_style2],styles = {'margin-left': '-400px','margin-top': '3px'}), column(trendbar, stylesheets=[fancy_div_style2],styles = {'margin-left': '20px','margin-top': '0px'})), row(column(timeseries_plot, stylesheets=[fancy_div_style2],styles = {'margin-left': '-400px','margin-top': '0px'}),column(cycleplot, stylesheets=[fancy_div_style2],styles = {'margin-left': '20px','margin-top': '0px'}))
                                    )
    else:
        curdoc().add_timeout_callback(poll_job_status, 1)

def on_mode_change(attr, old, new):
    minmax_auto_set['value'] = True
    update_slider_range(None, None, None)  # << Add this!
    on_click()  # triggers data reload via poll_job_status


def get_month_starts(start_date, end_date):
    # start_date, end_date: "YYYY-MM-DD"
    start = pd.to_datetime(start_date).replace(day=1)
    end = pd.to_datetime(end_date).replace(day=1)
    months = pd.date_range(start, end, freq='MS')  # Month start
    return [int(m.timestamp()*1000) for m in months]  # as ms since epoch

def on_box_change(attr, old, new):
    # Only proceed if there's at least one box with nonzero size
    xs = boxes_source.data.get('x', [])
    ys = boxes_source.data.get('y', [])
    widths = boxes_source.data.get('width', [])
    heights = boxes_source.data.get('height', [])
    if len(xs) == 0 or widths[0] == 0 or heights[0] == 0:
        info_div.text = "Draw a rectangle <br> on the map."
        timeseries_src.data = dict(time=[], value=[], hidden=[] )
        cycleplot_src.data = dict(time=[], value=[])
        trendbar_src.data = dict(time=[], value=[])
        return

    # Take the first box (since num_objects=1)
    x_center = xs[0]
    y_center = ys[0]
    width = widths[0]
    height = heights[0]
    if width == 0 or height == 0:
        info_div.text = "Draw a rectangle <br> on the map."
        timeseries_src.data = dict(time=[], value=[], hidden = [])
        cycleplot_src.data = dict(time=[], value=[])
        trendbar_src.data = dict(time=[], value=[])
        return

    # Convert from center/width/height to box bounds (Web Mercator)
    x0 = x_center - width/2
    x1 = x_center + width/2
    y0 = y_center - height/2
    y1 = y_center + height/2

    # Convert box corners to lon/lat
    lon0, lat0 = transformer.transform(x0, y0, direction='INVERSE')
    lon1, lat1 = transformer.transform(x1, y1, direction='INVERSE')
    min_lat, max_lat = min(lat0, lat1), max(lat0, lat1)
    min_lon, max_lon = min(lon0, lon1), max(lon0, lon1)
    doc._current_box_latlon = (min_lat, max_lat, min_lon, max_lon)
    box_bounds_div.text = f"box,{min_lat},{max_lat},{min_lon},{max_lon}"

    # Fetch and mask the variable data
    try:
        ds = doc._ds
        variable = variable_select.value
        varname = variable_netcdf_map.get(variable, variable)
        lats = ds.latitude.values
        lons = ds.longitude.values

        lat_mask = (lats >= min_lat) & (lats <= max_lat)
        lon_mask = (lons >= min_lon) & (lons <= max_lon)
        if not lat_mask.any() or not lon_mask.any():
            info_div.text = "Box: no grid points in region!"
            timeseries_src.data = dict(time=[], value=[], hidden=[])
            cycleplot_src.data = dict(time=[], value=[])
            trendbar_src.data = dict(time=[], value=[])
            return

        # Get the spatial region

        arr = ds[varname][:, lat_mask, :][:, :, lon_mask]
        lats_sub = ds.latitude.values[lat_mask]
        # Compute weights: shape (n_lats, 1)
        weights = np.cos(np.deg2rad(lats_sub)).reshape(-1, 1)
        weights = weights / weights.sum()  # normalize so sum=1

        # Weighted average for each timestep
        # arr: shape (time, n_lats, n_lons)
        # weights: (n_lats, 1), will broadcast over n_lons
        weighted = arr * weights  # shape (time, n_lats, n_lons)
        avg_ts = np.nansum(weighted, axis=(1,2)) / np.nansum(~np.isnan(arr) * weights, axis=(1,2))

        # Update timeseries plot

        # Times and values
        times = ds['valid_time'].values
        times = pd.to_datetime(times)
        values = avg_ts.values if hasattr(avg_ts, "values") else avg_ts
        timeseries_src.data = dict(time=times, value=values, hidden=[False]*len(times) )



        ylabel = f"{variable_units_map.get(variable)}"
        times = ds['valid_time'].values
        times = pd.to_datetime(times)


        months = times.month
        colors = [month_colors[m-1] for m in months]



        
        timeseries_src.data = dict(
            time=times,
            value=values,
            hidden=[False]*len(times),
            month=[month_names[m-1] for m in months],
            color=[month_colors[m-1] for m in months],
        )
        for i, name in enumerate(month_names):
            boolean_filters[i].booleans = [m == name for m in timeseries_src.data['month']]
            
        
        

        series = pd.Series(avg_ts, index=pd.to_datetime(times))
        monthly_means = series.groupby(series.index.month).mean()
        # print(monthly_means)
        # print('series', series)
        months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        timeseries_plot.yaxis.axis_label = ylabel
        x_min = times.min()
        x_max = times.max()
        # After updating timeseries_src.data and after calculating y_min/y_max:
        if len(values) > 0 and np.any(np.isfinite(values)):
            y_min = np.nanmin(values)
            y_max = np.nanmax(values)
            y_pad = (y_max - y_min) * 0.05 if y_max != y_min else 1.0
            timeseries_plot.y_range = Range1d(start=y_min - y_pad, end=y_max + y_pad)
            timeseries_plot.x_range = Range1d(start=x_min, end=x_max)

        else:
            timeseries_plot.y_range = Range1d(start=0, end=1)



        # --- CYCLE PLOT AND TRENDBAR LOGIC ---
        mode = mode_radio.active  # 0=hourly, 1=monthly

        dt = pd.to_datetime(times)
        avg_series = pd.Series(values, index=dt)

        if mode == 1:  # Monthly
            groupby_vals = dt.month
            group_labels = months_names
            group_colors = month_colors
            group_range = range(0, 12)
        else:
            groupby_vals = dt.hour
            group_labels = hour_labels
            group_colors = hour_colors
            group_range = range(24)

        # -- cycle (mean per group)
        means = []
        for g in group_range:
            vals = avg_series[groupby_vals == g if mode == 0 else (groupby_vals == g+1)]
            means.append(np.nanmean(vals) if np.any(~np.isnan(vals)) else np.nan)
        cycleplot_src.data = dict(time=group_labels, value=means)
        cycleplot.x_range.factors = group_labels

        mmin = np.nanmin(means)
        mmax = np.nanmax(means)
        cycleplot.y_range = Range1d(start=mmin, end=mmax)

        # -- trend (slope per group)
        trends = []
        for g in group_range:
            vals = avg_series[groupby_vals == g if mode == 0 else (groupby_vals == g+1)]
            if len(vals) < 2 or np.all(np.isnan(vals)):
                trends.append(np.nan)
                continue
            valid = ~np.isnan(vals)
            if np.sum(valid) < 2:
                trends.append(np.nan)
                continue
            t_sel = vals.index[valid]
            t_num = t_sel.view('int64') / (24 * 60 * 60 * 1e9)
            y_sel = vals.values[valid]
            slope, *_ = linregress(t_num, y_sel)
            trends.append(slope)

        colorss = ['purple' if v >= 0 else 'orange' for v in trends]
        trendbar_src.data = dict(time=group_labels, value=trends,colors=colorss)
        trendbar.y_range.factors = group_labels[::-1]
        mm = np.nanmax(np.abs(trends))
        trendbar.x_range = Range1d(start=-mm-mm*0.01, end=mm+mm*0.01)
        trendbar.title.text = f"Trend for the {len(group_labels)} {'hours' if mode == 0 else 'months'}"









        # Slope and p-value for the spatial mean
        mask = pd.notnull(values) & ~pd.isna(values)
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
            f"Box:<br>Lat [{min_lat:.3f}, {max_lat:.3f}], <br>"
            f"Lon [{min_lon:.3f}, {max_lon:.3f}] <br>"
            f"Slope: <b>{slope}</b> <br> p-value: <b>{pval}</b>"
        )
        download_info.data = dict(
            variable=[variable_select.value],
            lat=[f"{min_lat:.3f}_{max_lat:.3f}"],
            lon=[f"{min_lon:.3f}_{max_lon:.3f}"],
        )
    except Exception as e:
        info_div.text = f"Box error: {e}"
        timeseries_src.data = dict(time=[], value=[], hidden = [])
        cycleplot_src.data = dict(time=[], value=[])
        trendbar_src.data = dict(time=[], value=[])
# ─── WIDGETS ─────────────────────────────────────
data_error_div = Div(text="<pre>Waiting for Errors...</pre>", width=700, height=200, styles={ "background": "#11151c", "color": "#19ffe0", "font-family": "Consolas, monospace", "font-size": "1.06em", "margin-left": "32px", "border-radius": "12px", "box-shadow": "0 2px 16px #00ffe033", "overflow-y": "auto", "white-space": "pre-wrap", "padding": "8px 18px", 'margin-top': '30px' })
date_time_display = Div(text="", width=340, height=32, stylesheets=[fancy_div_style])
stats_div = Div(text="Min: --<br>Max: --<br>Mean: --", width=260, height=48,)
mode_radio = RadioButtonGroup( labels=["Hourly", "Monthly"], active=0, width=240, stylesheets=[radio_style],styles={"margin-top": "20px", "margin-bottom": "10px", "margin-left": "10px"} )
notes_textarea = TextAreaInput( title="Notes / Comments", value="", width=860, height=260, stylesheets=[textarea_style] )
logo_url = "https://raw.githubusercontent.com/mixstam1821/bokeh_showcases/refs/heads/main/assets0/ermes.png"  # <-- set your actual path
logo_div = Div( text=f'<img src="{logo_url}" style="width:200px; margin-bottom:10px;  margin-left:10px; border-radius:12px; box-shadow:0 2px 14px #00ffe055;">', width=200, height=150, styles={"display": "flex", "justify-content": "center"} )
about_div = Div( text=""" <div style="text-align:center; color:#00ffe0; font-size:1.07em; font-family:Consolas, monospace;"> Developed with <span style="color:#ff4c4c;">&#10084;&#65039;</span> by <a href="https://github.com/mixstam1821" target="_blank" style="color:#ffb031; font-weight:bold; text-decoration:none;"> mixstam1821 </a> </div> """, width=420, height=38, styles={"margin-top": "10px"} )
era5_div = Div( text=""" <div style="text-align:center; font-size:1.06em; color:#a5e7ff; font-family: Consolas, monospace;"> Powered by <a href="https://bokeh.org" target="_blank" style="color:#00ffe0; font-weight:bold; text-decoration:underline;">Bokeh</a> <span style="margin:0 6px;">and data from</span> <a href="https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels" target="_blank" style="color:#00ffe0; font-weight:bold; text-decoration:underline;"> ERA5 Reanalysis (Copernicus CDS) </a> </div> """, width=440, height=38, styles={"margin-top": "2px", 'margin-left': '-30px'} )
infdiv = Div( text=""" <div style="text-align:center; font-size:1.06em; color:#a5e7ff; font-family: Consolas, monospace;"> Visit the <a href="https://github.com/mixstam1821/ERMES" target="_blank" style="color:#00ffe0; font-weight:bold; text-decoration:underline;"> GitHub repo </a> for more details!  </a> </div> """, width=440, height=38, styles={"margin-top": "2px", 'margin-left': '10px'} )
box_bounds_div = Div(text="", visible=False)

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
info_div = Div( text="Lat: -- <br>Lon: -- <br>Slope: -- <br>p-value: --", width=300, height=30, styles={"font-size": "1.2em", "color": "#00ffe0", "margin": "4px","margin-left": "10px"} )
variable_select = Select( title="Variable", value="total_precipitation", options=era5_variables, stylesheets=[style2] )
play_button = Button(label="Play ▶️", button_type="primary", width=100, stylesheets=[style3])
date_time_display = Div(text="", width=420, height=30, styles = {"font-size": "20px", "font-family": "Consolas, 'Courier New', monospace", "color": "#00ffe0",})
start_picker = TextInput(title="Start Date", value="2023-01-01", width=130, stylesheets=[style2])
end_picker = TextInput(title="End Date", value="2025-06-01", width=130, stylesheets=[style2])

start_ts = datepicker_str_to_utc_ts(start_picker.value)
end_ts = datepicker_str_to_utc_ts_end_of_day(end_picker.value)
hour_slider = Slider( title="Date & Time", start=int(start_ts), end=int(end_ts+ 24*60*60*1000), value=int(start_ts), step=3600*1000, stylesheets=[slider_style] )
button = Button(label="▶️ Load ERA5 data", button_type="success", width=200,stylesheets=[style],styles = {'margin-top': '0px'})
date_multichoice = MultiChoice( title="Select Date/Time (UTC)", options=[], value=[], width=260, max_items=1, stylesheets=[multi_style] )


# ─── PLOTS ─────────────────────────────────────

# 1.
timeseries_src = ColumnDataSource(data=dict(time=[], value=[], month = [], color = [], hidden=[]))


# Set up the figure
timeseries_plot = figure(
    tools="pan,reset,box_zoom,save",
    x_axis_type='datetime',
    width=800, height=300,
    background_fill_color="#343838",
    border_fill_color="#343838",
    # styles={'margin-left': '-340px'},
)

# Add grey timeseries line (behind points)
tt = timeseries_plot.line('time', 'value', source=timeseries_src, line_width=1, color="grey")

# --- Add colored scatter points per month, with legend ---
from bokeh.models import CDSView, BooleanFilter
scatter_renderers = []
boolean_filters = []
for name, color in zip(month_names, month_colors):
    mask = [m == name for m in timeseries_src.data['month']]
    boolean_filter = BooleanFilter(mask)
    view = CDSView(filter=boolean_filter)
    r = timeseries_plot.scatter('time', 'value', source=timeseries_src,
                               color=color, size=6, view=view, legend_label=name)
    scatter_renderers.append(r)
    boolean_filters.append(boolean_filter)

# -- Axes and grid styling --
timeseries_plot.xaxis.axis_label = 'Time'
timeseries_plot.yaxis.axis_label = 'Value'
timeseries_plot.xgrid.grid_line_color = "#3c3c3c"
timeseries_plot.ygrid.grid_line_color = "#3c3c3c"

# --- HoverTool for line (tt) ---
custom_tooltip = """🕒 @time{%F %H:%M} <br> <b>Value:</b> @value{0.0000000} """
# If you have a custom hover function, use it, else just:
timeseries_plot.add_tools(HoverTool(
    tooltips=hovfun(custom_tooltip),
    formatters={'@time': 'datetime'},
    mode='vline',
    point_policy='snap_to_data',
    line_policy="none",
    attachment="above",show_arrow=False,
    renderers=[tt]
))

# --- TapTool for scatter points ---
scatter_taptool = TapTool(renderers=scatter_renderers)
timeseries_plot.add_tools(scatter_taptool)

# --- Wheel zoom only in x-direction ---
wheel_zoom_x = WheelZoomTool(dimensions='width')
timeseries_plot.add_tools(wheel_zoom_x)
timeseries_plot.toolbar.active_scroll = wheel_zoom_x

# --- Legend setup ---
timeseries_plot.legend.orientation = "horizontal"
timeseries_plot.legend.location = "top_center"
timeseries_plot.legend.label_text_font_size = '9pt'
timeseries_plot.add_layout(timeseries_plot.legend[0], 'below')
timeseries_plot.legend.click_policy = "hide"




# 1b) annual cycle

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# 1.
cycleplot_src = ColumnDataSource(data=dict(time=[], value=[]))
cycleplot = figure(tools="pan,reset,box_zoom,save",x_range=months,
    # x_axis_type='datetime',
    width=450, height=300,
    title="Cycle",
    background_fill_color="#343838",
    border_fill_color="#343838", styles = {'margin-left': '0px',},
)
cycleplot.vbar(x = 'time', top = 'value', source=cycleplot_src, width=0.9, line_color = 'black', hover_fill_color= 'yellow',color="deepskyblue")
cycleplot.xaxis.axis_label = 'Time'
cycleplot.yaxis.axis_label = 'Value'
cycleplot.xgrid.grid_line_color = "#3c3c3c"
cycleplot.ygrid.grid_line_color = "#3c3c3c"
custom_tooltip = """ <div style="background-color: #fff0eb; padding: 5px; border-radius: 5px; box-shadow: 0px 0px 5px rgba(0,0,0,0.3);"> <font size="3" style="background-color: #fff0eb; padding: 5px; border-radius: 5px;"> 🕒 @time <br> <b>Value:</b> @value{0.0000000} </font> </div> <style> :host { --tooltip-border: transparent;  /* Same border color used everywhere */ --tooltip-color: transparent; --tooltip-text: #2f2f2f; } </style> """
cycleplot.add_tools(HoverTool( tooltips=custom_tooltip, mode='vline', point_policy='snap_to_data',attachment="above", show_arrow=False))
# scatter_rendererq = cycleplot.scatter('time', 'value', source=cycleplot_src, size=9, line_color = 'black', color="orange", alpha=0.85)
# scatter_taptoolq = TapTool(renderers=[scatter_rendererq])
# cycleplot.add_tools(scatter_taptoolq)
cycleplot.xaxis.major_label_orientation = 0.6  # in radians (~34 degrees)



cross_source = ColumnDataSource(data=dict(x=[], y=[]))



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
    width=800, height=450,
    title="ERA5",
    tools="pan,wheel_zoom,reset",active_drag="pan", active_scroll="wheel_zoom",background_fill_color="#343838",border_fill_color="#343838",
    # styles = {'margin-left': '-330px'}
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

# Data source for rectangles (can support multiple, but start with one)
boxes_source = ColumnDataSource(data=dict(x=[], y=[], width=[], height=[]))
# This will show all rectangles in boxes_source
rb = p.rect(
    x='x', y='y',
    width='width', height='height',
    source=boxes_source,
    fill_alpha=0.3, fill_color="orange", line_color="red", line_width=3
)

# Add the BoxEditTool to your map and toolbar
box_edit_tool = BoxEditTool(renderers=[rb], num_objects=1)  # Limit to 1 rectangle at a time
p.add_tools(box_edit_tool)


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
    point_policy='snap_to_data', renderers = [image_renderer],attachment="above",show_arrow=False,
)
p.add_tools(hover)

p.scatter(x='x', y='y', source=cross_source, marker='+', size=20, color='red', line_width=2)


# 2B)


# 1b) annual cycle

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# 1.
trendbar_src = ColumnDataSource(data=dict(time=[], value=[], colors=[]))
# trendbar_src.data['time_str'] = [t.strftime('%Y-%m-%d %H:%M') for t in trendbar_src.data['time']]

# 2. Create the line figure
trendbar = figure(y_range=months[::-1],
    tools="pan,reset,box_zoom,save",
    # x_axis_type='datetime',
    width=450, height=450,
    title="Trend for the 12 months of the year.",
    background_fill_color="#343838",
    border_fill_color="#343838",
    # styles={'margin-left': '-340px',}
)

# 3. Draw the line
trendbar.hbar(y = 'time', right = 'value', source=trendbar_src, height=0.9, color="colors",border_radius=5, line_color = 'black', hover_fill_color= 'lime',)

# 4. Axis labels
trendbar.xaxis.axis_label = 'Value'
trendbar.yaxis.axis_label = 'Time'

# 5. Grid styling
trendbar.xgrid.grid_line_color = "#3c3c3c"
trendbar.ygrid.grid_line_color = "#3c3c3c"
# Add "legend only" bars at e.g. 'Jan', with zero length, fully transparent.
trendbar.hbar(y=['Jan'], right=[float('nan')], height=0.8, color='purple', legend_label='+')
trendbar.hbar(y=['Jan'], right=[float('nan')], height=0.8, color='orange', legend_label='–')

trendbar.legend.orientation = "vertical"
trendbar.legend.location = "top_left"
trendbar.legend.label_text_font_size = '11pt'
trendbar.legend.click_policy = "hide"
trendbar.xaxis.major_label_orientation = 0.8  # in radians (~34 degrees)

# 6. Custom tooltip
custom_tooltip = """
<div style="background-color: #fff0eb; padding: 5px; border-radius: 5px; box-shadow: 0px 0px 5px rgba(0,0,0,0.3);">
  <font size="3" style="background-color: #fff0eb; padding: 5px; border-radius: 5px;">
    🕒 @time <br>
    <b>Value:</b> @value{0.0000000}
  </font>
</div>
<style>
  :host {
    --tooltip-border: transparent;
    --tooltip-color: transparent;
    --tooltip-text: #2f2f2f;
  }
</style>
"""

trendbar.add_tools(
    HoverTool(
        tooltips=custom_tooltip,attachment="above",show_arrow=False,
        point_policy='snap_to_data'
    )
)

# ─── CALLBACKS ─────────────────────────────────────
mode_radio.active = 1

mode_radio.on_change('active', on_mode_change)
cycleplot.on_event('tap', on_timeseries_tap2)
trendbar.on_event('tap', on_timeseries_tap2)

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

# Connect the callback
boxes_source.on_change('data', on_box_change)

# ─── LAYOUT ─────────────────────────────────────

download_button = Button(label="Download Timeseries CSV", button_type="primary", width=190, stylesheets=[style3])
download_info = ColumnDataSource(data=dict(variable=[""], lat=[""], lon=[""]))

download_button.js_on_click(CustomJS(
    args=dict(source=timeseries_src, box_bounds_div=box_bounds_div, variable_select=variable_select),
    code="""
    const data = source.data;
    if (!data['time'] || data['time'].length === 0) {
        alert("No timeseries data to download!");
        return;
    }

    // Get variable name
    let var_name = variable_select.value || "variable";
    
    // Read the most recent selection metadata
    let meta = box_bounds_div.text.split(',');
    let fname = "";
    if (meta[0] === "box" && meta.length === 5) {
        let min_lat = parseFloat(meta[1]), max_lat = parseFloat(meta[2]);
        let min_lon = parseFloat(meta[3]), max_lon = parseFloat(meta[4]);
        fname = `timeseries_${var_name}_lat${min_lat.toFixed(2)}-${max_lat.toFixed(2)}_lon${min_lon.toFixed(2)}-${max_lon.toFixed(2)}.csv`;
    } else if (meta[0] === "point" && meta.length === 3) {
        let lat = parseFloat(meta[1]), lon = parseFloat(meta[2]);
        fname = `timeseries_${var_name}_lat${lat.toFixed(4)}_lon${lon.toFixed(4)}.csv`;
    } else {
        fname = `timeseries_${var_name}.csv`;
    }

    // Build CSV
    let csv = "time,value\\n";
    for (let i = 0; i < data['time'].length; i++) {
        let t = new Date(data['time'][i]).toISOString();
        let v = data['value'][i];
        csv += `${t},${v}\\n`;
    }
    let blob = new Blob([csv], { type: "text/csv" });
    let url = URL.createObjectURL(blob);
    let a = document.createElement("a");
    a.href = url;
    a.download = fname;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    """
))



controls_inner = column(
    row(min_lat_input, max_lat_input, stylesheets=[gstyle]),
    row(min_lon_input, max_lon_input, stylesheets=[gstyle]),
    row(start_picker, end_picker), variable_select, row(palette_select,
    row(min_input, max_input)),
    play_button, hour_slider, date_multichoice, download_button, #date_time_display, stats_div,
    sizing_mode="stretch_width", stylesheets=[gstyle]
)

controls = column(

    Div(text="", width=370, height=950, styles={
        "background": "linear-gradient(135deg, #212325 60%, #27293b 100%)",
        "box-shadow": "0 8px 36px #00ffe055",
        "border-radius": "18px", "position": "absolute",
        "z-index": "0", "margin": "-10px", "padding": "28px",'margin-right': '20px'
    }),
    controls_inner,styles = {'margin-left': '20px', 'margin-top': '10px', 'margin-bottom': '5px', 'width': '350px', 'height': '550px', 'position': 'relative', 'z-index': '1'},
    stylesheets=[gstyle]
)

layout = row(column(column(row(logo_div,column(date_time_display, stats_div)), row(mode_radio,info_div)),controls),div2,column(button,styles = {'margin-top': '30px'}),stylesheets=[gstyle])
doc = curdoc()
doc.title = "ERMES"


doc.add_root(column( layout, row(column(about_div, era5_div, infdiv),notes_textarea,data_error_div), stylesheets=[gstyle] ))
update_slider_range(None, None, None)
