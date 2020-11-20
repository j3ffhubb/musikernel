from pymarshal import type_assert, type_assert_iter


class PluginControl:
    def __init__(
        self,
        num,
        value,
    ):
        self.num = type_assert(
            num,
            int,
            desc="The controller number",
        )
        self.value = type_assert(
            value,
            int,
            desc="The controller value",
        )

class PluginCustomControl:
    _marshal_list_row_header = 'c'
    def __init__(
        self,
        name,
        value,
    ):
        self.name = type_assert(
            name,
            str,
            check=lambda x: all(y not in x for y in ('|', '\\')),
            desc="The name of the custom control",
        )
        self.value = type_assert(
            value,
            str,
            # TODO: Fully switch the engine to csv to make this not necessary
            check=lambda x: '\\' not in x,
            desc="The value of the custom control",
        )

class Plugin:
    def __init__(
        self,
        uid,
        plugin_id,
        controls,
        power=1,
    ):
        self.uid = type_assert(uid, int)
        self.plugin_id = type_assert(
            plugin_id,
            int,
            desc="The numeric plugin ID",
        )
        self.controls = type_assert_iter(
            controls,
            (PluginControl, PluginCustomControl),
            desc="The control numbers and values associated with this plugin",
        )
        self.power = type_assert(
            power,
            int,
            choices=(0, 1),
            desc="0 to power off the rack, 1 to power on",
        )

