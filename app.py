import os
import json
from shiny import App, ui, render, reactive
import pandas as pd
import folium

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & PATHS
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "csv")
DATASETS = [
    (os.path.join(CSV_DIR, "FY25 CNMI Fixed Sites.csv"), "2025", 0),
    (os.path.join(CSV_DIR, "FY26 AS PRIA Fixed Sites.csv"), "2026", 1),
    (os.path.join(CSV_DIR, "FY27 NCRMP HA Fixed Sites.csv"), "2024", 0),
]

REGION_BY_LOCATION_CODE = {
    **dict.fromkeys(
        ["FFS", "HAW", "KAH", "KAU", "KUR", "LAN", "LIS", "MAI", "MOL", "NII", "OAH", "PHR"],
        "Hawai'i",
    ),
    **dict.fromkeys(
        ["AGR", "ALA", "ASC", "FDP", "MAU", "PAG", "ROT", "SAI", "SAR", "SUP", "TIN"],
        "Northern Mariana Islands",
    ),
    **dict.fromkeys(["GUA", "GUG"], "Mariana Islands"),
    **dict.fromkeys(["BAK", "HOW", "JAR", "KIN", "PAL", "WAK"], "Pacific Remote Islands and Atolls"),
    **dict.fromkeys(["OFU", "ROS", "SWA", "TAU", "TUT"], "American Samoa"),
}

PHOTO_CATEGORIES = {
    "Site Photos": "Site_Photos",
    "STR Photos": "STR_Photos",
}
PHOTO_COLLECTIONS = {
    "2024": {
        "index_path": r"C:\~\HARAMP2024_fixed_site_str_photos.csv",
        "root_path": r"Z:\OCC_Map_Maker\HARAMP2024_FIXED_photos",
        "routes": {
            "Site Photos": "/haramp2024_site_photos",
            "STR Photos": "/haramp2024_str_photos",
        },
    },
    "2025": {
        "index_path": r"C:\~\CNMI.RAMP2025_fixed_site_str_photos.csv",
        "root_path": r"Z:\OCC_Map_Maker\CNMI_RAMP_2025_FIXED_photos",
        "routes": {
            "Site Photos": "/cnmi2025_site_photos",
            "STR Photos": "/cnmi2025_str_photos",
        },
    },
    "2026": {
        "index_path": r"C:\~\PRIA.ASRAMP2026_fixed_site_str_photos.csv",
        "root_path": r"Z:\OCC_Map_Maker\PRIA_ASRAMP2026_FIXED_photos",
        "routes": {
            "Site Photos": "/pria2026_site_photos",
            "STR Photos": "/pria2026_str_photos",
        },
    },
}

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS & DATA LOADING
# -----------------------------------------------------------------------------
def load_data():
    dataframes = []
    for csv_path, fiscal_year, skiprows in DATASETS:
        df = pd.read_csv(csv_path, skiprows=skiprows)
        if "LATITUDE" not in df.columns:
            df = df.rename(columns={"SITELAT": "LATITUDE", "SITELON": "LONGITUDE"})
        df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).copy()
        df["YEAR"] = fiscal_year
        df["OCC_SITEID"] = df["OCC_SITEID"].astype(str).str.strip()
        dataframes.append(df)
    combined_df = pd.concat(dataframes, ignore_index=True)
    location_codes = combined_df["LOCATIONCODE"].fillna("").astype(str).str.strip()
    combined_df["REGION_FILTER"] = location_codes.map(REGION_BY_LOCATION_CODE)
    return combined_df


def load_photo_indexes():
    photo_indexes = {}
    for year, collection in PHOTO_COLLECTIONS.items():
        photo_index = pd.read_csv(
            collection["index_path"],
            usecols=["site_id", "category", "photo_name"],
        )
        photo_index = photo_index.dropna(subset=["site_id", "category", "photo_name"])
        photo_index["site_id"] = photo_index["site_id"].astype(str).str.strip()
        photo_indexes[year] = photo_index
    return photo_indexes


def get_photos(category, site_id, year):
    photos = []
    collection = PHOTO_COLLECTIONS[year]
    matching_photos = photo_indexes[year]
    matching_photos = matching_photos[
        (matching_photos["site_id"] == site_id)
        & (matching_photos["category"] == category)
    ]
    route = collection["routes"][category]
    for filename in matching_photos["photo_name"]:
        photos.append({"name": filename, "url": f"{route}/{site_id}/{filename}"})
    return photos


