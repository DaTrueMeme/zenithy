import os
import psutil

CURRENT_VERSION = "Zenith TB0.0.6"

INSTALL_PATH = f'C:\\Users\\{os.getlogin()}\\.zenith'
HOME_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
GITHUB_REPO = f'https://datruememe.github.io/zenith'

total_ram = psutil.virtual_memory().total
TOTAL_RAM = round(total_ram / (1024 ** 3))
    
if not os.path.exists(INSTALL_PATH):
    os.makedirs(INSTALL_PATH, exist_ok=True)