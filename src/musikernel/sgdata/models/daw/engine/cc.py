from pymarshal import type_assert, type_assert_iter


class RackCCEvent:
    _marshal_list_row_header = "c"
    def __init__(
        self,
        pos,
        cc_num,
        value,
        note_uid,
    ):
        self.pos = type_assert(
            pos,
            int,
            check=lambda x: x >= 0,
            desc="The position of this event in the Sequence, in samples",
        )
        self.cc_num = type_assert(
            cc_num,
            int,
            choices=range(1, 128),
        )
        self.value = type_assert(
            value,
            float,
            check=lambda x: x >= 0. and x <= 1.,
        )
        self.note_uid = type_assert(
            note_uid,
            int,
            desc="An individual note uid this applies to, or -1 for all notes",
        )

