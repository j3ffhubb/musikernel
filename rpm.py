#!/usr/bin/env python3
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import os
import sys
import shutil

DELETE_ME = 'src/pydaw/mkpy/__pycache__'

IS_INSTALL = "-i" in sys.argv

if IS_INSTALL:
    for f_file in os.listdir("."):
        if f_file.startswith("core."):
            print("Deleting {}".format(f_file))
            os.remove(f_file)

#these files may or may not exist, and should not be packaged
if os.path.isdir(DELETE_ME):
    print('Deleting ' + DELETE_ME)
    shutil.rmtree(DELETE_ME)

# invoke sudo at the beginning of the script so that future invokations
# will automatically work without a password
if IS_INSTALL:
    os.system("sudo true")

PYTHON_VERSION = "".join(str(x) for x in sys.version_info[:2])

orig_wd = os.path.dirname(os.path.abspath(__file__))

os.chdir(orig_wd)
os.system("./src.sh")

with open("src/major-version.txt") as f_file:
    MAJOR_VERSION = f_file.read().strip()

with open("src/minor-version.txt") as f_file:
    MINOR_VERSION = f_file.read().strip()

global_version_fedora = MINOR_VERSION.replace("-", ".")
PACKAGE_NAME = "{}-{}".format(
    MAJOR_VERSION, global_version_fedora)

global_home = os.path.expanduser("~")
rpm_build_path = os.path.join(
    global_home,
    'rpmbuild',
    "BUILD",
    MAJOR_VERSION,
)
os.system('rm -rf {}*')

if not os.path.isdir("{}/rpmbuild".format(global_home)):
    os.system("rpmdev-setuptree")

SPEC_DIR = "{}/rpmbuild/SPECS/".format(global_home)
SOURCE_DIR = "{}/rpmbuild/SOURCES/".format(global_home)

TARBALL_NAME = "{}.tar.gz".format(PACKAGE_NAME)
TARBALL_URL = ("https://github.com/j3ffhubb/musikernel/archive"
    "/{}".format(TARBALL_NAME))

os.system('cp "{}" "{}"'.format(TARBALL_NAME, SOURCE_DIR))

global_spec_file = "{}.spec".format(MAJOR_VERSION,)

if "--native" in sys.argv:
    f_native = "native"
else:
    f_native = ""

