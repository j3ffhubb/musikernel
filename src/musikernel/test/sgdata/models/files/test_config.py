from sgdata.models.config import *
from sgdata.models.files.config import *
import os
import tempfile


def test_global_config_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'config.json')
        f = global_config_file(path=path)
        c = GlobalConfig.new()
        c.bookmarks.append(
            FileBrowserBookmark('test', d, 'test'),
        )
        f.save(c)

def test_device_config_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'device.csv')
        f = device_config_file(path=path)
        c = DeviceConfig(
            'ALSA',
            'some device',
            128,
            44100,
            0,
            0,
            1,
            1,
            2,
            "2,0,1",
        )
        f.save_obj(c)

