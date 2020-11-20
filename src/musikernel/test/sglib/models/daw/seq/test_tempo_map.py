from sglib.models.daw.seq.tempo_map import TempoMap, TempoMapPoint
from sglib.models.daw.seq.tempo_marker import TempoMarker
import pytest

LARGE_SIZE = 102

@pytest.fixture
def _large_map(
    size=LARGE_SIZE,
):
    # Note that this tempo map is not an accurate calcuation or a real
    # sample rate
    tmap = [
        TempoMapPoint(
            float(i),
            i * 100,
            100,
        ) for i in range(size)
    ]
    return TempoMap(tmap)

def test_sample_num(_large_map):
    for i in range(LARGE_SIZE):
        snum = _large_map.sample_num(i + 0.5)
        assert snum == (i * 100) + 50, snum
    past_end = float(LARGE_SIZE * 2)
    snum = _large_map.sample_num(past_end)
    assert snum == int(round(past_end * 100.)), (snum, past_end)

def test_factory():
    tmarkers = [
        TempoMarker(0., 120),
        TempoMarker(32., 140),
    ]
    sr = 48000
    tmap = TempoMap.factory(tmarkers, sr)
    assert tmap.tmap[1].sample_num == 768000, tmap.tmap[1].sample_num

def test_binary_search(_large_map):
    for i in range(LARGE_SIZE):
        j, point = _large_map.binary_search(i + 0.5)
        assert j == i, (j, i)
    j, point = _large_map.binary_search(2004.)
    last = LARGE_SIZE - 1
    assert j == last, (j, last)

def test_beat():
    tmap = TempoMap([
        TempoMapPoint(
            float(i),
            i * 100,
            100,
        ) for i in range(3)
    ])
    for args, expected in (
        ((0., 50), .5),
        ((0., 240), 2.4),
        ((1.5, 240), 2.4),
        ((1.5, 2400), 24),
    ):
        result = tmap.beat(*args)
        assert result == expected, (result, expected)

