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
import argparse

if not os.getuid() == 0:
    print("Error, this must be run as root.  Use su or sudo")
    exit(1)


parser = argparse.ArgumentParser()
parser.add_argument(
    "--de", help="Select the desktop environment, choices are:\n"
    "--de=gnome|kde|lxde|xfce|mate", default="kde")
args = parser.parse_args()

if args.de == "gnome":
    ks_file = "/usr/share/spin-kickstarts/fedora-live-desktop.ks"
    de_label = "Gnome"
elif args.de == "lxde":
    ks_file = "/usr/share/spin-kickstarts/fedora-live-lxde.ks"
    de_label = "LXDE"
elif args.de == "xfce":
    ks_file = "/usr/share/spin-kickstarts/fedora-live-xfce.ks"
    de_label = "XFCE"
elif args.de == "kde":
    ks_file = "/usr/share/spin-kickstarts/fedora-live-kde.ks"
    de_label = "KDE"
elif args.de == "mate":
    ks_file = "/usr/share/spin-kickstarts/fedora-live-mate-compiz.ks"
    de_label = "Mate"
else:
    print("Invalid --de={}".format(args.de))
    parser.print_help()
    exit(1)

if not os.path.exists(ks_file):
    print(
        "{} not found, please run "
        "'sudo dnf install spin-kickstarts'".format(
            ks_file,
        )
    )
    exit(1)

os.system("setenforce 0")

pydaw_version_file = open("../src/major-version.txt")
global_pydaw_version = pydaw_version_file.read().strip()
pydaw_version_file.close()

pydaw_version_file = open("../src/minor-version.txt")
pydaw_version = pydaw_version_file.read().strip()
pydaw_version_file.close()

pydaw_rpm_file = None

global_rpm_dir = os.path.abspath("{}/..".format(os.getcwd()))

pydaw_rpm_file = None

for f_rpm_file in os.listdir(global_rpm_dir):
    if f_rpm_file.startswith(global_pydaw_version) and \
    f_rpm_file.endswith(".rpm") and \
    pydaw_version in f_rpm_file and \
    "debuginfo" not in f_rpm_file:
        pydaw_rpm_file = f_rpm_file
        print("Using {}".format(pydaw_rpm_file))

if pydaw_rpm_file is None:
    print("No MusiKernel .rpm files with current version {} found in {}, \n"
        "please run the following commands before running this script:".format(
        pydaw_version, global_rpm_dir))
    print("\n\ncd ..")
    print("./rpm.py")
    print("cd fedora")
    exit(1)

rpm_file = open("{}/{}".format(global_rpm_dir, pydaw_rpm_file), "rb")
rpm_bytes = rpm_file.read()
rpm_file.close()

kickstart_template = \
"""#kickstart file for PyDAW-OS-Fedora, generated by {}

%include {}

%packages

#MusiKernel Dependencies
python3-qt5
alsa-lib-devel
liblo-devel
libsndfile-devel
python3-numpy
fftw-devel
portaudio-devel
portmidi-devel
rubberband
python3-devel
vorbis-tools

#Not actually dependencies, but giving people with Firewire devices
#a fighting chance of being able to use the live DVD/USB after an excessive
#amount of configuration
ffado
qjackctl

%end

%post

# I know, I should configure SELinux to only look the other
# way for MusiKernel instead of disabling it, grumble, grumble...
sed -i s/SELINUX=enforcing/SELINUX=disabled/g /etc/selinux/config

%end

%post --interpreter /usr/bin/python3

# embed the PyDAW rpm file into the kickstart template, to subvert the need
# to setup a Yum respository somewhere on the internet, or worry about DNS

import os

my_rpm_file = open("/tmp/pydaw.rpm", "wb")
my_rpm_file.write({})
my_rpm_file.close()

os.system("rpm -ivh /tmp/pydaw.rpm")

%end
""".format(os.path.abspath(__file__), ks_file, str(rpm_bytes))

kickstart_file = open("kickstart.ks", "w")
kickstart_file.write(kickstart_template)
kickstart_file.close()

#TODO:  Maybe use --base-on=live-cd.iso and then run yum update ?
#Or automate a chroot into tmpdir afterwards?

kickstart_command = \
"""livecd-creator --verbose \
--config=./kickstart.ks \
--fslabel=MusiKernel-OS-Fedora \
--cache=cache/live """
#--tmpdir=tmpdir """
#--nocleanup """

os.system(kickstart_command)

os.system('mv MusiKernel-OS-Fedora.iso MusiKernel-OS-Fedora-{}-{}.iso'.format(
    de_label, pydaw_version))

#os.system("setenforce 1")
