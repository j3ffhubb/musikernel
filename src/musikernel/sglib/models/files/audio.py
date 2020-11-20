from .lib.abstract import AbstractProjectFolders
from .lib.csv import ProjectFileCSV
from .lib.json import ProjectFileJSON
from pymarshal.json import type_assert
from sglib.models.audio import *
import os


class ProjectFoldersAudio(AbstractProjectFolders):
    def __init__(
        self,
        root,
        cache,
        local,
        samplegraph,
        wav_pool,
        recordings,
        stretches,
    ):
        self.root = type_assert(
            root,
            str,
            desc="The root audio folder",
        )
        self.cache = type_assert(
            cache,
            str,
            desc="""
                Files from disk are cached in this directory, so that the
                project will always be completely self-contained and not
                reliant on having particular files in particular locations.
            """,
        )
        self.local = type_assert(
            local,
            str,
            desc="""
                Files that are local to the project, such as those that were
                recorded, or created by processing within the project.  These
                files are not cached.
            """,
        )
        self.samplegraph = type_assert(
            samplegraph,
            str,
            desc="Generated sample graphs data files for each wav pool entry",
        )
        self.wav_pool = type_assert(
            wav_pool,
            ProjectFileCSV,
            desc="The wave pool for this project",
        )
        self.recordings = type_assert(
            recordings,
            ProjectFileJSON,
            desc="Tracks files that were created by recordings",
        )
        self.stretches = type_assert(
            stretches,
            ProjectFileJSON,
            desc="Tracks files that were time stretched or pitch shifted",
        )

    @staticmethod
    def new(project_root):
        root = os.path.join(
            os.path.abspath(project_root),
            'audio',
        )
        return ProjectFoldersAudio(
            root=root,
            cache=os.path.join(root, 'cache'),
            local=os.path.join(root, 'local'),
            samplegraph=os.path.join(root, 'samplegraph'),
            wav_pool=ProjectFileCSV(
                os.path.join(root, 'wav_pool.csv'),
                WavPoolEntry,
            ),
            recordings=ProjectFileJSON(
                os.path.join(root, 'recordings.json'),
                Recordings,
            ),
            stretches=ProjectFileJSON(
                os.path.join(root, 'stretches.json'),
                Stretches,
            ),
        )

    def create(self):
        for dirname in (
            self.root,
            self.cache,
            self.local,
            self.samplegraph,
        ):
            if not os.path.isdir(dirname):
                os.makedirs(dirname)

