from .audio_send import AudioSend
from .midi_send import MIDISend
from collections import defaultdict
from pymarshal import (
    type_assert,
    type_assert_iter,
)
from sgdata.models.daw.engine import *


class Item:
    def __init__(
        self,
        uid,
        audio_patterns,
        midi_patterns,
        audio_sends,
        midi_sends,
    ):
        self.uid = type_assert(uid, int)
        self.audio_patterns = type_assert_iter(
            audio_patterns,
            int,
            desc="The uids of the audio patterns referenced by this item"
        )
        self.midi_patterns = type_assert_iter(
            midi_patterns,
            int,
            desc="The uids of the MIDI patterns referenced by this item"
        )
        self.audio_sends = type_assert_iter(audio_sends, AudioSend)
        self.midi_sends = type_assert_iter(midi_sends, MIDISend)

    def compile_audio(
        self,
        result,
        item_ref,
        audio_p,
        ref_spos,
        tempo_map,
        wp_by_uid,
        sr,
    ):
        """
            @result:    defaultdict(list), plugin_rack_uid: [ event, ... ]
            @item_ref:  ItemRef, The item ref that called this
            @audio_p:   ProjectFolder, The audio patterns for this project
            @ref_spos:  int, The position of the item ref, in samples
            @tempo_map: TempoMap, The tempo map for the current sequence
            @wp_by_uid: dict {uid: WavPoolEntry{, The wave pool
        """
        send_lookup = defaultdict(list)
        for send in self.audio_sends:
            send_lookup[send.pattern_uid].append(send)
        for pattern_uid in self.audio_patterns:
            pattern = audio_p.load(pattern_uid)
            for item in pattern.items:
                wav = wp_by_uid[item.wav_pool_uid]
                start = tempo_map.sample_num(
                    item_ref.pos + item.pos
                )
                end = tempo_map.sample_num(
                    item_ref.pos + item.end
                )
                fade_in_end = int(
                    round((end - start) * item.fade_in_end)
                ) + start
                fade_out_start = int(
                    round((end - start) * item.fade_out_start)
                ) + start
                # This is at the audio file's sample rate, not the project
                # as above
                start_offset = int(
                    round(
                        (item.start_offset * wav.sample_count)
                        *
                        (wav.sample_rate / sr)
                    )
                )
                for send in send_lookup[pattern_uid]:
                    rack_event = RackAudioEvent(
                        item.wav_pool_uid,
                        start,
                        end,
                        start_offset,
                        fade_in_end,
                        1. / (fade_in_end - start or 1.),
                        fade_out_start,
                        1. / (end - fade_out_start or 1.),
                        item.fade_in_vol,
                        item.fade_out_vol,
                        item.volume + send.volume,
                        item.pitch_mode,
                        item.pitch_start,
                        item.pitch_end,
                        item.reverse,
                        send.send_mode,
                        item.paifx_uid,
                    )
                    result[send.plugin_rack_uid].append(rack_event)

    def compile_midi(
        self,
        result,
        item_ref,
        midi_p,
        ref_spos,
        tempo_map,
    ):
        """
            @result:    defaultdict(list), plugin_rack_uid: [ event, ... ]
            @item_ref:  The item ref that called this
            @midi_p:    ProjectFolder, The midi patterns for this project
            @ref_spos:  int, The position of the item ref, in samples
            @tempo_map: TempoMap, The tempo map for the current sequence
        """
        send_lookup = defaultdict(list)
        for send in self.midi_sends:
            send_lookup[send.pattern_uid].append(send)
        for pattern_uid in self.midi_patterns:
            pattern = midi_p.load(pattern_uid)
            for note in pattern.notes:
                # Do not play notes that start before the item ref
                # The current behavior is to play notes to their end even
                # if it is longer than the item ref
                if note.pos < item_ref.item_start:
                    continue
                start_beat = item_ref.pos + note.pos
                start = tempo_map.sample_num(start_beat)
                end = tempo_map.sample_num(start_beat + note.length)
                rack_event = RackNoteEvent(
                    note.uid,
                    start,
                    note.note,
                    note.velocity,
                    note_off=end,
                )
                for send in send_lookup[pattern_uid]:
                    if not send.mute_notes:
                        result[send.plugin_rack_uid].append(rack_event)
            for cc in pattern.ccs:
                if cc.pos < item_ref.item_start:
                    continue
                pos = tempo_map.sample_num(item_ref.pos + cc.pos)
                rack_event = RackCCEvent(
                    pos,
                    cc.cc_num,
                    cc.value,
                    note_uid=cc.note_uid,
                )
                for send in send_lookup[pattern_uid]:
                    if not send.mute_ccs:
                        result[send.plugin_rack_uid].append(rack_event)
            for pb in pattern.pbs:
                if pb.pos < item_ref.item_start:
                    continue
                pos = tempo_map.sample_num(item_ref.pos + pb.pos)
                rack_event = RackPBEvent(
                    pos,
                    pb.value,
                    note_uid=pb.note_uid,
                )
                for send in send_lookup[pattern_uid]:
                    if not send.mute_pbs:
                        result[send.plugin_rack_uid].append(rack_event)

