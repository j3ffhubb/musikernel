from .audio import ProjectFoldersAudio
from .daw import ProjectFoldersDaw
from .misc import ProjectFoldersMisc
from pymarshal import type_assert


class ProjectFoldersAll:
    def __init__(
        self,
        audio,
        daw,
        misc,
    ):
        self.audio = type_assert(audio, ProjectFoldersAudio)
        self.daw = type_assert(daw, ProjectFoldersDaw)
        self.misc = type_assert(misc, ProjectFoldersMisc)

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
        )