def wrap_longitudes(longitudes):
    normalized = [float(longitude) % 360 for longitude in longitudes]
    sorted_longitudes = sorted(normalized)
    gaps = [
        (sorted_longitudes[(index + 1) % len(sorted_longitudes)] - longitude) % 360
        for index, longitude in enumerate(sorted_longitudes)
    ]
    largest_gap_index = max(range(len(gaps)), key=gaps.__getitem__)
    west = sorted_longitudes[(largest_gap_index + 1) % len(sorted_longitudes)]
    wrapped = [longitude if longitude >= west else longitude + 360 for longitude in normalized]
    return wrapped


df = load_data()
photo_indexes = load_photo_indexes()
unique_years = ["ALL"] + sorted(df['YEAR'].unique().tolist())
all_sites = ["-- Select Site ID --"] + sorted(df['OCC_SITEID'].unique().tolist())
region_choices = {"ALL": "All Regions"}
region_choices.update(
    {
        region: region
        for region in sorted(df["REGION_FILTER"].dropna().unique().tolist())
    }
)

# Mount static web routes in Shiny
app_assets = {
    route: os.path.join(collection["root_path"], PHOTO_CATEGORIES[category])
    for collection in PHOTO_COLLECTIONS.values()
    for category, route in collection["routes"].items()
}
app_assets["/assets"] = ASSETS_DIR

# -----------------------------------------------------------------------------
# 3. STYLING & LIGHTBOX SCRIPTS
# -----------------------------------------------------------------------------
custom_css = """
body, .page-sidebar-layout {
    background-color: #2C3E50 !important;
    color: #ECF0F1;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.navbar, header, .app-title, .bslib-page-title {
    background-color: #1A252F !important;
    color: #ECF0F1 !important;
    padding: 8px 20px !important;
    font-weight: 600;
    letter-spacing: 0.5px;
    width: 100%;
}

.sidebar, .bslib-sidebar-content {
    background-color: #34495E !important;
    color: #ECF0F1 !important;
    border-right: 1px solid #1A252F !important;
    padding-top: 15px !important;
}

.sidebar h4, .sidebar label {
    color: #ECF0F1 !important;
}

.sidebar select, .sidebar input {
    background-color: #2C3E50 !important;
    color: #ffffff !important;
    border: 1px solid #5D6D7E !important;
    border-radius: 4px;
}

.sidebar select:focus {
    border-color: #3498DB !important;
    outline: none;
}

.sidebar .shiny-input-radiogroup label {
    color: #ECF0F1 !important;
}

hr {
    border-top: 1px solid #5D6D7E !important;
}
"""

lightbox_html_js = """
<style>
.photo-modal-overlay {
    display: none;
    position: fixed;
    z-index: 99999;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.88);
    justify-content: center;
    align-items: center;
}

.photo-modal-content {
    position: relative;
    max-width: 85%;
    max-height: 85%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.photo-modal-content img {
    max-width: 100%;
    max-height: 75vh;
    border-radius: 6px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
}

.photo-modal-caption {
    color: #ffffff;
    margin-top: 10px;
    font-family: Arial, sans-serif;
    font-size: 14px;
}

.photo-modal-close {
    position: absolute;
    top: -35px;
    right: -10px;
    color: #ffffff;
    font-size: 32px;
    font-weight: bold;
    cursor: pointer;
}

.photo-modal-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: none;
    font-size: 28px;
    padding: 10px 16px;
    cursor: pointer;
    border-radius: 4px;
    user-select: none;
}

.photo-modal-btn:hover {
    background: rgba(255, 255, 255, 0.5);
}

.photo-modal-prev { left: -60px; }
.photo-modal-next { right: -60px; }
</style>

<div id="photoModal" class="photo-modal-overlay" onclick="closePhotoModal(event)">
    <div class="photo-modal-content" onclick="event.stopPropagation()">
        <span class="photo-modal-close" onclick="closePhotoModal(event)">&times;</span>
        <button class="photo-modal-btn photo-modal-prev" onclick="changeModalPhoto(-1)">&#10094;</button>
        <img id="modalImg" src="" alt="Site Photo">
        <div id="modalCaption" class="photo-modal-caption"></div>
        <button class="photo-modal-btn photo-modal-next" onclick="changeModalPhoto(1)">&#10095;</button>
    </div>
</div>

<script>
var currentPhotoList = [];
var currentPhotoIdx = 0;

function openPhotoGallery(photoUrlsJson, startIndex) {
    currentPhotoList = photoUrlsJson;
    currentPhotoIdx = startIndex;
    updateModalImage();
    document.getElementById('photoModal').style.display = 'flex';
}

function updateModalImage() {
    if (currentPhotoList.length === 0) return;
    var imgObj = currentPhotoList[currentPhotoIdx];
    document.getElementById('modalImg').src = imgObj.url;
    document.getElementById('modalCaption').innerText = imgObj.title + ' (' + (currentPhotoIdx + 1) + ' of ' + currentPhotoList.length + ')';
}

function changeModalPhoto(dir) {
    if (currentPhotoList.length === 0) return;
    currentPhotoIdx = (currentPhotoIdx + dir + currentPhotoList.length) % currentPhotoList.length;
    updateModalImage();
}

function closePhotoModal(e) {
    document.getElementById('photoModal').style.display = 'none';
}

document.addEventListener('keydown', function(e) {
    var modal = document.getElementById('photoModal');
    if (modal && modal.style.display === 'flex') {
        if (e.key === 'ArrowLeft') changeModalPhoto(-1);
        if (e.key === 'ArrowRight') changeModalPhoto(1);
        if (e.key === 'Escape') closePhotoModal();
    }
});
</script>
"""

