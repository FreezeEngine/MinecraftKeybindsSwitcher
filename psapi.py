from ctypes import byref, create_unicode_buffer, sizeof, WinDLL
from ctypes.wintypes import DWORD, HMODULE, MAX_PATH

# ref https://stackoverflow.com/questions/17474574/tasklist-does-not-list-all-modules-in-64-systems

Psapi = WinDLL('Psapi.dll')
Kernel32 = WinDLL('kernel32.dll')

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

LIST_MODULES_ALL = 0x03

def EnumProcessModulesEx(hProcess):
    buf_count = 256
    while True:
        buf = (HMODULE * buf_count)()
        buf_size = sizeof(buf)
        needed = DWORD()
        if not Psapi.EnumProcessModulesEx(hProcess, byref(buf), buf_size,
                                          byref(needed), LIST_MODULES_ALL):
            raise OSError('EnumProcessModulesEx failed')
        if buf_size < needed.value:
            buf_count = needed.value // (buf_size // buf_count)
            continue
        count = needed.value // (buf_size // buf_count)
        return map(HMODULE, buf[:count])


def GetModuleFileNameEx(hProcess, hModule):
    buf = create_unicode_buffer(MAX_PATH)
    nSize = DWORD()
    if not Psapi.GetModuleFileNameExW(hProcess, hModule,
                                      byref(buf), byref(nSize)):
        raise OSError('GetModuleFileNameEx failed')
    return buf.value