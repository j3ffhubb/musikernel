from .audio_send import AudioSend
from .midi_send import MIDISend
from collections import defaultdict
from sglib.math import pan_stereo
from pymarshal import (
    type_assert,
    type_assert_iter,
)
from sglib.models.daw.engine import *


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
        audio_items,
    ):
        """
            @result:
                defaultdict(list), plugin_rack_uid: [ event, ... ]
            @item_ref:
                ItemRef, The item ref that called this
            @audio_p:
                ProjectFolder, The audio patterns for this project
            @ref_spos:
                int, The position of the item ref, in samples
            @tempo_map:
                TempoMap, The tempo map for the current sequence
            @wp_by_uid:
                dict {uid: WavPoolEntry{, The wave pool
            @sr:
                int, The sample rate of the audio device, in hertz
            @audio_items:
                ProjectFolder, The audio items for this project
        """
        send_lookup = defaultdict(list)
        for send in self.audio_sends:
            send_lookup[send.pattern_uid].append(send)
        for pattern_uid in self.audio_patterns:
            pattern = audio_p.load(pattern_uid)
            for audio_item_ref in pattern.items:
                audio_item = audio_items.load(
                    audio_item_ref.audio_item_uid,
                )
                wav = wp_by_uid[audio_item.wav_pool_uid]
                pos = tempo_map.sample_num(
                    item_ref.pos + audio_item_ref.pos
                )
                length = wav.project_length(
                    sr,
                    audio_item.start,
                    audio_item.end,
                    audio_item.get_rate(),
                )

                (
                    attack_end,
                    attack_recip,
                    attack_vol,
                    fade_in_end,
                    fade_in_recip,
                ) = audio_item.compile_fade_in(
                    pos,
                    length,
                    sr,
                )
                (
                    fade_out_start,
                    fade_out_recip,
                    release_start,
                    release_recip,
                    release_vol,
                ) = audio_item.compile_fade_out(
                    pos,
                    length,
                    sr,
                )
                # This is at the audio file's sample rate, not the project
                # as above
                start = int(
                    round(
                        audio_item.start * wav.sample_count
                    )
                )
                end = start + length
                for send in send_lookup[pattern_uid]:
                    volume_left, volume_right = pan_stereo(
                        (
                            audio_item_ref.pan,
                            audio_item.pan,
                            wav.pan,
                        ),
                        wav.pan_law,
                        sum((
                            wav.volume,
                            audio_item.volume,
                            audio_item_ref.volume,
                            send.volume,
                        ))
                    )
                    rack_event = RackAudioEvent(
                        wav_pool_uid=audio_item.wav_pool_uid,
                        pos=pos,
                        start=start,
                        end=end,
                        attack_end=attack_end,
                        attack_recip=attack_recip,
                        attack_vol=attack_vol,
                        fade_in_end=fade_in_end,
                        fade_in_recip=fade_in_recip,
                        fade_in_vol=audio_item.fade_in_vol,
                        fade_out_start=fade_out_start,
                        fade_out_recip=fade_out_recip,
                        fade_out_vol=audio_item.fade_out_vol,
                        release_start=release_start,
                        release_recip=release_recip,
                        release_vol=release_vol,
                        volume_left=volume_left,
                        volume_right=volume_right,
                        pitch_mode=audio_item.pitch_mode,
                        pitch_start=audio_item.pitch_start,
                        pitch_end=audio_item.pitch_end,
                        reverse=audio_item.reverse,
                        send_mode=send.send_mode,
                        paifx_uid=audio_item.paifx_uid,
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

