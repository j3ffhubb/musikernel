from sgdata.models.files import ProjectFileJSON, ProjectFolderJSON
from sgdata.models.daw.pattern.note import Note
from sgdata.models.daw.track import DawTracks
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

