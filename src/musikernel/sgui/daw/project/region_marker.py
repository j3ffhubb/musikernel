from . import _shared
from sgui.glbl.mk_project import *
from sgui.lib.util import *
from sgui.lib.translate import _
from sgui.sgqt import *


class loop_marker(_shared.abstract_marker):
    def __init__(self, a_beat, a_start_beat):
        self.type = 1
        self.beat = int(a_beat)
        self.start_beat = int(a_start_beat)

    def __str__(self):
        return "|".join(str(x) for x in
            ("E", self.type, self.beat, self.start_beat))

    @staticmethod
    def from_str(self, a_str):
        return _shared.sequencer_marker(*a_str.split("|", 1))

