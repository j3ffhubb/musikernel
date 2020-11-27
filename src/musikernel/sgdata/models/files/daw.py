from .lib.abstract import AbstractProjectFolders
from .lib.csv import (
    ProjectFolderCSV,
    ProjectFolderNestedCSV,
)
from .lib.json import (
    ProjectFileJSON,
    ProjectFolderJSON,
)
from mkpy.log import LOG
from pymarshal import type_assert
from sgdata.models.daw.engine import *
from sgdata.models.daw.item import Item
from sgdata.models.daw.paifx import PerAudioItemFXControls
from sgdata.models.daw.pattern.audio import AudioPattern
from sgdata.models.daw.pattern.midi import MIDIPattern
from sgdata.models.daw.project import DawProject
from sgdata.models.daw.seq import Sequence
from sgdata.models.plugin import Plugin
from sgdata.models.plugin import PluginRack
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
        engine_plugins,
        engine_rack_events,
        items,
        midi_patterns,
        paifx,
        plugin_racks,
        plugins,
        sequences,
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
        self.engine_plugins = type_assert(
            engine_plugins,
            ProjectFolderCSV,
        )
        self.engine_rack_events = type_assert(
            engine_rack_events,
            ProjectFolderNestedCSV,
        )
        self.items = type_assert(items, ProjectFolderJSON)
        self.midi_patterns = type_assert(midi_patterns, ProjectFolderJSON)
        self.paifx = type_assert(paifx, ProjectFolderCSV)
        self.plugin_racks = type_assert(plugin_racks, ProjectFolderJSON)
        self.plugins = type_assert(plugins, ProjectFolderJSON)
        self.sequences = type_assert(sequences, ProjectFolderJSON)

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
        return ProjectFoldersDaw(
            root=root,
            project=ProjectFileJSON(
                os.path.join(root, 'project.json'),
                DawProject,
            ),
            audio_patterns=ProjectFolderJSON(
                os.path.join(root, 'audio_patterns'),
                AudioPattern,
            ),
            engine_plugins=ProjectFolderCSV(
                os.path.join(root, 'engine', 'plugins'),
                Plugin,  # TODO: Plugin control format
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
                os.path.join(root, 'items'),
                Item,
            ),
            midi_patterns=ProjectFolderJSON(
                os.path.join(root, 'midi_patterns'),
                MIDIPattern,
            ),
            paifx=ProjectFolderCSV(
                os.path.join(root, 'paifx'),
                PerAudioItemFXControls,
            ),
            plugin_racks=ProjectFolderJSON(
                os.path.join(root, 'plugin_racks'),
                PluginRack,
            ),
            plugins=ProjectFolderJSON(
                os.path.join(root, 'plugins'),
                Plugin,
            ),
            sequences=ProjectFolderJSON(
                os.path.join(root, 'sequences'),
                Sequence,
            ),
        )

