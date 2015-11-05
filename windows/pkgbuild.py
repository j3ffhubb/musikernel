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

import hashlib
import os

PKGBUILD_TEMPLATE = """# Maintainer: Jeff Hubbard <musikernel@gmail.com>

_realname={major_version}
pkgname="${{MINGW_PACKAGE_PREFIX}}-${{_realname}}"
pkgver={minor_version}
pkgrel=1
pkgdesc="DAWs/hosts, instrument and effect plugins, and a new approach to audio development. (mingw-w64)"
arch=('any')
url="http://www.github.com/j3ffhubb/musikernel"
license=("GPL")
makedepends=("${{MINGW_PACKAGE_PREFIX}}-gcc" "${{MINGW_PACKAGE_PREFIX}}-pkg-config")
depends=("${{MINGW_PACKAGE_PREFIX}}-gcc-libs"
         "${{MINGW_PACKAGE_PREFIX}}-rubberband"
         "${{MINGW_PACKAGE_PREFIX}}-portaudio"
         "${{MINGW_PACKAGE_PREFIX}}-portmidi"
         "${{MINGW_PACKAGE_PREFIX}}-libsndfile"
         "${{MINGW_PACKAGE_PREFIX}}-fftw"
         "${{MINGW_PACKAGE_PREFIX}}-python3-numpy"
         "${{MINGW_PACKAGE_PREFIX}}-libvorbis"
         "${{MINGW_PACKAGE_PREFIX}}-python3-pyqt5")
source=("https://github.com/j3ffhubb/musikernel/archive/musikernel1.zip")
md5sums=('{zip_md5sum}')

build() {{
  #export PATH="${{MINGW_PREFIX}}:$PATH"
  cd "${{srcdir}}/musikernel-musikernel1/src"
  CC=${{MINGW_PREFIX}}/bin/gcc.exe make mingw
}}

package() {{
  #export PATH="${{MINGW_PREFIX}}:$PATH"
  cd "${{srcdir}}/musikernel-musikernel1/src"
  make PREFIX=${{MINGW_PREFIX}} DESTDIR="$pkgdir" install_mingw
}}

"""

CWD = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(CWD, "..", "src", "minor-version.txt")) as fh:
    MINOR_VERSION = fh.read().strip()

with open(os.path.join(CWD, "..", "src", "major-version.txt")) as fh:
    MAJOR_VERSION = fh.read().strip()

file_name = os.path.join(CWD, "musikernel1.zip")

with open(file_name, "rb") as fh:
    MD5_ZIP = hashlib.md5(fh.read()).hexdigest()

PKGBUILD = os.path.join(CWD, "PKGBUILD")

with open(PKGBUILD, "w") as fh:
    tmp_str = PKGBUILD_TEMPLATE.format(
        major_version=MAJOR_VERSION, minor_version=MINOR_VERSION,
        zip_md5sum=MD5_ZIP)
    fh.write(tmp_str)

