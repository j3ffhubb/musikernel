from sglib.models.daw.audio import *
from sglib.models.daw.item import *
from sglib.models.daw.midi import *
from sglib.models.daw.paifx import PerAudioItemFX
from sglib.models.daw.seq.sequence import *
from sglib.models.files._all import ProjectFoldersAll


def test_compile_empty(tempdir, _wav_pool):
    d = tempdir()
    wav_pool = _wav_pool(d)
    _all = ProjectFoldersAll.new(d)
    _all.create()
    s = Sequence.new(0, 'name')
    result = s.compile(
        44100,
        _all.daw.items,
        _all.daw.audio_patterns,
        _all.daw.midi_patterns,
        _all.daw.audio_items,
        wav_pool,
        set(range(32)),
    )
    assert not result, result

def test_compile(tempdir, _wav_pool):
    d = tempdir()
    wav_pool = _wav_pool(d)
    _all = ProjectFoldersAll.new(d)
    _all.create()

    s = Sequence.new(0, 'name')
    s.add_item_ref(
        ItemRef(0, 0, 0., 1., 6., 0),
    )
    _all.daw.midi_patterns.save(
        MIDIPattern(
            0,
            [
                Note(0, 33, 0., 1., 1.),
                Note(1, 33, 1., 1., 1.),
            ],
            [
                CC(0., 24, 0.5, -1),
                CC(1., 24, 0.5, 0),
            ],
            [
                PB(0., 0., 0),
                PB(1., 0., 1),
            ],
        ),
    )
    _all.daw.paifx.save(
        0,
        PerAudioItemFX.new(0).controls,
    )
    _all.daw.audio_items.save(
        AudioItem(
            uid=0,
            wav_pool_uid=0,
            end=1.,
            start=0.24,
            attack=5,
            fade_in_end=0.,
            fade_in_vol=-18.,
            fade_out_start=1.,
            fade_out_vol=-18.,
            release=5,
            volume=-6.,
            pitch_mode=0,
            pitch_start=0.,
            pitch_end=0.,
            reverse=0,
            paifx_uid=0,
            pan=None,
        ),
    )
    _all.daw.audio_patterns.save(
        AudioPattern(
            0,
            [
                AudioItemRef(0, 0, 0.0),
            ],
        ),
    )
    _all.daw.items.save(
        Item(
            0,
            [0],
            [0],
            [
                AudioSend(0, 0, 0, 0, 0.),
            ],
            [
                MIDISend(0, 0, 0, False, False, False),
                MIDISend(1, 0, 0, True, True, True),
            ],
        ),
    )

    result = s.compile(
        44100,
        _all.daw.items,
        _all.daw.audio_patterns,
        _all.daw.midi_patterns,
        _all.daw.audio_items,
        wav_pool,
        set(range(32)),
    )

    _all.daw.engine_rack_events.save(
        s.uid,
        result,
    )
    # Test deleting the old directory
    _all.daw.engine_rack_events.save(
        s.uid,
        result,
    )
    assert result, result
    assert len(result[0]) == 4, result[0]

