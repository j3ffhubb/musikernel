"""
A (currently) limited wrapper around the library libsndfile by Erik Castro de Lopo

http://www.mega-nerd.com/libsndfile/

licensed under the LGPL
(http://www.gnu.org/copyleft/lesser.html)

All sounds formats supported by libsndfile are available and a class interface
is implemented with some helper methods.

Requires numpy and ctypes. Tested under windows only.
"""

import sys
import ctypes as ct
import numpy as np

if sys.platform == "win32" :
    dllName = 'libsndfile-1'
elif "linux" in sys.platform:
    dllName = 'libsndfile.so'
elif "cygwin" in sys.platform:
    dllName = 'libsndfile-1.dll'
elif "darwin" in sys.platform:
    dllName = 'libsndfile.dylib'
else :
    dllName = 'libsndfile'

_lib=None
try:
    from ctypes.util import find_library
    #does the user already have libsamplerate installed?
    if sys.platform == 'win32' :
        dllPath = find_library(dllName)
    else :
        dllPath = dllName
    _lib = ct.CDLL(dllPath)
except:
    try:
        #if not, get the dll installed with the wrapper
        import os
        dllPath = os.path.dirname(os.path.abspath(__file__))
        _lib = ct.CDLL(os.path.join(dllPath, dllName))
    except:
        raise Exception("could not import libsndfile dll, make sure the dll '%s' is in the path"%(dllName))

_lib.sf_version_string.restype = ct.c_char_p
_lib.sf_version_string.argtypes = None
#print "libsndfile loaded version:", _lib.sf_version_string()



class FILE_FORMATS():
    SF_FORMAT_WAV        = 0x010000    # Microsoft WAV format (little endian default).
    SF_FORMAT_AIFF       = 0x020000    # Apple/SGI AIFF format (big endian).
    SF_FORMAT_AU         = 0x030000    # Sun/NeXT AU format (big endian).
    SF_FORMAT_RAW        = 0x040000    # RAW PCM data.
    SF_FORMAT_PAF        = 0x050000    # Ensoniq PARIS file format.
    SF_FORMAT_SVX        = 0x060000    # Amiga IFF / SVX8 / SV16 format.
    SF_FORMAT_NIST       = 0x070000    # Sphere NIST format.
    SF_FORMAT_VOC        = 0x080000    # VOC files.
    SF_FORMAT_IRCAM      = 0x0A0000    # Berkeley/IRCAM/CARL
    SF_FORMAT_W64        = 0x0B0000    # Sonic Foundry's 64 bit RIFF/WAV
    SF_FORMAT_MAT4       = 0x0C0000    # Matlab (tm) V4.2 / GNU Octave 2.0
    SF_FORMAT_MAT5       = 0x0D0000    # Matlab (tm) V5.0 / GNU Octave 2.1
    SF_FORMAT_PVF        = 0x0E0000    # Portable Voice Format
    SF_FORMAT_XI         = 0x0F0000    # Fasttracker 2 Extended Instrument
    SF_FORMAT_HTK        = 0x100000    # HMM Tool Kit format
    SF_FORMAT_SDS        = 0x110000    # Midi Sample Dump Standard
    SF_FORMAT_AVR        = 0x120000    # Audio Visual Research
    SF_FORMAT_WAVEX      = 0x130000    # MS WAVE with WAVEFORMATEX
    SF_FORMAT_SD2        = 0x160000    # Sound Designer 2
    SF_FORMAT_FLAC       = 0x170000    # FLAC lossless file format
    SF_FORMAT_CAF        = 0x180000    # Core Audio File format
    SF_FORMAT_WVE        = 0x190000    # Psion WVE format
    SF_FORMAT_OGG        = 0x200000    # Xiph OGG container
    SF_FORMAT_MPC2K      = 0x210000    # Akai MPC 2000 sampler
    SF_FORMAT_RF64       = 0x220000    # RF64 WAV file

    # Subtypes from here on.

    SF_FORMAT_PCM_S8     = 0x0001    # Signed 8 bit data
    SF_FORMAT_PCM_16     = 0x0002    # Signed 16 bit data
    SF_FORMAT_PCM_24     = 0x0003    # Signed 24 bit data
    SF_FORMAT_PCM_32     = 0x0004    # Signed 32 bit data

    SF_FORMAT_PCM_U8     = 0x0005    # Unsigned 8 bit data (WAV and RAW only)

    SF_FORMAT_FLOAT      = 0x0006    # 32 bit float data
    SF_FORMAT_DOUBLE     = 0x0007    # 64 bit float data

    SF_FORMAT_ULAW       = 0x0010    # U-Law encoded.
    SF_FORMAT_ALAW       = 0x0011    # A-Law encoded.
    SF_FORMAT_IMA_ADPCM  = 0x0012    # IMA ADPCM.
    SF_FORMAT_MS_ADPCM   = 0x0013    # Microsoft ADPCM.

    SF_FORMAT_GSM610     = 0x0020    # GSM 6.10 encoding.
    SF_FORMAT_VOX_ADPCM  = 0x0021    # OKI / Dialogix ADPCM

    SF_FORMAT_G721_32    = 0x0030    # 32kbs G721 ADPCM encoding.
    SF_FORMAT_G723_24    = 0x0031    # 24kbs G723 ADPCM encoding.
    SF_FORMAT_G723_40    = 0x0032    # 40kbs G723 ADPCM encoding.

    SF_FORMAT_DWVW_12    = 0x0040    # 12 bit Delta Width Variable Word encoding.
    SF_FORMAT_DWVW_16    = 0x0041    # 16 bit Delta Width Variable Word encoding.
    SF_FORMAT_DWVW_24    = 0x0042    # 24 bit Delta Width Variable Word encoding.
    SF_FORMAT_DWVW_N     = 0x0043    # N bit Delta Width Variable Word encoding.

    SF_FORMAT_DPCM_8     = 0x0050    # 8 bit differential PCM (XI only)
    SF_FORMAT_DPCM_16    = 0x0051    # 16 bit differential PCM (XI only)

    SF_FORMAT_VORBIS     = 0x0060    # Xiph Vorbis encoding.

    # Endian-ness options.

    SF_ENDIAN_FILE       = 0x00000000    # Default file endian-ness.
    SF_ENDIAN_LITTLE     = 0x10000000    # Force little endian-ness.
    SF_ENDIAN_BIG        = 0x20000000    # Force big endian-ness.
    SF_ENDIAN_CPU        = 0x30000000    # Force CPU endian-ness.

    SF_FORMAT_SUBMASK    = 0x0000FFFF
    SF_FORMAT_TYPEMASK   = 0x0FFF0000
    SF_FORMAT_ENDMASK    = 0x30000000


