from pymarshal.json import type_assert, type_assert_iter


class CC:
    def __init__(
        self,
        pos,
        cc_num,
        value,
        note_uid,
    ):
        self.pos = type_assert(
            pos,
            float,
            check=lambda x: x >= 0.,
            desc="The position of this event within the pattern, in beats",
        )
        self.cc_num = type_assert(
            cc_num,
            int,
            desc="MIDI CC number",
        )
        self.value = type_assert(
            value,
            float,
            check=lambda x: x >= 0. and x <= 1.,
            desc="Controller value, mapped 0.0 to 1.0",
        )
        self.note_uid = type_assert(
            note_uid,
            int,
            desc=(
                "The uid of a specific note this applies to, "
                "or -1 for all notes"
            )
        )

