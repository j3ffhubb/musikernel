#!/bin/sh -x

#dependencies
sudo dnf install
    alsa-lib-devel \
    @development-tools \
    fedora-packager \
    ffmpeg \
    fftw-devel \
    gcc \
    gcc-c++ \
    gettext \
    git \
    lame \
    liblo-devel \
    libsndfile-devel \
    livecd-tools \
    portaudio-devel \
    portmidi-devel \
    python3-Cython
    python3-devel \
    python3-numpy \
    python3-qt5 \
    rubberband \
    spin-kickstarts \
    vorbis-tools

#system-config-kickstart

# Now run:
#
#   make clean
#   make
#
# followed by this command as root
#
#   make install

# or this command if packaging
#
#   make DESTDIR=/your/packaging/dir install
#
