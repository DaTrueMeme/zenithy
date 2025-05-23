import shutil
from scr.app_data import AppData
from scr.server_manager import ServerManager
from scr.app import app

if ServerManager.running_servers != {} and not AppData.getAppData("keep_servers_online"):
    servers = ServerManager.running_servers
    for server in servers:
        ServerManager.stopServer(server)
    ServerManager.closeAllPorts()
shutil.rmtree("temp/versions")

# from scr.server_manager import retriveMSJ
# print(retriveMSJ("fabric", "1.21", True))