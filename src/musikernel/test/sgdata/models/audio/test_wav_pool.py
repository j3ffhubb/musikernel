from sgdata.models.audio.wav_pool import WavPool, WavPoolEntry
import os
import pytest
import tempfile


def test_by_uid(wav_paths, wav_pool):
    wav1, wav2 = wav_paths
    by_uid = wav_pool.by_uid()
    assert by_uid[0].path == wav1
    assert by_uid[1].path == wav2
    assert by_uid.get(2) is None

def test_find_by_path(wav_paths, wav_pool):
    wav1, wav2 = wav_paths
    by_path = wav_pool.by_path()
    assert by_path[wav1].uid == 0
    assert by_path[wav2].uid == 1
    assert by_path.get("test") is None

def test_entry_add(wav_paths):
    wav_pool = WavPool.new()
    with tempfile.TemporaryDirectory() as t:
        for i, path in zip(
            range(len(wav_paths)),
            wav_paths,
        ):
            w = WavPoolEntry.new(
                i,
                path,
                t,
                True,
                3,
            )
            assert w.path == os.path.join(t, path), (t, path, w.path)
            wav_pool.add(w)

