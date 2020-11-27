from .lib.abstract import AbstractProjectFolders
from pymarshal.json import type_assert
import os


class ProjectFoldersMisc(AbstractProjectFolders):
    """ Catch-all for the less complex folder structures """
    def __init__(
        self,
        root,
        backups,
        user,
    ):
        self.root = type_assert(root, str)
        self.backups = type_assert(backups, str)
        self.user = type_assert(user, str)

    @staticmethod
    def new(root):
        root = os.path.abspath(root)
        return ProjectFoldersMisc(
            root,
            backups=os.path.join(root, 'backups'),
            user=os.path.join(root, 'user'),
        )

