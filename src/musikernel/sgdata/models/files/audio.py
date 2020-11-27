from .lib.abstract import AbstractProjectFolders
from pymarshal.json import type_assert
import os


class ProjectFoldersAudio(AbstractProjectFolders):
    def __init__(
        self,
        root,
        cache,
        local,
        samplegraph,
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
        )

