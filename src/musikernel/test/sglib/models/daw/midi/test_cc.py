from sglib.models.daw.midi.cc import CC


def test_init():
    CC(
        1.,
        64,
        .75,
        -1,
    )
