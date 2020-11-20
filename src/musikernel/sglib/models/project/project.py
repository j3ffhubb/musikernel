from .midi import MIDIConfig
from pymarshal import type_assert, type_assert_iter
from sglib.models.util.next_uid import NextUID


class GlobalProject:
    """ Contains settings global to all sub-projects  """
    def __init__(
        self,
        next_wav_pool_uid,
        next_plugin_uid,
        midi_config,
    ):
        self.next_wav_pool_uid = type_assert(
            next_wav_pool_uid,
            NextUID,
            desc="The next available wav pool uid",
        )
        self.next_plugin_uid = type_assert(
            next_plugin_uid,
            NextUID,
            desc="The next available plugin uid",
        )
        self.midi_config = type_assert(
            midi_config,
            MIDIConfig,
        )

    @staticmethod
    def new():
        return GlobalProject(
            NextUID.new(),
            NextUID.new(),
            MIDIConfig.new(),
        )