# String types that can be set and read from files. Not all file types
# support this and even the file types which support one, may not support
# all string types.
class FILE_STRINGS():
    SF_STR_TITLE     = 0x01
    SF_STR_COPYRIGHT = 0x02
    SF_STR_SOFTWARE  = 0x03
    SF_STR_ARTIST    = 0x04
    SF_STR_COMMENT   = 0x05
    SF_STR_DATE      = 0x06
    SF_STR_ALBUM     = 0x07
    SF_STR_LICENSE   = 0x08

# Public error values. These are guaranteed to remain unchanged for the duration
# of the library major version number.
# There are also a large number of private error numbers which are internal to
# the library which can change at any time.
SF_ERR_NO_ERROR             = 0
SF_ERR_UNRECOGNISED_FORMAT  = 1
SF_ERR_SYSTEM               = 2
SF_ERR_MALFORMED_FILE       = 3
SF_ERR_UNSUPPORTED_ENCODING = 4


#other definitions :
sf_count_t = ct.c_int64


#structs:
class SF_INFO(ct.Structure):
    _fields_ = [
        ("frames", sf_count_t), #Used to be called samples.  Changed to avoid confusion.
        ("samplerate", ct.c_int),
        ("channels", ct.c_int),
        ("format", ct.c_int),
        ("sections", ct.c_int),
        ("seekable", ct.c_int)
    ]

