from mkpy import libmk
from mkpy import mkplugins
from mkpy.libdawnext.osc import DawNextOsc
from mkpy.libmk.mk_project import *
from mkpy.libpydaw import pydaw_history
from mkpy.libpydaw.pydaw_util import *
from mkpy.libpydaw.pydaw_widgets import pydaw_modulex_settings
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *
import numpy
import os
import re
import traceback

TRACK_COUNT_ALL = 32
#Anything smaller gets deleted when doing a transform
pydaw_min_note_length = 4.0 / 129.0

class pydaw_abstract_marker:
    def __lt__(self, other):
        if self.beat == other.beat:
            return self.type < other.type
        else:
            return self.beat < other.beat

class pydaw_sequencer_marker(pydaw_abstract_marker):
    def __init__(self, a_beat, a_text):
        self.type = 3
        self.beat = int(a_beat)
        self.text = str(a_text)

    def __str__(self):
        return "|".join(
            str(x)
            for x in ("E", self.type, self.beat, self.text)
        )

    @staticmethod
    def from_str(self, a_str):
        return pydaw_sequencer_marker(*a_str.split("|", 1))