f_spec_template = \
"""
Name:           {0}
Version:        {1}

Release:        1%{{?dist}}
Summary:        Digital audio workstations, instrument and effect plugins

License:        GPLv3
URL:            http://github.com/j3ffhubb/musikernel/
Source0:        {2}

BuildRequires: \
    alsa-lib-devel \
    fftw-devel \
    gcc \
    gcc-c++ \
    liblo-devel \
    libsndfile-devel \
    portaudio-devel \
    portmidi-devel \
    python3-devel \

Requires: \
    alsa-lib-devel \
    fftw-devel \
    lame \
    liblo-devel \
    libsndfile-devel \
    portaudio-devel \
    portmidi-devel \
    python3-devel \
    python3-numpy \
    python3-qt5 \
    rubberband \
    vorbis-tools \

Recommends: \
    ffmpeg \

%define __provides_exclude_from ^%{{_usr}}/lib/{0}/.*$
%global __python %{{__python3}}

%description
MusiKernel is digital audio workstations (DAWs), instrument and effect plugins

%prep
%setup -q

%build
make {3}

%install
export DONT_STRIP=1
rm -rf $RPM_BUILD_ROOT
%make_install

%post
%preun

%files

%defattr(644, root, root)

%attr(4755, root, root) %{{_usr}}/bin/{0}-engine

%attr(755, root, root) %{{_usr}}/bin/{0}.py
%attr(755, root, root) %{{_usr}}/bin/{0}-engine-dbg
%attr(755, root, root) %{{_usr}}/bin/{0}-engine-no-root
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/scripts/pydaw_paulstretch.py
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/main.py
%attr(755, root, root) %{{_usr}}/lib/{0}/sbsms/bin/sbsms
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/scripts/project_recover.py
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_device_dialog.py

%{{_usr}}/lib/{0}/pydaw/mkengine/{0}.so
%{{_usr}}/lib/{0}/presets/MODULEX.mkp
%{{_usr}}/lib/{0}/presets/RAYV.mkp
%{{_usr}}/lib/{0}/presets/RAYV2.mkp
%{{_usr}}/lib/{0}/presets/WAYV.mkp
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/portaudio.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/portmidi.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_history.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_util.py

%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/_shared.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/abstract_plugin_ui.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/add_mul_dialog.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/additive_osc.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/adsr.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/audio_item_viewer.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/cc_mapping.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/control.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/distortion.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/eq.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/file_browser.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/file_select.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/filter.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/knob.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/lfo.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/lfo_dialog.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/master.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/modulex.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/modulex_settings.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/note_selector.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/ordered_table.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/paif.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/peak_meter.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/perc_env.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/playback_widget.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/plugin_file.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/preset_browser.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/preset_manager.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/pysound.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/ramp_env.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/rect_item.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/routing_matrix.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/sample_viewer.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/spectrum.py
%{{_usr}}/lib/{0}/pydaw/mkpy/widgets/va_osc.py

%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/staging.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/super_formant_maker.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/translate.py
%{{_usr}}/lib/{0}/major-version.txt
%{{_usr}}/lib/{0}/minor-version.txt

%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/filedragdrop.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/hardware.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/abstract.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/audio/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/audio/_shared.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/audio/fade_vol_dialog.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/audio/item.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/audio/item_context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/audio/time_pitch_dialog.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/automation.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/editor.py

%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/notes/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/notes/editor.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/notes/key.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/notes/note.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/item_editor/notes/_shared.py

%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/_shared.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/atm_point.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/atm_region.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/audio_item.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/item.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/midi_file.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/project.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/region_marker.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/seq_item.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/sequencer.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/tempo_marker.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/project/text_marker.py

%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/_shared.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/atm_context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/atm_item.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/audio_input.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/header_context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/item.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/seq.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/track.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/sequencer/transport.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/shared.py

%{{_usr}}/lib/{0}/themes/default/play_checked.svg
%{{_usr}}/lib/{0}/themes/default/rec_checked.svg
%{{_usr}}/lib/{0}/themes/default/stop_checked.svg
%{{_usr}}/lib/{0}/themes/default/draw.svg
%{{_usr}}/lib/{0}/themes/default/erase.svg
%{{_usr}}/lib/{0}/themes/default/select.svg
%{{_usr}}/lib/{0}/themes/default/slice.svg
%{{_usr}}/lib/{0}/themes/default/split.svg
%{{_usr}}/lib/{0}/themes/default/drop-down.png
%{{_usr}}/lib/{0}/themes/default/h-fader.png
%{{_usr}}/lib/{0}/themes/default/mute-off.png
%{{_usr}}/lib/{0}/themes/default/mute-on.png
%{{_usr}}/lib/{0}/themes/default/play.svg
%{{_usr}}/lib/{0}/themes/default/knob-fg.png
%{{_usr}}/lib/{0}/themes/default/knob-bg.png
%{{_usr}}/lib/{0}/themes/default/rec.svg
%{{_usr}}/lib/{0}/themes/default/record-off.png
%{{_usr}}/lib/{0}/themes/default/record-on.png
%{{_usr}}/lib/{0}/themes/default/solo-off.png
%{{_usr}}/lib/{0}/themes/default/solo-on.png
%{{_usr}}/lib/{0}/themes/default/spinbox-down.png
%{{_usr}}/lib/{0}/themes/default/spinbox-up.png
%{{_usr}}/lib/{0}/themes/default/stop.svg
%{{_usr}}/lib/{0}/themes/default/default.pytheme
%{{_usr}}/lib/{0}/themes/default/palette.json
%{{_usr}}/lib/{0}/themes/default/v-fader.png
%{{_usr}}/lib/{0}/themes/default/hide-on.png
%{{_usr}}/lib/{0}/themes/default/hide-off.png
%{{_usr}}/lib/{0}/themes/default/power-on.png
%{{_usr}}/lib/{0}/themes/default/power-off.png
%{{_usr}}/share/applications/{0}.desktop
%{{_usr}}/share/doc/{0}/copyright
%{{_usr}}/share/pixmaps/{0}.png

%{{_usr}}/lib/{0}/pydaw/mkpy/splash.png
%{{_usr}}/lib/{0}/pydaw/mkpy/mkqt.py

%{{_usr}}/lib/{0}/pydaw/mkpy/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/strings.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/scales.py

%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/euphoria.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/mk_channel.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/mk_compressor.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/mk_delay.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/mk_eq.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/mk_limiter.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/mk_vocoder.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/modulex.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/rayv2.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/sidechain_comp.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/simple_fader.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/simple_reverb.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/trigger_fx.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/wayv.py
%{{_usr}}/lib/{0}/pydaw/mkpy/plugins/xfade.py

%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/audio_inputs.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/audio_item.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/midi_events.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/project.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/routing.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/sample_graph.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/takes.py
%{{_usr}}/lib/{0}/pydaw/mkpy/glbl/mk_project/tracks.py

%{{_usr}}/lib/{0}/pydaw/mkpy/wave_edit/__init__.py

%{{_usr}}/lib/{0}/pydaw/mkpy/daw/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/daw/entrypoint.py
%{{_usr}}/lib/{0}/pydaw/mkpy/daw/osc.py
%{{_usr}}/lib/{0}/pydaw/mkpy/daw/strings.py

%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/liblo.*.so
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/wavefile/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/wavefile/libsndfile.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/wavefile/wavefile.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/backend.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/portmidi.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/portmidi_init.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/pygame.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/rtmidi.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/parser.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/ports.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/sockets.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/syx.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/__about__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/_parser_queue.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/amidi.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/rtmidi_python.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/backends/rtmidi_utils.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/frozen.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/messages/
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/midifiles/
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/py2.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/tokenizer.py
%{{_usr}}/lib/{0}/pydaw/mkpy/vendor/mido/version.py

%doc

""".format(MAJOR_VERSION, global_version_fedora,
    TARBALL_URL, f_native, PYTHON_VERSION)

f_spec_file = open(global_spec_file, "w")
f_spec_file.write(f_spec_template)
f_spec_file.close()

os.system('cp "{}" "{}"'.format(global_spec_file, SPEC_DIR))

if IS_INSTALL:
    os.system('rm -f {}-*'.format(MAJOR_VERSION))

os.chdir(SPEC_DIR)
f_rpm_result = os.system("rpmbuild -ba {}".format(global_spec_file))

if f_rpm_result:
    print("Error:  rpmbuild returned {}".format(f_rpm_result))
    exit(f_rpm_result)
else:
    pkg_name = "{}-*{}*rpm".format(
        MAJOR_VERSION, MINOR_VERSION)

    cp_cmd = "cp ~/rpmbuild/RPMS/*/{} '{}'".format(pkg_name, orig_wd)
    print(cp_cmd)
    os.system(cp_cmd)

    if IS_INSTALL:
        os.system("sudo dnf remove -y {0} '{0}-*'".format(MAJOR_VERSION))
        #os.system("sudo rpm -e {0}".format(MAJOR_VERSION))
        #os.system("sudo rpm -e {0}-debuginfo".format(MAJOR_VERSION))
        os.system("sudo rpm -ivh {}/{}".format(orig_wd, pkg_name))

