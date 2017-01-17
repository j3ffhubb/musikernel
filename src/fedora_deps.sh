#dependencies
sudo dnf install python3-qt5 gcc alsa-lib-devel liblo-devel \
libsndfile-devel gcc-c++ git python3-numpy \
fftw-devel portmidi-devel portaudio-devel rubberband python3-devel \
@development-tools fedora-packager livecd-tools spin-kickstarts \
vorbis-tools gettext
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
