# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""MPL-2.0. Brand a temporary unsigned installer SFX with documented Win32 APIs."""

import ctypes
import os
import struct
from ctypes import wintypes
from pathlib import Path


def _align(value):
    return (value + 3) & ~3


def _version_node(data, offset=0, depth=0):
    if depth > 12 or offset + 6 > len(data):
        raise ValueError("Invalid version resource nesting")
    length, value_length, kind = struct.unpack_from("<HHH", data, offset)
    end = offset + length
    if length < 6 or end > len(data) or kind not in (0, 1):
        raise ValueError("Invalid version resource length")
    cursor = offset + 6
    start = cursor
    while cursor + 2 <= end and data[cursor : cursor + 2] != b"\0\0":
        cursor += 2
    if cursor + 2 > end:
        raise ValueError("Unterminated version resource key")
    key = data[start:cursor].decode("utf-16-le")
    cursor = _align(cursor + 2)
    size = value_length * (2 if kind else 1)
    if size and cursor + size > end:
        if kind == 1 and value_length == end - cursor and not value_length % 2:
            size = value_length
        else:
            raise ValueError(f"Truncated version resource value: {key}")
    value = data[cursor : cursor + size]
    cursor = _align(cursor + size)
    children = []
    while cursor + 6 <= end and struct.unpack_from("<H", data, cursor)[0]:
        child, child_end = _version_node(data, cursor, depth + 1)
        children.append(child)
        cursor = _align(child_end)
    return [key, kind, value, children], end


