import requests

def getVersions(manifest):
    versions = {}
    loader_version = None
    installer_version = None
    for v in manifest["game"]:
        ver = v["version"]
        if loader_version is None:
            loader_path = f'https://meta.fabricmc.net/v2/versions/loader/{ver}/'
            loader_version = requests.get(loader_path).json()[0]["loader"]["version"]
        if installer_version is None:
            installer_path = 'https://meta.fabricmc.net/v2/versions/installer'
            installer_version = requests.get(installer_path).json()[0]["version"]
        versions[ver] = f'https://meta.fabricmc.net/v2/versions/loader/{ver}/{loader_version}/{installer_version}/server/jar'
    return versions

def getServerURL(versions, version):
    return versions[version]