def getVersions(manifest):
    return manifest["versions"]

def getServerURL(versions, version):
    return versions[version]