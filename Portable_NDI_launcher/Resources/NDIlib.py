import ctypes
import ctypes.util
import os
import sys
from typing import Optional

# Optional accelerated conversion
try:
    import numpy as np
except Exception:
    np = None
try:
    import cv2
except Exception:
    cv2 = None

# Try common locations for the NDI dylib
def _find_ndi_library() -> Optional[str]:
    # Respect explicit env var first
    env_path = os.environ.get('NDI_SDK_PATH')
    if env_path:
        # If a file given, prefer it
        if os.path.isabs(env_path) and os.path.exists(env_path):
            return env_path

    # Platform-specific candidates
    candidates = []
    if sys.platform.startswith('darwin'):
        candidates = [
            "/Library/NDI SDK for Apple/lib/macOS/libndi.dylib",
            "/usr/local/lib/libndi.dylib",
        ]
    elif sys.platform.startswith('linux'):
        candidates = [
            "/usr/lib/libndi.so",
            "/usr/local/lib/libndi.so",
        ]
    elif sys.platform.startswith('win'):
        candidates = [
            "NDIlib.dll",
            "libndi.dll",
        ]

    # Add ctypes discovery fallback
    libname = ctypes.util.find_library('ndi')
    if libname:
        candidates.append(libname)

    for p in candidates:
        if not p:
            continue
        try:
            if os.path.isabs(p) and os.path.exists(p):
                return p
        except Exception:
            pass

    # As last resort let the OS resolver pick the name
    if sys.platform.startswith('darwin'):
        return 'libndi.dylib'
    if sys.platform.startswith('linux'):
        return 'libndi.so'
    if sys.platform.startswith('win'):
        return 'NDIlib.dll'
    return None

_libpath = _find_ndi_library()
if not _libpath:
    raise OSError('Could not locate libndi native library. Install the NewTek NDI SDK or set NDI_SDK_PATH')

_lib = ctypes.CDLL(_libpath)

# Basic constants used by the example script
FRAME_TYPE_VIDEO = 1
FRAME_TYPE_AUDIO = 2
FRAME_TYPE_METADATA = 3
FRAME_TYPE_NONE = 0
FRAME_TYPE_ERROR = 4
FRAME_TYPE_STATUS_CHANGE = 100

def FOURCC(a,b,c,d):
    return (ord(a) | (ord(b) << 8) | (ord(c) << 16) | (ord(d) << 24))

FOURCC_VIDEO_TYPE_UYVY = FOURCC('U','Y','V','Y')

# Recv enums
RECV_COLOR_FORMAT_BGRX_BGRA = 0
RECV_BANDWIDTH_HIGHEST = 50
# Not strictly defined in headers here; example code uses 1 as TCP fallback
RECV_TRANSMISSION_TYPE_PREFER_TCP = 1

_c_uint32_p = ctypes.POINTER(ctypes.c_uint32)

# C-types mapping of a small subset of SDK structs
class NDIlib_source_t(ctypes.Structure):
    _fields_ = [
        ("p_ndi_name", ctypes.c_char_p),
        ("p_url_address", ctypes.c_char_p),
    ]

class NDIlib_find_create_t(ctypes.Structure):
    _fields_ = [
        ("show_local_sources", ctypes.c_bool),
        ("p_groups", ctypes.c_char_p),
        ("p_extra_ips", ctypes.c_char_p),
    ]

class NDIlib_video_frame_v2_t(ctypes.Structure):
    _fields_ = [
        ("xres", ctypes.c_int),
        ("yres", ctypes.c_int),
        ("FourCC", ctypes.c_uint32),
        ("frame_rate_N", ctypes.c_int),
        ("frame_rate_D", ctypes.c_int),
        ("picture_aspect_ratio", ctypes.c_float),
        ("frame_format_type", ctypes.c_int),
        ("timecode", ctypes.c_int64),
        ("p_data", ctypes.POINTER(ctypes.c_uint8)),
        ("line_stride_in_bytes", ctypes.c_int),
        ("p_metadata", ctypes.c_char_p),
        ("timestamp", ctypes.c_int64),
    ]

class NDIlib_audio_frame_v2_t(ctypes.Structure):
    _fields_ = [
        ("sample_rate", ctypes.c_int),
        ("no_channels", ctypes.c_int),
        ("no_samples", ctypes.c_int),
        ("timecode", ctypes.c_int64),
        ("p_data", ctypes.POINTER(ctypes.c_float)),
        ("channel_stride_in_bytes", ctypes.c_int),
        ("p_metadata", ctypes.c_char_p),
        ("timestamp", ctypes.c_int64),
    ]

