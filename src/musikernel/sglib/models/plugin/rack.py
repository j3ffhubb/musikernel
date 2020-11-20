from pymarshal import type_assert, type_assert_iter


class PluginRack:
    def __init__(
        self,
        uid,
        plugin_uids,
    ):
        self.uid = type_assert(uid, int)
        self.plugin_uids = type_assert_iter(
            plugin_uids,
            int,
            desc="""
                The plugin uids associated with this rack, or -1 for empty
                slots.
            """
        )

