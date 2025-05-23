import requests

def getVersions(manifest):
    return {v["id"]: v["url"] for v in manifest["versions"]}

def getServerURL(versions, version):
    version_data = requests.get(versions[version]).json()
    server_url = version_data["downloads"]["server"]["url"]
    return server_url