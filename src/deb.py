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
import subprocess
import sys
import platform

f_base_dir = os.path.dirname(os.path.abspath(__file__))

print(f_base_dir)

os.chdir(f_base_dir)

def pydaw_read_file_text(a_file):
    f_handle = open(str(a_file))
    f_result = f_handle.read()
    f_handle.close()
    return f_result

def pydaw_write_file_text(a_file, a_text):
    f_handle = open(str(a_file), "w")
    f_handle.write(str(a_text))
    f_handle.close()

with open("major-version.txt") as f_file_handle:
    global_pydaw_version_string = f_file_handle.read().strip()

if "--native" in sys.argv or \
platform.machine().lower().startswith("arm"):
    f_target = "native_src"
else:
    f_target = "pydaw_src"

f_build_cmd = (
    'make clean && make {} && make '
    'DESTDIR="{}/../ubuntu/debian" install').format(f_target, f_base_dir)

f_version_file = "{}/minor-version.txt".format(f_base_dir)

f_short_name = global_pydaw_version_string
f_arch = subprocess.getoutput("dpkg --print-architecture").strip()

os.system("rm -rf ../ubuntu/debian/usr")
os.system("mkdir -p ../ubuntu/debian/usr")
os.system('find ./../ubuntu/debian -type f -name *~  -exec rm -f {} \\;')
os.system('find ./../ubuntu/debian -type f -name *.pyc  -exec rm -f {} \\;')
os.system('find ./../ubuntu/debian -type f -name core  -exec rm -f {} \\;')

f_makefile_exit_code = os.system(f_build_cmd)

if f_makefile_exit_code != 0:
    print("Makefile exited abnormally with exit code {}, "
          "see output for error messages.".format(f_makefile_exit_code))
    sys.exit(f_makefile_exit_code)

f_version = pydaw_read_file_text(f_version_file).strip()

if not "--default-version" in sys.argv:
    f_version_new = input("""Please enter the version number of this release.
    The format should be something like:  1.1.3-1 or 12.04-1
    Hit enter to accept the auto-generated default version number:  {}
    [version number]: """.format(f_version,))
    if f_version_new.strip() != "":
        f_version = f_version_new.strip()
        pydaw_write_file_text(f_version_file, f_version)

f_size = subprocess.getoutput(
    'du -s "{}/../ubuntu/debian/usr"'.format(f_base_dir))
f_size = f_size.replace("\t", " ")
f_size = f_size.split(" ")[0].strip()

f_debian_control = \
("Package: {}\n"
"Priority: extra\n"
"Section: sound\n"
"Installed-Size: {}\n"
"Maintainer: MusiKernel Team <musikernel@nospam.org>\n"
"Architecture: {}\n"
"Version: {}\n"
"Depends: libasound2-dev, liblo-dev, libsndfile1-dev, "
"libportmidi-dev, portaudio19-dev, libfftw3-dev, libjack0,"
"python3-pyqt5, python3-dev, python3-numpy, rubberband-cli, "
"libav-tools, lame, vorbis-tools, libqt5svg5\n"
"Provides: {}\n"
"Conflicts:\n"
"Replaces:\n"
"Description: MusiKernel is digital audio workstations (DAWs), "
"instrument and effect plugins.\n"
" MusiKernel is a powerful all-in-one suite of music production tools, "
"and a complete open source framework for developing any type of "
"audio application.\n"
"").format(f_short_name, f_size, f_arch, f_version, f_short_name)

f_debian_dir = "{}/../ubuntu/debian/DEBIAN".format(f_base_dir)

if not os.path.isdir(f_debian_dir):
    os.makedirs(f_debian_dir)

f_debian_control_path = "{}/control".format(f_debian_dir)

pydaw_write_file_text(f_debian_control_path, f_debian_control)

os.system('chmod 755 "{}"'.format(f_debian_control_path))
os.system("cd ../ubuntu/debian; find . -type f ! -regex '.*\.hg.*' !"
    " -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' "
    "| xargs md5sum > DEBIAN/md5sums")
os.system("chmod -R 755 ../ubuntu/debian/usr ; "
    "chmod 644 ../ubuntu/debian/DEBIAN/md5sums")

f_build_suffix_file = '{}/build-suffix.txt'.format(f_base_dir)
if os.path.exists(f_build_suffix_file):
    f_build_suffix = pydaw_read_file_text(f_build_suffix_file)
else:
    f_build_suffix = input("""You may enter an optional build suffix.
Usually this will be the operating system you are compiling for on this
machine, for example: ubuntu1210

Please enter a build suffix, or hit 'enter' to leave blank: """).strip()
    if f_build_suffix != "": f_build_suffix = "-" + f_build_suffix
    pydaw_write_file_text(f_build_suffix_file, f_build_suffix)

f_package_name = "{}-{}-{}{}.deb".format(
    f_short_name, f_version, f_arch, f_build_suffix)

os.system('rm -f "{}"/../ubuntu/musikernel*.deb'.format(f_base_dir))

if os.geteuid() == 0:
    f_eng_bin = '"{}"/../ubuntu/debian/usr/bin/{}-engine'.format(
        f_base_dir, global_pydaw_version_string)
    os.system('chown root {}'.format(f_eng_bin))
    os.system('chmod 4755 {}'.format(f_eng_bin))
    os.system('cd "{}"/../ubuntu && dpkg-deb --build debian &&'
        ' mv debian.deb "{}"'.format(f_base_dir,f_package_name))
else:
    print("Not running as root, using fakeroot to build Debian package.")
    os.system('cd "{}"/../ubuntu && fakeroot dpkg-deb --build '
    'debian && mv debian.deb "{}"'.format(f_base_dir, f_package_name))

if not "--keep" in sys.argv:
    print("Deleting build folder, run with --keep to not "
        "delete the build folder.")
    os.system('rm -rf "{}/../ubuntu/debian"'.format(f_base_dir))

print("Finished creating {}".format(f_package_name))
