import re
import subprocess
from pathlib import Path

INIT_FILE = Path("app/__init__.py")

def get_current_version():
    for line in INIT_FILE.read_text().splitlines():
        match = re.match(r'^__version__ = [\'"]([^\'"]+)[\'"]', line)
        if match:
            return match.group(1)
    raise RuntimeError("Couldn't find __version__ in app/__init__.py")

def get_latest_tag():
    try:
        # e.g., returns 'v0.4.8' or '0.4.8'
        tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip()
        return tag
    except subprocess.CalledProcessError:
        # If no tags exist yet
        return None

def main():
    current_version = get_current_version()
    latest_tag = get_latest_tag()

    if not latest_tag:
        print("No existing tag found. Skipping version comparison.")
        return

    # If your tags have a "v" prefix like v0.4.8, remove the "v"
    latest_tag_stripped = latest_tag.lstrip("v")

    if current_version == latest_tag_stripped:
        raise SystemExit(
            f"❌ Version has NOT been bumped. Current version {current_version} "
            f"matches latest tag {latest_tag}. Please bump before merging."
        )
    else:
        print(f"✅ Version check passed. Current version {current_version}, latest tag {latest_tag}")

if __name__ == "__main__":
    main()
