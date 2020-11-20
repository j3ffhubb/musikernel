from sglib.models.daw.seq import Playlist, Sequence, SequenceRef


def test_compile():
    playlist = Playlist([
        SequenceRef(
            0,
            0,
            4,
        ),
        SequenceRef(
            1,
            0,
            -1,
        ),
    ])
    result = playlist.compile(
        seq_by_uid={
            0: Sequence.new(0, 'test1'),
            1: Sequence.new(1, 'test2'),
        },
        sr=44100,
    )
    assert len(result) == 2, result
    assert result[0].start == 0, result[0].start
    # Default tempo 120, 4 beats, 44100hz
    assert result[0].end == 88200, result[0].end
    assert result[1].start == 0, result[1].start
    assert result[1].end == 0, result[1].end

