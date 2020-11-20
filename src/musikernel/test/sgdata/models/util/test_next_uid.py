from sgdata.models.util.next_uid import NextUID


def test_next_uid():
    n = NextUID.new()
    for i in range(100):
        assert n.get() == i

