from sgdata.models.daw.pattern import *
from sgdata.models.daw.paifx import PerAudioItemFX
from sgdata.models.daw.item import *
from sgdata.models.daw.seq.sequence import *


def test_compile_empty(daw_project_folders, wav_pool):
    s = Sequence.new(0, 'name')
    result = s.compile(
        44100,
        daw_project_folders.items,
        daw_project_folders.audio_patterns,
        daw_project_folders.midi_patterns,
        wav_pool,
        daw_project_folders.engine_rack_events,
        set(range(32)),
    )
    assert not result, result

def test_compile(daw_project_folders, wav_pool):
    s = Sequence.new(0, 'name')
    s.add_item_ref(
        ItemRef(0, 0, 0., 1., 6., 0),
    )
    daw_project_folders.midi_patterns.save(
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
    daw_project_folders.paifx.save(
        0,
        PerAudioItemFX.new(0).controls,
    )
    daw_project_folders.audio_patterns.save(
        AudioPattern(
            0,
            [
                AudioItem(
                    0,
                    0.,
                    2.,
                    0.24,
                    0.,
                    1.,
                    -18.,
                    -18.,
                    -6.,
                    0,
                    0.,
                    0.,
                    0,
                    0,
                    0,
                ),
            ],
        ),
    )
    daw_project_folders.items.save(
        Item(
            0,
            [0],
            [0],
            [
                AudioSend(0, 0, 0, 0, 0.),
            ],
            [
                MIDISend(0, 0, 0),
            ],
        ),
    )

    result = s.compile(
        44100,
        daw_project_folders.items,
        daw_project_folders.audio_patterns,
        daw_project_folders.midi_patterns,
        wav_pool,
        daw_project_folders.engine_rack_events,
        set(range(32)),
    )
    assert result, result

