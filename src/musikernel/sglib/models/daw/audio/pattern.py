from .item_ref import AudioItemRef
from pymarshal.json import type_assert, type_assert_iter


class AudioPattern:
    def __init__(
        self,
        uid,
        items,
    ):
        self.uid = type_assert(uid, int)
        self.items = type_assert_iter(items, AudioItemRef)

