from mkpy.log import LOG
from pymarshal.json import type_assert
import json
import os


class AbstractProjectFolders:
    """ A grouping of related project folders  """
    def create(self):
        """ Create a new project directory structure """
        if (
            hasattr(self, 'root')
            and
            not os.path.isdir(self.root)
        ):
            os.makedirs(self.root)
        for v in (
            x for x in self.__dict__.values()
            if hasattr(x, 'create')
        ):
            v.create()

class AbstractProjectFolder:
    """ An implementation of a single folder
        Inheriting classes must override save and load.
    """
    def __init__(
            self,
            folder,
            _type,
            cache=None,
        ):
        self.folder = type_assert(
            folder,
            str,
            desc="The full path to a project folder",
        )
        self._type = type_assert(
            _type,
            (type, tuple),
            desc='The type of the model that is saved to this folder',
        )
        self.cache = type_assert(
            cache,
            dict,
            dynamic={},
            desc='A cache of objects, to avoid unneccessary disk reads',
        )

    def create(self):
        """ Create a new project directory structure """
        LOG.info("Creating" + self.folder)
        os.makedirs(self.folder)

    def get_path(self, uid):
        """ Return the path to an object
            @uid: int, the uid of the object
        """
        type_assert(uid, int)
        return os.path.join(
            self.folder,
            str(uid),
        )

    def save(self, obj):
        raise NotImplementedError

    def load(self, uid):
        raise NotImplementedError

class AbstractProjectNestedFolder:
    """ Provides a 2 level hierarchy of
        root/
          uid1/
            uida
            uidb
          uid2/
            uidc
            uidd
    """
    def __init__(
        self,
        folder,
        _type,
    ):
        self.folder = type_assert(
            folder,
            str,
            desc="The full path to a project folder",
        )
        self._type = type_assert(
            _type,
            (type, tuple),
            desc='The type of the model that is saved to this folder',
        )

    def create(self):
        """ Create a new project directory structure """
        LOG.info("Creating" + self.folder)
        os.makedirs(self.folder)

    def save(self, uid, _dict):
        raise NotImplementedError

class AbstractProjectFile:
    def __init__(
        self,
        path,
        _type,
        cache=None,
    ):
        self.path = type_assert(
            path,
            str,
            desc="The full path to a project file",
        )
        self._type = type_assert(
            _type,
            (type, tuple),
            desc='The type of the model that is saved to this folder',
        )
        self.cache = type_assert(
            cache,
            _type,
            allow_none=True,
            desc='A cache of the object, to avoid unneccessary disk reads',
        )

    def save(self, obj):
        raise NotImplementedError

    def load(self, uid):
        raise NotImplementedError

