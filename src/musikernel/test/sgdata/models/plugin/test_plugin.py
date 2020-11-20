from sgdata.models.plugin.plugin import (
    Plugin,
    PluginControl,
    PluginCustomControl,
)


def test_init():
    Plugin(
        0,
        12,
        [
            PluginControl(0, 0),
            PluginCustomControl('name', 'value'),
        ],
        1,
    )

