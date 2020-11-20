from .cc import CC
from .note import Note
from .pb import PB
from pymarshal.json import type_assert, type_assert_iter


class MIDIPattern:
    def __init__(
        self,
        uid,
        notes,
        ccs,
        pbs,
    ):
        self.uid = type_assert(uid, int)
        self.notes = type_assert_iter(notes, Note)
        self.ccs = type_assert_iter(ccs, CC)
        self.pbs = type_assert_iter(pbs, PB)

    @staticmethod
    def new(uid):
        return MIDIPattern(
            uid,
            [],
            [],
            [],
        )
