from .abstract import (
    AbstractProjectFile,
    AbstractProjectFolder,
)
from sglib.log import LOG
from pymarshal.csv import (
    marshal_csv,
    type_assert,
    type_assert_iter,
    unmarshal_csv,
)
from pymarshal.json import (
    marshal_json,
    unmarshal_json,
)
import csv
import json
import os


class ProjectFolderJSON(AbstractProjectFolder):
    """ A project folder that stores serialized objects as JSON

        Multiple of these will be stored under the main project root folder
    """
    def save(self, obj):
        """ Save a file to a directory
            @obj: The object to save.  Must match the type for this folder and
                  have a .uid member
        """
        type_assert(obj, self._type)
        path = self.get_path(obj.uid)
        j = marshal_json(obj)
        with open(path, 'w') as f:
            json.dump(j, f, indent=2, sort_keys=True)
        # cache last, in case any other step fails
        self.cache[obj.uid] = obj

    def load(
        self,
        uid,
        force=False,
    ):
        """ Load an object from disk
            @uid:   int, the uid of the item to load
            @force: bool, True to force a reload from disk even if in cache
        """
        type_assert(uid, int)
        if (
            not force
            and
            uid in self.cache
        ):
            return self.cache[uid]
        path = self.get_path(uid)
        with open(path) as f:
            j = json.load(f)
        obj = unmarshal_json(j, self._type)
        self.cache[uid] = obj
        return obj

class ProjectFileJSON(AbstractProjectFile):
    def save(self, obj=None):
        if not obj:
            obj = self.cache
        j = marshal_json(obj)
        with open(self.path, 'w') as f:
            json.dump(j, f, indent=2, sort_keys=True)
        # cache last, in case any other step fails
        self.cache = obj

    def load(self, force=False):
        if not force:
            return self.cache
        with open(self.path) as f:
            j = json.load(f)
        obj = unmarshal_json(j, self._type)
        self.cache = obj
        return obj

    def create(self):
        """ Create a new project directory structure """
        LOG.info("Creating" + self.path)
        self.cache = self._type.new()
        self.save(self.cache)

