"""MPL-2.0. Generate original Lumen vector-derived branding using only the stdlib."""

from pathlib import Path
import math
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "branding/assets"


def chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data))
    )


def png(width, height, pixels):
    rows = b"".join(
        b"\0" + bytes(pixels[y * width * 4 : (y + 1) * width * 4])
        for y in range(height)
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, 9))
        + chunk(b"IEND", b"")
    )


def logo(size, private=False):
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            samples = []
            for dy, dx in [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25), (0.75, 0.75)]:
                px, py = (x + dx) * 256 / size, (y + dy) * 256 / size
                qx, qy = abs(px - 128) - 68, abs(py - 128) - 68
                distance = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - 44
                alpha = max(0, min(1, 0.5 - distance * size / 256))
                radius = math.hypot(px - 128, py - 128)
                angle = math.atan2(py - 128, px - 128)
                rgb = [18, 18, 20]
                # A restrained toothed bezel: readable silhouette, no tiny ornament.
                outer = 98 + (6 if math.cos(angle * 12) > 0.35 else 0)
                if 85 <= radius <= outer:
                    rgb = [112, 24, 30] if py > 128 else [182, 36, 44]
                if private:
                    if any(
                        ((px - cx) / 36) ** 2 + ((py - 130) / 28) ** 2 <= 1
                        for cx in (99, 157)
                    ) or (116 <= px <= 140 and 116 <= py <= 133):
                        rgb = [239, 232, 226]
                    if any(
                        ((px - cx) / 20) ** 2 + ((py - 130) / 10) ** 2 <= 1
                        for cx in (99, 157)
                    ):
                        rgb = [18, 18, 20]
                else:
                    if (78 <= px <= 111 and 66 <= py <= 185) or (
                        78 <= px <= 177 and 152 <= py <= 185
                    ):
                        rgb = [239, 232, 226]
                    if abs(px - 161) + abs(py - 87) <= 15:
                        rgb = [230, 42, 52]
                if size >= 48:
                    for cx, cy in ((57, 57), (199, 57), (57, 199), (199, 199)):
                        if math.hypot(px - cx, py - cy) <= 4:
                            rgb = [125, 110, 106]
                samples.append((*rgb, alpha))
            coverage = sum(s[3] for s in samples)
            rgb = [
                round(sum(s[c] * s[3] for s in samples) / coverage) if coverage else 0
                for c in range(3)
            ]
            pixels.extend((*rgb, round(coverage / 4 * 255)))
    return pixels


def bmp(width, height, sidebar=False, rtl=False):
    pixels = bytearray()
    mark_size = 104 if sidebar else 40
    mark = logo(mark_size)
    left = (
        (width - mark_size) // 2 if sidebar else (12 if rtl else width - mark_size - 12)
    )
    top = 64 if sidebar else (height - mark_size) // 2
    for y in range(height - 1, -1, -1):
        row = bytearray()
        for x in range(width):
            t = y / max(height - 1, 1)
            rgb = (
                [round(a + (b - a) * t) for a, b in zip((12, 12, 14), (45, 17, 21))]
                if sidebar
                else [18, 18, 20]
            )
            if left <= x < left + mark_size and top <= y < top + mark_size:
                i = ((y - top) * mark_size + x - left) * 4
                alpha = mark[i + 3] / 255
                rgb = [
                    round(mark[i + c] * alpha + rgb[c] * (1 - alpha)) for c in range(3)
                ]
            row.extend(reversed(rgb))
        row.extend(b"\0" * (-len(row) % 4))
        pixels.extend(row)
    return (
        b"BM"
        + struct.pack("<IHHI", len(pixels) + 54, 0, 0, 54)
        + struct.pack(
            "<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(pixels), 2835, 2835, 0, 0
        )
        + pixels
    )


def ico(encoded, private=False):
    sizes = (16, 32, 48, 256)
    frames = {}
    for size in sizes:
        if size == 256:
            frames[size] = encoded[size]
            continue
        rgba = logo(size, private=private)
        image = bytearray()
        mask = bytearray()
        for y in range(size - 1, -1, -1):
            bits = bytearray((size + 31) // 32 * 4)
            for x in range(size):
                i = (y * size + x) * 4
                image.extend((rgba[i + 2], rgba[i + 1], rgba[i], rgba[i + 3]))
                if not rgba[i + 3]:
                    bits[x // 8] |= 1 << (7 - x % 8)
            mask.extend(bits)
        frames[size] = (
            struct.pack(
                "<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, len(image), 0, 0, 0, 0
            )
            + image
            + mask
        )
    offset = 6 + 16 * len(sizes)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(sizes)))
    for size in sizes:
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                size % 256,
                size % 256,
                0,
                0,
                1,
                32,
                len(frames[size]),
                offset,
            )
        )
        offset += len(frames[size])
    return bytes(directory) + b"".join(frames[size] for size in sizes)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    encoded = {
        size: png(size, size, logo(size))
        for size in (16, 22, 24, 32, 48, 64, 70, 128, 150, 256)
    }
    for size, data in encoded.items():
        (ASSETS / f"logo-{size}.png").write_bytes(data)
    (ASSETS / "lumen.ico").write_bytes(ico(encoded))
    private = {
        size: png(size, size, logo(size, private=True))
        for size in (16, 32, 48, 70, 128, 150, 256)
    }
    for size in (70, 128, 150, 256):
        (ASSETS / f"logo-private-{size}.png").write_bytes(private[size])
    (ASSETS / "lumen-private.ico").write_bytes(ico(private, private=True))
    (ASSETS / "wizard.bmp").write_bytes(bmp(164, 314, sidebar=True))
    (ASSETS / "header.bmp").write_bytes(bmp(150, 57))
    (ASSETS / "header-rtl.bmp").write_bytes(bmp(150, 57, rtl=True))
    print("Generated original Lumen Browser black/red PNG/ICO/BMP assets")


if __name__ == "__main__":
    main()
