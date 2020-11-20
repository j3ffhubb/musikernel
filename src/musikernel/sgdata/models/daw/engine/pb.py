from pymarshal import type_assert, type_assert_iter


class RackPBEvent:
    _marshal_list_row_header = "p"
    def __init__(
        self,
        pos,
        value,
        note_uid,
    ):
        self.pos = type_assert(
            pos,
            int,
            check=lambda x: x >= 0,
        )
        self.value = type_assert(
            value,
            float,
            desc="""
                Pitchbend value, -1.0 to 1.0, no pitchbend == 0.0
                Actual pitchbend amount will be determined by plugin settings
            """,
        )
        self.note_uid = type_assert(
            note_uid,
            int,
            desc="An individual note uid this applies to, or -1 for all notes",
        )

