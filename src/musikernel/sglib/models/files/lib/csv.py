from .abstract import (
    AbstractProjectFile,
    AbstractProjectFolder,
    AbstractProjectNestedFolder,
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
import glob
import os
import shutil


class ProjectFolderCSV(AbstractProjectFolder):
    def save(
        self,
        uid,
        _list,
    ):
        """ Save a file to a directory
            @uid:   The uid of the object to save
            @_list: The list of objects to save.  Must match the type
                    for this folder
        """
        type_assert_iter(_list, self._type)
        path = self.get_path(uid)
        _csv = marshal_csv(_list)
        with open(path, 'w') as f:
            w = csv.writer(f)
            w.writerows(_csv)
        # cache last, in case any other step fails
        self.cache[uid] = _list

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
            r = csv.reader(f)
            _list = list(r)
        result = unmarshal_csv(_list, self._type)
        self.cache[uid] = result
        return result

class ProjectFolderNestedCSV(AbstractProjectNestedFolder):
    def save(self, uid, _dict):
        """
            @uid:   int, the first-level folder to write to
            @_dict: dict, a dict of
                    {
                        0: [obj, ...],
                        1: [obj, ...],
                        ...
                    }
                    where 'obj' can be serialized to CSV
        """
        for v in _dict.values():
            type_assert_iter(v, self._type)
        path = os.path.join(
            self.folder,
            str(uid),
        )
        tmp_path = os.path.join(
            self.folder,
            str(uid) + 'tmp',
        )
        os.makedirs(tmp_path)
        for k, v in _dict.items():
            fpath = os.path.join(
                tmp_path,
                str(k),
            )
            _csv = marshal_csv(v)
            with open(fpath, 'w') as f:
                c = csv.writer(f)
                c.writerows(_csv)
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.rename(tmp_path, path)

class ProjectFileCSV(AbstractProjectFile):
    def save(
        self,
        _list,
    ):
        """ Save a list to a file
            @_list: The list of objects to save.  Must match the type
                    for this folder
        """
        type_assert_iter(_list, self._type)
        _csv = marshal_csv(_list)
        with open(self.path, 'w') as f:
            w = csv.writer(f)
            w.writerows(_csv)
        # cache last, in case any other step fails
        self.cache = _list

    def save_obj(
        self,
        obj,
    ):
        """ Save an object to a file
            @obj:
                The object to save.  Must match the type for this folder
        """
        type_assert(obj, self._type)
        _csv = [
            [k, v]
            for k, v in obj.__dict__.items()
        ]
        with open(self.path, 'w') as f:
            w = csv.writer(f)
            w.writerows(_csv)
        # cache last, in case any other step fails
        self.cache = obj

    def load(
        self,
        force=False,
    ):
        """ Load an object from disk
            @uid:   int, the uid of the item to load
            @force: bool, True to force a reload from disk even if in cache
        """
        if not force:
            return self.cache
        with open(self.path) as f:
            r = csv.reader(f)
            _list = list(r)
        result = unmarshal_csv(_list, self._type)
        self.cache = result
        return result

