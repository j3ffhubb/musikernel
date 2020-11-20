from pymarshal import type_assert


class EngineSeqRef:
    def __init__(
        self,
        uid,
        start,
        end,
    ):
        self.uid = type_assert(
            uid,
            int,
            desc="The uid of the sequence",
        )
        self.start = type_assert(
            start,
            int,
            desc="""
                The position to start at within the sequence, in samples.
            """,
        )
        self.end = type_assert(
            end,
            int,
            desc="""
                The position to stop playing this sequence on, in samples.
            """
        )

