from sgui import glbl
from sgui import plugins
from sgui.daw.osc import DawOsc
from sgui.glbl.mk_project import *
from sgui.lib import history
from sgui.lib.util import *
from sgui.widgets import modulex_settings
from sgui.lib.translate import _
from sgui.sgqt import *
import numpy
import os
import re
import traceback

TRACK_COUNT_ALL = 32
#Anything smaller gets deleted when doing a transform
min_note_length = 4.0 / 129.0

class abstract_marker:
    def __lt__(self, other):
        if self.beat == other.beat:
            return self.type < other.type
        else:
            return self.beat < other.beat

class sequencer_marker(abstract_marker):
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
        return sequencer_marker(*a_str.split("|", 1))