class NDIlib_metadata_frame_t(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_int),
        ("timecode", ctypes.c_int64),
        ("p_data", ctypes.c_char_p),
    ]

class NDIlib_recv_create_v3_t(ctypes.Structure):
    _fields_ = [
        ("source_to_connect_to", NDIlib_source_t),
        ("color_format", ctypes.c_int),
        ("bandwidth", ctypes.c_int),
        ("allow_video_fields", ctypes.c_bool),
        ("p_ndi_recv_name", ctypes.c_char_p),
    ]

# Python-side convenience class matching original wrapper expectations
class RecvCreateV3:
    def __init__(self):
        self.source_to_connect_to = None
        self.color_format = RECV_COLOR_FORMAT_BGRX_BGRA
        self.bandwidth = RECV_BANDWIDTH_HIGHEST
        self.allow_video_fields = True
        self.p_ndi_recv_name = None
        # Some apps set transmission_type; keep attribute for compatibility
        self.transmission_type = None

# Setup function prototypes
_lib.NDIlib_initialize.restype = ctypes.c_bool
_lib.NDIlib_destroy.restype = None

_lib.NDIlib_find_create_v2.argtypes = [ctypes.POINTER(NDIlib_find_create_t)]
_lib.NDIlib_find_create_v2.restype = ctypes.c_void_p
_lib.NDIlib_find_destroy.argtypes = [ctypes.c_void_p]
_lib.NDIlib_find_wait_for_sources.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.NDIlib_find_wait_for_sources.restype = ctypes.c_bool
_lib.NDIlib_find_get_current_sources.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
_lib.NDIlib_find_get_current_sources.restype = ctypes.POINTER(NDIlib_source_t)

_lib.NDIlib_recv_create_v3.argtypes = [ctypes.POINTER(NDIlib_recv_create_v3_t)]
_lib.NDIlib_recv_create_v3.restype = ctypes.c_void_p
_lib.NDIlib_recv_destroy.argtypes = [ctypes.c_void_p]
_lib.NDIlib_recv_connect.argtypes = [ctypes.c_void_p, ctypes.POINTER(NDIlib_source_t)]

_lib.NDIlib_recv_capture_v2.argtypes = [ctypes.c_void_p,
                                        ctypes.POINTER(NDIlib_video_frame_v2_t),
                                        ctypes.POINTER(NDIlib_audio_frame_v2_t),
                                        ctypes.POINTER(NDIlib_metadata_frame_t),
                                        ctypes.c_uint32]
_lib.NDIlib_recv_capture_v2.restype = ctypes.c_int

_lib.NDIlib_recv_free_video_v2.argtypes = [ctypes.c_void_p, ctypes.POINTER(NDIlib_video_frame_v2_t)]
_lib.NDIlib_recv_free_audio_v2.argtypes = [ctypes.c_void_p, ctypes.POINTER(NDIlib_audio_frame_v2_t)]
_lib.NDIlib_recv_free_metadata.argtypes = [ctypes.c_void_p, ctypes.POINTER(NDIlib_metadata_frame_t)]

# Python-friendly wrappers
def initialize():
    return bool(_lib.NDIlib_initialize())

def destroy():
    _lib.NDIlib_destroy()

def find_create_v2():
    create = NDIlib_find_create_t()
    create.show_local_sources = True
    create.p_groups = None
    create.p_extra_ips = None
    return _lib.NDIlib_find_create_v2(ctypes.byref(create))

def find_destroy(finder):
    _lib.NDIlib_find_destroy(finder)

def find_wait_for_sources(finder, timeout_ms):
    return bool(_lib.NDIlib_find_wait_for_sources(finder, ctypes.c_uint32(timeout_ms)))

def find_get_current_sources(finder):
    count = ctypes.c_uint32(0)
    ptr = _lib.NDIlib_find_get_current_sources(finder, ctypes.byref(count))
    n = int(count.value)
    sources = []
    if not ptr or n == 0:
        return sources
    for i in range(n):
        src = ptr[i]
        name = src.p_ndi_name.decode('utf-8') if src.p_ndi_name else ''
        url = src.p_url_address.decode('utf-8') if src.p_url_address else ''
        # Provide a lightweight object similar to official wrapper
        obj = type('Src',(object,),{})()
        obj.ndi_name = name
        obj.url_address = url
        obj.p_ndi_name = src.p_ndi_name
        obj.p_url_address = src.p_url_address
        sources.append(obj)
    return sources

