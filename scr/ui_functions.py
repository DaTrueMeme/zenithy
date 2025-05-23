import os
import threading
import webbrowser
import json
import requests
from scr.settings import *
from scr.javaJDK_downloader import downloadAndRunJavaJDK
from scr.server_manager import ServerManager, retriveMSJ
from scr.updater import Updater

def newServer(element_manager):
    name = element_manager.elements["entry"]["server_name"].get()
    if name == "" or ServerManager.servers.__contains__(name):
        return
    port = element_manager.elements["entry"]["server_port"].get()
    server_type = element_manager.elements["segmentedbutton"]["type_selector"].get()
    version = element_manager.elements["optionmenu"]["version_selector"].get()

    max_memory = round(element_manager.elements["slider"]["memory_selector"]["obj"].get())
    max_memory = max_memory * 1024

    allow_transfers = element_manager.elements["switch"]["allow_transfers"]["obj"].get()
    use_upnp = element_manager.elements["switch"]["use_upnp"]["obj"].get()

    def create_server():
        ServerManager.newServer(name, port, server_type.lower(), version=version, max_memory=max_memory, use_upnp=use_upnp, custom_data={"allow-transfers": allow_transfers, "accepted-eula": False})

        element_manager.selectServer(name)
        element_manager.loadPage("server/server")

    thread = threading.Thread(target=create_server)
    thread.start()

    element_manager.elements["button"]["create_server"].configure(state="disabled")
    element_manager.loadPage("new_server/waiting/waiting")

def deleteServer(element_manager):
    name = element_manager.data["selected_server"]
    ServerManager.deleteServer(name)
    element_manager.loadPage("home/home")

def changeServerType(element_manager):
    server_type = element_manager.elements["segmentedbutton"]["type_selector"].get()
    element_manager.elements["optionmenu"]["version_selector"].configure(values=retriveMSJ(server_type.lower(), "", True))

def startServer(element_manager):
    ServerManager.servers = ServerManager.retriveServers()
    name = element_manager.data["selected_server"]
    server_path = ServerManager.servers[name]["path"]

    def run_server():
        process = ServerManager.startServer(name)
        process.wait()

        check_eula(element_manager, server_path)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    element_manager.elements["button"]["stop_server"].configure(state="normal")
    element_manager.elements["button"]["send_command_button"].configure(state="normal")
    element_manager.elements["button"]["start_server"].configure(state="disabled")

def stopServer(element_manager):
    name = element_manager.data["selected_server"]
    ServerManager.stopServer(name)

    element_manager.elements["button"]["start_server"].configure(state="normal")
    element_manager.elements["button"]["stop_server"].configure(state="disabled")
    element_manager.elements["button"]["send_command_button"].configure(state="disabled")

def sendCommand(element_manager):
    name = element_manager.data["selected_server"]
    command = element_manager.elements["entry"]["send_command"].get()
    ServerManager.sendCommand(name, command)

    element_manager.elements["entry"]["send_command"].delete(0, "end")

def stopAll(element_manager):
    servers = ServerManager.servers
    for server in servers:
        ServerManager.stopServer(server)
    
    element_manager.elements["button"]["stop_all_servers"].configure(state="disabled")

def uploadIcon(element_manager):
    name = element_manager.data["selected_server"]
    ServerManager.importIcon(name)

def check_eula(element_manager, server_path):
    eula_path = os.path.join(server_path, "eula.txt")
    
    if os.path.exists(eula_path):
        with open(eula_path, "r") as f:
            data = f.read()
        eula_accepted = "eula=true" in data

        if not eula_accepted:
            element_manager.elements["button"]["accept_eula"].configure(state="normal")
    else:
        element_manager.elements["button"]["accept_eula"].configure(state="disabled")

def acceptEula(element_manager):
    name = element_manager.data["selected_server"]
    port = ServerManager.getServerData(name)["port"]
    allow_transfers = ServerManager.getServerData(name)["allow-transfers"]
    allow_transfers = True if allow_transfers else False

    ServerManager.updateServerProperties(name, [{"key": "server-port", "value": port}, {"key": "query.port", "value": port}])
    ServerManager.updateServerProperties(name, [{"key": "accepts-transfers", "value": allow_transfers}])

    ServerManager.acceptEula(name)
    stopServer(element_manager)
    element_manager.elements["button"]["accept_eula"].configure(state="disabled")
    ServerManager.setServerData(name, "accepted-eula", True)

    element_manager.loadPage("server/server")

def retriveServerLog(element_manager):
    ServerManager.servers = ServerManager.retriveServers()
    name = element_manager.data["selected_server"]
    log_path = f'{ServerManager.servers[name]["path"]}\\output.txt'

    try:
        with open(log_path, "r") as f:
            log = f.read()
    except:
        log = "No log has been generted yet. Start the server to generate one."

    log += "\n"
    return log

