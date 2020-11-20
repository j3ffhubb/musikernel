from sglib.models.util.object_name import ObjectName, ObjectNames
import pytest


def test_add_rename_version():
    n = ObjectNames([])
    names = n.by_uid()
    assert not names
    n.add(0, 'name')

    names = n.by_uid()
    assert names[0].name == 'name'

    n.rename('name', 'test')
    names2 = n.by_uid()
    assert names2[0].name == 'test'

    n.new_version(1, 'test')
    names3 = n.by_uid()
    assert names3[1].version == 1

