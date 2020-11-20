from .csv import ProjectFileCSV
from .json import ProjectFileJSON
from mkpy.lib.util import global_pydaw_version_string
from sgdata.models.config import (
    DeviceConfig,
    FileBrowserBookmark,
    GlobalConfig,
)
import os


__all__ = [
    'global_config_file',
    'device_config_file',
]

GLOBAL_CONFIG_DIR = os.path.join(
    os.path.expanduser('~'),
    global_pydaw_version_string,
)

def global_config_file(
    path=os.path.join(
        GLOBAL_CONFIG_DIR,
        'config.json',
    ),
    _type=GlobalConfig,
):
    return ProjectFileJSON(path, _type)

def device_config_file(
    path=os.path.join(
        os.path.expanduser('~'),
        global_pydaw_version_string,
        'device.csv',
    ),
    _type=DeviceConfig,
):
    return ProjectFileCSV(path, _type)

