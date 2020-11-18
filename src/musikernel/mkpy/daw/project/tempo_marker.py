from . import _shared
from mkpy.glbl.mk_project import *
from mkpy.lib.util import *
from mkpy.lib.translate import _
from mkpy.mkqt import *


class pydaw_tempo_marker(_shared.pydaw_abstract_marker):
    def __init__(self, a_beat, a_tempo, a_tsig_num, a_tsig_den):
        self.type = 2
        self.beat = int(a_beat)
        self.tempo = round(float(a_tempo), 1)
        self.tsig_num = int(a_tsig_num)
        self.tsig_den = int(a_tsig_den)
        self.real_tempo = (float(a_tsig_den) / 4.0) * self.tempo

    def __str__(self):
        return "|".join(
            str(x)
            for x in (
                "E",
                self.type,
                self.beat,
                self.tempo,
                self.tsig_num,
                self.tsig_den,
            )
        )

    @staticmethod
    def from_str(self, a_str):
        return _shared.pydaw_sequencer_marker(*a_str.split("|"))

