"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

from libpydaw.translate import _

sequencer = _(
"""Click 'Menu->Show Tooltips' in the transport to disable these tooltips

This is sequencer, it consists of items, tracks and automation.
Click on the timeline at the top of the sequencer to set playback position,
or right-click the timeline to set various markers.

Tracks:

A track can be any/all of: instrument, audio, bus or send.
An item can contain MIDI data (notes, CCs, pitchbend) and/or one or
more audio files.

Items:

CTRL+click to add a new item

Select multiple items or automation points using CTRL+click+drag
(automation points only allow selecting from one track at a time)

Double click an item to open it in the item editor

The term 'unlink' means to create a new copy of the item that does not
change it's parent item when edited. (by default all items are
'ghost items' that update all items with the same name)

See the right-click context menu for additional actions and keyboard shortcuts.

Automation:

An automation point moves a control on a plugin.  The automation points are
steppy, you must smooth the points to get a continuous line by selecting
points using CTRL+drag and pressing ALT+s.

Shift+click+drag to cut/delete automation points

See the right-click context menu for additional actions and keyboard shortcuts.

""")

sequencer_item = _(
"""Right click on an item to see the various tools and actions available.
Click and drag selected to move.
SHIFT+Click to split items
CTRL+drag to copy selected items

You can glue together multiple items by selecting items and pressing CTRL+G
""")

transport = _(
"""Click 'Menu->Show Tooltips' in the transport to disable these tooltips

The MIDI controllers and audio inputs used for recording can be
configured in the dropdown

The 'Loop Mode' combobox can be used to loop a region.
""")

