from . import _shared
from mkpy.glbl.mk_project import *
from mkpy.lib.util import *
from mkpy.lib.translate import _
from mkpy.mkqt import *


class pydaw_loop_marker(_shared.pydaw_abstract_marker):
    def __init__(self, a_beat, a_start_beat):
        self.type = 1
        self.beat = int(a_beat)
        self.start_beat = int(a_start_beat)

    def __str__(self):
        return "|".join(str(x) for x in
            ("E", self.type, self.beat, self.start_beat))

    @staticmethod
    def from_str(self, a_str):
        return _shared.pydaw_sequencer_marker(*a_str.split("|", 1))

