from pymarshal import type_assert
from sglib.models.files.lib.json import (
    ProjectFileJSON,
    ProjectFolderJSON,
)
from sglib.models.daw.midi.note import Note
from sglib.models.daw.project.track import DawTracks
import json
import os
import pytest
import shutil
import tempfile


@pytest.fixture
def _folder():
    with tempfile.TemporaryDirectory() as tempdir:
        pass
    return ProjectFolderJSON(
        tempdir,
        Note,
    )

@pytest.fixture
def _file():
    with tempfile.NamedTemporaryFile() as _file:
        pass
    return ProjectFileJSON(
        _file.name,
        DawTracks,
    )

def test_create_save_load_folder(_folder):
    note = Note(
        0,
        60,
        0.,
        1.,
        1.,
    )
    try:
        assert not os.path.isdir(_folder.folder), _folder.folder
        _folder.create()
        assert os.path.isdir(_folder.folder), _folder.folder
        _folder.save(note)
        note2 = _folder.load(note.uid)
        assert note.__dict__ == note2.__dict__, (note.__dict__, note2.__dict__)
        note3 = _folder.load(note.uid, force=True)
        assert note.__dict__ == note3.__dict__, (note.__dict__, note3.__dict__)
    finally:
        shutil.rmtree(_folder.folder)

def test_create_save_load_file(_file):
    tracks = DawTracks.new()
    try:
        assert not os.path.exists(_file.path), _file.path
        _file.create()
        assert os.path.isfile(_file.path), _file.path
        _file.save(tracks)
        _file.save()
        tracks2 = _file.load()
        for track, track2 in zip(tracks.tracks, tracks2.tracks):
            assert track.__dict__ == track2.__dict__, (
                track.__dict__,
                track2.__dict__,
            )
        tracks3 = _file.load(force=True)
        for track, track3 in zip(tracks.tracks, tracks3.tracks):
            assert track.__dict__ == track3.__dict__, (
                track.__dict__,
                track3.__dict__,
            )
    finally:
        os.remove(_file.path)

def test_folder_by_uid():
    class Cls:
        def __init__(self, a):
            self.a = type_assert(a, int)

    with tempfile.TemporaryDirectory() as d:
        folder = ProjectFolderJSON(d, Cls)
        path = os.path.join(d, '0')
        with open(path, 'w') as f:
            json.dump({'a': 1}, f)
        path = os.path.join(d, 'test')
        with open(path, 'w') as f:
            json.dump({'a': 2}, f)
        by_uid = folder.by_uid()
    assert len(by_uid) == 1
    assert by_uid[0].a == 1, by_uid[0].a

