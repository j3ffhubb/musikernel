from .track import DawTracks
from sgdata.models.util.next_uid import NextUID
from sgdata.models.util.object_name import ObjectName, ObjectNames
from pymarshal.json import type_assert


class DawProject:
    def __init__(
        self,
        tracks,
        next_audio_item_uid,
        next_audio_pattern_uid,
        next_midi_pattern_uid,
        next_note_uid,
        sequence_names,
        item_names,
        audio_pattern_names,
        midi_pattern_names,
    ):
        self.tracks = type_assert(
            tracks,
            DawTracks,
            desc="The tracks for this project",
        )
        self.next_audio_item_uid = type_assert(
            next_audio_item_uid,
            NextUID,
        )
        self.next_audio_pattern_uid = type_assert(
            next_audio_pattern_uid,
            NextUID,
        )
        self.next_midi_pattern_uid = type_assert(
            next_midi_pattern_uid,
            NextUID,
        )
        self.next_note_uid = type_assert(
            next_note_uid,
            NextUID,
        )
        self.sequence_names = type_assert(
            sequence_names,
            ObjectNames,
            desc="The display names of the sequences",
        )
        self.item_names = type_assert(
            item_names,
            ObjectNames,
            desc="The display names of the items",
        )
        self.audio_pattern_names = type_assert(
            audio_pattern_names,
            ObjectNames,
            desc="The display names of the audio_patterns",
        )
        self.midi_pattern_names = type_assert(
            midi_pattern_names,
            ObjectNames,
            desc="The display names of the midi_patterns",
        )

    @staticmethod
    def new():
        """ Create a new, empty project """
        return DawProject(
            DawTracks.new(),
            NextUID.new(),
            NextUID.new(),
            NextUID.new(),
            NextUID.new(),
            sequence_names=ObjectNames([
                ObjectName(0, 'default', 0)
            ]),
            item_names=ObjectNames([]),
            audio_pattern_names=ObjectNames([]),
            midi_pattern_names=ObjectNames([]),
        )

