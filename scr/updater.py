import os
import shutil
import json
import requests
import zipfile
import io
from scr.settings import *
from scr.app_data import AppData

class UPDATER:
    def __init__(self):
        self.latest_version = self.getLatestVersion()
        self.blacklisted = AppData.getAppData("update_blacklist")

    def getLatestVersion(self):
        latest_path = f'{GITHUB_REPO}/latest.json'
        r = requests.get(latest_path)

        if r.status_code == 200:
            return json.loads(r.text)["version"]

        return None
    
    def update(self):
        if self.latest_version is None:
            return False
        
        latest_build = f'{GITHUB_REPO}/builds/{self.latest_version}.zip'
        r = requests.get(latest_build)

        local = os.getcwd()

        if r.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(r.content)) as zip:
                if "update.json" in zip.namelist():
                    with zip.open("update.json") as f:
                        update_data = json.load(f)

                    for modified in update_data["modified"]:
                        if modified in self.blacklisted:
                            continue

                        new_data = zip.read(modified).decode("utf-8")
                        with open(modified, "w") as f:
                            f.write(new_data)

                for file in zip.namelist():
                    is_dir = file[-1] == "/"
                    if file in self.blacklisted:
                        continue
                    
                    if not os.path.exists(file):
                        if not is_dir:
                            with open(file, "wb") as f:
                                f.write(zip.read(file))
                        else:
                            if is_dir:
                                os.makedirs(file, exist_ok=True)
                
                for file in os.listdir(local):
                    if file in self.blacklisted:
                        continue

                    is_dir = not file.__contains__(".")
                    file = f"{file}/" if is_dir else file
                    if file not in zip.namelist():
                        if is_dir:
                            shutil.rmtree(f'{local}/{file}')
                        else:
                            os.remove(f'{local}/{file}')
        
            AppData.setAppData("version", self.latest_version)
Updater = UPDATER()