def recv_create_v3(py_recv_create=None):
    if py_recv_create is None:
        return _lib.NDIlib_recv_create_v3(None)
    c = NDIlib_recv_create_v3_t()
    # accept a simple object with the expected attributes
    try:
        src = py_recv_create.source_to_connect_to
        if getattr(src, 'p_ndi_name', None) is not None:
            if isinstance(src.p_ndi_name, bytes):
                c.source_to_connect_to.p_ndi_name = src.p_ndi_name
            else:
                c.source_to_connect_to.p_ndi_name = src.p_ndi_name.encode('utf-8')
        if getattr(src, 'p_url_address', None) is not None:
            if isinstance(src.p_url_address, bytes):
                c.source_to_connect_to.p_url_address = src.p_url_address
            else:
                c.source_to_connect_to.p_url_address = src.p_url_address.encode('utf-8')
    except Exception:
        # allow passing None source
        pass
    c.color_format = int(getattr(py_recv_create,'color_format', RECV_COLOR_FORMAT_BGRX_BGRA))
    c.bandwidth = int(getattr(py_recv_create,'bandwidth', RECV_BANDWIDTH_HIGHEST))
    c.allow_video_fields = bool(getattr(py_recv_create,'allow_video_fields', True))
    c.p_ndi_recv_name = getattr(py_recv_create,'p_ndi_recv_name', None)
    if c.p_ndi_recv_name is not None:
        c.p_ndi_recv_name = c.p_ndi_recv_name.encode('utf-8')
    return _lib.NDIlib_recv_create_v3(ctypes.byref(c))

def recv_destroy(recv):
    _lib.NDIlib_recv_destroy(recv)

def recv_connect(recv, src):
    # src expected to be a python object with p_ndi_name and p_url_address attributes
    csrc = NDIlib_source_t()
    p_name = getattr(src, 'p_ndi_name', None)
    if p_name is not None:
        csrc.p_ndi_name = p_name if isinstance(p_name, bytes) else p_name.encode('utf-8')
    p_url = getattr(src, 'p_url_address', None)
    if p_url is not None:
        csrc.p_url_address = p_url if isinstance(p_url, bytes) else p_url.encode('utf-8')
    _lib.NDIlib_recv_connect(recv, ctypes.byref(csrc))

def recv_capture_v2(recv, timeout_ms=500):
    video = NDIlib_video_frame_v2_t()
    audio = NDIlib_audio_frame_v2_t()
    meta = NDIlib_metadata_frame_t()
    ft = _lib.NDIlib_recv_capture_v2(recv, ctypes.byref(video), ctypes.byref(audio), ctypes.byref(meta), ctypes.c_uint32(timeout_ms))
    # Convert returned C structs into lightweight python wrappers
    vobj = None
    aobj = None
    mobj = None
    if ft == FRAME_TYPE_VIDEO and video.p_data:
        vobj = type('Vf',(object,),{})()
        vobj.xres = int(video.xres)
        vobj.yres = int(video.yres)
        vobj.FourCC = int(video.FourCC)
        vobj.frame_rate_N = int(video.frame_rate_N)
        vobj.frame_rate_D = int(video.frame_rate_D)
        vobj.picture_aspect_ratio = float(video.picture_aspect_ratio)
        vobj.frame_format_type = int(video.frame_format_type)
        vobj.timecode = int(video.timecode)
        # expose raw buffer & stride as zero-copy memoryview / numpy array when possible
        size = (video.line_stride_in_bytes or (video.xres * 4)) * video.yres if video.yres else 0
        if size > 0 and bool(video.p_data):
            # create a ctypes array object that shares the underlying memory
            c_array = ctypes.cast(video.p_data, ctypes.POINTER(ctypes.c_ubyte * size)).contents
            try:
                m = memoryview(c_array)
            except Exception:
                m = None

            if np is not None and m is not None:
                # create numpy view without copy
                arr = np.frombuffer(m, dtype=np.uint8)
                try:
                    arr = arr.reshape((video.yres, video.line_stride_in_bytes))
                except Exception:
                    # fallback to 1D view
                    pass
                vobj.data = arr
            else:
                vobj.data = m
        else:
            vobj.data = None
        vobj.line_stride_in_bytes = int(video.line_stride_in_bytes)
        vobj.yres = int(video.yres)
        vobj.xres = int(video.xres)
        vobj.FourCC = int(video.FourCC)
        # keep reference to the original ctypes struct for freeing and lifetime
        vobj._c_struct = video
    if ft == FRAME_TYPE_AUDIO and audio.p_data:
        aobj = type('Af',(object,),{})()
        aobj.sample_rate = int(audio.sample_rate)
        aobj.no_channels = int(audio.no_channels)
        aobj.no_samples = int(audio.no_samples)
        aobj.timecode = int(audio.timecode)
        aobj.p_data = audio.p_data
        aobj.channel_stride_in_bytes = int(audio.channel_stride_in_bytes)
        aobj._c_struct = audio
    if ft == FRAME_TYPE_METADATA and meta.p_data:
        mobj = type('Mf',(object,),{})()
        mobj.length = int(meta.length)
        mobj.timecode = int(meta.timecode)
        mobj.p_data = meta.p_data
        mobj._c_struct = meta
    return ft, vobj, aobj, mobj


