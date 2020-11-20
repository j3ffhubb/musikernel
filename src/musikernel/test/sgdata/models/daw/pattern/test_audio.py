from sgdata.models.daw.pattern.audio import AudioPattern
from sgdata.models.daw.pattern.audio_item import AudioItem


def test_init():
    AudioPattern(
        0,
        [
            AudioItem(
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
            ),
        ],
    )

