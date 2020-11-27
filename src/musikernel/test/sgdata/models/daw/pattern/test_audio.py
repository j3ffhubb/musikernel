from mkpy.lib.util import pydaw_db_to_lin
from sgdata.models.daw.pattern.audio import AudioPattern
from sgdata.models.daw.pattern.audio_item import AudioItem
import pytest


@pytest.fixture
def audio_item():
    return AudioItem(
        0,
        0.,
        1.,
        0.,
        1.,
        1.,
        -18.,
        -18.,
        0.,
        0,
        9.,
        0.,
        0,
        0,
        0,
        5,
        5,
    )

def test_init(audio_item):
    AudioPattern(
        0,
        [
            audio_item,
        ],
    )

def test_compile_fade_in(audio_item):
    minus18db = pydaw_db_to_lin(-18.)
    # Use 1000 for the sample rate so that each sample is 1ms
    for (
        attack,
        fade_in_end,
        args,
        expected,
    ) in (
        (0, 0., (0, 1000, 1000), (0, 1., 1., 0)),
        (0, 0.5, (0, 1000, 1000), (0, 1., minus18db, 500)),
        (10, 0.5, (0, 1000, 1000), (10, 0.1, minus18db, 510)),
        (50, 0.5, (1000, 1000, 1000), (1050, 0.02, minus18db, 1550)),
    ):
        audio_item.attack = attack
        audio_item.fade_in_end = fade_in_end
        result = audio_item.compile_fade_in(*args)
        assert result == expected, (result, expected)

