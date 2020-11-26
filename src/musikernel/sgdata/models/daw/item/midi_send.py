from pymarshal import type_assert


class MIDISend:
    def __init__(
        self,
        uid,
        pattern_uid,
        plugin_rack_uid,
    ):
        self.uid = type_assert(uid, int)
        self.pattern_uid = type_assert(pattern_uid, int)
        self.plugin_rack_uid = type_assert(plugin_rack_uid, int)

