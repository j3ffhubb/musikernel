from pymarshal import type_assert


class AudioSend:
    def __init__(
        self,
        uid,
        pattern_uid,
        plugin_rack_uid,
        send_mode,
        volume,
    ):
        self.uid = type_assert(uid, int)
        self.pattern_uid = type_assert(pattern_uid, int)
        self.plugin_rack_uid = type_assert(plugin_rack_uid, int)
        self.send_mode = type_assert(
            send_mode,
            int,
            choices=(0, 1, 2),
            desc="0: Normal, 1: Sidechain, 2: Both",
        )
        self.volume = type_assert(
            volume,
            float,
            check=lambda x: x >= -50. and x <= 24.,
            desc="The volume of the send, in decibels",
        )