def enableProp(element_manager, prop, value=True):
    name = element_manager.data["selected_server"]

    value = "true" if value else "false"

    ServerManager.updateServerProperties(name, [{"key": prop, "value": value}])

def saveMOTD(element_manager):
    name = element_manager.data["selected_server"]
    motd = element_manager.elements["entry"]["motd"].get()
    ServerManager.updateServerProperties(name, [{"key": "motd", "value": motd}])

def openServerDir(element_manager):
    name = element_manager.data["selected_server"]
    path = ServerManager.servers[name]["path"]
    os.startfile(path)

def downloadJDK(element_manager, method):
    element_manager.elements["button"]["download_jdk"].configure(state="disabled")
    element_manager.elements["button"]["download_jdk_manual"].configure(state="disabled")

    if method == "auto":
        install_path = f"{INSTALL_PATH}\\temp\\jdk"
        os.makedirs(install_path, exist_ok=True)

        thread = threading.Thread(target=downloadAndRunJavaJDK, args=(install_path,))
        thread.start()
    else:
        url = "https://www.oracle.com/java/technologies/downloads/"
        webbrowser.open(url)

def addToWhitelist(element_manager):
    username = element_manager.elements["entry"]["add_player"].get()
    if username == "":
        return
    name = element_manager.data["selected_server"]
    
    server_path = ServerManager.servers[name]["path"]
    whitelist_path = f'{server_path}\\whitelist.json'

    api_url = f'https://api.mojang.com/users/profiles/minecraft/{username}'
    response = requests.get(api_url)

    element_manager.elements["entry"]["add_player"].delete(0, "end")
    if response.status_code != 200:
        element_manager.elements["entry"]["add_player"].insert(0, "Invalid username")
        return
    uuid = response.json()["id"]

    with open(whitelist_path, "r") as f:
        data = json.load(f)

    addition = {
        "uuid": uuid,
        "name": username
    }
    data.append(addition)

    with open(whitelist_path, "w") as f:
        json.dump(data, f)

    element_manager.loadPage("server/configure_server/whitelist/whitelist")

def removeFromWhitelist(element_manager):
    player = element_manager.data["current_data"]
    name = element_manager.data["selected_server"]

    server_path = ServerManager.servers[name]["path"]
    whitelist_path = f'{server_path}\\whitelist.json'

    with open(whitelist_path, "r") as f:
        data = json.load(f)

    data.remove(player)

    with open(whitelist_path, "w") as f:
        json.dump(data, f)

    element_manager.loadPage("server/configure_server/whitelist/whitelist")

def downloadNewUpdate(element_manager):
    element_manager.elements["button"]["new_zenith_version"].configure(state="disabled")
    element_manager.elements["button"]["home_button"].configure(state="disabled")

    def download():
        Updater.update()
        element_manager.root.destroy()

    thread = threading.Thread(target=download)
    thread.start()

def closePorts(element_manager):
    ServerManager.closeAllPorts()
    element_manager.elements["button"]["close_all_ports"].configure(state="disabled")

def renameServer(element_manager):
    name = element_manager.elements["entry"]["rename_server"].get()
    if name == "":
        return
    
    ServerManager.renameServer(element_manager.data["selected_server"], name)
    element_manager.loadPage("home/home")

def editPlayerWhitelist(element_manager, player):
    element_manager.data["current_data"] = dict(player)
    element_manager.loadPage('server/configure_server/whitelist/edit_player/edit_player')

def savePort(element_manager):
    port_name = element_manager.elements["entry"]["port"].get()
    protocol = element_manager.elements["optionmenu"]["protocol"].get()

    if port_name == "" or protocol == "" or any(char.isalpha() for char in port_name):
        return

    server = element_manager.data["selected_server"]
    ports = ServerManager.getServerData(server)["custom_ports"]

    ports.append({"port": port_name, "protocol": protocol})
    ServerManager.setServerData(server, "custom_ports", ports)

    element_manager.loadPage("server/configure_server/custom_ports/custom_ports")

def removeCustomPort(element_manager):
    port = element_manager.data["current_data"]
    server = element_manager.data["selected_server"]
    ports = ServerManager.getServerData(server)["custom_ports"]

    ports.remove(port)
    ServerManager.setServerData(server, "custom_ports", ports)

    element_manager.loadPage("server/configure_server/custom_ports/custom_ports")

def editCustomPort(element_manager, port):
    element_manager.data["current_data"] = dict(port)
    element_manager.loadPage("server/configure_server/custom_ports/edit_port/edit_port")

def getMemory(element_manager):
    name = element_manager.data["selected_server"]
    return ServerManager.getMemoryUsage(name)

def getStorage(element_manager):
    name = element_manager.data["selected_server"]
    return ServerManager.getUsedStorage(name)