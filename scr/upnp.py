import miniupnpc

def openPort(port=25565, protocol='TCP', server_manager=None, server=None):
    upnp = miniupnpc.UPnP()
    upnp.discover()
    upnp.selectigd()
    upnp.addportmapping(port, protocol, upnp.lanaddr, port, "MC Server Manager", "", 0)
    if server_manager is not None:
        server_manager.log(server, f"[UPnP] Port {port} opened. Protocol: {protocol}")

def closePort(port=25565, protocol='TCP', server_manager=None, server=None):
    upnp = miniupnpc.UPnP()
    upnp.discover()
    upnp.selectigd()
    upnp.deleteportmapping(port, protocol)
    if server_manager is not None:
        server_manager.log(server, f"[UPnP] Port {port} closed. Protocol: {protocol}")