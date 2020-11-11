- [**How to install**](#how-to-install)
    - [Windows](#windows)
    - [Mac OS X](#mac-os-x)
    - [Fedora](#fedora)
    - [Ubuntu](#ubuntu)

- [**How to Build**](#how-to-build)
    - [Debian and Ubuntu](#debian-and-ubuntu)
    - [Fedora](#fedora-1)
    - [All Other Linux Distros](#all-other-linux-distros)
    - [Mac OS X](#mac-os-x-1)
    - [Windows](#windows-1)


### What is MusiKernel?

MusiKernel is an all-in-one DAW and suite of instrument & effect plugins,
designed to be easy to install and use without the need for any 3rd party
software.  Simply install the package for your operating system, select your
audio and MIDI hardware, and start making music.

### How to Install

###### Linux, Windows

Download and install from [here](https://github.com/j3ffhubb/musikernel/releases/)

###### Mac OS X

[Follow the instructions here](https://github.com/j3ffhubb/homebrew-musikernel)

###### Others

See the build instructions below to compile from source

### How to Build

###### Debian and Ubuntu

```
cd [musikernel dir]/src
./ubuntu_deps.sh   # as root
make deps
make deb  # as root
cd ../ubuntu
dpkg -i musikernel[your_version].deb  # as root
```

###### Fedora

```
cd [musikernel src dir]/src
./fedora_deps.sh
cd ..
./rpm.py  # add -i to install automatically after building, or:
sudo dnf install ./musikernel[version number].rpm
```

###### All Other Linux Distros

```
# figure out the dependencies based on the Fedora or Ubuntu dependencies
cd [musikernel src dir]/src
make
# You can specify DESTDIR or PREFIX if packaging,
# the result is fully relocatable
make install
```

###### Mac OS X

Same as the install instructions

###### Windows

It's complicated...
