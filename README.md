- **Twitter** - Follow @musikernel for the latest news and release announcements
- [**KVR** - See screenshots](http://www.kvraudio.com/product/musikernel-by-musikernel)
- [**Youtube** - Watch MusiKernel tutorial videos](https://www.youtube.com/channel/UCf_PgsosvLpxkN6bff9NESA/videos)
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
			

###What is MusiKernel?

MusiKernel is an all-in-one DAW and suite of instrument & effect plugins, designed to be easy to install and use without the need for any 3rd party software.  Simply install the package for your operating system, select your audio and MIDI hardware, and start making music.

###How to Install

######Windows

Download and run the Windows installer [here](https://github.com/j3ffhubb/musikernel/releases/) (64 bit only)

######Mac OS X

[Follow the instructions here](https://github.com/j3ffhubb/homebrew-musikernel)

######Fedora

From [here](https://copr.fedoraproject.org/coprs/musikernel/musikernel/)

```
sudo dnf copr enable -y musikernel/musikernel
sudo dnf install -y musikernel1
```

RPM packages can be downloaded directly from [here](https://github.com/j3ffhubb/musikernel/releases)

######Ubuntu

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

######All Other Linux Distros

```
# figure out the dependencies based on the Fedora or Ubuntu dependencies
cd [musikernel src dir]/src
make
# You can specify DESTDIR or PREFIX if packaging,
# the result is fully relocatable
make install
```

######Mac OS X

Same as the install instructions

######Windows

It's complicated...
