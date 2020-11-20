from .lib.abstract import AbstractProjectFolders
from .lib.csv import (
    ProjectFolderCSV,
    ProjectFolderNestedCSV,
)
from .lib.json import (
    ProjectFileJSON,
    ProjectFolderJSON,
)
from sglib.log import LOG
from pymarshal import type_assert
from sglib.models.daw.audio import AudioItem
from sglib.models.daw.engine import *
from sglib.models.daw.item import Item
from sglib.models.daw.paifx import PerAudioItemFXControls
from sglib.models.daw.audio import AudioPattern
from sglib.models.daw.midi import MIDIPattern
from sglib.models.daw.project import DawProject
from sglib.models.daw.seq import Playlist, Sequence
from sglib.models.plugin import PluginRack
import os


__all__ = [
    'ProjectFoldersDaw',
]

class ProjectFoldersDaw(AbstractProjectFolders):
    def __init__(
        self,
        root,
        project,
        audio_patterns,
        engine_rack_events,
        items,
        midi_patterns,
        paifx,
        plugin_racks,
        sequences,
        playlist,
        audio_items,
        routing,
    ):
        self.root = type_assert(
            root,
            str,
            desc="""
                The root directory of the DAW files,
                $project_root/projects/daw
            """,
        )
        self.project = type_assert(
            project,
            ProjectFileJSON,
        )
        self.audio_patterns = type_assert(
            audio_patterns,
            ProjectFolderJSON,
        )
        self.engine_rack_events = type_assert(
            engine_rack_events,
            ProjectFolderNestedCSV,
        )
        self.items = type_assert(items, ProjectFolderJSON)
        self.midi_patterns = type_assert(midi_patterns, ProjectFolderJSON)
        self.paifx = type_assert(paifx, ProjectFolderCSV)
        self.plugin_racks = type_assert(plugin_racks, ProjectFolderJSON)
        self.sequences = type_assert(sequences, ProjectFolderJSON)
        self.playlist = type_assert(playlist, ProjectFileJSON)
        self.audio_items = type_assert(audio_items, ProjectFolderJSON)
        self.routing = type_assert(
            routing,
            str,
            desc="""
                The plugin rack routing file.  Ported over from legacy code,
                will be changed to ProjectFileCSV once the code can be updated
                to match the newer ways of doing things.
            """,
        )

    @staticmethod
    def new(project_root):
        """
            @project_root: str, The root directory of the entire project
        """
        root = os.path.join(
            os.path.abspath(
                project_root,
            ),
            'projects',
            'daw',
        )
        pool = os.path.join(
            root,
            'pool',
        )
        return ProjectFoldersDaw(
            root=root,
            project=ProjectFileJSON(
                os.path.join(root, 'project.json'),
                DawProject,
            ),
            audio_patterns=ProjectFolderJSON(
                os.path.join(pool, 'patterns', 'audio'),
                AudioPattern,
            ),
            engine_rack_events=ProjectFolderNestedCSV(
                os.path.join(root, 'engine', 'rack_events'),
                (
                    RackAudioEvent,
                    RackCCEvent,
                    RackNoteEvent,
                    RackPBEvent,
                ),
            ),
            items=ProjectFolderJSON(
                os.path.join(pool, 'items'),
                Item,
            ),
            midi_patterns=ProjectFolderJSON(
                os.path.join(pool, 'patterns', 'midi'),
                MIDIPattern,
            ),
            paifx=ProjectFolderCSV(
                os.path.join(pool, 'paifx'),
                PerAudioItemFXControls,
            ),
            plugin_racks=ProjectFolderJSON(
                os.path.join(pool, 'plugin_racks'),
                PluginRack,
            ),
            sequences=ProjectFolderJSON(
                os.path.join(pool, 'sequences'),
                Sequence,
            ),
            playlist=ProjectFileJSON(
                os.path.join(root, 'playlist.json'),
                Playlist,
            ),
            audio_items=ProjectFolderJSON(
                os.path.join(pool, 'audio_items'),
                AudioItem,
            ),
            routing=os.path.join(
                root,
                'routing.csv',
            )
        )

