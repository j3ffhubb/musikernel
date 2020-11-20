from pymarshal import type_assert


class SequenceRef:
    def __init__(
        self,
        uid,
        start,
        end,
    ):
        self.uid = type_assert(
            uid,
            int,
            desc="The uid of the Sequence",
        )
        self.start = type_assert(
            start,
            int,
            desc="""
                The position within the sequence where playback starts,
                in beats
            """,
        )
        self.end = type_assert(
            end,
            int,
            desc="""
                The position within the sequence where playback ends,
                in beats, or -1 to calculate the end of the sequence.
            """,
        )

