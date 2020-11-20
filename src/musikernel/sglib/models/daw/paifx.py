from pymarshal import (
    pm_assert,
    type_assert,
    type_assert_iter,
)


class PerAudioItemFXControls:
    def __init__(
        self,
        knob1,
        knob2,
        knob3,
        combobox,
    ):
        self.knob1 = type_assert(knob1, int, cast_from=str)
        self.knob2 = type_assert(knob2, int, cast_from=str)
        self.knob3 = type_assert(knob3, int, cast_from=str)
        # TODO: Get the actual count of choices
        self.combobox = type_assert(combobox, int, cast_from=str)

    @staticmethod
    def new(uid):
        return PerAudioItemFXControls(
            64,
            64,
            64,
            0,
        )

class PerAudioItemFX:
    def __init__(
        self,
        uid,
        controls
    ):
        self.uid = type_assert(uid, int)
        self.controls = type_assert_iter(
            controls,
            PerAudioItemFXControls,
        )
        pm_assert(
            len(controls) == 8,
            ValueError,
            len(controls),
        )

    @staticmethod
    def new(uid):
        return PerAudioItemFX(
            uid,
            [
                PerAudioItemFXControls.new(i)
                for i in range(8)
            ],
        )
