# PIFSC ESD ARP OCC Sitemap
- Developed as a resource to view OCC sites quickly for planning purposes and make use of existing site photo data.

## Overview
- **Input:**
  - **Site Metadata CSVs:** `FY25 CNMI Fixed Sites.csv`, `FY26 AS PRIA Fixed Sites.csv`, `FY27 NCRMP HA Fixed Sites.csv` containing coordinates (`LATITUDE`/`LONGITUDE`), site IDs (`OCC_SITEID`), locations, and depth (`DEPTH_M`).
  - **Photo Index CSVs:** `HARAMP2024_fixed_site_str_photos.csv`, `CNMI.RAMP2025_fixed_site_str_photos.csv`, `PRIA.ASRAMP2026_fixed_site_str_photos.csv` linking site IDs to photo filenames and categories (`Site Photos`, `STR Photos`).
  - **Photo Image Assets:** Local network directories housing actual site and STR image files (`Z:\OCC_Map_Maker\...`) and UI logos (`noaa_logo.png`, `cimar_logo.jpg`).
  - **UI Controls:** Interactive web selections for Region (`region_filter`), Fiscal Year (`year_filter`), Zoom to Site ID (`site_select`), and Photo Category (`category_filter`).

- **Output:**
  - **Interactive Map (`map_out`):** A Folium/Esri World Imagery satellite map rendered in Shiny for Python featuring custom dive flag markers with wrapped longitude coordinates across the International Date Line.
  - **Site Detail Popups:** Interactive map popups presenting site metadata (`Site ID`, `Location`, `Depth`, `Year`) alongside thumbnail galleries.
  - **Full-Screen Lightbox Gallery:** An embedded JavaScript/CSS overlay modal allowing high-resolution photo viewing, image counter titles, modal controls, and keyboard navigation (`ArrowLeft`, `ArrowRight`, `Escape`).

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

2. Install required dependencies:
   ```bash
   pip install shiny pandas folium
   ```

3. Run the Shiny app:
   ```bash
   shiny run app.py
   ```

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
