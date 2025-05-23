import os
import requests
import json
import subprocess
from pathlib import Path
from packaging import version

def javaJDKUpdateAvailable():
    try:
        users_version = subprocess.run(['java', '--version'], capture_output=True, text=True).stdout.strip().split('\n')[0].split(' ')[1]
    except Exception as e:
        return True
    latest_version = getLatestJDKVersion()

    return version.parse(latest_version) > version.parse(users_version)

def getLatestJDKVersion():
    version_url = "https://api.adoptium.net/v3/info/available_releases"
    response = requests.get(version_url).json()
    
    latest_lts = response["most_recent_lts"]
    
    return str(latest_lts)

def getDownloadLink():
    latest_jdk_version = getLatestJDKVersion()
    manifest = f"https://api.adoptium.net/v3/assets/latest/{latest_jdk_version}/hotspot"

    response = requests.get(manifest).json()

    for asset in response:
        if asset["binary"]["os"] == "windows" and asset["binary"]["architecture"] == "x64" and asset["binary"]["image_type"] == "jdk":
            return asset["binary"]["installer"]["link"]

    return None

def downloadAndRunJavaJDK(download_path):
    download_link = getDownloadLink()

    filename = download_link.split("/")[-1]
    filepath = f"{download_path}\\{filename}"

    if download_link is None:
        return False
    
    response = requests.get(download_link)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        return False

    os.startfile(filepath)
    return True