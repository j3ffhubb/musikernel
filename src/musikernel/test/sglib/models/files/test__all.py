from sglib.models.files import ProjectFoldersAll
import tempfile


def test_create():
    with tempfile.TemporaryDirectory() as d:
        p = ProjectFoldersAll.new(d)
        p.create()

