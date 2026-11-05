import shutil
import subprocess
import sys


GCLOUD = shutil.which("gcloud.cmd") or shutil.which("gcloud")
SOURCE_ROOT = (
    "gs://nmfs-dev-uc1-pifsc/Optical/Cruise/CruiseData/MP2404_MHI/"
    "Optical/OAH/REA/CLIMATE"
)
DESTINATION_ROOT = (
    "gs://nmfs_odp_pifsc/PIFSC/ESD/ARP/Fixed_Sites_Projects/"
    "occ_map_maker/HARAMP2024_FIXED_photos/Site_Photos"
)


def run_gcloud(
    *args: str, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    if not GCLOUD:
        raise RuntimeError(
            "Could not find gcloud. Make sure the Google Cloud SDK is installed "
            "and its bin folder is on PATH."
        )

    command = [GCLOUD, *args]
    if GCLOUD.lower().endswith((".cmd", ".bat")):
        command = [
            shutil.which("cmd.exe") or "cmd.exe",
            "/d",
            "/c",
            "call",
            *command,
        ]
    return subprocess.run(
        command,
        capture_output=capture_output,
        text=True,
        check=False,
    )


def gcloud_output(*args: str, allow_no_match: bool = False) -> list[str]:
    result = run_gcloud(*args, capture_output=True)
    if result.returncode:
        error = f"{result.stderr}\n{result.stdout}".lower()
        if allow_no_match and (
            "matched no objects" in error or "no urls matched" in error
        ):
            return []
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"gcloud {' '.join(args)} failed: {message}")
    return result.stdout.splitlines()


def main() -> int:
    try:
        site_folders = [
            folder.strip()
            for folder in gcloud_output("storage", "ls", f"{SOURCE_ROOT}/")
            if folder.strip().endswith("/")
        ]

        copy_plan = []
        for site_folder in site_folders:
            site_name = site_folder.rstrip("/").rsplit("/", 1)[-1]
            photo_folder = f"{site_folder}SITE_PHOTOS"
            photos = gcloud_output(
                "storage",
                "ls",
                "--recursive",
                f"{photo_folder}/",
                allow_no_match=True,
            )
            if photos:
                copy_plan.append((site_name, photo_folder))

        if not copy_plan:
            raise RuntimeError("No SITE_PHOTOS folders containing files were found.")

        print("These folders will be copied:")
        for site_name, photo_folder in copy_plan:
            print(
                f"  {site_name}: {photo_folder} -> "
                f"{DESTINATION_ROOT}/{site_name}/"
            )

        if input("Type Y to start copying: ").strip().upper() != "Y":
            print("Copy cancelled.")
            return 0

        for site_name, photo_folder in copy_plan:
            print(f"Copying {site_name}...")
            result = run_gcloud(
                "storage",
                "cp",
                "--recursive",
                "--no-clobber",
                photo_folder,
                f"{DESTINATION_ROOT}/{site_name}/",
            )
            if result.returncode:
                raise RuntimeError(f"Copy failed for site {site_name}.")

        print("Copy complete.")
        return 0
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
