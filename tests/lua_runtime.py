"""Optional Lua ABI harness, using an already installed shared library only."""

import ctypes
import ctypes.util
import unittest


def execute(source):
    library = next((ctypes.util.find_library(name) for name in ("lua5.4", "lua5.3", "texlua53")
                    if ctypes.util.find_library(name)), None)
    if library is None:
        raise unittest.SkipTest("optional Lua 5.3/5.4 shared library unavailable; Python adapter contract tests still run")
    lua = ctypes.CDLL(library)
    lua.luaL_newstate.restype = ctypes.c_void_p
    lua.luaL_openlibs.argtypes = [ctypes.c_void_p]
    lua.luaL_loadbufferx.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]
    lua.luaL_loadbufferx.restype = ctypes.c_int
    lua.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ssize_t, ctypes.c_void_p]
    lua.lua_pcallk.restype = ctypes.c_int
    lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
    lua.lua_tolstring.restype = ctypes.c_char_p
    lua.lua_close.argtypes = [ctypes.c_void_p]
    state = lua.luaL_newstate()
    if not state:
        raise RuntimeError("cannot allocate Lua state")
    try:
        lua.luaL_openlibs(state)
        data = source.encode("utf-8")
        code = lua.luaL_loadbufferx(state, data, len(data), b"kuang-contract-test", None)
        if code == 0:
            code = lua.lua_pcallk(state, 0, 0, 0, 0, None)
        if code:
            message = lua.lua_tolstring(state, -1, None)
            raise AssertionError(message.decode("utf-8", errors="replace") if message else f"Lua error {code}")
    finally:
        lua.lua_close(state)
