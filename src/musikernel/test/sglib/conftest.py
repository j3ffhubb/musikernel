from sglib.models.audio.wav_pool import WavPool, WavPoolEntry
import glob
import inspect
import os
import pytest
import tempfile


with tempfile.TemporaryDirectory() as d:
    TEMPDIR = d

def _tempdir(pos=1):
    """ Return a temporary directory path with the unit test module::func
        as the last directory.  The directory must be created by the caller.

        @pos: The stack frame position, 0==current, 1==caller
    """
    frame = inspect.stack()[pos]
    mod = inspect.getmodule(frame[0])
    dirname = "::".join([mod.__name__, frame[3]])
    return os.path.join(
        TEMPDIR,
        dirname,
    )

@pytest.fixture(scope='session')
def tempdir():
    return _tempdir

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
def _wav_pool():
    def wav_pool(d):
        cache_dir = os.path.join(
            d,
            'audio',
            'cache',
        )
        paths = _wav_paths()
        return WavPool(
            [
                WavPoolEntry.new(
                    i,
                    x,
                    cache_dir,
                    True,
                    i,
                )
                for i, x in zip(
                    range(len(paths)),
                    paths,
                )
            ],
        )
    return wav_pool