# Header Banner Layout (Title on left, Logos on far right)
header_title_layout = ui.div(
    ui.span("National Coral Reef Monitoring Program (NCRMP)", style="font-size: 28px; font-weight: 600;"),
    ui.div(
        ui.img(src="/assets/noaa_logo.png", height="42px", style="margin-right: 12px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));"),
        ui.img(src="/assets/cimar_logo.jpg", height="42px", style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));"),
        style="display: flex; align-items: center;"
    ),
    style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
)

# -----------------------------------------------------------------------------
# 4. SHINY USER INTERFACE (UI)
# -----------------------------------------------------------------------------
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(
            id="region_filter",
            label="Region:",
            choices=region_choices,
            selected="ALL"
        ),
        ui.input_select(
            id="year_filter",
            label="Year:",
            choices=unique_years,
            selected="ALL"
        ),
        ui.input_select(
            id="site_select",
            label="Zoom to Site ID:",
            choices=all_sites,
            selected="-- Select Site ID --"
        ),
        ui.input_radio_buttons(
            id="category_filter",
            label="Photo Category:",
            choices={
                "BOTH": "All Photos (Site & STR)",
                "SITE": "Site Photos Only",
                "STR": "STR Photos Only"
            },
            selected="BOTH"
        ),
        width=320
    ),
    ui.tags.head(ui.tags.style(custom_css)),
    ui.output_ui("map_out"),
    title=header_title_layout
)

