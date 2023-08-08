"""Reading game data from memory
   
   First function maps the memory to a readable variable,
   the remaining function correspond to the bit addresses of desired game variables
"""

import warnings
import ctypes
from ctypes import wintypes
import struct
import numpy as np

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

FILE_MAP_READ = SECTION_MAP_READ = 0x0004
FILE_MAP_WRITE = SECTION_MAP_WRITE = 0x0002

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = (('BaseAddress', wintypes.LPVOID),
               ('AllocationBase', wintypes.LPVOID),
               ('AllocationProtect', wintypes.DWORD),
               ('PartitionId', wintypes.WORD),
               ('RegionSize', ctypes.c_size_t),
               ('State', wintypes.DWORD),
               ('Protect', wintypes.DWORD),
               ('Type', wintypes.DWORD))

PMEMORY_BASIC_INFORMATION = ctypes.POINTER(MEMORY_BASIC_INFORMATION)

kernel32.OpenFileMappingW.restype = wintypes.HANDLE
kernel32.OpenFileMappingW.argtypes = (wintypes.DWORD, wintypes.BOOL,
    wintypes.LPWSTR)

kernel32.MapViewOfFile.restype = wintypes.LPVOID
kernel32.MapViewOfFile.argtypes = (wintypes.HANDLE, wintypes.DWORD,
    wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t)

kernel32.UnmapViewOfFile.restype = wintypes.BOOL
kernel32.UnmapViewOfFile.argtypes = (wintypes.LPCVOID,)

kernel32.VirtualQuery.restype = ctypes.c_size_t
kernel32.VirtualQuery.argtypes = (wintypes.LPCVOID,
    PMEMORY_BASIC_INFORMATION, ctypes.c_size_t)

class BaseSharedMem(ctypes.Array):
    _type_ = ctypes.c_char
    _length_ = 0

    def __del__(self, *, UnmapViewOfFile=kernel32.UnmapViewOfFile,
                warn=warnings.warn):
        if not UnmapViewOfFile(self):
            warn("UnmapViewOfFile failed", ResourceWarning, source=self)


def map_section(name, mode='r'):
    mbi = MEMORY_BASIC_INFORMATION()

    access = FILE_MAP_READ

    h = kernel32.OpenFileMappingW(access, False, name)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        address = kernel32.MapViewOfFile(h, access, 0, 0, 0)
            
    finally:
        pass

    result = kernel32.VirtualQuery(address, ctypes.byref(mbi),
                ctypes.sizeof(mbi))

    array_t = type('SharedMem_{}'.format(mbi.RegionSize),
                (BaseSharedMem,), {'_length_': mbi.RegionSize})
    mv = memoryview(array_t.from_address(address)).cast('B')

    return mv

file = map_section("ManiaPlanet_Telemetry")

def game_state():
    state = struct.unpack("i",bytes(file[560:564]))[0]   
    return state

def angle():
    ang = struct.unpack("f",bytes(file[1344:1348]))[0]% (2 * np.pi)
    return ang
    
def gamepad():
    steer = struct.unpack("f",bytes(file[1196:1200]))[0]
    gas = struct.unpack("f",bytes(file[1200:1204]))[0]
    return (steer, gas)

def lap():
    lap = int(struct.unpack("I",bytes(file[572:576]))[0]/struct.unpack("I",bytes(file[1076:1080]))[0])
    return lap

def vehicle():
    pos_x = struct.unpack("f",bytes(file[1132:1136]))[0]+32
    pos_y = struct.unpack("f",bytes(file[1140:1144]))[0]+32
    vel = struct.unpack("I",bytes(file[1288:1292]))[0]
    return(pos_x, pos_y, vel)

def time():
    time = struct.unpack("I",bytes(file[564:568]))[0]
    return time

def slip():
    slip = sum(struct.unpack("iiii",bytes(file[1244:1260])))#[0]
    return slip
