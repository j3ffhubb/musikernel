from pymarshal.json import type_assert, type_assert_iter


class Note:
    def __init__(
        self,
        uid,
        note,
        pos,
        length,
        velocity,
    ):
        self.uid = type_assert(uid, int)
        self.note = type_assert(
            note,
            int,
            choices=range(1, 128),
            desc="The MIDI note number",
        )
        self.pos = type_assert(
            pos,
            float,
            check=lambda x: x >= 0.,
            desc="The position of this event within the pattern, in beats",
        )
        self.length = type_assert(
            length,
            float,
            check=lambda x: x > 0.,
            desc="The length of this event within the pattern, in beats",
        )
        self.velocity = type_assert(
            velocity,
            float,
            check=lambda x: x >= 0. and x <= 1.27,
            desc="Note velocity, mapped from 0.0 to 1.27",
        )

