from sglib.models.files.daw import ProjectFoldersDaw
import os
import tempfile


def test_create():
    with tempfile.TemporaryDirectory() as d:
        f = ProjectFoldersDaw.new(d)
        audio_items_dir = os.path.join(
            d,
            'projects',
            'daw',
            'pool',
            'audio_items',
        )
        assert f.audio_items.folder == audio_items_dir, (
            f.audio_items.folder,
            audio_items_dir,
        )
        f.create()
        assert os.path.isdir(audio_items_dir)

