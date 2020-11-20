from sglib.math import db_to_lin
from sglib.models.daw.audio import AudioItem
import pytest


@pytest.fixture
def audio_item():
    return AudioItem(
        uid=0,
        wav_pool_uid=0,
        start=0.,
        end=1.,
        attack=5,
        fade_in_end=1.,
        fade_in_vol=-18.,
        fade_out_start=1.,
        fade_out_vol=-18.,
        release=5,
        volume=0.,
        pitch_mode=0,
        pitch_start=9.,
        pitch_end=0.,
        reverse=0,
        paifx_uid=0,
        pan=None,
    )

def test_compile_fade_in(audio_item):
    m18db = db_to_lin(-18.)
    # Use 1000 for the sample rate so that each sample is 1ms
    for (
        attack,
        fade_in_end,
        args,
        expected,
    ) in (
        (0, 0., (0, 1000, 1000), (0, 1., 1., 0, 1.)),
        (0, 0.5, (0, 1000, 1000), (0, 1., m18db, 500, 1. / 500)),
        (10, 0.5, (0, 1000, 1000), (10, 0.1, m18db, 510, 1. / 500)),
        (50, 0.5, (1000, 1000, 1000), (1050, 0.02, m18db, 1550, 1. / 500)),
        # Corner case: Attack longer than item
        (50, 0.5, (0, 30, 1000), (30, 1. / 30, 1., 30, 1.)),
        (50, 0.5, (100, 30, 1000), (130, 1. / 30, 1., 130, 1.)),
    ):
        audio_item.attack = attack
        audio_item.fade_in_end = fade_in_end
        result = audio_item.compile_fade_in(*args)
        assert result == expected, (result, expected)

def test_compile_fade_out(audio_item):
    m18db = db_to_lin(-18.)
    # Use 1000 for the sample rate so that each sample is 1ms
    for (
        release,
        fade_out_start,
        args,
        expected,
    ) in (
        (0, 1., (0, 1000, 1000), (1000, 1., 1000, 1., 1.)),
        (0, 0.5, (0, 1000, 1000), (500, 1. / 500, 1000, 1., m18db)),
        (10, 0.5, (0, 1000, 1000), (490, 1. / 500, 990, 0.1, m18db)),
        (50, 0.5, (1000, 1000, 1000), (1450, 1. / 500, 1950, 0.02, m18db)),
        # Corner case: release longer than item
        (50, 0.5, (0, 30, 1000), (0, 1., 0, 1. / 30., 1.)),
        (50, 0.5, (100, 30, 1000), (100, 1., 100, 1. / 30., 1.)),
    ):
        audio_item.release = release
        audio_item.fade_out_start = fade_out_start
        result = audio_item.compile_fade_out(*args)
        assert result == expected, (result, expected)

def test_rate(audio_item):
    for pitch_mode, pitch_start, expected in (
        (0, 0., 1.),
        (0, 12., 2.),
        (0, -12., 0.5),
        (1, 2., 2.),
        (1, 5., 5.),
    ):
        audio_item.pitch_mode = pitch_mode
        audio_item.pitch_start = pitch_start
        result = round(audio_item.get_rate(), 3)
        assert result == expected, (result, expected)

def test_rate_raises(audio_item):
    audio_item.pitch_mode = 99
    with pytest.raises(ValueError):
        audio_item.get_rate()

