# PIFSC ESD ARP OCC Sitemap
Developed by Zach Taylor as a planning resource to quickly view OCC sites and their associated photo data.  Co-developed by Lori Luers: sanitized, cleaned, updated worfklow to pull from Google Cloud Bucket, made reproducible, and published on NMFS Posit Connect.
<br>
Posit Connect Shiny App: https://connect.fisheries.noaa.gov/esd-occ-sitemap/ 

## Features

- Filter site markers by region, year, and photo category.
- Zoom to a selected site ID.
- View site metadata and associated Site Photos or STR Photos in map popups.
- Open photos in a full-screen lightbox; use the left and right arrow keys to navigate and Escape to close it.
- Handle longitudes across the International Date Line.

Popup photo previews use the original bucket images at a small display size and load lazily. They are not separately resized thumbnail files, so the first load of a preview may take time.

### Screenshots

Full map:

![Full map](screenshots/1.full_map.png)

Filter by region:

![Region filter](<screenshots/2. region_filter.png>)

Filter by year:

![Year filter](<screenshots/3. year_filter.png>)

Filter by site:

![Site filter](<screenshots/4. site_filter.png>)

Select a site:

![Site selection](<screenshots/5. site_selection.png>)

Site details and photo previews:

![Site data display](<screenshots/6. site_data_display.png>)

View a full-resolution photo:

![High-resolution image view](<screenshots/7. high_resolution_image_view.png>)

## Prerequisites
- Python 3.8+
- Python Packages:
  - `shiny`
  - `pandas`
  - `folium`

## Installing
1. Clone the repository:
   ```bash
   git clone https://github.com/LoriLuers-PIFSC/esd-occ-sitemap.git
   cd esd-occ-sitemap
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Generate the photo indexes from the public Google Cloud Storage bucket:
   ```bash
   python scripts/build_photo_indexes.py
   ```

   The script lists image objects under the 2024, 2025, and 2026 photo collections
   and writes `_data/bucket_photo_index_<year>.csv` files. Each manifest records
   the site ID, photo category, filename, and actual bucket folder. Folder suffixes
   such as `(Second time)` are retained for the image URL and removed when matching
   the folder to the map site ID. The generated manifests are required at app
   startup; run the script again when bucket contents change.

4. Run the Shiny app:
   ```bash
   shiny run app.py
   ```

## Deployment

When deploying, include `app.py`, `requirements.txt`, the site data CSVs in
`_data/`, all three generated `bucket_photo_index_<year>.csv` manifests, and the
logo file under `icons/`. The photo image files remain in Google Cloud Storage;
they are not downloaded into the deployment bundle.

## Resources
- Related metadata for this ESA project is described here: https://www.fisheries.noaa.gov/inport/item/76360

## Contact
- primary point of contact: Zach Taylor
- secondary contact: Lori Luers

## Version Control Platform
- Git

## License
See the [LICENSE.md](./LICENSE.md) for details

## Disclaimer
This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.
