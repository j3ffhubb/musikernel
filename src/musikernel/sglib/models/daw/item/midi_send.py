from pymarshal import type_assert


class MIDISend:
    def __init__(
        self,
        uid,
        pattern_uid,
        plugin_rack_uid,
        mute_ccs,
        mute_notes,
        mute_pbs,
    ):
        self.uid = type_assert(uid, int)
        self.pattern_uid = type_assert(
            pattern_uid,
            int,
            desc="The uid of an existing MIDI pattern",
        )
        self.plugin_rack_uid = type_assert(
            plugin_rack_uid,
            int,
            desc="The uid of the plugin rack to send these events to",
        )
        self.mute_ccs = type_assert(
            mute_ccs,
            bool,
            desc="True to not send CC events from this pattern",
        )
        self.mute_notes = type_assert(
            mute_notes,
            bool,
            desc="True to not send note events from this pattern",
        )
        self.mute_pbs = type_assert(
            mute_pbs,
            bool,
            desc="True to not send pitchbend events from this pattern",
        )