def _version_bytes(node, replacements):
    key, kind, value, children = node
    if key in replacements:
        value = (replacements[key] + "\0").encode("utf-16-le")
    output = bytearray(
        struct.pack("<HHH", 0, len(value) // 2 if kind else len(value), kind)
    )
    output.extend((key + "\0").encode("utf-16-le"))
    output.extend(b"\0" * (-len(output) % 4))
    output.extend(value)
    for child in children:
        output.extend(b"\0" * (-len(output) % 4))
        output.extend(_version_bytes(child, replacements))
    if len(output) > 65535:
        raise ValueError("Version resource is too large")
    struct.pack_into("<H", output, 0, len(output))
    return bytes(output)


def brand_sfx(source, destination, icon, version):
    if os.name != "nt":
        raise OSError(
            "Lumen installer resource branding requires a native Windows build"
        )
    source, destination, icon = Path(source), Path(destination), Path(icon)
    if destination.exists():
        raise FileExistsError(destination)
    data = source.read_bytes()
    if data[:2] != b"MZ":
        raise ValueError("SFX must be a PE executable")
    pe = struct.unpack_from("<I", data, 60)[0]
    if data[pe : pe + 4] != b"PE\0\0":
        raise ValueError("Invalid SFX PE signature")
    optional = pe + 24
    magic = struct.unpack_from("<H", data, optional)[0]
    directory = optional + {0x10B: 96, 0x20B: 112}[magic]
    if any(struct.unpack_from("<II", data, directory + 4 * 8)):
        raise ValueError("Refusing to invalidate an existing SFX signature")
    ico = icon.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", ico)
    if reserved or kind != 1 or not 1 <= count <= 32 or len(ico) < 6 + count * 16:
        raise ValueError("Invalid installer icon directory")
    frames = []
    for index in range(count):
        w, h, colors, zero, planes, bits, size, offset = struct.unpack_from(
            "<BBBBHHII", ico, 6 + index * 16
        )
        if zero or not size or offset + size > len(ico):
            raise ValueError("Truncated installer icon image")
        frames.append((w, h, colors, planes, bits, ico[offset : offset + size]))
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    pointer = ctypes.c_void_p
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HMODULE, pointer, pointer, wintypes.LPARAM
    )
    language_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMODULE,
        pointer,
        pointer,
        wintypes.WORD,
        wintypes.LPARAM,
    )
    kernel.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
    kernel.LoadLibraryExW.restype = wintypes.HMODULE
    kernel.FreeLibrary.argtypes = [wintypes.HMODULE]
    kernel.EnumResourceNamesW.argtypes = [
        wintypes.HMODULE,
        pointer,
        callback_type,
        wintypes.LPARAM,
    ]
    kernel.EnumResourceLanguagesW.argtypes = [
        wintypes.HMODULE,
        pointer,
        pointer,
        language_type,
        wintypes.LPARAM,
    ]
    kernel.FindResourceExW.argtypes = [
        wintypes.HMODULE,
        pointer,
        pointer,
        wintypes.WORD,
    ]
    kernel.FindResourceExW.restype = wintypes.HRSRC
    kernel.SizeofResource.argtypes = [wintypes.HMODULE, wintypes.HRSRC]
    kernel.SizeofResource.restype = wintypes.DWORD
    kernel.LoadResource.argtypes = [wintypes.HMODULE, wintypes.HRSRC]
    kernel.LoadResource.restype = wintypes.HGLOBAL
    kernel.LockResource.argtypes = [wintypes.HGLOBAL]
    kernel.LockResource.restype = pointer
    kernel.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
    kernel.BeginUpdateResourceW.restype = wintypes.HANDLE
    kernel.UpdateResourceW.argtypes = [
        wintypes.HANDLE,
        pointer,
        pointer,
        wintypes.WORD,
        pointer,
        wintypes.DWORD,
    ]
    kernel.EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]
    library = kernel.LoadLibraryExW(str(source), None, 2)
    if not library:
        raise ctypes.WinError(ctypes.get_last_error())

    def resource_key(value):
        return (
            pointer(value)
            if isinstance(value, int)
            else ctypes.cast(ctypes.c_wchar_p(value), pointer)
        )

    def names(resource_type):
        result = []

        def collect(module, kind, name, parameter):
            result.append(name if name <= 65535 else ctypes.wstring_at(name))
            return True

        if not kernel.EnumResourceNamesW(
            library, pointer(resource_type), callback_type(collect), 0
        ):
            error = ctypes.get_last_error()
            if error != 1813:
                raise ctypes.WinError(error)
        return result

    def languages(resource_type, name):
        result = []

        def collect(module, kind, key, language, parameter):
            result.append(language)
            return True

        if not kernel.EnumResourceLanguagesW(
            library,
            pointer(resource_type),
            resource_key(name),
            language_type(collect),
            0,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return result

    def contents(resource_type, name, language):
        resource = kernel.FindResourceExW(
            library, pointer(resource_type), resource_key(name), language
        )
        if not resource:
            raise ctypes.WinError(ctypes.get_last_error())
        size = kernel.SizeofResource(library, resource)
        address = kernel.LockResource(kernel.LoadResource(library, resource))
        if not size or not address:
            raise ctypes.WinError(ctypes.get_last_error())
        return ctypes.string_at(address, size)

    try:
        groups = names(14)
        versions = names(16)
        if not groups or not versions:
            raise ValueError("SFX must contain icon and version resources")
        existing = [name for name in names(3) if isinstance(name, int)]
        first = max(existing, default=0) + 1
        if first + count > 65535:
            raise ValueError("No free SFX icon resource identifiers")
        group = bytearray(struct.pack("<HHH", 0, 1, count))
        for index, (w, h, colors, planes, bits, image) in enumerate(frames):
            group.extend(
                struct.pack(
                    "<BBBBHHIH",
                    w,
                    h,
                    colors,
                    0,
                    planes,
                    bits,
                    len(image),
                    first + index,
                )
            )
        updates = []
        for name in groups:
            for language in languages(14, name):
                updates.append((14, name, language, bytes(group)))
                updates.extend(
                    (3, first + index, language, frame[-1])
                    for index, frame in enumerate(frames)
                )
        for name in versions:
            for language in languages(16, name):
                tree, _ = _version_node(contents(16, name, language))
                replacements = {
                    "ProductName": "Lumen Browser",
                    "FileDescription": "Lumen Browser Setup",
                    "CompanyName": "Lumen Project",
                    "ProductVersion": str(version),
                    "OriginalFilename": "LumenSetup.exe",
                    "InternalName": "LumenSetup",
                }
                updates.append((16, name, language, _version_bytes(tree, replacements)))
        with destination.open("xb") as output:
            output.write(data)
        handle = kernel.BeginUpdateResourceW(str(destination), False)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            for resource_type, name, language, value in updates:
                buffer = ctypes.create_string_buffer(value)
                if not kernel.UpdateResourceW(
                    handle,
                    pointer(resource_type),
                    resource_key(name),
                    language,
                    buffer,
                    len(value),
                ):
                    raise ctypes.WinError(ctypes.get_last_error())
            completed, handle = handle, None
            if not kernel.EndUpdateResourceW(completed, False):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            if handle:
                kernel.EndUpdateResourceW(handle, True)
    finally:
        kernel.FreeLibrary(library)
