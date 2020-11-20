from sglib.models.audio.stretch import Stretch, Stretches


def test_add():
    stretches = Stretches([])
    stretch = Stretch(
        0,
        0,
        "SBSMS",
        1.25,
        12.,
    )
    stretches.add(stretch)
    stretches.add(stretch)
    assert len(stretches.entries) == 1

