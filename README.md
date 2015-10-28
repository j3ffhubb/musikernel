######Important

The master branch is the development branch for the unreleased MusiKernel v2.
If you're looking for the code for the released MusiKernel v1, use the
"musikernel1" branch.

- **Twitter** - Follow @musikernel for the latest news and release announcements
- [**KVR** - See screenshots](http://www.kvraudio.com/product/musikernel-by-musikernel)
- [**Youtube** - Watch MusiKernel tutorial videos](https://www.youtube.com/channel/UCf_PgsosvLpxkN6bff9NESA/videos)
- [**How to install**](#how-to-install)
			- [Windows](#windows)
			- [Fedora](#fedora)
			- [Ubuntu](#ubuntu)
- [**How to Build**](#how-to-build)
			- [Debian and Ubuntu](#debian-and-ubuntu)
			- [Fedora](#fedora-1)
			- [All Other Linux Distros](#all-others)
- [**What is MusiKernel?**](#what-is-musikernel)

###How to Install

######Windows

Download and run the Windows installer [here](https://github.com/j3ffhubb/musikernel/releases/) (64 bit only)

######Fedora

From [here](https://copr.fedoraproject.org/coprs/musikernel/musikernel/)

```
sudo dnf copr enable -y musikernel/musikernel
sudo dnf install -y musikernel1
```

RPM packages can be downloaded directly from [here](https://github.com/j3ffhubb/musikernel/releases)

######Ubuntu

Import the MusiKernel public GPG key (prevents apt-get from complaining about verification)

`sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 0D94797D691048C1`

Follow the instructions in the "Adding this PPA to your system" section [here](https://launchpad.net/~musikernel/+archive/ubuntu/musikernel1), then:

`sudo apt-get update && sudo apt-get install musikernel1`

Ubuntu packages can be downloaded directly from [here](https://github.com/j3ffhubb/musikernel/releases)

###How to Build

######Debian and Ubuntu

```
cd [musikernel dir]/src
./ubuntu_deps.sh   # as root
make deps
make deb  # as root
cd ../ubuntu
dpkg -i musikernel[your_version].deb  # as root
```

######Fedora

```
cd [musikernel src dir]/src
./fedora_deps.sh
make rpm
cd ~/rpmbuild/RPMS/[your arch]
sudo yum localinstall musikernel[version number].rpm
```

######All Others

```
# figure out the dependencies based on the Fedora or Ubuntu dependencies
cd [musikernel src dir]/src
make
# You can specify DESTDIR or PREFIX if packaging,
# the result is fully relocatable
make install
```

###What is MusiKernel?

MusiKernel is DAWs/hosts, instrument & effect plugins, and a new approach to developing an audio software ecosystem.  By promoting centralized development and quality control with maximal code re-use, MusiKernel aims to avoid many of the compatibility problems that have plagued traditional host/plugin architectures.

MusiKernel's UI is powered entirely by Python3 and PyQt5.  MusiKernel's audio/MIDI engine is written in C (C89 dialect) for maximum performance and low memory usage.

