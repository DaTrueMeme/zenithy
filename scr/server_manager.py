import importlib.util
import time
import os
import shutil
import json
import requests
import subprocess
import psutil
import time
import importlib
from PIL import Image
from scr.settings import INSTALL_PATH
from scr.file_upload import uploadFile
from scr.upnp import openPort, closePort

def retriveMSJ(server_type, version, just_version_list=False):
    if just_version_list:
        if os.path.exists(f'temp/versions/{server_type}.json'):
            with open(f'temp/versions/{server_type}.json', 'r') as f:
                versions = json.load(f)
            return versions

    data_path = f'data/server_types/{server_type}'
    with open(f'{data_path}/data.json', 'r') as f:
        data = json.load(f)

    manifest_url = data["manifest_url"]
    manifest = requests.get(manifest_url).json()

    def loadHandler(handler_path):
        spec = importlib.util.spec_from_file_location("handler", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    handler = loadHandler(f'{data_path}/{data["handler"]}')
    versions = handler.getVersions(manifest)

    if just_version_list:
        blacklist = ["pre", "rc", "rd", "w", "snapshot", "combat"]
        v = []
        for i in versions:
            valid = True
            for b in blacklist:
                if b in i.lower():
                    valid = False
                    break
            if valid:
                v.append(i)
    
        temp_path = f'temp/versions/{server_type}.json'
        os.makedirs("temp/versions", exist_ok=True)
        with open(temp_path, "w") as f:
            json.dump(v, f)

        return v

    if version not in versions:
        print("Version not found!")
        return

    server_url = handler.getServerURL(versions, version)

    return server_url

class SERVERMANAGER:
    def __init__(self):
        self.install_path = f'{INSTALL_PATH}\\servers'
        
        self.servers = self.retriveServers()
        self.running_servers = {}

        self.opened_ports = {}

        self.processes = {}

        self.memory_check_interval = 1
        self.last_check_time = 0
        self.last_usage = 0

    def retriveServers(self):
        servers = {}
        if os.path.exists(self.install_path):
            for folder in os.listdir(self.install_path):
                if folder[0:2] == "__": continue

                path = f'{self.install_path}\\{folder}'
                try:
                    with open(os.path.join(path, "data.json"), "r") as f:
                        data = json.load(f)
                except:
                    data = {}

                if os.path.isdir(os.path.join(self.install_path, folder)):
                    servers[folder] = {
                        "path": path,
                        "data": data
                    }

        return servers
    
    def newServer(self, name, port, server_type, version="1.21.4", max_memory=1024, min_memory=1024, use_upnp=False, custom_data={}):
        self.servers = self.retriveServers()
        if name in self.servers:
            print("Server with that name already exists!")
            return

        self.processes["server_creation"] = 0
        levels = 5

        server_path = f"{self.install_path}\\{name}"
        try:
            os.makedirs(server_path, exist_ok=True)
        except Exception as e:
            self.deleteServer(name)
            return False
        self.processes["server_creation"] += 1 / levels

        version_url = retriveMSJ(server_type, version)
        self.processes["server_creation"] += 1 / levels
        
        r = requests.get(version_url)
        file_path = f"{server_path}\\server.jar"

        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)
        else:
            self.deleteServer(name)
            return False
        self.processes["server_creation"] += 1 / levels

        with open(f"{server_path}\\start.bat", "w") as f:
            f.write(f"java -Xmx{max_memory}M -Xms{min_memory}M -jar server.jar nogui")
        self.processes["server_creation"] += 1 / levels

        with open(f"{server_path}\\data.json", "w") as f:
            data = {
                "version": version,
                "port": port,
                "max_memory": max_memory,
                "min_memory": min_memory,
                "use_upnp": use_upnp,
                "custom_ports": []
            }
            data.update(custom_data)
            json.dump(data, f)
        self.processes["server_creation"] += 1 / levels
        return True

    def deleteServer(self, name, force=False):
        if name not in self.servers and not force:
            return False

        server_path = self.servers[name]["path"]

        try:
            shutil.rmtree(server_path)
        except Exception as e:
            print(f"Error deleting directory: {e}")

    def getServerData(self, name):
        if name not in self.servers:
            print("Server not found!")
            return False

        try:
            data = self.servers[name]["data"]
        except:
            data = {}

        return data

    def setServerData(self, name, key, value):
        if name not in self.servers:
            print("Server not found!")
            return False
        
        server_path = self.servers[name]["path"]
        data = self.getServerData(name)
        data[key] = value

        with open(f"{server_path}\\data.json", "w") as f:
            json.dump(data, f)
        return True

    def returnServerFile(self, name, file):
        if name not in self.servers:
            print("Server not found!")
            return False

        server_path = self.servers[name]["path"]
        file_path = f'{server_path}\\{file}'
        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r") as f:
            file_type = file.split(".")[1]
            if file_type == "json":
                return json.load(f)
            return f.read()

    def getServerProperty(self, name, key):
        if name not in self.servers:
            print("Server not found!")
            return False

        path = self.servers[name]["path"]

        try:
            with open(f'{path}\\server.properties', 'r') as f:
                lines = f.readlines()
        except:
            return ""

        for line in lines:
            if line.startswith(f'{key}='):
                return line.split('=')[1].strip()
        return ""

    def updateServerProperties(self, name, data):
        if name not in self.servers:
            print("Server not found!")
            return False

        path = self.servers[name]["path"]

        with open(f'{path}\\server.properties', 'r') as f:
            lines = f.readlines()

        with open(f'{path}\\server.properties', 'w') as f:
            for line in lines:
                replaced = False
                for item in data:
                    if line.startswith(f'{item["key"]}='):
                        f.write(f'{item["key"]}={item["value"]}\n')
                        replaced = True
                        break
                if not replaced:
                    f.write(line)
        return True

    def acceptEula(self, name):
        if name not in self.servers:
            print("Server not found!")
            return False

        server_path = self.servers[name]["path"]
        eula_path = os.path.join(server_path, "eula.txt")

        try:
            with open(eula_path, "w") as f:
                f.write("eula=true")
        except Exception as e:
            print(e)
        return True

    def importIcon(self, name):
        if name not in self.servers:
            print("Server not found!")
            return False

        server_path = self.servers[name]["path"]
        icon_path = uploadFile()

        if icon_path is not None:
            img = Image.open(icon_path)
            img = img.resize((64, 64))
            img.save(f'{server_path}\\server-icon.png', 'PNG')
        return True

    def log(self, name, text):
        if name not in self.servers:
            print("Server not found!")
            return False

        server_path = self.servers[name]["path"]
        log_path = os.path.join(server_path, "output.txt")

        with open(log_path, "a") as f:
            f.write(f'{text}\n')
        return True

    def startServer(self, name):
        if name not in self.servers or name in self.running_servers:
            return False
        
        with open(f"{self.servers[name]['path']}\\output.txt", "w") as f:
            f.write("")

        server_path = self.servers[name]["path"]
        bat_file = os.path.join(server_path, "start.bat")

        with open(f"{server_path}\\output.txt", "a") as f:
            process = subprocess.Popen(
                bat_file,
                cwd=server_path,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=f,
                stderr=f,
                text=True
            )

        if self.getServerData(name)["use_upnp"]:
            custom_ports = self.getServerData(name)["custom_ports"]
            if len(custom_ports) > 0:
                for port in custom_ports:
                    protocol = port["protocol"]
                    if port["port"] not in self.opened_ports:
                        openPort(int(port["port"]), protocol=protocol, server_manager=self, server=name)
                        self.opened_ports[port["port"]] = protocol
                        time.sleep(1)

            port = self.getServerData(name)["port"]
            if port not in self.opened_ports:
                openPort(int(port), server_manager=self, server=name)
                self.opened_ports[port] = "TCP"
        self.running_servers[name] = process
        return process

    def stopServer(self, name):
        if name not in self.running_servers:
            return False

        self.sendCommand(name, "stop")
        self.running_servers.pop(name)
        return True

    def closeAllPorts(self):
        for port in self.opened_ports:
            protocol = self.opened_ports[port]
            closePort(int(port), protocol, server_manager=self)
        self.opened_ports = {}

    def getMemoryUsage(self, name):
        if name not in self.running_servers:
            return 0
        
        current_time = time.time()

        if current_time - self.last_check_time < self.memory_check_interval:
            return self.last_usage
        
        self.last_check_time = current_time

        process = self.running_servers[name]

        try:
            pid = process.pid
            proc = psutil.Process(pid)

            total_memory = proc.memory_info().rss

            for child in proc.children(recursive=True):
                total_memory += child.memory_info().rss

            memory_usage_gb = total_memory / (1024 ** 3)
            
            self.last_usage = round(memory_usage_gb, 3)
            return self.last_usage
        
        except Exception as e:
            print(f"Error getting memory usage: {e}")
            return self.last_usage

    def getCPUUsage(self, name):
        if name not in self.running_servers:
            return -1

        process = self.running_servers[name]

        try:
            pid = process.pid
            proc = psutil.Process(pid)

            cpu_usage = proc.cpu_percent(interval=0.1)
            return cpu_usage

        except Exception as e:
            print(e)
            return -1

    def getUsedStorage(self, name):
        if name not in self.servers:
            return 0

        server_path = self.servers[name]["path"]
        total_size = 0

        for dirpath, dirnames, filenames in os.walk(server_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if not os.path.islink(filepath):
                    total_size += os.path.getsize(filepath)
        
        return round(total_size / (1024 * 1024))

    def sendCommand(self, name, command):
        if command == "": return

        if name not in self.running_servers:
            print("Server not running!")
            return False

        process = self.running_servers[name]

        try:
            process.stdin.write(command + "\n")
            process.stdin.flush()
        except Exception as e:
            print(e)
            return False
        return True
    
    def renameServer(self, name, new_name):
        if name not in self.servers:
            print("Server not found!")
            return False

        server_path = self.servers[name]["path"]
        self.servers[new_name] = self.servers.pop(name)
        new_server_path = os.path.join(self.install_path, new_name)

        try:
            os.rename(server_path, new_server_path)
            self.servers[new_name]["path"] = new_server_path
        except Exception as e:
            print(f"Error renaming server folder: {e}")
            return False
        return True

        
ServerManager = SERVERMANAGER()
