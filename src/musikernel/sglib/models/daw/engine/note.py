from pymarshal import type_assert, type_assert_iter


class RackNoteEvent:
    _marshal_list_row_header = "n"
    """ A note on or off event.  Velocity==0 is note off """
    def __init__(
        self,
        uid,
        pos,
        note,
        velocity,
        note_off,
    ):
        self.uid = type_assert(uid, int)
        self.pos = type_assert(
            pos,
            int,
            check=lambda x: x >= 0,
            desc="""
                The sample number within the sequence that this event
                happens at
            """,
        )
        self.note = type_assert(
            note,
            int,
            check=lambda x: x >= 0 and x <= 127
        )
        self.velocity = type_assert(
            velocity,
            float,
            check=lambda x: x >= 0. and x <= 1.27,
        )
        self.note_off = type_assert(
            note_off,
            int,
            desc="""
                The sample number within the sequence that the note is
                released
            """,
        )

