from sgdata.models.files.daw import ProjectFoldersDaw
from sgdata.models.audio.wav_pool import WavPool, WavPoolEntry
import glob
import os
import pytest
import tempfile


def _wav_paths():
    path = os.path.abspath(__file__)
    dirname = os.path.dirname(path)
    wavs = os.path.join(dirname, 'files', 'wavs', '*.wav')
    return sorted(
        glob.glob(wavs)
    )

@pytest.fixture(scope='session')
def wav_paths():
    return _wav_paths()

@pytest.fixture(scope='session')
def wav_pool():
    paths = _wav_paths()
    return WavPool(
        [
            WavPoolEntry(i, 16, 44100, 2, 1, x, i)
            for i, x in zip(
                range(len(paths)),
                paths,
            )
        ],
    )

@pytest.fixture(scope='session')
def daw_project_folders():
    with tempfile.TemporaryDirectory() as d:
        result = ProjectFoldersDaw.new(d)
    result.create()
    return result

