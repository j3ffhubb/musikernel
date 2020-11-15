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
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_paulstretch.py
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/musikernel.py
%attr(755, root, root) %{{_usr}}/lib/{0}/sbsms/bin/sbsms
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/project_recover.py
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_device_dialog.py

%{{_usr}}/lib/{0}/pydaw/mkengine/{0}.so
%{{_usr}}/lib/{0}/presets/MODULEX.mkp
%{{_usr}}/lib/{0}/presets/RAYV.mkp
%{{_usr}}/lib/{0}/presets/RAYV2.mkp
%{{_usr}}/lib/{0}/presets/WAYV.mkp
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/liblo.*.so
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/portaudio.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/portmidi.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_history.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_util.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/pydaw_widgets.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/staging.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/super_formant_maker.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/translate.py
%{{_usr}}/lib/{0}/major-version.txt
%{{_usr}}/lib/{0}/minor-version.txt

%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/filedragdrop.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/hardware.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/abstract.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/audio/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/audio/_shared.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/audio/fade_vol_dialog.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/audio/item_context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/audio/time_pitch_dialog.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/automation.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/editor.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/item_editor/notes.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/__init__.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/_shared.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/atm_context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/audio_input.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/header_context_menu.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/track.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/sequencer/transport.py
%{{_usr}}/lib/musikernel3/pydaw/mkpy/libdawnext/shared.py

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
%{{_usr}}/lib/{0}/pydaw/mkpy/wavefile/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/wavefile/libsndfile.py
%{{_usr}}/lib/{0}/pydaw/mkpy/wavefile/wavefile.py

%{{_usr}}/lib/{0}/pydaw/mkpy/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/strings.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libpydaw/scales.py

%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/euphoria.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/modulex.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/rayv2.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/wayv.py

%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/mk_delay.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/mk_eq.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/simple_fader.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/simple_reverb.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/trigger_fx.py

%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/sidechain_comp.py

%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/mk_channel.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/xfade.py

%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/mk_compressor.py

%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/mk_vocoder.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mkplugins/mk_limiter.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libmk/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libmk/mk_project.py
%{{_usr}}/lib/{0}/pydaw/mkpy/wavenext.py

%{{_usr}}/lib/{0}/pydaw/mkpy/dawnext.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libdawnext/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libdawnext/osc.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libdawnext/project.py
%{{_usr}}/lib/{0}/pydaw/mkpy/libdawnext/strings.py

%{{_usr}}/lib/{0}/pydaw/mkpy/mido/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/backends/__init__.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/backends/backend.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/backends/portmidi.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/backends/portmidi_init.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/backends/pygame.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/backends/rtmidi.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/backends/test_backend.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/messages.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/midifiles.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/midifiles_meta.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/parser.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/ports.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/sockets.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/syx.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/test_messages.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/test_midifiles.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/test_parser.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/test_ports.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/test_sockets.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/test_string_format.py
%{{_usr}}/lib/{0}/pydaw/mkpy/mido/test_syx.py

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

