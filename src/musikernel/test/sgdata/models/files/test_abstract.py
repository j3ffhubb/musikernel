from sgdata.models.files.abstract import (
    AbstractProjectFile,
    AbstractProjectFolder,
    AbstractProjectNestedFolder,
)
import pytest


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

