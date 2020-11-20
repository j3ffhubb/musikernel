from pymarshal.json import type_assert


class TempoMarker:
    def __init__(
        self,
        pos,
        tempo,
    ):
        self.pos = type_assert(
            pos,
            float,
            desc="The marker position, in beats",
        )
        self.tempo = type_assert(
            tempo,
            int,
            desc="The tempo, in beats per minute",
        )

