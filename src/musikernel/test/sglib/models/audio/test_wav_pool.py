from sglib.models.audio.wav_pool import WavPool, WavPoolEntry
import os
import pytest
import tempfile


def test_by_uid(tempdir, wav_paths, _wav_pool):
    d = tempdir()
    wav_pool = _wav_pool(d)
    wav1, wav2 = wav_paths
    by_uid = wav_pool.by_uid()
    assert by_uid[0].path == wav1
    assert by_uid[1].path == wav2
    assert by_uid.get(2) is None

def test_find_by_path(tempdir, wav_paths, _wav_pool):
    d = tempdir()
    wav_pool = _wav_pool(d)
    wav1, wav2 = wav_paths
    by_path = wav_pool.by_path()
    assert by_path[wav1].uid == 0
    assert by_path[wav2].uid == 1
    assert by_path.get("test") is None

def test_entry_add(tempdir, wav_paths):
    d = tempdir()
    wav_pool = WavPool.new()
    for i, path in zip(
        range(len(wav_paths)),
        wav_paths,
    ):
        w = WavPoolEntry.new(
            i,
            path,
            d,
            True,
            3,
        )
        assert w.path == os.path.join(d, path), (d, path, w.path)
        wav_pool.add(w)

def test_project_length():
    for args, expected in (
        ((10000, 0., 1., 1.), 10000),
        ((10000, 0.25, 0.75, 1.), 5000),
        ((10000, 0.25, 0.75, 2.), 2500),
        ((5000, 0.25, 0.75, 2.), 1250),
    ):
        wav = WavPoolEntry(
            0,
            10000,
            10000,
            2,
            1,
            'test',
            0,
            0.,
            None,
            0.,
        )
        result = wav.project_length(*args)
        assert result == expected, (result, expected)

