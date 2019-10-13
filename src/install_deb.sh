#/bin/bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root, use sudo or su" 1>&2
   exit 1
fi


if [ -e ./core ]; then
	#Delete the core file if exists, sometimes the binary won't
	#delete it and then replace with a new core
	rm -f ./core
fi

VERSION=$(cat major-version.txt)

( ./deb.py --default-version || \
(echo "
#############################################################
You may need to run 'make deps' and/or ./ubuntu_deps.sh first
#############################################################
"  \
&& false )) \
&& dpkg -i ../ubuntu/$VERSION*.deb

