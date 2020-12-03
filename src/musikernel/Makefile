#!/usr/bin/make -f

CC ?= gcc

PREFIX ?= /usr
VERSION = $(shell cat ../major-version.txt)

#Default flags are mostly x86 specific
PLAT_FLAGS     ?= -mstackrealign -msse -msse2 -msse3 -mfpmath=sse \
-mtune=generic

CACHE_LINE_SIZE = $(shell getconf LEVEL1_DCACHE_LINESIZE || echo 64)

#Flags that LLVM/Clang complain about
OPTIMIZE_FLAGS ?= -fprefetch-loop-arrays -floop-optimize \
-fsingle-precision-constant -fstrength-reduce -finline-functions

BASE_FLAGS     = $(OPTIMIZE_FLAGS) -ffast-math -funroll-loops -Wall \
-fstrict-aliasing -Wstrict-aliasing -fno-stack-protector \
-DCACHE_LINE_SIZE=$(CACHE_LINE_SIZE) -z now

BUILD_CFLAGS   = -std=gnu89 $(PLAT_FLAGS) $(BASE_FLAGS) $(CFLAGS)
MATH_LIB_FLAG ?= -lm
ALSA_FLAG ?= $(shell pkg-config --libs alsa)
LIBLO_FLAG ?= $(shell pkg-config --libs liblo)
PORTMIDI_FLAG ?= -lportmidi

PLAT_LINK_CFLAGS ?= $(ALSA_FLAG) $(LIBLO_FLAG)

LINK_CFLAGS  = -lpthread $(PORTMIDI_FLAG) -lportaudio $(LDFLAGS) \
$(shell pkg-config --libs sndfile fftw3f fftw3) $(MATH_LIB_FLAG) \
$(PLAT_LINK_CFLAGS)

C_OBJS   = src/main.o

# --------------------------------------------------------------

all:
	make lib
	make dbg
	make eng

dbg:
	rm -f src/*.o $(VERSION)-engine $(VERSION)-engine-dbg ; echo
	make CFLAGS+=" -O0 -g -gdwarf-3 " $(VERSION)-engine
	mv $(VERSION)-engine $(VERSION)-engine-dbg

gprof:
	make CFLAGS+=" -O2 -pg " LDFLAGS+=" -pg "

eng:
	rm -f src/*.o $(VERSION)-engine ; echo
	rm -f $(VERSION)-engine src/*.o
	make CFLAGS+=" -O2 " $(VERSION)-engine

lib:
	rm -f src/*.o $(VERSION)-engine ; echo
	make CFLAGS+=" -O2 -fPIC -DMK_DLL " \
		LDFLAGS+=" -shared " $(VERSION)-engine
	mv $(VERSION)-engine.exe $(VERSION).dll || \
	mv $(VERSION)-engine $(VERSION).so

mingw:
	make lib
	make eng

mac_osx:
	OPTIMIZE_FLAGS= CC=clang PREFIX=/usr/local make lib
	mv $(VERSION).so $(VERSION).dylib
	make eng

# --------------------------------------------------------------

$(VERSION)-engine: $(C_OBJS)
	$(CC) $(C_OBJS) $(LINK_CFLAGS) -o $@

# --------------------------------------------------------------

.c.o:
	$(CC) -c $< $(BUILD_CFLAGS) -o $@

# --------------------------------------------------------------
clean_pyc:
	find . -name __pycache__ -exec rm -rf {} \; || true

install_non_linux: clean_pyc
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 $(VERSION).py $(DESTDIR)$(PREFIX)/bin
	install -s -m 755 $(VERSION)-engine $(DESTDIR)$(PREFIX)/bin
	install -d $(DESTDIR)$(PREFIX)/lib/$(VERSION)
	install -d $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel
	cp -r sgui $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel
	cp -r sglib $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel
	install -d $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel/mkengine
	install -m 555 $(VERSION).dll \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel/mkengine || \
	install -m 555 $(VERSION).so \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel/mkengine || \
	install -m 555 $(VERSION).dylib \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel/mkengine
	cp -r files/themes $(DESTDIR)$(PREFIX)/lib/$(VERSION)
	cp -r files/presets $(DESTDIR)$(PREFIX)/lib/$(VERSION)
	cp -r files/share $(DESTDIR)$(PREFIX)
	install -m 644 ../major-version.txt \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)
	install -m 644 ../minor-version.txt \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)
	#Add the Git revision to the version.txt file if possible
	@       if [ -e /usr/bin/git ] && [ -e ../../.git ]; then \
                        echo "\n\nGit: " `/usr/bin/git rev-parse HEAD` >> \
			$(DESTDIR)$(PREFIX)/lib/$(VERSION)/minor-version.txt ; \
                fi

install: clean_pyc
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 $(VERSION).py $(DESTDIR)$(PREFIX)/bin
	install -d $(DESTDIR)$(PREFIX)/lib/$(VERSION)
	install -d $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel
	install -m 755 $(VERSION)-engine-dbg $(DESTDIR)$(PREFIX)/bin
	install -s -m 4755 $(VERSION)-engine $(DESTDIR)$(PREFIX)/bin
	install -s -m 755 $(VERSION)-engine \
	$(DESTDIR)$(PREFIX)/bin/$(VERSION)-engine-no-root
	cp -r sgui $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel
	cp -r sglib $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel
	install -d $(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel/mkengine
	install -m 555 $(VERSION).dll \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel/mkengine || \
	install -m 555 $(VERSION).so \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)/musikernel/mkengine
	cp -r files/themes $(DESTDIR)$(PREFIX)/lib/$(VERSION)
	cp -r files/presets $(DESTDIR)$(PREFIX)/lib/$(VERSION)
	cp -r files/share $(DESTDIR)$(PREFIX)
	install -m 644 ../major-version.txt \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)
	install -m 644 ../minor-version.txt \
		$(DESTDIR)$(PREFIX)/lib/$(VERSION)
	#Add the Git revision to the version.txt file if possible
	@       if [ -e /usr/bin/git ] && [ -e ../../.git ]; then \
                        echo "\n\nGit: " `/usr/bin/git rev-parse HEAD` >> \
			$(DESTDIR)$(PREFIX)/lib/$(VERSION)/minor-version.txt ; \
                fi

clean:
	rm -f src/*.o *.so $(VERSION)-engine* core sgui/core  \
	*.pyo *.pyc */*.pyo */*.pyc */*/*.pyo */*/*.pyc \
	*~ */*~ */*/*~ */*/*/*~
	rm -rf htmlcov/

