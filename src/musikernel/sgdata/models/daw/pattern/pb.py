from pymarshal.json import type_assert, type_assert_iter


class PB:
    def __init__(
        self,
        pos,
        value,
        note_uid,
    ):
        self.pos = type_assert(
            pos,
            float,
            desc="The position of this event within the pattern, in beats",
        )
        self.value = type_assert(
            value,
            float,
            desc="Pitchbend value, -1.0 to 1.0, no pitchbend == 0.0",
        )
        self.note_uid = type_assert(
            note_uid,
            int,
            desc=(
                "The uid of a specific note this applies to, "
                "or -1 for all notes"
            )
        )

