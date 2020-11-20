from .lib.abstract import AbstractProjectFolders
from .lib.csv import ProjectFolderCSV
from .lib.json import ProjectFolderJSON
from pymarshal.json import type_assert
from sglib.models.plugin import Plugin
import os


class ProjectFoldersMisc(AbstractProjectFolders):
    """ Catch-all for the less complex folder structures """
    def __init__(
        self,
        root,
        backups,
        user,
        plugins,
    ):
        self.root = type_assert(root, str)
        self.backups = type_assert(backups, str)
        self.user = type_assert(user, str)
        self.plugins = type_assert(plugins, ProjectFolderCSV)

    def create(self):
        super().create()
        for dirname in (
            self.root,
            self.backups,
            self.user,
        ):
            if not os.path.isdir(dirname):
                os.makedirs(dirname)

    @staticmethod
    def new(root):
        root = os.path.abspath(root)
        return ProjectFoldersMisc(
            root,
            backups=os.path.join(root, 'backups'),
            user=os.path.join(root, 'user'),
            plugins=ProjectFolderCSV(
                os.path.join(root, 'plugins'),
                Plugin,
            ),
        )

