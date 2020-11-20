from .lib.csv import ProjectFileCSV
from .lib.json import ProjectFileJSON
from sgui.lib.util import MAJOR_VERSION
from sglib.models.config import (
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
    MAJOR_VERSION,
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
        MAJOR_VERSION,
        'device.csv',
    ),
    _type=DeviceConfig,
):
    return ProjectFileCSV(path, _type)

