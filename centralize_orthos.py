import os
import re
import shutil
import pandas as pd

SOURCE_ROOT = r"N:\Fixed_Sites"
TARGET_REGIONS = ["MHI", "NWHI"]
TARGET_YEAR = "2024"

DEST_DIR = r"Z:\OCC_Map_Maker\HARAMP2024_orthomosaics"
INDEX_CSV = r"Z:\OCC_Map_Maker\site_orthomosaic_index.csv"

# Matches OCC site ID (e.g., OCC-HAW-002, OCC-FFS-002)
SITE_ID_PATTERN = re.compile(r"OCC-[A-Z]{3}-\d{3}", re.IGNORECASE)

os.makedirs(DEST_DIR, exist_ok=True)
records = []

print(f"Targeting regions: {TARGET_REGIONS} for year: {TARGET_YEAR}")

for region in TARGET_REGIONS:
    region_path = os.path.join(SOURCE_ROOT, region)
    
    if not os.path.exists(region_path):
        print(f"Warning: Region path not found: {region_path}")
        continue
        
    print(f"\n--- Scanning {region} ({region_path}) ---")
    
    for root, dirs, files in os.walk(region_path):
        # Prevent diving into older years (e.g., 2019, 2022, 2023)
        # Modifying dirs in-place tells os.walk to completely ignore non-matching year folders
        dirs[:] = [d for d in dirs if not (d.isdigit() and len(d) == 4 and d != TARGET_YEAR)]
        
        # Verify the current directory path contains \2024\
        path_parts = os.path.normpath(root).split(os.sep)
        if TARGET_YEAR not in path_parts:
            continue

        for file in files:
            if file.lower().endswith(("_mos.tif", "orthomosaic.tif", "_mos.pdf")):
                src_path = os.path.join(root, file)
                
                match = SITE_ID_PATTERN.search(src_path)
                if not match:
                    continue
                    
                site_id = match.group(0).upper()
                ext = os.path.splitext(file)[1].lower()
                dest_filename = f"{site_id}_mos{ext}"
                dest_path = os.path.join(DEST_DIR, dest_filename)

                # Skip identical files (prevents unnecessary re-copies and avoids locks)
                if not os.path.exists(dest_path) or os.path.getsize(src_path) != os.path.getsize(dest_path):
                    print(f"Copying: {site_id} ({TARGET_YEAR}) -> {dest_filename}")
                    try:
                        shutil.copy2(src_path, dest_path)
                    except Exception as e:
                        print(f"Error copying {src_path}: {e}")
                        continue
                else:
                    print(f"Skipping already copied: {dest_filename}")

                records.append({
                    "REGION": region,
                    "OCC_SITEID": site_id,
                    "YEAR": TARGET_YEAR,
                    "ORTHO_FILENAME": dest_filename,
                    "ORTHO_LOCAL_PATH": dest_path,
                    "ORIGINAL_SOURCE_PATH": src_path
                })

df = pd.DataFrame(records)
if not df.empty:
    df = df.drop_duplicates(subset=["OCC_SITEID"], keep="last")
    df.to_csv(INDEX_CSV, index=False)
    df.to_csv("site_orthomosaic_index.csv", index=False)
    print(f"\nCompleted! {len(df)} orthomosaics centralized and index saved to:")
    print(f" - {INDEX_CSV}")
    print(f" - site_orthomosaic_index.csv (local repo)")
else:
    print(f"\nNo orthomosaic files found matching {TARGET_YEAR} criteria in MHI or NWHI.")