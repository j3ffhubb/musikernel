from pymarshal import (
    pm_assert,
    type_assert,
    type_assert_iter,
)


class ObjectName:
    def __init__(
        self,
        uid,
        name,
        version,
    ):
        self.uid = type_assert(
            uid,
            int,
            desc="The uid of an object"
        )
        self.name = type_assert(
            name,
            str,
            check=lambda x: len(x) < 32,
            desc="The display name of the sequence",
        )
        self.version = type_assert(
            version,
            int,
            desc="A version number for an object",
        )

class ObjectNames:
    def __init__(
        self,
        names,
    ):
        self.names = type_assert_iter(
            names,
            ObjectName,
            desc="The names associated with these objects",
        )

    def by_uid(self):
        # Done this way to avoid JSON keys being cast to str
        return {
            x.uid: x
            for x in self.names
        }

    def add(self, uid, name, version=0):
        _dict = self.by_uid()
        _dict[uid] = ObjectName(
            uid,
            name,
            version,
        )
        self.save(_dict)

    def save(self, _dict):
        self.names = list(_dict.values())
        self.names.sort(
            key=lambda x: x.uid
        )

    def rename(self, old, new):
        for obj in self.names:
            if obj.name == old:
                obj.name = new

    def new_version(self, uid, name):
        version = self.next_version(name)
        self.add(uid, name, version)

    def next_version(self, name):
        objects = [
            x for x in self.names
            if x.name == name
        ]
        pm_assert(
            objects,
            KeyError,
            msg="{} not found".format(name),
        )
        return max(x.version for x in objects) + 1

