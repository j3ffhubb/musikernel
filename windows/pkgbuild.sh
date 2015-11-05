#!/bin/sh

rm *.zip
wget https://github.com/j3ffhubb/musikernel/archive/musikernel1.zip
python3 pkgbuild.py
rm *.tar.xz *.exe *.zip
dos2unix PKGBUILD  #why the fuck this is necessary I don't understand
makepkg-mingw -Cfs

echo "Now run nsis.py from outside of MSYS2 using Windows-native Python"

