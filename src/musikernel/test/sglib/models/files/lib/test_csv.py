from sglib.models.files.lib.csv import (
    ProjectFileCSV,
    ProjectFolderCSV,
)
from sglib.models.daw.paifx import (
    PerAudioItemFX,
    PerAudioItemFXControls,
)
import os
import pytest
import shutil
import tempfile


class MockCSVFileType:
    """ Because no file yet exists for this purpose """
    def __init__(self, a):
        self.a = a

    @staticmethod
    def new():
        return MockCSVFileType(
            [
                MockCSVFileTypeMember('a', 'b'),
                MockCSVFileTypeMember('c', 'd'),
            ],
        )

class MockCSVFileTypeMember:
    def __init__(self, a, b):
        self.a = a
        self.b = b


@pytest.fixture
def _folder():
    with tempfile.TemporaryDirectory() as tempdir:
        pass
    return ProjectFolderCSV(
        tempdir,
        PerAudioItemFXControls,
    )

@pytest.fixture
def _file():
    with tempfile.NamedTemporaryFile() as _file:
        pass
    return ProjectFileCSV(
        _file.name,
        MockCSVFileTypeMember,
    )

def test_create_save_load_folder(_folder):
    paifx = PerAudioItemFX.new(0)
    try:
        assert not os.path.exists(_folder.folder), _folder.folder
        _folder.create()
        assert os.path.isdir(_folder.folder), _folder.folder
        _folder.save(paifx.uid, paifx.controls)
        paifx2 = _folder.load(paifx.uid)
        for c1, c2 in zip(paifx.controls, paifx2):
            assert c1.__dict__ == c2.__dict__, (
                c1.__dict__,
                c2.__dict__,
            )
        paifx3 = _folder.load(paifx.uid, force=True)
        for c1, c2 in zip(paifx.controls, paifx3):
            assert c1.__dict__ == c2.__dict__, (
                c1.__dict__,
                c2.__dict__,
            )
    finally:
        shutil.rmtree(_folder.folder)

def test_create_save_load_file(_file):
    obj = MockCSVFileType.new()
    try:
        assert not os.path.exists(_file.path), _file.path
        _file.save(obj.a)
        assert os.path.isfile(_file.path), _file.path
        obj2 = _file.load()
        for c1, c2 in zip(obj.a, obj2):
            assert c1.__dict__ == c2.__dict__, (
                c1.__dict__,
                c2.__dict__,
            )
        obj3 = _file.load(force=True)
        for c1, c2 in zip(obj.a, obj3):
            assert c1.__dict__ == c2.__dict__, (
                c1.__dict__,
                c2.__dict__,
            )
    finally:
        os.remove(_file.path)

