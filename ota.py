import os
import sys
import json
import urllib.request
import subprocess
import time
from i18n import t

# OTA Configuration
GITHUB_USER = "louis70109"
GITHUB_REPO = "farm-check"
VERSION_FILE = "version.json"
CURRENT_VERSION = "1.1.0"  # Current local version

def check_for_updates():
    """Checks GitHub for a newer version of the scripts."""
    print(f"\n[OTA] {t('checking_updates', CURRENT_VERSION)}")
    
    try:
        # 1. Fetch latest version info from GitHub (raw content)
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{VERSION_FILE}"
        with urllib.request.urlopen(url, timeout=5) as response:
            remote_data = json.loads(response.read().decode())
            remote_version = remote_data.get("version")
            
        if remote_version and remote_version > CURRENT_VERSION:
            print(f"[OTA] {t('new_version_found', remote_version)}")
            return remote_data
        else:
            print(f"[OTA] {t('already_latest')}")
            return None
            
    except Exception as e:
        print(f"[OTA] {t('update_check_failed', e)}")
        return None

def apply_patch(update_info):
    """Downloads updated files and replaces local ones."""
    print(f"\n[OTA] {t('starting_patch')}")
    
    files_to_update = update_info.get("files", ["timer.py", "i18n.py", "window_utils.py"])
    
    try:
        for filename in files_to_update:
            url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{filename}"
            print(f"  -> Downloading {filename}...")
            
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read()
                
            # Direct overwrite (Patch)
            with open(filename, 'wb') as f:
                f.write(content)
                
        print(f"\n[OTA] {t('patch_applied_success')}")
        return True
    except Exception as e:
        print(f"\n[OTA] {t('patch_failed', e)}")
        return False

def run_ota_flow():
    """Main OTA flow to be called at startup."""
    update_info = check_for_updates()
    if update_info:
        # Prompt user to update
        print(f"\n{t('update_prompt')}")
        choice = input(t('update_choice_prompt')).strip().lower()
        
        if choice == 'y' or choice == '':
            if apply_patch(update_info):
                print(f"\n{t('restarting_program')}")
                # Restart the current script
                os.execv(sys.executable, ['python'] + sys.argv)
    
if __name__ == "__main__":
    # Test block
    print("Testing OTA module...")
