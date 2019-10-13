#!/bin/bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root, use sudo or su" 1>&2
   exit 1
fi

apt-get update

apt-get install -y \
    autoconf \
    automake \
    build-essential \
    debhelper \
    dh-make \
    ffmpeg \
    g++ \
    gcc \
    gdb \
    genisoimage \
    gettext \
    lame \
    libasound2-dev \
    libfftw3-dev \
    liblo-dev \
    libportmidi-dev \
    libsbsms-dev \
    libsndfile1-dev \
    libtool \
    portaudio19-dev \
    python3 \
    python3-dev \
    python3-numpy \
    python3-pyqt5 \
    rubberband-cli
    squashfs-tools \
    vorbis-tools \

