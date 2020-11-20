from pymarshal import type_assert


class AudioItemRef:
    def __init__(
        self,
        uid,
        audio_item_uid,
        pos,
        volume=0.0,
        pan=None,
    ):
        self.uid = type_assert(
            uid,
            int,
            desc="The uid of this item reference",
        )
        self.audio_item_uid = type_assert(
            audio_item_uid,
            int,
            desc="The uid of the audio item this refers to",
        )
        self.pos = type_assert(
            pos,
            float,
            desc="""
                The position of this audio item within the pattern, in beats
            """,
        )
        self.volume = type_assert(
            volume,
            float,
            desc="""
                The volume of the audio item ref, in decibels.  Note that this
                is added to the volume for the audio item itself, which can
                be used to adjust the volume of all instances, where this
                allows tweaking individual item references.
            """,
        )
        self.pan = type_assert(
            pan,
            float,
            allow_none=True,
            desc="""
                Pan for this file.
                -1 == left only, 0 == center, 1 == right only
            """,
        )

