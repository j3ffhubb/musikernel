from pymarshal import type_assert, type_assert_iter
from sgdata.models.util.next_uid import NextUID


class GlobalProject:
    """ Contains settings global to all sub-projects  """
    def __init__(
        self,
        next_wav_pool_uid,
        next_plugin_uid,
        next_paifx_uid,
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
        self.next_paifx_uid = type_assert(
            next_paifx_uid,
            NextUID,
            desc="The next available per-audio-item-effects uid",
        )

    @staticmethod
    def new():
        return GlobalProject(
            NextUID.new(),
            NextUID.new(),
            NextUID.new(),
        )