def frame_to_ndarray(vobj):
    """Convert a video wrapper object returned from recv_capture_v2 into a displayable
    HxWx3 BGR numpy array when possible.

    Returns (ndarray, fourcc_str) or (None, None) if conversion is not possible.
    """
    if vobj is None:
        return None, None
    if np is None:
        return None, None
    fourcc = vobj.FourCC
    h = vobj.yres
    w = vobj.xres
    stride = getattr(vobj, 'line_stride_in_bytes', None) or (w * 4)
    data = vobj.data
    if data is None:
        return None, None

    # Ensure numpy array with shape (h, stride)
    if data.ndim == 1:
        try:
            data2d = data.reshape((h, stride))
        except Exception:
            data2d = data[:h*stride].reshape((h, stride))
    elif data.ndim == 2:
        data2d = data
    else:
        data2d = data

    # UYVY
    if fourcc == FOURCC_VIDEO_TYPE_UYVY:
        expected = w * 2
        valid = data2d[:, :expected]
        yuyv = valid.reshape((h, w, 2))
        if cv2 is not None:
            bgr = cv2.cvtColor(yuyv, cv2.COLOR_YUV2BGR_UYVY)
            return bgr, 'UYVY'
        return yuyv, 'UYVY'

    # BGRA/BGRX
    # BGRA fourcc value maps to BGRA; we treat as 4 channels and convert to BGR
    if getattr(vobj, 'data', None) is not None:
        # try interpret as BGRA
        try:
            pixels = data2d[:, :w*4].reshape((h, w, 4))
            if cv2 is not None:
                bgr = cv2.cvtColor(pixels, cv2.COLOR_BGRA2BGR)
                return bgr, 'BGRA'
            return pixels, 'BGRA'
        except Exception:
            pass

    return None, None

def recv_free_video_v2(recv, video):
    # Accept C-struct pointer or our python wrapper
    if hasattr(video, '_c_struct'):
        _lib.NDIlib_recv_free_video_v2(recv, ctypes.byref(video._c_struct))
    elif isinstance(video, NDIlib_video_frame_v2_t):
        _lib.NDIlib_recv_free_video_v2(recv, ctypes.byref(video))
    else:
        raise TypeError('recv_free_video_v2 expects a wrapper with _c_struct or a ctypes NDIlib_video_frame_v2_t')

def recv_free_audio_v2(recv, audio):
    if hasattr(audio, '_c_struct'):
        _lib.NDIlib_recv_free_audio_v2(recv, ctypes.byref(audio._c_struct))
    elif isinstance(audio, NDIlib_audio_frame_v2_t):
        _lib.NDIlib_recv_free_audio_v2(recv, ctypes.byref(audio))
    else:
        raise TypeError('recv_free_audio_v2 expects a wrapper with _c_struct or a ctypes NDIlib_audio_frame_v2_t')

def recv_free_metadata(recv, meta):
    if hasattr(meta, '_c_struct'):
        _lib.NDIlib_recv_free_metadata(recv, ctypes.byref(meta._c_struct))
    elif isinstance(meta, NDIlib_metadata_frame_t):
        _lib.NDIlib_recv_free_metadata(recv, ctypes.byref(meta))
    else:
        raise TypeError('recv_free_metadata expects a wrapper with _c_struct or a ctypes NDIlib_metadata_frame_t')
