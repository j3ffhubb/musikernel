from sgdata.models.files.daw import ProjectFoldersDaw
import os
import tempfile


def test_create():
    with tempfile.TemporaryDirectory() as d:
        f = ProjectFoldersDaw.new(d)
        plugins_dir = os.path.join(
            d,
            'projects',
            'daw',
            'plugins',
        )
        assert f.plugins.folder == plugins_dir, (
            f.plugins.folder,
            plugins_dir,
        )
        f.create()
        assert os.path.isdir(plugins_dir)

