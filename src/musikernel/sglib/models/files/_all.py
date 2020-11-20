from .audio import ProjectFoldersAudio
from .daw import ProjectFoldersDaw
from .lib.json import ProjectFileJSON
from .misc import ProjectFoldersMisc
from sgui.lib.util import MAJOR_VERSION
from pymarshal import type_assert
from sglib.models.project import GlobalProject
import os


class ProjectFoldersAll:
    def __init__(
        self,
        audio,
        daw,
        misc,
        main,
    ):
        self.audio = type_assert(audio, ProjectFoldersAudio)
        self.daw = type_assert(daw, ProjectFoldersDaw)
        self.misc = type_assert(misc, ProjectFoldersMisc)
        self.main = type_assert(main, ProjectFileJSON)

    def create(self):
        """ Create the project """
        for k in sorted(self.__dict__.keys()):
            v = self.__dict__[k]
            v.create()

    @staticmethod
    def new(project_root):
        return ProjectFoldersAll(
            audio=ProjectFoldersAudio.new(project_root),
            daw=ProjectFoldersDaw.new(project_root),
            misc=ProjectFoldersMisc.new(project_root),
            main=ProjectFileJSON(
                os.path.join(
                    project_root,
                    '{}.json'.format(MAJOR_VERSION),
                ),
                GlobalProject,
            ),
        )