# -----------------------------------------------------------------------------
# 5. SHINY SERVER LOGIC
# -----------------------------------------------------------------------------
def server(input, output, session):

    @reactive.effect
    def update_site_choices():
        selected_year = input.year_filter()
        selected_region = input.region_filter()

        available_sites = df.copy()
        if selected_year != "ALL":
            available_sites = available_sites[available_sites["YEAR"] == selected_year]
        if selected_region != "ALL":
            available_sites = available_sites[
                available_sites["REGION_FILTER"] == selected_region
            ]

        site_choices = ["-- Select Site ID --"] + sorted(
            available_sites["OCC_SITEID"].unique().tolist()
        )
        selected_site = input.site_select()
        if selected_site not in site_choices:
            selected_site = "-- Select Site ID --"

        ui.update_select(
            "site_select",
            choices=site_choices,
            selected=selected_site,
            session=session,
        )

    @render.ui
    def map_out():
        selected_site = input.site_select()
        selected_year = input.year_filter()
        selected_region = input.region_filter()
        selected_cat = input.category_filter()

        filtered_df = df.copy()
        if selected_year != "ALL":
            filtered_df = filtered_df[filtered_df['YEAR'] == selected_year]
        if selected_region != "ALL":
            filtered_df = filtered_df[filtered_df['REGION_FILTER'] == selected_region]

        map_df = filtered_df.copy()
        if not map_df.empty:
            map_df["MAP_LONGITUDE"] = wrap_longitudes(map_df["LONGITUDE"])

        initial_location = [20.7, -157.5]
        initial_zoom = 7

        if selected_site != "-- Select Site ID --":
            site_row = map_df[map_df['OCC_SITEID'] == selected_site]
            if site_row.empty:
                site_row = df[df['OCC_SITEID'] == selected_site]
            if not site_row.empty:
                site_longitude = float(site_row['LONGITUDE'].values[0])
                if not map_df.empty:
                    reference_longitude = map_df["MAP_LONGITUDE"].mean()
                    site_longitude += 360 * round(
                        (reference_longitude - site_longitude) / 360
                    )
                initial_location = [
                    float(site_row['LATITUDE'].values[0]),
                    site_longitude,
                ]
                initial_zoom = 16

        m = folium.Map(
            location=initial_location,
            zoom_start=initial_zoom,
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Imagery'
        )
        if (
            selected_site == "-- Select Site ID --"
            and not map_df.empty
        ):
            m.fit_bounds(
                [
                    [map_df["LATITUDE"].min(), map_df["MAP_LONGITUDE"].min()],
                    [map_df["LATITUDE"].max(), map_df["MAP_LONGITUDE"].max()],
                ],
                padding=(30, 30),
            )

        dive_flag_svg = """
        <svg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 32 32'>
          <rect x='2' y='4' width='28' height='20' fill='#d9534f' rx='2' stroke='#ffffff' stroke-width='1.5'/>
          <polygon points='2,4 6,4 30,22 30,24 26,24 2,6' fill='#ffffff'/>
          <rect x='2' y='4' width='3' height='26' fill='#333333'/>
        </svg>
        """

        for _, row in map_df.iterrows():
            site_id = str(row['OCC_SITEID']).strip()
            location = str(row['LOCATION'])
            depth = str(row['DEPTH_M'])
            site_year = str(row['YEAR'])
            lat = float(row['LATITUDE'])
            lon = float(row['MAP_LONGITUDE'])

            site_photos = (
                get_photos("Site Photos", site_id, site_year)
                if selected_cat in ['BOTH', 'SITE']
                else []
            )
            str_photos = (
                get_photos("STR Photos", site_id, site_year)
                if selected_cat in ['BOTH', 'STR']
                else []
            )

            gallery_items = []
            for img in site_photos:
                gallery_items.append({"url": img["url"], "title": f"{site_id} - Site Photo: {img['name']}"})
            for img in str_photos:
                gallery_items.append({"url": img["url"], "title": f"{site_id} - STR Photo: {img['name']}"})

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 13px; width: 320px; color: #333333;">
                <b>Site ID:</b> {site_id}<br>
                <b>Location:</b> {location}<br>
                <b>Depth:</b> {depth} m | <b>Year:</b> {site_year}<br>
                <hr style="margin: 6px 0; border: 0; border-top: 1px solid #ccc;">
            """

            photo_counter = 0

            # Site Photos Section
            if selected_cat in ['BOTH', 'SITE']:
                popup_html += f"<b>Site Photos ({len(site_photos)}):</b><br>"
                if site_photos:
                    popup_html += "<div style='display: flex; flex-wrap: wrap; max-height: 120px; overflow-y: auto; margin-bottom: 8px;'>"
                    for img in site_photos:
                        img_url = img["url"]
                        gallery_json = json.dumps(gallery_items).replace('"', '&quot;')
                        popup_html += f'<img src="{img_url}" onclick="openPhotoGallery({gallery_json}, {photo_counter})" style="width:75px; height:55px; object-fit:cover; margin:2px; border-radius:3px; cursor:pointer;" title="Click to view full screen">'
                        photo_counter += 1
                    popup_html += "</div>"
                else:
                    popup_html += "<i style='color: #777;'>No site photos available.</i><br><br>"

            # STR Photos Section
            if selected_cat in ['BOTH', 'STR']:
                popup_html += f"<b>STR Photos ({len(str_photos)}):</b><br>"
                if str_photos:
                    popup_html += "<div style='display: flex; flex-wrap: wrap; max-height: 120px; overflow-y: auto;'>"
                    for img in str_photos:
                        img_url = img["url"]
                        gallery_json = json.dumps(gallery_items).replace('"', '&quot;')
                        popup_html += f'<img src="{img_url}" onclick="openPhotoGallery({gallery_json}, {photo_counter})" style="width:75px; height:55px; object-fit:cover; margin:2px; border-radius:3px; cursor:pointer;" title="Click to view full screen">'
                        photo_counter += 1
                    popup_html += "</div>"
                else:
                    popup_html += "<i style='color: #777;'>No STR photos available.</i>"

            popup_html += "</div>"

            icon = folium.DivIcon(
                html=dive_flag_svg,
                icon_size=(28, 28),
                icon_anchor=(14, 14)
            )

            should_open = (site_id == selected_site)

            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=350, show=should_open),
                tooltip=f"{site_id} ({site_year})",
                icon=icon
            )
            marker.add_to(m)

        m.get_root().html.add_child(folium.Element(lightbox_html_js))

        return ui.HTML(m._repr_html_())

app = App(app_ui, server, static_assets=app_assets)
