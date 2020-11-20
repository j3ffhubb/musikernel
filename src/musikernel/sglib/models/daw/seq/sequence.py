from .item_ref import ItemRef
from .tempo_map import TempoMap
from .tempo_marker import TempoMarker
from collections import defaultdict
from pymarshal.csv import marshal_csv
from pymarshal.json import type_assert, type_assert_iter
import csv
import glob
import os


class Sequence:
    def __init__(
        self,
        uid,
        name,
        item_refs,
        tempo_markers,
        region_start,
        region_end,
    ):
        self.uid = type_assert(uid, int)
        self.name = type_assert(name, str)
        self.item_refs = type_assert_iter(item_refs, ItemRef)
        self.tempo_markers = type_assert_iter(tempo_markers, TempoMarker)
        self.region_start = type_assert(
            region_start,
            int,
            desc="The start of the loop and offline render region, in beats",
        )
        self.region_end = type_assert(
            region_end,
            int,
            desc="The end of the loop and offline render region, in beats",
        )

    @staticmethod
    def new(uid, name):
        return Sequence(
            uid=uid,
            name=name,
            item_refs=[],
            tempo_markers=[
                TempoMarker(
                    0.,
                    120,
                ),
            ],
            region_start=0,
            region_end=8,
        )

    def add_item_ref(self, item_ref):
        type_assert(item_ref, ItemRef)
        self.item_refs.append(item_ref)

    def compile(
        self,
        sr,
        items,
        audio_p,
        midi_p,
        audio_items,
        wav_pool,
        active_tracks,
    ):
        """
            @sr:
                int, The sample rate, in hertz
            @items:
                ProjectFolder, The items for this project
            @audio_p:
                ProjectFolder, The audio patterns for this project
            @midi_p:
                ProjectFolder, The midi patterns for this project
            @wav_pool:
                WavPool, the wave pool for this project
            @active_tracks:
                set-of-int, The active track numbers
            @audio_items:
                ProjectFolder, The audio items for this project
        """
        self.item_refs.sort(
            key=lambda x: x.pos
        )
        tempo_map = self.tempo_map(sr)
        # A dict of plugin_rack_uid: [event, ....]
        result = defaultdict(list)
        wp_by_uid = wav_pool.by_uid()
        for ref in (
            x for x in self.item_refs
            if x.track_num in active_tracks
        ):
            spos = tempo_map.sample_num(ref.pos)
            item = ref.item(items)
            item.compile_audio(
                result,
                ref,
                audio_p,
                spos,
                tempo_map,
                wp_by_uid,
                sr,
                audio_items,
            )
            item.compile_midi(
                result,
                ref,
                midi_p,
                spos,
                tempo_map,
            )

        for k, v in result.items():
            v.sort(key=lambda x: x.pos)

        return result

    def tempo_map(self, sr):
        return TempoMap.factory(self.tempo_markers, sr)

    def __len__(self):
        return max(
            (x.pos + x.length for x in self.item_refs),
            default=0,
        )