def __init_lib_methods():
    SNDFILE = ct.c_void_p

    #SNDFILE*     sf_open        (const char *path, int mode, SF_INFO *sfinfo) ;
    _lib.sf_open.restype = SNDFILE
    _lib.sf_open.argtypes = [ct.c_char_p, ct.c_int, ct.POINTER(SF_INFO)]

    #int        sf_error        (SNDFILE *sndfile) ;
    _lib.sf_error.restype = ct.c_int
    _lib.sf_error.argtypes = [SNDFILE]

    #const char* sf_strerror (SNDFILE *sndfile) ;
    _lib.sf_strerror.restype = ct.c_char_p
    _lib.sf_strerror.argtypes = [SNDFILE]

    #const char* sf_error_number (int ) ;
    _lib.sf_error_number.restype = ct.c_char_p
    _lib.sf_error_number.argtypes = [ct.c_int]

    #int        sf_format_check    (const SF_INFO *info) ;
    _lib.sf_format_check.restype = ct.c_int
    _lib.sf_format_check.argtypes = [ct.POINTER(SF_INFO)]

    #sf_count_t    sf_seek         (SNDFILE *sndfile, sf_count_t frames, int whence) ;
    _lib.sf_seek.restype = sf_count_t
    _lib.sf_seek.argtypes = [SNDFILE, sf_count_t, ct.c_int]

    #const char* sf_get_string (SNDFILE *sndfile, int str_type) ;
    _lib.sf_get_string.restype = ct.c_char_p
    _lib.sf_get_string.argtypes = [SNDFILE, ct.c_int]

    #int         sf_set_string    (SNDFILE *sndfile, int str_type, const char* str) ;
    #TODO
    _lib.sf_set_string.restype = ct.c_int
    _lib.sf_set_string.argtypes = [SNDFILE, ct.c_int, ct.c_char_p]

    #sf_count_t    sf_read_raw        (SNDFILE *sndfile, void *ptr, sf_count_t bytes) ;
    _lib.sf_read_raw.restype = sf_count_t
    _lib.sf_read_raw.argtypes = [SNDFILE, ct.c_void_p, sf_count_t]

    # Functions for reading and writing the data chunk in terms of frames.
    # The number of items actually read/written = frames * number of channels.
    #     sf_xxxx_raw        read/writes the raw data bytes from/to the file
    #     sf_xxxx_short    passes data in the native short format
    #     sf_xxxx_int        passes data in the native int format
    #     sf_xxxx_float    passes data in the native float format
    #     sf_xxxx_double    passes data in the native double format
    # All of these read/write function return number of frames read/written.
    #sf_count_t    sf_readf_float    (SNDFILE *sndfile, float *ptr, sf_count_t frames) ;
    _lib.sf_read_float.restype = sf_count_t
    _lib.sf_read_float.argtypes = [SNDFILE, ct.POINTER(ct.c_float), sf_count_t]
    _lib.sf_read_double.restype = sf_count_t
    _lib.sf_read_double.argtypes = [SNDFILE, ct.POINTER(ct.c_double), sf_count_t]
    _lib.sf_read_short.restype = sf_count_t
    _lib.sf_read_short.argtypes = [SNDFILE, ct.POINTER(ct.c_short), sf_count_t]
    _lib.sf_read_int.restype = sf_count_t
    _lib.sf_read_int.argtypes = [SNDFILE, ct.POINTER(ct.c_int), sf_count_t]

    #sf_count_t    sf_write_raw     (SNDFILE *sndfile, const void *ptr, sf_count_t bytes) ;
    _lib.sf_write_raw.restype = sf_count_t
    _lib.sf_write_raw.argtypes = [SNDFILE, ct.c_void_p, sf_count_t]

    #int        sf_close        (SNDFILE *sndfile) ;
    _lib.sf_close.restype = ct.c_int
    _lib.sf_close.argtypes = [SNDFILE]

    #writing functions
    #sf_count_t  sf_write_short   (SNDFILE *sndfile, short *ptr, sf_count_t items) ;
    #sf_count_t  sf_write_int     (SNDFILE *sndfile, int *ptr, sf_count_t items) ;
    #sf_count_t  sf_write_float   (SNDFILE *sndfile, float *ptr, sf_count_t items) ;
    #sf_count_t  sf_write_double  (SNDFILE *sndfile, double *ptr, sf_count_t items) ;
    _lib.sf_write_int.restype = sf_count_t
    _lib.sf_write_int.argtypes = [SNDFILE, ct.POINTER(ct.c_int), sf_count_t]
    _lib.sf_write_short.restype = sf_count_t
    _lib.sf_write_short.argtypes = [SNDFILE, ct.POINTER(ct.c_short), sf_count_t]
    _lib.sf_write_float.restype = sf_count_t
    _lib.sf_write_float.argtypes = [SNDFILE, ct.POINTER(ct.c_float), sf_count_t]
    _lib.sf_write_double.restype = sf_count_t
    _lib.sf_write_double.argtypes = [SNDFILE, ct.POINTER(ct.c_double), sf_count_t]

__init_lib_methods()


#class definitions :
class OPEN_MODES():
    SFM_READ  = 0x10
    SFM_WRITE = 0x20
    SFM_RDWR  = 0x30

# deprecated
class SEEK_MODES():
    #stdio.h :
    SEEK_SET = 0
    SEEK_CUR = 1
    SEEK_END = 2

