from sglib.models.files.lib.abstract import (
    AbstractProjectFile,
    AbstractProjectFolder,
    AbstractProjectNestedFolder,
)
import os
import pytest
import tempfile


def test_folder_not_implemented():
    project_folder = AbstractProjectFolder("test", object)
    with pytest.raises(NotImplementedError):
        project_folder.save(1)

    with pytest.raises(NotImplementedError):
        project_folder.load(1)

def test_nested_folder_not_implemented():
    project_folder = AbstractProjectNestedFolder("test", object)
    with pytest.raises(NotImplementedError):
        project_folder.save(1, {})

def test_file_not_implemented():
    project_file = AbstractProjectFile("test", object)
    with pytest.raises(NotImplementedError):
        project_file.save(1)

    with pytest.raises(NotImplementedError):
        project_file.load(1)

def test_file_create():
    with tempfile.TemporaryDirectory() as d:
        dirname = os.path.join(d, 'test')
        fname = os.path.join(dirname, 'test.test')
        project_file = AbstractProjectFile(fname, object)
        project_file.create()
        assert os.path.isdir(dirname)
        # 2nd scenario:  Already exists
        project_file.create()

