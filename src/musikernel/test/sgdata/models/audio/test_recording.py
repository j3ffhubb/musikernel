from sgdata.models.audio.recording import Recording, Recordings
import datetime


def test_init():
    Recordings([
        Recording(
            datetime.datetime.now(),
            datetime.datetime.now(),
            {
                "drums": 0,
            },
        )
    ])

