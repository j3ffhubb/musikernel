#!/usr/bin/make -f

PREFIX ?= /usr
DESTDIR ?=
CC  ?= gcc
PYDAW_VERSION = $(shell cat ../major-version.txt)
PYDAW_FILE = $(PYDAW_VERSION)_render
PYDAW_DBG = $(PYDAW_FILE)-dbg
CACHE_LINE_SIZE = 64  # $(shell getconf LEVEL1_DCACHE_LINESIZE)

#Default flags are mostly x86 specific
PLAT_FLAGS     ?= -mstackrealign -msse -msse2 -msse3 -mfpmath=sse \
-mtune=generic

#Flags that LLVM/Clang complain about
OPTIMIZE_FLAGS ?= -fprefetch-loop-arrays -floop-optimize \
-fsingle-precision-constant -fstrength-reduce -finline-functions

BASE_FLAGS     = -std=gnu89 $(OPTIMIZE_FLAGS) -ffast-math -funroll-loops \
 -Wall -fstrict-aliasing -Wstrict-aliasing -fno-stack-protector \
-DCACHE_LINE_SIZE=$(CACHE_LINE_SIZE)


BUILD_CFLAGS   = $(PLAT_FLAGS) $(BASE_FLAGS) $(CFLAGS)
LINK_CFLAGS    = -pthread -lm -fno-stack-protector \
$(shell pkg-config --libs sndfile fftw3f) $(LDFLAGS)

C_OBJS   = main.o

# --------------------------------------------------------------

all:
	make debug
	make release

debug:
	rm *.o || true
	make CFLAGS+=" -O0 -gdwarf-3 " $(PYDAW_FILE)
	mv $(PYDAW_FILE) $(PYDAW_DBG)

release:
	rm *.o || true
	make CFLAGS+=" -O2 " $(PYDAW_FILE)

gprof:
	make CFLAGS+=" -O2 -pg " LDFLAGS+=" -pg "

$(PYDAW_FILE): $(C_OBJS)
	$(CC) $(C_OBJS) $(LINK_CFLAGS) -o $@

# --------------------------------------------------------------

.c.o:
	$(CC) -c $< $(BUILD_CFLAGS) -o $@

# --------------------------------------------------------------

clean:
	rm -f *.o *.so $(PYDAW_FILE) $(PYDAW_DBG) *.pymap *.wav \
	profile.txt gmon.out

install:
	install -d $(DESTDIR)/$(PREFIX)
	install -d $(DESTDIR)/$(PREFIX)/bin
	install -s -m 755 $(PYDAW_FILE) $(DESTDIR)/$(PREFIX)/bin
	install -m 755 $(PYDAW_DBG) $(DESTDIR)/$(PREFIX)/bin

