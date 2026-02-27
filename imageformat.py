# This Python script implements the reading and writing
# of certain classic pixel image, icon, and cursor formats,
# and the writing of certain animation formats.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under the Unlicense: https://unlicense.org/
#
# To improve the handling of certain file types, answers to the following
# questions would be welcome:
#
# 1. When OS/2 Presentation Manager draws a color icon, does
# Presentation Manager ignore the color table of the icon's
# AND/XOR mask (a two-level bitmap with the AND mask at the top and the XOR mask at
# the bottom)?
# 2. Can an Apple icon resource (.icns) have two or more icons of the same type
# (such as 'il32' or 'l8mk')? If so, is the first icon of a given type used? The
# last icon? All icons of that kind?
# 3. For icon types with a separate mask (such as 'ich4'), can an Apple icon resource
# (.icns) have an icon of that type but not its corresponding mask ('ich#' in
# this example)?
#

import os
import math
import random
import base64
import struct
import zlib
import io
import sys

import desktopwallpaper as dw

try:
    import PIL.Image
except:
    pass

# IO over a limited portion of
# another IO, which must be readable
# and seekable.  This class is not
# thread safe, and it uses the
# underlying IO, so the underlying IO
# should not be used while an object
# created from it is being used.
class _LimitedIO:
    # 'f' is the underlying IO; the portion
    # will begin at the current position
    # of 'f'. 'size' is the
    # size in bytes of the portion.
    def __init__(self, f, size):
        self.start = f.tell()
        self.f = f
        self.size = size

    def tell(self):
        return self.f.tell() - self.start

    def seek(self, pos):
        if pos < 0:
            raise ValueError
        if pos > self.size:
            raise ValueError
        self.f.seek(self.start + pos)

    def read(self, count=None):
        if not count:
            return self.f.read(self.size - self.tell())
        else:
            return self.f.read(min(count, self.size - self.tell()))

class _MemIO:
    def __init__(self):
        self.mem = b""

    def write(self, data):
        self.mem += data

    def get(self):
        return self.mem

def _errprint(s):
    print(s, file=sys.stderr)

# Image has the same format returned by the _desktopwallpaper_ module's blankimage() method with alpha=False.
def writeppm(f, image, width, height, raiseIfExists=False):
    if not image:
        raise ValueError
    if width < 0 or height < 0:
        raise ValueError
    if len(image) != width * height * 3:
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    fd = open(f, "xb" if raiseIfExists else "wb")
    fd.write(bytes("P6\n%d %d\n255\n" % (width, height), "utf-8"))
    fd.write(bytes(image))
    fd.close()

# Image has the same format returned by the _desktopwallpaper_ module's
# blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
def writepng(f, image, width, height, raiseIfExists=False, alpha=False):
    if not image:
        raise ValueError
    if width < 0 or height < 0:
        raise ValueError
    if len(image) != width * height * (4 if alpha else 3):
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    fd = open(f, "xb" if raiseIfExists else "wb")
    try:
        _writepng(fd, image, width, height, alpha)
    finally:
        fd.close()

# Image has the same format returned by the _desktopwallpaper_ module's
# blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
def pngbytes(image, width, height, alpha=False):
    fd = _MemIO()
    _writepng(fd, image, width, height, alpha=alpha)
    return fd.get()

def _writepng(fd, image, width, height, alpha=False):
    if not image:
        raise ValueError
    if width < 0 or height < 0:
        raise ValueError
    if len(image) != width * height * (4 if alpha else 3):
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    fd.write(b"\x89PNG\x0d\n\x1a\n")
    chunk = b"IHDR" + struct.pack(
        ">LLbbbbb", width, height, 8, 6 if alpha else 2, 0, 0, 0
    )
    fd.write(struct.pack(">L", 0x0D))
    fd.write(chunk)
    fd.write(struct.pack(">L", zlib.crc32(chunk)))
    newimage = []
    pos = 0
    for y in range(height):
        newimage.append(0)
        newimage += [image[x] for x in range(pos, pos + width * (4 if alpha else 3))]
        pos += width * (4 if alpha else 3)
    chunk = b"IDAT" + zlib.compress(bytes(newimage))
    fd.write(struct.pack(">L", len(chunk) - 4))
    fd.write(chunk)
    fd.write(struct.pack(">L", zlib.crc32(chunk)))
    fd.write(b"\0\0\0\0IEND\xae\x42\x60\x82")

def _isRiffOrListChunk(chunk):
    return chunk[0] == b"RIFF" or chunk[0] == b"LIST"

def _getRiffChunkSize(chunk):
    if _isRiffOrListChunk(chunk):
        sz = 4
        for subchunk in chunk[2]:
            sz += 8 + _getRiffChunkSize(subchunk)
        return sz
    else:
        return chunk[1]

def _writeChunkHead(f, chunk):
    f.write(bytes(chunk[0]))
    f.write(struct.pack("<L", _getRiffChunkSize(chunk)))
    if _isRiffOrListChunk(chunk):
        f.write(bytes(chunk[1]))

def _blackWhiteOnly(colortable, numuniques):
    return (
        numuniques == 0
        or (
            numuniques == 1
            and colortable[0] == colortable[1]
            and colortable[0] == colortable[2]
            and (colortable[0] == 0 or colortable[0] == 255)
        )
        or (
            numuniques == 2
            and colortable[0] == colortable[1]
            and colortable[0] == colortable[2]
            and (colortable[0] == 0 or colortable[0] == 255)
            and colortable[4] == colortable[5]
            and colortable[4] == colortable[6]
            and (colortable[4] == 0 or colortable[4] == 255)
        )
    )

# Images have the same format returned by the _desktopwallpaper_ module's blankimage() method with alpha=True.
# Note that, for mouse pointers (cursors), 32 &times; 32 pixels are the standard width and height.
def writeanicursor(
    outfile,
    images,
    width,
    height,
    raiseIfExists=False,
    singleFrameAsCur=False,
    asIcon=False,
    hotx=0,
    hoty=0,
    fps=20,
):
    if (not images) or len(images) == 0:
        raise ValueError
    if width < 0 or height < 0:
        raise ValueError
    # large animated cursors are not supported
    if width > 256 or height > 256:
        raise ValueError
    if fps <= 0:
        raise ValueError
    if (
        hotx < 0
        or hoty < 0
        or (hotx > width and hotx != 0xFFFF)
        or (hoty > height and hoty != 0xFFFF)
    ):
        raise ValueError
    newimages = [dw.splitmask(img, width, height) for img in images]
    colortables = []
    numuniqueslist = []
    uniquecolorslist = []
    bpplist = []
    for i in range(len(images)):
        colormask = newimages[i][0]
        monomask = newimages[i][1]
        uniquecolorshash = {}
        colortable = [0 for i in range(1024)]
        numuniques = 0
        pos = 0
        semitransparent = False
        for a in monomask:
            if a > 0 and a < 255:
                semitransparent = True
                break
        pos = 0
        if semitransparent:
            # Image has semitransparent pixels, so set the mono mask
            # to zero on all such pixels, to conform to how Windows
            # behaves when icons with such pixels are drawn
            for i in range(len(monomask)):
                if monomask[i] < 255:
                    monomask[i] = 0
            # Only 32-bit-per-pixel icons support semitransparent pixels, so
            # assume image has more than 256 colors to avoid relying
            # on the color table
            numuniques = 257
        else:
            for y in range(height * width):
                c = (
                    colormask[pos]
                    | (colormask[pos + 1] << 8)
                    | (colormask[pos + 2] << 16)
                )
                if c not in uniquecolorshash:
                    uniquecolorshash[c] = numuniques
                    if numuniques >= 256:
                        # More than 256 unique colors
                        numuniques += 1
                        break
                    colortable[numuniques * 4] = colormask[pos + 2]
                    colortable[numuniques * 4 + 1] = colormask[pos + 1]
                    colortable[numuniques * 4 + 2] = colormask[pos]
                    colortable[numuniques * 4 + 3] = 0
                    numuniques += 1
                pos += 3
        bpp = (
            1
            if _blackWhiteOnly(colortable, numuniques)
            else (
                4
                if numuniques <= 16
                else (8 if numuniques <= 256 else (32 if semitransparent else 24))
            )
        )
        bpplist.append(bpp)
        numuniqueslist.append(numuniques)
        colortables.append(colortable)
        uniquecolorslist.append(uniquecolorshash)
    riff = [b"RIFF", b"ACON", []]
    riff[2].append([b"anih", 0x24])
    riff[2].append([b"rate", len(images) * 4])
    listchunk = [b"LIST", b"fram", []]
    riff[2].append(listchunk)
    iconheaders = []
    for i in range(len(images)):
        numuniques = numuniqueslist[i]
        bpp = bpplist[i]
        scansize = ((width * bpp + 31) >> 5) << 2
        scansize1 = ((width * 1 + 31) >> 5) << 2
        imagesize = (
            0x28
            + (0 if bpp > 8 else 4 * (1 << bpp))
            + scansize * height
            + scansize1 * height
        )
        iconheader = struct.pack(
            "<HHHBBBBHHLL",
            0,
            1 if asIcon else 2,
            1,
            0 if width == 256 else width,
            0 if height == 256 else height,
            0,
            0,
            0 if asIcon else hotx,
            0 if asIcon else hoty,
            imagesize,
            0x16,
        )
        iconheaders.append(iconheader)
        # Assert icon chunk size is even, to avoid problems
        # when the file is read
        if imagesize % 2 == 0:
            raise ValueError
        listchunk[2].append([b"icon", 0x16 + imagesize])
    f = open(outfile, "xb" if raiseIfExists else "wb")
    multiIcon = len(images) > 1 or not singleFrameAsCur
    try:
        if multiIcon:
            _writeChunkHead(f, riff)
        for sub in riff[2]:
            if multiIcon:
                _writeChunkHead(f, sub)
            if sub[0] == b"anih":
                anih = struct.pack(
                    "<LLLLLLLLL",
                    0x24,
                    len(images),  # number of images
                    len(images),  # number of frames
                    0,
                    0,
                    0,
                    0,
                    max(1, 60 // fps),
                    1,
                )
                if multiIcon:
                    f.write(anih)
            elif sub[0] == b"rate":
                if multiIcon:
                    for i in range(len(images)):
                        f.write(struct.pack("<L", max(1, 60 // fps)))
            elif sub[0] == b"LIST":
                for i in range(len(sub[2])):
                    sub2 = sub[2][i]
                    if multiIcon:
                        _writeChunkHead(f, sub2)
                    if sub2[0] == b"icon":
                        # NOTE: Size of this chunk is always even, so no
                        # padding at the end of the chunk is necessary
                        numuniques = numuniqueslist[i]
                        bpp = bpplist[i]
                        scansize = ((width * bpp + 31) >> 5) << 2
                        scansize1 = ((width * 1 + 31) >> 5) << 2
                        colormask = newimages[i][0]
                        origmask = images[i]
                        monomask = newimages[i][1]
                        bitmapinfo = struct.pack(
                            "<LllHHLLllLL",
                            40,
                            width,
                            height * 2,
                            1,
                            bpp,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                        )
                        if bpp <= 8:
                            bitmapinfo += bytes(
                                [colortables[i][k] for k in range((1 << bpp) * 4)]
                            )
                        f.write(iconheaders[i])
                        f.write(bitmapinfo)
                        uniquecolorshash = uniquecolorslist[i]
                        bitmapbits = [0 for i in range(scansize * height)]
                        maskbits = [0 for i in range(scansize1 * height)]
                        pos = 0
                        mpos = 0
                        for y in range(height):
                            for x in range(width):
                                if bpp <= 8:
                                    col = uniquecolorshash[
                                        colormask[pos]
                                        | (colormask[pos + 1] << 8)
                                        | (colormask[pos + 2] << 16)
                                    ]
                                    if bpp == 1:
                                        bitmapbits[
                                            scansize * (height - 1 - y) + (x >> 3)
                                        ] |= col << (7 - (x & 7))
                                    elif bpp == 4:
                                        bitmapbits[
                                            scansize * (height - 1 - y) + (x >> 1)
                                        ] |= col << (4 * (1 - (x & 1)))
                                    else:
                                        bitmapbits[scansize * (height - 1 - y) + x] = (
                                            col
                                        )
                                    pos += 3
                                elif bpp == 32:
                                    bpos = scansize * (height - 1 - y) + x * 4
                                    bitmapbits[bpos] = origmask[pos + 2]
                                    bitmapbits[bpos + 1] = origmask[pos + 1]
                                    bitmapbits[bpos + 2] = origmask[pos + 0]
                                    bitmapbits[bpos + 3] = origmask[pos + 3]
                                    pos += 4
                                elif bpp == 24:
                                    bpos = scansize * (height - 1 - y) + x * 3
                                    bitmapbits[bpos] = colormask[pos + 2]
                                    bitmapbits[bpos + 1] = colormask[pos + 1]
                                    bitmapbits[bpos + 2] = colormask[pos + 0]
                                    pos += 3
                                mask = 1 if monomask[mpos] != 0 else 0
                                maskbits[
                                    scansize1 * (height - 1 - y) + (x >> 3)
                                ] |= mask << (7 - (x & 7))
                                mpos += 3
                        f.write(bytes(bitmapbits))
                        f.write(bytes(maskbits))
                    else:
                        raise RuntimeError
    finally:
        f.close()

# Images have the same format returned by the _desktopwallpaper_ module's blankimage() method with alpha=False.
def writeavi(
    f, images, width, height, raiseIfExists=False, singleFrameAsBmp=False, fps=20
):
    # NOTE: at least 20 frames per second is adequate for fluid animations
    if not images:
        raise ValueError
    if len(images) == 0:
        raise ValueError
    if width < 0 or height < 0 or width > 0x7FFF or height > 0x7FFF:
        raise ValueError
    for image in images:
        if not image:
            raise ValueError
        if len(image) != width * height * 3:
            raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    aviheader = struct.pack(
        "<LLLLLLLLLLLLLL",
        1000000 // fps,  # microseconds per frame
        width * height * 4 * fps + 256,  # maximum data rate in bytes
        0,
        0x010010,  # 0x10 = AVIF_HASINDEX
        len(images),
        0,  # not needed for noninterleaved AVIs
        1,  # number of streams (one video stream)
        max(256, width * height * 3 + 16),  # suggested buffer size to read the file
        width,
        height,
        0,
        0,
        0,
        0,
    )
    aviheader = b"avih" + struct.pack("<L", len(aviheader)) + aviheader
    streamheader = b"vids" + struct.pack(
        "<LLLLLLLLLLL" + "hhhh",
        0,
        0,
        0,
        0,
        1,
        fps,
        0,
        len(images),
        width * height * 4 * fps + 256,  # suggested buffer size
        0xFFFFFFFF,  # quality
        0,  # sample size (here, variable)
        0,
        0,
        width,
        height,
    )
    streamheader = b"strh" + struct.pack("<L", len(streamheader)) + streamheader
    uniquecolorshash = {}
    colortable = [0 for i in range(1024)]
    numuniques = 0
    for image in images:
        pos = 0
        for y in range(height * width):
            c = image[pos] | (image[pos + 1] << 8) | (image[pos + 2] << 16)
            if c not in uniquecolorshash:
                uniquecolorshash[c] = numuniques
                if numuniques >= 256:
                    # More than 256 unique colors
                    numuniques += 1
                    break
                colortable[numuniques * 4] = image[pos + 2]
                colortable[numuniques * 4 + 1] = image[pos + 1]
                colortable[numuniques * 4 + 2] = image[pos]
                colortable[numuniques * 4 + 3] = 0
                numuniques += 1
            pos += 3
    bmoffset = 0
    dowriteavi = len(images) > 1 or not singleFrameAsBmp
    if dowriteavi:
        if numuniques > 256:
            _errprint("AVI writing in more than 256 colors is not supported")
            return
        numuniques = 256  # Apparently needed for GStreamer compatibility
    rle4 = numuniques <= 16 and not dowriteavi
    rle8 = (numuniques > 16 and numuniques <= 256) or (dowriteavi and numuniques <= 16)
    compressionMode = 2 if rle4 else (1 if rle8 else 0)
    # For compatibility reasons, support writing two-color BMPs/AVIs only if no colors
    # other than black and white are in the color table and if uncompressed
    support2color = (compressionMode == 0) and _blackWhiteOnly(colortable, numuniques)
    scansize = 0
    bpp = 24
    if support2color and numuniques <= 2:
        scansize = (width + 7) // 8
        bpp = 1
    elif rle4:
        scansize = (width + 1) // 2
        bpp = 4
    elif numuniques <= 256 or rle8:
        scansize = width
        bpp = 8
    else:
        scansize = width * 3
        bpp = 24
    padding = ((scansize + 3) // 4) * 4 - scansize
    sizeImage = (scansize + padding) * height
    bitmapinfo = struct.pack(
        "<LllHHLLllLL",
        40,
        width,
        height,
        1,
        bpp,
        compressionMode,
        sizeImage if (rle4 or rle8) else 0,
        0,
        0,
        numuniques if numuniques <= 256 else 0,
        0,
    )
    bitmapcolortable = b""
    if bpp <= 8:
        bitmapcolortable = bytes([colortable[i] for i in range(numuniques * 4)])
    fd = open(f, "xb" if raiseIfExists else "wb")
    if compressionMode == 0 and not dowriteavi:
        bmsize = 14 + len(bitmapinfo) + len(bitmapcolortable) + sizeImage
        bmoffset = 14 + len(bitmapinfo) + len(bitmapcolortable)
        chunk = b"BM" + struct.pack("<LhhL", bmsize, 0, 0, bmoffset)
        fd.write(chunk)
        fd.write(bitmapinfo)
        fd.write(bitmapcolortable)
    imagedatas = []
    frameindex = []
    indexpos = 4
    paddingBytes = bytes([0 for i in range(padding)]) if padding > 0 else b""
    for index in range(len(images)):  # for image in images:
        image = images[index]
        # if dowriteavi: image=images[min(len(images)-1,index-index%3+2)]
        # if dowriteavi:
        #    image=images[14];
        pos = width * (height - 1) * 3  # Reference the bottom row first
        imagescans = []
        if bpp == 1:
            for y in range(height):
                scan = [0 for i in range(scansize)]
                for x in range(width // 8):
                    for i in range(8):
                        pp = pos + x * 24 + i * 3
                        scan[x] |= uniquecolorshash[
                            image[pp] | (image[pp + 1] << 8) | (image[pp + 2] << 16)
                        ] << (7 - i)
                if width % 8 != 0:
                    x = width // 8
                    for i in range(width % 8):
                        pp = pos + x * 24 + i * 3
                        scan[x] |= uniquecolorshash[
                            image[pp] | (image[pp + 1] << 8) | (image[pp + 2] << 16)
                        ] << (7 - i)
                if compressionMode == 0:
                    fd.write(bytes(scan))
                    fd.write(paddingBytes)
                else:
                    imagescans.append(bytes([scan[i] for i in range(scansize)]))
                pos -= width * 3
        elif bpp == 4:
            scan = [0 for i in range(scansize)]
            for y in range(height):
                for x in range(width // 2):
                    scan[x] = (
                        uniquecolorshash[
                            image[pos + x * 6]
                            | (image[pos + x * 6 + 1] << 8)
                            | (image[pos + x * 6 + 2] << 16)
                        ]
                        << 4
                    ) | (
                        uniquecolorshash[
                            image[pos + x * 6 + 3]
                            | (image[pos + x * 6 + 4] << 8)
                            | (image[pos + x * 6 + 5] << 16)
                        ]
                    )
                if width % 2 != 0:
                    x = width // 2
                    scan[x] = (
                        uniquecolorshash[
                            image[pos + x * 6]
                            | (image[pos + x * 6 + 1] << 8)
                            | (image[pos + x * 6 + 2] << 16)
                        ]
                        << 4
                    )
                if compressionMode == 0:
                    fd.write(bytes(scan))
                    fd.write(paddingBytes)
                else:
                    imagescans.append(bytes([scan[i] for i in range(scansize)]))
                pos -= width * 3
        elif bpp == 8:
            for y in range(height):
                scan = bytes(
                    [
                        uniquecolorshash[
                            image[pos + x * 3]
                            | (image[pos + x * 3 + 1] << 8)
                            | (image[pos + x * 3 + 2] << 16)
                        ]
                        for x in range(width)
                    ]
                )
                if compressionMode == 0:
                    fd.write(bytes(scan))
                    fd.write(paddingBytes)
                else:
                    imagescans.append(scan)
                pos -= width * 3
        else:
            for y in range(height):
                p = pos
                imagescan = b""
                for x in range(width):
                    imagescan += bytes([image[p + 2], image[p + 1], image[p]])
                    p += 3
                if compressionMode == 0:
                    fd.write(imagescan)
                    fd.write(paddingBytes)
                else:
                    imagescans.append(imagescan)
                pos -= width * 3
        if rle4 or rle8:
            newbytes = b""
            firstRow = True
            for sindex in range(len(imagescans)):  # imagebytes in imagescans:
                imagebytes = imagescans[sindex]
                if not firstRow:
                    newbytes += bytes([0, 0])
                lastbyte = -1
                lastIndex = 0
                lastRun = 0
                isConsecutive = True
                minRun = 2 if rle4 else 3
                runMult = 2 if rle4 else 1
                scanPixelCount = 0
                nbindex = len(newbytes)
                for i in range(len(imagebytes) + 1):
                    if i == len(imagebytes) or imagebytes[i] != lastbyte:
                        if isConsecutive and (i - lastIndex) >= minRun:
                            cnt = i - lastIndex
                            cnt = cnt * runMult
                            if width % 2 == 1 and rle4 and i == len(imagebytes):
                                cnt -= 1
                            while cnt > 0:
                                realcnt = min(cnt, 255)
                                # make even, in RLE4 case, to avoid problems
                                if rle4 and realcnt >= 255:
                                    realcnt = 254
                                if rle4 and cnt != realcnt and realcnt % 2 != 0:
                                    raise ValueError
                                newbytes += bytes([realcnt, lastbyte])
                                scanPixelCount += realcnt
                                # if index==0 and sindex==height-1: _errprint(["cnt",bytes([realcnt, lastbyte])])
                                cnt -= realcnt
                            lastIndex = i
                            isConsecutive = False
                        elif isConsecutive and i < len(imagebytes):
                            if i > 0:
                                isConsecutive = False
                        elif (
                            (not isConsecutive)
                            and (i - lastRun) < minRun
                            and i < len(imagebytes)
                        ):
                            pass
                        else:
                            cnt = lastRun - lastIndex
                            if lastRun >= i:
                                raise ValueError
                            if i - lastRun == 1 and (
                                rle8 or i < len(imagebytes) or width % 2 == 0
                            ):
                                lastRun = i
                                cnt += 1
                            cntpos = lastIndex
                            nb = b""
                            while cnt >= minRun:
                                realcnt = min(cnt, 127 if rle4 else 255)
                                nb += bytes([0, realcnt * runMult])
                                scanPixelCount += realcnt * runMult
                                rc = imagebytes[cntpos : cntpos + realcnt]
                                # if index==0 and sindex==height-1:
                                #  _errprint(rc)
                                #  _errprint([realcnt*runMult,"spc",scanPixelCount,"i",i,"li",lastIndex,"lr",lastRun])
                                if len(rc) != realcnt:
                                    raise ValueError
                                nb += rc
                                # padding
                                if (len(nb) & 1) == 1:
                                    nb += bytes([0])
                                cnt -= realcnt
                                cntpos += realcnt
                            for j in range(0, cnt):
                                nb += bytes([runMult, imagebytes[cntpos + j]])
                                scanPixelCount += runMult
                            # if index==0 and sindex==height-1: _errprint([runMult,"spc",scanPixelCount,"i",i,"li",lastIndex,"lr",lastRun])
                            cnt = i - lastRun
                            cnt = cnt * runMult
                            if (
                                cnt > 0
                                and width % 2 == 1
                                and rle4
                                and i == len(imagebytes)
                            ):
                                cnt -= 1
                            while cnt > 0:
                                realcnt = min(cnt, 255)
                                # make even, in RLE4 case, to avoid problems
                                if rle4 and realcnt >= 255:
                                    realcnt = 254
                                if rle4 and cnt != realcnt and realcnt % 2 != 0:
                                    raise ValueError
                                nb += bytes([realcnt, lastbyte])
                                # if index==0 and sindex==height-1: _errprint(bytes([realcnt, lastbyte]))
                                scanPixelCount += realcnt
                                # if index==0 and sindex==height-1: _errprint(["run",realcnt, "spc", scanPixelCount,"i", i,"li",lastIndex,"lr", lastRun])
                                cnt -= realcnt
                            if (len(nb) & 1) != 0:
                                raise ValueError
                            # if index==0 and sindex==height-1: _errprint(nb)
                            newbytes += nb
                            lastIndex = i
                            isConsecutive = True
                        lastRun = i
                    if i < len(imagebytes):
                        lastbyte = imagebytes[i]
                # if index==0 and sindex==height-1:
                #   _errprint(imagebytes)
                #   _errprint(newbytes[nbindex:len(newbytes)])
                if scanPixelCount != width:
                    raise ValueError(str([scanPixelCount, width]))
                firstRow = False
            newbytes += bytes([0, 1])
            frameindex.append([indexpos, len(newbytes)])
            indexpos += len(newbytes) + 8
            imagedatas.append(newbytes)
        else:
            fd.write(b"".join(imagescans))
    if dowriteavi:
        bitmapinfo = (
            b"strf"
            + struct.pack("<L", len(bitmapinfo) + len(bitmapcolortable))
            + bitmapinfo
            + bitmapcolortable
        )
        streamlist = b"strl" + streamheader + bitmapinfo
        aviheaderlist = (
            b"hdrl"
            + aviheader
            + b"LIST"
            + struct.pack("<L", len(streamlist))
            + streamlist
        )
        aviheaderlist = b"LIST" + struct.pack("<L", len(aviheaderlist)) + aviheaderlist
        movilist = sum(len(img) + 8 for img in imagedatas) + 4
        fullriff = (movilist + 8) + len(aviheaderlist) + 4
        indexinfo = b"".join(
            [b"00dc" + struct.pack("<LLL", 0x00, x, y) for x, y in frameindex]
        )
        indexinfo = b"idx1" + struct.pack("<L", len(indexinfo)) + indexinfo
        fullriff += len(indexinfo)
        fd.write(b"RIFF" + struct.pack("<L", fullriff) + b"AVI ")
        fd.write(aviheaderlist)
        fd.write(b"LIST" + struct.pack("<L", movilist) + b"movi")
        for img in imagedatas:
            fd.write(b"00dc")
            fd.write(struct.pack("<L", len(img)))
            fd.write(img)
        fd.write(indexinfo)
    elif rle4 or rle8:
        bitmapinfo = struct.pack(
            "<LllHHLLllLL",
            40,
            width,
            height,
            1,
            bpp,
            compressionMode,
            sum(len(img) for img in imagedatas),
            0,
            0,
            numuniques if numuniques <= 256 else 0,
            0,
        )
        bmsize = (
            14
            + len(bitmapinfo)
            + len(bitmapcolortable)
            + sum(len(img) for img in imagedatas)
        )
        bmoffset = 14 + len(bitmapinfo) + len(bitmapcolortable)
        chunk = b"BM" + struct.pack("<LhhL", bmsize, 0, 0, bmoffset)
        fd.write(chunk)
        fd.write(bitmapinfo)
        fd.write(bitmapcolortable)
        for img in imagedatas:
            fd.write(img)
    fd.close()

def writebmp(f, image, width, height, raiseIfExists=False):
    return writeavi(
        f, [image], width, height, raiseIfExists=raiseIfExists, singleFrameAsBmp=True
    )

def _rle8decompress(bitdata, dst, width, height):
    # RLE compression for 8-bit-per-pixel bitmaps.
    # This method assumes that all the elements in 'dst' are zeros.
    if (not dst) or (not bitdata):
        return False
    szDst = len(dst)
    x = 0
    y = 0
    bits = 0
    length = 0
    escape_code = 0
    linesz = ((width * 8 + 31) >> 5) << 2  # bytes per scan line
    dstln = 0
    x = 0
    y = height - 1
    while y >= 0:
        if bits >= len(bitdata):
            return False
        length = bitdata[bits]
        bits += 1
        if length != 0:  # encoded mode
            if bits >= len(bitdata):
                return False
            color = bitdata[bits]
            bits += 1
            while True:
                if length > 0:
                    length -= 1
                    if x >= width:
                        break
                else:
                    break
                if dstln + x >= szDst:
                    return False
                dst[dstln + x] = color
                x += 1
        else:  # escape
            if bits >= len(bitdata):
                return False
            escape_code = bitdata[bits]
            bits += 1
            match (escape_code):
                case 0:  # end of line
                    x = 0
                    dstln += linesz
                    y -= 1
                case 1:  # end of bitmap
                    return True
                case 2:  # delta
                    if bits >= len(bitdata):
                        return False
                    x += bitdata[bits]
                    bits += 1
                    if bits >= len(bitdata):
                        return False
                    dstln += (bitdata[bits]) * linesz
                    y -= bitdata[bits]
                    bits += 1
                case _:
                    length = escape_code
                    while length > 0:
                        length -= 1
                        if bits >= len(bitdata):
                            return False
                        color = bitdata[bits]
                        bits += 1
                        if x >= width:
                            if bits + length > len(bitdata):
                                return False
                            bits += length
                            break
                        if dstln + x >= szDst:
                            return False
                        dst[dstln + x] = color
                        x += 1
                    if (escape_code & 1) > 0:
                        if bits >= len(bitdata):
                            return False
                        bits += 1
    return True

def _rle24decompress(bitdata, dst, width, height):
    # RLE compression for 24-bit-per-pixel bitmaps.
    # This method assumes that all the elements in 'dst' are zeros.
    if (not dst) or (not bitdata):
        return False
    szDst = len(dst)
    x = 0
    y = 0
    bits = 0
    length = 0
    escape_code = 0
    linesz = ((width * 24 + 31) >> 5) << 2  # bytes per scan line
    dstln = 0
    x = 0
    y = height - 1
    while True:
        if bits >= len(bitdata):
            return False
        length = bitdata[bits]
        bits += 1
        if length != 0:  # encoded mode
            if bits + 2 >= len(bitdata):
                return False
            if y < 0:
                return False
            color = bitdata[bits]
            color1 = bitdata[bits + 1]
            color2 = bitdata[bits + 2]
            bits += 3
            while True:
                if length > 0:
                    length -= 1
                    if x >= width:
                        break
                else:
                    break
                if dstln + x * 3 + 2 >= szDst:
                    return False
                dst[dstln + x * 3] = color
                dst[dstln + x * 3 + 1] = color1
                dst[dstln + x * 3 + 2] = color2
                x += 1
        else:  # escape
            if bits >= len(bitdata):
                return False
            escape_code = bitdata[bits]
            bits += 1
            match (escape_code):
                case 0:  # end of line
                    if y < 0:
                        return False
                    x = 0
                    dstln += linesz
                    y -= 1
                case 1:  # end of bitmap
                    return True
                case 2:  # delta
                    if bits >= len(bitdata):
                        return False
                    if y < 0:
                        return False
                    x += bitdata[bits]
                    bits += 1
                    if bits >= len(bitdata):
                        return False
                    dstln += (bitdata[bits]) * 3 * linesz
                    y -= bitdata[bits]
                    bits += 1
                case _:
                    if y < 0:
                        return False
                    length = escape_code
                    while length > 0:
                        length -= 1
                        if bits + 2 >= len(bitdata):
                            return False
                        color = bitdata[bits]
                        color1 = bitdata[bits + 1]
                        color2 = bitdata[bits + 2]
                        bits += 3
                        if x >= width:
                            if bits + length * 3 > len(bitdata):
                                return False
                            bits += length * 3
                            break
                        if dstln + x * 3 + 2 >= szDst:
                            return False
                        dst[dstln + x * 3] = color
                        dst[dstln + x * 3 + 1] = color1
                        dst[dstln + x * 3 + 2] = color2
                        x += 1
                    if (escape_code & 1) > 0:
                        if bits >= len(bitdata):
                            return False
                        bits += 1
    return True

_HUFFBOTH = {
    (4, 8): 91,
    (4, 12): 92,
    (4, 13): 93,
    (5, 18): 94,
    (5, 19): 95,
    (5, 20): 96,
    (5, 21): 97,
    (5, 22): 98,
    (5, 23): 99,
    (5, 28): 100,
    (5, 29): 101,
    (5, 30): 102,
    (5, 31): 103,
}
_TRAIL2_WHITE = [-1, -1, -1, -1, -1, -1, -1, -1, -1, 13, -1, 22, 29, 30, -1, -1]
_TRAIL2_BLACK = [3, 2, 1, 4, 6, 5, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1]

_HUFFWHITES = {
    (0, 4, 8): 3,
    (0, 4, 11): 4,
    (0, 4, 12): 5,
    (0, 4, 14): 6,
    (0, 4, 15): 7,
    (0, 5, 18): 65,
    (0, 5, 19): 8,
    (0, 5, 20): 9,
    (0, 5, 27): 64,
    (0, 6, 42): 16,
    (0, 6, 43): 17,
    (0, 6, 52): 14,
    (0, 6, 53): 15,
    (1, 3, 7): 2,
    (1, 4, 8): 11,
    (1, 5, 23): 66,
    (1, 5, 24): 89,
    (1, 6, 36): 27,
    (1, 6, 39): 18,
    (1, 6, 40): 24,
    (1, 6, 43): 25,
    (1, 6, 55): 67,
    (1, 7, 74): 59,
    (1, 7, 75): 60,
    (1, 7, 82): 49,
    (1, 7, 83): 50,
    (1, 7, 84): 51,
    (1, 7, 85): 52,
    (1, 7, 88): 55,
    (1, 7, 89): 56,
    (1, 7, 90): 57,
    (1, 7, 91): 58,
    (1, 7, 100): 70,
    (1, 7, 101): 71,
    (1, 7, 103): 73,
    (1, 7, 104): 72,
    (1, 8, 152): 86,
    (1, 8, 153): 87,
    (1, 8, 154): 88,
    (1, 8, 155): 90,
    (1, 8, 204): 74,
    (1, 8, 205): 75,
    (1, 8, 210): 76,
    (1, 8, 211): 77,
    (1, 8, 212): 78,
    (1, 8, 213): 79,
    (1, 8, 214): 80,
    (1, 8, 215): 81,
    (1, 8, 216): 82,
    (1, 8, 217): 83,
    (1, 8, 218): 84,
    (1, 8, 219): 85,
    (2, 3, 7): 10,
    (2, 4, 8): 12,
    (2, 5, 19): 26,
    (2, 5, 23): 21,
    (2, 5, 24): 28,
    (2, 6, 36): 53,
    (2, 6, 37): 54,
    (2, 6, 40): 39,
    (2, 6, 41): 40,
    (2, 6, 42): 41,
    (2, 6, 43): 42,
    (2, 6, 44): 43,
    (2, 6, 45): 44,
    (2, 6, 50): 61,
    (2, 6, 51): 62,
    (2, 6, 52): 63,
    (2, 6, 53): 0,
    (2, 6, 54): 68,
    (2, 6, 55): 69,
    (3, 3, 7): 1,
    (3, 4, 8): 20,
    (3, 4, 12): 19,
    (3, 5, 18): 33,
    (3, 5, 19): 34,
    (3, 5, 20): 35,
    (3, 5, 21): 36,
    (3, 5, 22): 37,
    (3, 5, 23): 38,
    (3, 5, 26): 31,
    (3, 5, 27): 32,
    (4, 3, 4): 23,
    (4, 4, 10): 47,
    (4, 4, 11): 48,
    (5, 3, 4): 45,
    (5, 3, 5): 46,
}
_HUFFBLACKS = {
    (3, 3, 4): 9,
    (3, 3, 5): 8,
    (4, 3, 4): 10,
    (4, 3, 5): 11,
    (4, 3, 7): 12,
    (4, 5, 24): 15,
    (4, 6, 55): 0,
    (4, 7, 103): 19,
    (4, 7, 104): 20,
    (4, 7, 108): 21,
    (4, 8, 200): 65,
    (4, 8, 201): 66,
    (4, 8, 202): 26,
    (4, 8, 203): 27,
    (4, 8, 204): 28,
    (4, 8, 205): 29,
    (4, 8, 210): 34,
    (4, 8, 211): 35,
    (4, 8, 212): 36,
    (4, 8, 213): 37,
    (4, 8, 214): 38,
    (4, 8, 215): 39,
    (4, 8, 218): 42,
    (4, 8, 219): 43,
    (5, 3, 4): 13,
    (5, 3, 7): 14,
    (5, 5, 23): 16,
    (5, 5, 24): 17,
    (5, 6, 40): 23,
    (5, 6, 55): 22,
    (5, 7, 82): 50,
    (5, 7, 83): 51,
    (5, 7, 84): 44,
    (5, 7, 85): 45,
    (5, 7, 86): 46,
    (5, 7, 87): 47,
    (5, 7, 88): 57,
    (5, 7, 89): 58,
    (5, 7, 90): 61,
    (5, 7, 91): 67,
    (5, 7, 100): 48,
    (5, 7, 101): 49,
    (5, 7, 102): 62,
    (5, 7, 103): 63,
    (5, 7, 104): 30,
    (5, 7, 105): 31,
    (5, 7, 106): 32,
    (5, 7, 107): 33,
    (5, 7, 108): 40,
    (5, 7, 109): 41,
    (6, 4, 8): 18,
    (6, 4, 15): 64,
    (6, 5, 23): 24,
    (6, 5, 24): 25,
    (6, 6, 36): 52,
    (6, 6, 39): 55,
    (6, 6, 40): 56,
    (6, 6, 43): 59,
    (6, 6, 44): 60,
    (6, 6, 51): 68,
    (6, 6, 52): 69,
    (6, 6, 53): 70,
    (6, 6, 55): 53,
    (6, 6, 56): 54,
    (6, 7, 74): 73,
    (6, 7, 75): 74,
    (6, 7, 76): 75,
    (6, 7, 77): 76,
    (6, 7, 82): 83,
    (6, 7, 83): 84,
    (6, 7, 84): 85,
    (6, 7, 85): 86,
    (6, 7, 90): 87,
    (6, 7, 91): 88,
    (6, 7, 100): 89,
    (6, 7, 101): 90,
    (6, 7, 108): 71,
    (6, 7, 109): 72,
    (6, 7, 114): 77,
    (6, 7, 115): 78,
    (6, 7, 116): 79,
    (6, 7, 117): 80,
    (6, 7, 118): 81,
    (6, 7, 119): 82,
}

def _createhuffctx(bitdata, dst, width, height):
    linesz = ((width + 31) >> 5) << 2  # bytes per scan line
    # bitdata, dst, width, height, dstbytepos, dstbitpos, dstX, linesz,
    # color, srcbytepos, srcbitpos
    return [bitdata, dst, width, height, 0, 0, 0, linesz, 0, 0, 0]

def _nextbit(ctx):
    bitdata = ctx[0]
    if ctx[9] >= len(bitdata):
        return -1
    ret = bitdata[ctx[9]] & (1 << (7 - ctx[10]))
    ctx[10] += 1
    if ctx[10] >= 8:
        ctx[10] = 0
        ctx[9] += 1
    return ret

def _nexthuffcode(ctx):
    color = ctx[8]
    zeros = 0
    for i in range(12):
        b = _nextbit(ctx)
        if b < 0:
            return None
        if b != 0:
            break
        zeros += 1
    if zeros == 11:
        # start-of-line code
        return [0, -1]
    if zeros >= 8:
        return None
    b = _nextbit(ctx)
    if b < 0:
        return None
    trail = 2 if b == 0 else 3
    pos = zeros * 2 + (trail - 2)
    tr = _TRAIL2_WHITE[pos] if color == 0 else _TRAIL2_BLACK[pos]
    if tr >= 0:
        ret = [color, tr]
        # switch to other color, since this
        # is a terminating code
        ctx[8] = 1 - color
        return ret
    if color == 1 and zeros < 3:
        return None
    for i in range(6):
        b = _nextbit(ctx)
        if b < 0:
            return None
        trail = (trail << 1) | (0 if b == 0 else 1)
        key = (zeros, i + 3, trail) if zeros < 7 else (i + 3, trail)
        if color == 0 and key in (_HUFFWHITES if zeros < 7 else _HUFFBOTH):
            ret = [0, _HUFFWHITES[key] if zeros < 7 else _HUFFBOTH[key]]
            if _istermcode(ret):
                ctx[8] = 1  # switch to black
            return ret
        elif color == 1 and key in (_HUFFBLACKS if zeros < 7 else _HUFFBOTH):
            ret = [1, _HUFFBLACKS[key] if zeros < 7 else _HUFFBOTH[key]]
            if _istermcode(ret):
                ctx[8] = 0  # switch to white
            return ret
    return None

def _ismakeupcode(code):
    return code != None and code[1] >= 64

def _istermcode(code):
    return code != None and code[1] >= 0 and code[1] < 64

def _isstartcode(code):
    return code != None and code[1] == -1

def _codebitcount(code):
    if code == None or code[1] == -1:
        raise ValueError
    return code[1] if code[1] < 64 else (code[1] - 63) * 64

def _codecolor(code):
    if code == None or code[1] == -1:
        raise ValueError
    return code[0]

def _newscan(ctx, y):
    ctx[8] = 0  # switch to white
    ctx[6] = 0  # set X to 0
    ctx[4] = (ctx[3] - 1 - y) * ctx[7]  # set scan position
    ctx[5] = 0  # set scan bit position

def _writebitstodest(ctx, bit, count):
    dst = ctx[1]
    if ctx[6] + count > ctx[2]:
        # would exceed width
        return False
    ctx[6] += count
    i = 0
    while i < count:
        if ctx[4] >= len(dst):
            return False
        if i + 8 < count and ctx[5] == 0:
            # fill whole byte
            dst[ctx[4]] = 0 if bit == 0 else 0xFF
            ctx[5] += 8
            i += 8
        elif bit == 1:
            # set next bit
            dst[ctx[4]] |= 1 << (7 - ctx[5])
            ctx[5] += 1
            i += 1
        else:
            # clear next bit
            dst[ctx[4]] &= ~(1 << (7 - ctx[5]))
            ctx[5] += 1
            i += 1
        if ctx[5] >= 8:
            # move to next byte
            ctx[4] += 1
            ctx[5] = 0
    return True

def _huffmandecompress(bitdata, dst, width, height):
    # Group 3 one-dimensional encoding (ITU-T Rec. T.4),
    # where zero-bits are interpreted
    # as white and one-bits as black, solely for purposes of the encoding.
    # The encoded and decoded data are
    # stored most-significant-bit-first in this Python method.
    # This method assumes that all the elements in 'dst' are zeros.
    if (not dst) or (not bitdata):
        return False
    linesz = ((width + 31) >> 5) << 2  # bytes per scan line
    ctx = _createhuffctx(bitdata, dst, width, height)
    starting = True
    consecstartcodes = 0
    y = height
    bitcount = 0
    lastWasMakeup = False
    while True:
        code = _nexthuffcode(ctx)
        if starting and not _isstartcode(code):
            return False
        if _istermcode(code):
            if y < 0:
                return False
            consecstartcodes = 0
            bitcount += _codebitcount(code)
            if not _writebitstodest(ctx, _codecolor(code), bitcount):
                return False
            bitcount = 0
            lastWasMakeup = False
        elif _ismakeupcode(code):
            if y < 0:
                return False
            consecstartcodes = 0
            bitcount += _codebitcount(code)
        elif _isstartcode(code):
            if lastWasMakeup:
                return False
            y -= 1
            if y >= 0:
                _newscan(ctx, y)
            lastWasMakeup = False
            consecstartcodes += 1
            if consecstartcodes >= 6:
                return True
        else:  # invalid code
            return False
        starting = False
    return True

def _rle4decompress(bitdata, dst, width, height):
    # RLE compression for 4-bit-per-pixel bitmaps.
    # This method assumes that all the elements in 'dst' are zeros.
    if (not dst) or (not bitdata):
        return False
    szDst = len(dst)
    x = 0
    y = height - 1
    c = 0
    length = 0
    escapecode = 0
    begin = 0
    bits = 0
    linesz = ((width * 4 + 31) >> 5) << 2  # bytes per scan line
    dstln = 0
    masks = [0xF0, 0x0F]
    shifts = [4, 0]
    lastbit = 0
    while True:
        if bits >= len(bitdata):
            return False
        length = bitdata[bits]
        bits += 1
        if length > 0:  # encoded
            if bits >= len(bitdata):
                return False
            if y < 0:
                return False
            c = bitdata[bits]
            bits += 1
            while length > 0:
                length -= 1
                if x >= width:
                    break
                lastbit = (x) & 1
                if dstln + ((x) >> 1) >= szDst:
                    return False
                dst[dstln + ((x) >> 1)] &= ~masks[lastbit]
                dst[dstln + ((x) >> 1)] |= (c >> 4) << shifts[lastbit]
                (x) += 1
                if length == 0:
                    break
                length -= 1
                if x >= width:
                    break
                lastbit = (x) & 1
                if dstln + ((x) >> 1) >= szDst:
                    return False
                dst[dstln + ((x) >> 1)] &= ~masks[lastbit]
                dst[dstln + ((x) >> 1)] |= (c & 0x0F) << shifts[lastbit]
                (x) += 1
        else:
            if bits >= len(bitdata):
                return False
            length = bitdata[bits]
            bits += 1
            match length:
                case 0:  # end of line
                    if x != width:
                        return False
                    if y < 0:
                        return False
                    x = 0
                    y -= 1
                    dstln += linesz
                case 1:  # end of bitmap
                    return True
                case 2:  # delta
                    if bits >= len(bitdata):
                        return False
                    if y < 0:
                        return False
                    x += bitdata[bits]
                    bits += 1
                    if bits >= len(bitdata):
                        return False
                    dstln += bitdata[bits] * linesz
                    y -= bitdata[bits]
                    bits += 1
                case _:  # absolute
                    if y < 0:
                        return False
                    escapecode = length
                    while length > 0:
                        length -= 1
                        if bits >= len(bitdata):
                            return False
                        c = bitdata[bits]
                        bits += 1
                        if x < width:
                            lastbit = (x) & 1
                            if dstln + ((x) >> 1) >= szDst:
                                return False
                            dst[dstln + ((x) >> 1)] &= ~masks[lastbit]
                            dst[dstln + ((x) >> 1)] |= (c >> 4) << shifts[lastbit]
                            (x) += 1
                        if length == 0:
                            break
                        length -= 1
                        if x < width:
                            lastbit = (x) & 1
                            if dstln + ((x) >> 1) >= szDst:
                                return False
                            dst[dstln + ((x) >> 1)] &= ~masks[lastbit]
                            dst[dstln + ((x) >> 1)] |= (c & 0x0F) << shifts[lastbit]
                            (x) += 1
                    if ((bits - begin) & 1) != 0:
                        if bits >= len(bitdata):
                            return False
                        bits += 1

# Reads an OS/2 Presentation Manager (PM) icon, mouse pointer (cursor), bitmap (pixel image), or bitmap array,
# or a Windows bitmap, icon, or cursor.
# PM and Windows icons have the '.ico' file extension; PM cursors, '.ptr';
# PM and Windows bitmaps, '.bmp'; and Windows cursors, '.cur'.
# Returns a list of five-element lists, representing the decoded images
# in the order in which they were read.  If an icon, pointer, or
# bitmap could not be read, the value None takes the place of the
# corresponding five-element list.
# Each five-element list in the returned list contains the image,
# its width, its height, its hot spot x-coordinate, and its hot spot
# y-coordinate in that order. The image has the same format returned by the
# _desktopwallpaper_ module's blankimage() method with alpha=True. Notes:
# 1. The hot spot is the point in the image
# that receives the system's mouse position when that image is
# drawn on the screen.  The hot spot makes sense only for mouse pointers;
# the hot spot x- and y-coordinates are each 0 if the image relates to
# an icon or bitmap, rather than a pointer.
# 2. Although PM and Windows icons and cursors support pixels that invert
# the screen colors, this feature is not supported in images returned by
# this function; areas where the icon or cursor would invert screen colors
# are treated as transparent instead.
#
# NOTE: Windows icons and cursors (and OS/2 PM two-color icons and cursors) are
# stored in the form of an _XOR mask_ (color mask) as well as an _AND mask_
# ("inverted alpha" mask) where each pixel is either 0 or 1, a format that
# additionally allows for so-called "inverted pixels", where some existing
# pixels have their colors inverted.
# 1. First, the output pixels are combined using a bit-by-bit AND operation
# with the pixels in the AND mask, so that the output pixels become "black"
# (all bits zeros) where the AND mask pixel equals 0, in the _opaque_ areas
# of the icon or cursor, and left unchanged elsewhere.
# 2. Then, the output pixels are combined using a bit-by-bit exclusive-OR
# (XOR) operation with the pixels in the XOR mask, so that, among other things,
# the mask is copied to the output where the output is "black" (all its bits
# are zeros), and the rest of the output is inverted where the mask is "white"
# (all its bits are ones).
# For icons and cursors with only colored and transparent pixels (and no
# inverted, translucent, or semitransparent pixels), the XOR mask should be
# "black" (all bits zeros) wherever
# the AND mask pixel equals 1.  Later versions of Windows also allow for icons
# in Portable Network Graphics (PNG) format and icons where the XOR mask is 32
# bits per pixel, 8 of which is an _alpha component_ (an opacity value from 0,
# transparent, through 255, opaque); the latter kind of icon is drawn as
# follows: Where the AND mask is 0, the XOR mask's pixels are blended onto
# the output pixels with the specified alpha component as opacity, and where
# the AND mask is 1, the output pixels are left unchanged.
# Presentation Manager color icons employ three masks: a two-level AND mask, a two-level XOR
# mask, and a color mask: where the AND mask is 0, the color mask is copied to
# the output; otherwise, where the XOR mask is 1, the output's colors are
# inverted; otherwise, the output is left unchanged (see "Bitmap File Format",
# in the _Presentation Manager Programming Guide and Reference_).
def reados2icon(infile):
    f = open(infile, "rb")
    try:
        return reados2iconcore(f)
    finally:
        f.close()

# Reads cursor images from a file in the XCursor format.  The return value
# has the same format returned by the 'reados2icon' method.
def readxcursor(infile):
    f = open(infile, "rb")
    try:
        hdr = f.read(16)
        if len(hdr) != 16 or hdr[0:4] != b"Xcur":
            raise ValueError
        s = struct.unpack("<LLLL", hdr)
        if s[1] != 0x10 or s[2] != 0x10000:
            raise ValueError
        toccount = s[3]
        tocs = []
        images = []
        for i in range(toccount):
            tocs.append(struct.unpack("<LLL", f.read(12)))
        for toc in tocs:
            f.seek(toc[2])
            chunk = struct.unpack("<LLLL", f.read(16))
            if chunk[0] < 16 or chunk[1] != toc[0] or chunk[2] != toc[1]:
                _errprint(chunk)
                raise ValueError
            # There are also comments with chunk[1]==0xfffe0001,
            # but ignore them
            if chunk[1] == 0xFFFD0002:
                if chunk[0] < 36 or chunk[3] > 1:
                    # chunk too small, or unsupported cursor version
                    images.append(None)
                    continue
                chunk = struct.unpack("<LLLLL", f.read(20))
                # chunk[4] is delay in milliseconds
                if (
                    chunk[0] >= 0x8000
                    or chunk[1] >= 0x8000
                    or chunk[2] > chunk[0]
                    or chunk[3] > chunk[1]
                ):
                    images.append(None)
                    continue
                image = [0 for i in range(chunk[0] * chunk[1] * 4)]
                for i in range(chunk[0] * chunk[1]):
                    argb = f.read(4)
                    if len(argb) < 4:
                        images.append(None)
                        continue
                    image[i * 4] = argb[2]
                    image[i * 4 + 1] = argb[1]
                    image[i * 4 + 2] = argb[0]
                    image[i * 4 + 3] = argb[3]
                images.append([image, chunk[0], chunk[1], chunk[2], chunk[3]])
        return images
    finally:
        f.close()

# Same as 'reados2icon', but takes an I/O object such as one
# returned by Python's 'open' method.
def reados2iconcore(f):
    ft = f.tell()
    tag = f.read(2)
    # Bitmap array (BA)
    # NOTE: BA=>'PT'/'CP' allows for animated pointers.
    # NOTE: BA=>'IC'/'CI' allows for varying the icon's
    #   size or color depth.
    if tag == b"BA":
        f.seek(ft)
        # The first offset is "device independent";
        # the others are "device dependent".
        offsets = [ft + 0x0E]
        infos = []
        while True:
            tag = f.read(2)
            if tag != b"BA":
                raise ValueError
            info = struct.unpack(
                "<LLHH", f.read(0x0C)
            )  # size, next, display width in pixels,
            # display height in pixels (the latter two
            # can be zero)
            # Combinations of display width/height seen
            # include 640 &times; 200 (CGA, usually with half-height
            # icons), 640 &times; 350 (EGA), 640 &times; 480, 1024 &times; 768.
            endInfo = f.tell()
            infos.append(info)
            if info[1] == 0:
                break
            else:
                contentSize = (ft + info[1]) - endInfo
                if contentSize < 2:
                    raise ValueError("unsupported content size")
                offsets.append((ft + info[1]) + 0x0E)
                f.seek(ft + info[1])
        ret = []
        for i in range(len(offsets)):
            f.seek(offsets[i])
            ret.append(_readicon(f))
        return ret
    elif tag == bytes([2, 0]):
        # Old Windows bitmap
        f.seek(ft)
        return _readoldbitmap(f)
    elif tag == bytes([2, 0x81]):
        # Old Windows bitmap
        f.seek(ft)
        return _readoldbitmap(f)
    elif tag == bytes([2, 0x01]):
        # Old Windows bitmap
        f.seek(ft)
        return _readoldbitmap(f)
    elif (
        tag == bytes([1, 0])
        or tag == bytes([3, 0])
        or tag == bytes([1, 1])
        or tag == bytes([1, 2])
        or tag == bytes([3, 2])
    ):
        # Old Windows icon or cursor
        return _readoldicon(f, tag[0], tag[1])
    elif tag == bytes([0, 0]):
        # Windows icon
        f.seek(ft)
        return _readwinicon(f)
    elif (
        tag != b"CI" and tag != b"CP" and tag != b"IC" and tag != b"PT" and tag != b"BM"
    ):
        return []
    else:
        f.seek(ft)
        return [_readicon(f)]

# Reads the color table from an OS/2 Presentation Manager or Windows palette file.
# Returns an list of the colors read from the file.
# Each element in the list is a color in the form of a three-element list consisting of
# the color's red, green, and blue component, in that
# order; each component is an integer from 0 through 255.
def reados2palette(infile):
    f = open(infile, "rb")
    try:
        tag1 = f.read(4)
        if tag1 == b"RIFF":
            return _readwinpal(f)
        tag = struct.unpack("<HH", tag1)
        if tag[0] != 0x983:
            raise ValueError
        pal = [None for i in range(tag[1])]
        for i in range(tag[1]):
            col = f.read(3)
            # NOTE: The ordering of the elements
            # in palette resources is blue, green,
            # red.
            pal[i] = [col[2], col[1], col[0]]
        # After the colors come tag[1] many bytes,
        # but all of them are zeros in the palette files
        # I've found so far
        return pal
    finally:
        f.close()

def _readwinpal(f):
    ret = []
    sz = struct.unpack("<L", f.read(4))[0]
    if sz < 4:
        raise ValueError
    endpos = f.tell() + sz
    fcc = f.read(4)
    if fcc != b"PAL ":
        raise ValueError
    while True:
        if f.tell() >= endpos:
            raise ValueError
        fcc = f.read(4)
        sz = struct.unpack("<L", f.read(4))[0]
        if fcc == b"data":
            if sz < 4:
                raise ValueError
            info = struct.unpack("<HH", f.read(4))
            if info[0] != 0x300:
                raise ValueError
            if info[1] * 4 + 4 != sz:
                return None
            for i in range(info[1]):
                color = struct.unpack("<BBBB", f.read(4))
                ret.append([color[0], color[1], color[2]])
            return ret
        else:
            f.seek(f.tell() + sz)

def _readoldicon(f, kind, num):
    if num == 0:
        return _readoldiconcore(f, kind)
    ret = [None for i in range(num)]
    for i in range(num):
        ic = _readoldiconcore(f, kind, keepopen=True)
        if len(ic) == 0:
            break
        ret[i] = ic[0]
    f.close()
    return ret

def _readoldiconcore(f, kind, keepopen=False):
    # Read Windows 2.x icon or cursor
    fr = f.read(12)
    if len(fr) < 12:
        if not keepopen:
            f.close()
        return []
    header = (kind, 0) + struct.unpack("<HHHHHH", fr)
    if header[0] != 0x01 and header[0] != 0x03:
        # Not an icon or cursor
        print("A")
        if not keepopen:
            f.close()
        return []
    # Hot spots are valid for icons and pointers (cursors).
    hotspotx = header[1]
    hotspoty = header[2]
    width = header[4]
    height = header[5]
    widthbytes = header[6]
    needed = (width + 7) >> 3
    if widthbytes < needed:
        # Widthbytes insufficient
        print("C")
        if not keepopen:
            f.close()
        return []
    if header[7] != 0:
        # Not supported
        print(["D", header[7]])
        if not keepopen:
            f.close()
        return []
    if width == 0 or height == 0 or widthbytes == 0:
        print("E")
        if not keepopen:
            f.close()
        return []
    img = dw.blankimage(width, height, [0, 0, 0, 255], alpha=True)
    pos = 0
    # AND mask
    for y in range(height):
        fr = f.read(widthbytes)
        if len(fr) != widthbytes:
            if not keepopen:
                f.close()
            return []
        for x in range(width):
            bit = fr[x >> 3] & (1 << (7 - (x & 7)))
            if bit != 0:
                img[pos + 3] = 0
            pos += 4
    # XOR mask
    pos = 0
    for y in range(height):
        fr = f.read(widthbytes)
        if len(fr) != widthbytes:
            if not keepopen:
                f.close()
            return []
        for x in range(width):
            bit = fr[x >> 3] & (1 << (7 - (x & 7)))
            if bit != 0:
                img[pos] = img[pos + 1] = img[pos + 2] = 255
            else:
                img[pos] = img[pos + 1] = img[pos + 2] = 0
            pos += 4
    if not keepopen:
        f.close()
    return [[img, width, height, hotspotx, hotspoty]]

def _readoldbitmap(f):
    # Read Windows 2.x bitmap
    fr = f.read(16)
    if len(fr) < 16:
        f.close()
        return []
    header = struct.unpack("<BBBBHHHBBL", fr)
    if header[0] != 0x02:
        # Not a bitmap
        f.close()
        return []
    if header[7] != 0x01:
        # Unsupported plane count
        f.close()
        return []
    if header[8] != 0x01:
        # Unsupported bits per pixel
        f.close()
        return []
    width = header[4]
    height = header[5]
    widthbytes = header[6]
    needed = (width + 7) >> 3
    if widthbytes < needed:
        # Widthbytes insufficient
        f.close()
        return []
    if header[9] != 0 or header[4] == 0 or header[5] == 0 or header[6] == 0:
        f.close()
        return []
    img = dw.blankimage(header[4], header[5], [0, 0, 0, 255], alpha=True)
    pos = 0
    for y in range(header[5]):
        fr = f.read(header[6])
        if len(fr) != header[6]:
            f.close()
            return []
        for x in range(header[4]):
            bit = fr[x >> 3] & (1 << (7 - (x & 7)))
            if bit != 0:
                img[pos] = img[pos + 1] = img[pos + 2] = 255
            pos += 4
    f.close()
    return [[img, header[4], header[5], 0, 0]]

# Reads the bitmaps, icons, and pointers in an OS/2 Presentation Manager theme resource file.
# A Presentation Manager theme resource file is a collection of Presentation Manager-compatible
# resources such as bitmaps, icons, pointers, and text string tables.
# These theme resource files have the extensions .itr, .cmr, .ecr,
# .inr, .mmr, and .pmr.
# Returns a list of elements, each of which has the format described
# in the _reados2icon_ method.
def readitr(infile):
    _errprint(infile)
    f = open(infile, "rb")
    try:
        ret = []
        i = 0
        nextpos = 0
        while True:
            f.seek(nextpos)
            head = f.read(12)
            if len(head) == 0:
                return ret
            st = struct.unpack("<HBHBHL", head)
            st0 = (st[1] << 8) | st[0]
            st1 = (st[3] << 8) | st[2]
            if (st[0] & 0xFF) != 0xFF and len(ret) == 0:
                # probably not a theme resource file
                return ret
            size = st[5]
            if size < 2:
                raise ValueError("unsupported content size")
            curpos = f.tell()
            nextpos = curpos + size
            limf = _LimitedIO(f, size)
            tag = limf.read(2)
            if (
                tag != b"CI"
                and tag != b"BA"
                and tag != b"CP"
                and tag != b"IC"
                and tag != b"PT"
                and tag != b"BM"
            ):
                # Not an image, skipping
                i += 1
                continue
            limf.seek(0)
            ret.append(reados2iconcore(limf))
            i += 1
    finally:
        f.close()

def _read1bppBitmap(byteData, scanSize, height, x, y):
    # Reads the bit value of an array of bottom-up 1-bit-per-pixel
    # Windows or Presentation Manager bitmap data.
    return (byteData[scanSize * (height - 1 - y) + (x >> 3)] >> (7 - (x & 7))) & 1

def _read2bppBitmap(byteData, scanSize, height, x, y):
    # Reads the bit value of an array of bottom-up 2-bit-per-pixel
    # Windows CE bitmap data.
    # References: Black, J., Christiansen, J., "Microsoft Windows CE Display
    # Drivers and Hardware", September 1997.
    return (byteData[scanSize * (height - 1 - y) + (x >> 2)] >> (3 - (x & 3))) & 3

def _read4bppBitmap(byteData, scanSize, height, x, y):
    # Reads the bit value of an array of bottom-up 4-bit-per-pixel
    # Windows or Presentation Manager bitmap data.
    return (
        byteData[scanSize * (height - 1 - y) + (x >> 1)] >> (4 * (1 - (x & 1)))
    ) & 0x0F

def _readBitmapAlpha(byteData, scanSize, height, bpp, x, y):
    # Reads the alpha value at the specified pixel position of a pixel image,
    # represented by an array of bottom-up Windows or Presentation Manager bitmap data.
    # Returns 255 if bpp is not 32.
    if bpp == 32:
        row = scanSize * (height - 1 - y)
        return byteData[row + x * 4 + 3]
    else:
        return 255

def _readBitmapAsAlphaBitfields(byteData, scanSize, height, bpp, x, y, alphamask):
    # Reads the alpha at the specified pixel position of a pixel image
    # that uses a bitfield format and is
    # represented by an array of bottom-up Windows bitmap data.
    # Returns bytes([255]) if bpp is not 16 or 32.
    match bpp:
        case 16:
            row = scanSize * (height - 1 - y)
            ret = byteData[row + x * 2 : row + x * 2 + 2]
            v = ret[0] | (ret[1] << 8)
            return bytes([((v & alphamask[0]) >> alphamask[2]) << alphamask[1]])
        case 32:
            row = scanSize * (height - 1 - y)
            ret = byteData[row + x * 4 : row + x * 4 + 4]
            v = ret[0] | (ret[1] << 8) | (ret[2] << 16) | (ret[3] << 24)
            return bytes([((v & alphamask[0]) >> alphamask[2]) << alphamask[1]])
        case _:
            return bytes([255])

def _readBitmapAsColorBitfields(byteData, scanSize, height, bpp, x, y, bitfields):
    # Reads the pixel color value at the specified position of a pixel image
    # that uses a bitfield format and is
    # represented by an array of bottom-up Windows bitmap data.
    # The color value is returned as an array containing the blue, green,
    # and red components, in that order.
    match bpp:
        case 16:
            row = scanSize * (height - 1 - y)
            ret = byteData[row + x * 2 : row + x * 2 + 2]
            v = ret[0] | (ret[1] << 8)
            return bytes(
                [
                    ((v & bitfields[2][0]) >> bitfields[2][2]) << bitfields[2][1],
                    ((v & bitfields[1][0]) >> bitfields[1][2]) << bitfields[1][1],
                    ((v & bitfields[0][0]) >> bitfields[0][2]) << bitfields[0][1],
                ]
            )
        case 32:
            row = scanSize * (height - 1 - y)
            ret = byteData[row + x * 4 : row + x * 4 + 4]
            v = ret[0] | (ret[1] << 8) | (ret[2] << 16) | (ret[3] << 24)
            return bytes(
                [
                    ((v & bitfields[2][0]) >> bitfields[2][2]) << bitfields[2][1],
                    ((v & bitfields[1][0]) >> bitfields[1][2]) << bitfields[1][1],
                    ((v & bitfields[0][0]) >> bitfields[0][2]) << bitfields[0][1],
                ]
            )
        case _:
            raise ValueError("Bits per pixel not supported")

def _readBitmapAsColorBGR(byteData, scanSize, height, bpp, x, y, palette):
    # Reads the pixel color value at the specified position of a pixel image,
    # represented by an array of bottom-up Windows or Presentation Manager bitmap data.
    # The color value is returned as an array containing the blue, green,
    # and red components, in that order.
    match bpp:
        case 1:
            return palette[_read1bppBitmap(byteData, scanSize, height, x, y)]
        case 2:
            return palette[_read2bppBitmap(byteData, scanSize, height, x, y)]
        case 4:
            return palette[_read4bppBitmap(byteData, scanSize, height, x, y)]
        case 8:
            return palette[byteData[scanSize * (height - 1 - y) + x]]
        case 16:
            row = scanSize * (height - 1 - y)
            ret = byteData[row + x * 2 : row + x * 2 + 2]
            v = ret[0] | (ret[1] << 8)
            vr, vg, vb = (
                ((v) & 0x1F) << 3,
                ((v >> 5) & 0x1F) << 3,
                ((v >> 10) & 0x1F) << 3,
            )
            return bytes(
                [
                    0xFF if vr == 0x1F else vr,
                    0xFF if vg == 0x1F else vg,
                    0xFF if vb == 0x1F else vb,
                ]
            )
        case 24:
            row = scanSize * (height - 1 - y)
            return byteData[row + x * 3 : row + x * 3 + 3]
        case 32:
            row = scanSize * (height - 1 - y)
            return byteData[row + x * 4 : row + x * 4 + 3]
        case _:
            raise ValueError("Bits per pixel not supported")

def _pilReadImage(imagebytes):
    try:
        image = PIL.Image.open(io.BytesIO(imagebytes))
    except:
        return [None, 0, 0]
    if not image:
        return [None, 0, 0]
    if image.mode == "1":
        # PIL (or at least the Pillow fork) has a bug where transparent
        # 1-bit PNGs are not recognized as transparent after conversion
        # to RGBA
        return [None, 0, 0]
    image = image.convert("RGBA")
    iconimg = [0 for i in range(image.width * image.height * 4)]
    pos = 0
    for y in range(image.height):
        for x in range(image.width):
            px = image.getpixel((x, y))
            iconimg[pos] = px[0]
            iconimg[pos + 1] = px[1]
            iconimg[pos + 2] = px[2]
            iconimg[pos + 3] = px[3]
            pos += 4
    return [iconimg, image.width, image.height]

def _readwiniconcore(f, entry, isicon, hotspot, resourceSize):
    ft = f.tell()
    tagbytes = f.read(4)
    if len(tagbytes) < 4:
        return None
    tag = struct.unpack("<L", tagbytes)
    if tag[0] != 0x28:
        if (
            tag[0] == 0x474E5089
            and resourceSize >= 8
            and f.read(4) == b"\x0d\x0a\x1a\x0a"
        ):
            imagebytes = tagbytes + b"\x0d\x0a\x1a\x0a" + f.read(resourceSize - 8)
            iconimg, width, height = _pilReadImage(imagebytes)
            if not iconimg:
                return None
            return [
                iconimg,
                width,
                height,
                hotspot[0] if hotspot else 0,
                hotspot[1] if hotspot else 1,
            ]
        else:
            if tag[0] < 512:
                _errprint("unsupported header size: %d [%08X]" % (tag[0], ft))
            return None
    bmih = tag + struct.unpack("<llHHLLllLL", f.read(0x24))
    bitcount = bmih[4]
    colortablesize = 1 << bitcount if bitcount <= 8 else 0
    if colortablesize > 0 and bmih[9] != 0:
        if bmih[9] > colortablesize:
            _errprint("bad biClrUsed")
            return None
        colortablesize = min(colortablesize, bmih[9])
    if bmih[7] != 0 or bmih[8] != 0:
        _errprint("unusual: resolution given: %d, %d" % (bmih[7], bmih[8]))
    # if entry and (bmih[1] != entry[0] or bmih[2] != entry[1] * 2):
    #    # Nonmatching width and height
    #    _errprint("bad header: bmih=%dx%d entry=%dx%d"%(bmih[1],bmih[2],entry[0],entry[1]*2))
    #    return None
    # if entry and isicon and entry[3]!=bmih[4]:
    #   # nonmatching bit count
    #   return None
    if (
        bmih[1] < 0
        or bmih[2] < 0
        or bmih[3] != 1
        or bmih[5] != 0
        or (bmih[9] != 0 and (colortablesize == 0 or bmih[9] > colortablesize))
        or (
            bmih[10] != 0
            and (
                colortablesize == 0
                or bmih[9] > colortablesize
                or (bmih[9] > 0 and bmih[10] > bmih[9])
            )
        )
    ):
        _errprint(["bad header", bmih])
        return None
    sizeImage = bmih[6]
    width = bmih[1]
    if bmih[2] % 2 != 0:
        _errprint("odd height value")
        return None
    height = bmih[2] // 2
    if (
        bitcount != 1
        and bitcount != 4
        and bitcount != 8
        and bitcount != 16
        and bitcount != 24
        and bitcount != 32
    ):
        _errprint("unsupported bit count")
        return None
    xormaskscan = ((width * bitcount + 31) >> 5) << 2
    andmaskscan = ((width * 1 + 31) >> 5) << 2
    xormaskbytes = xormaskscan * height
    andmaskbytes = andmaskscan * height
    if isicon and bitcount <= 8 and entry and entry[2] > colortablesize:
        _errprint("too few colors")
        return None
    colortable = []
    failed = False
    for j in range(colortablesize):
        r = f.read(3)
        if len(r) != 3:
            failed = True
            break
        colortable.append(r)
        if len(f.read(1)) != 1:
            failed = True
            break
    if failed:
        _errprint("color table read failed")
        return None
    xormask = f.read(xormaskbytes)
    if len(xormask) != xormaskbytes:
        _errprint(
            "xormask length doesn't match: %d, xormaskbytes=%d [sizeimage=%d]"
            % (len(xormask), xormaskbytes, bmih[6])
        )
        return None
    andmask = f.read(andmaskbytes)
    if len(andmask) != andmaskbytes:
        _errprint(
            "andmask length doesn't match: %d, andmaskbytes=%d [sizeimage=%d]"
            % (len(andmask), andmaskbytes, bmih[6])
        )
        # _errprint(bmih)
        return None
    bl = dw.blankimage(width, height, alpha=True)
    alpha1 = bytes([0xFF])
    alpha0 = bytes([0])
    for y in range(height):
        for x in range(width):
            bitand = _read1bppBitmap(andmask, andmaskscan, height, x, y)
            pxalpha = _readBitmapAlpha(xormask, xormaskscan, height, bitcount, x, y)
            # if pxalpha>255: raise ValueError
            px = _readBitmapAsColorBGR(
                xormask, xormaskscan, height, bitcount, x, y, colortable
            ) + (
                (bytes(pxalpha) if pxalpha != 255 else alpha1)
                if bitand == 0
                else alpha0
            )
            try:
                dw.setpixelbgralpha(bl, width, height, x, y, px)
            except:
                _errprint("failure to set pixel")
                return None
    return [
        bl,
        width,
        height,
        hotspot[0] if hotspot else 0,
        hotspot[1] if hotspot else 0,
    ]

def _dup(x):
    if x == None:
        return None
    return [([[z for z in y[0]], y[1], y[2], y[3], y[4]] if y else None) for y in x]

# Reads from a Windows animated icon/cursor file.  The return value
# has the same format returned by the 'readitr' method.
def readanimicon(infile):
    f = open(infile, "rb")
    try:
        ret = []
        if f.read(4) != b"RIFF":
            return ret
        sz = struct.unpack("<L", f.read(4))[0]
        if sz < 4:
            return ret
        endpos = f.tell() + sz + (sz & 1)
        fcc = f.read(4)
        if fcc != b"ACON":
            return ret
        haveAnih = False
        anih = None
        seq = None
        while True:
            if f.tell() >= endpos:
                return ret
            fcc = f.read(4)
            sz = struct.unpack("<L", f.read(4))[0]
            if fcc == b"LIST":
                if sz < 4:
                    raise ValueError
                ft = f.tell()
                listSz = sz
                fcc = f.read(4)
                if fcc == b"fram":
                    if not haveAnih:
                        return ret
                    content = io.BytesIO(f.read(sz - 4))
                    # adjust in case chunk size is odd (see Win32
                    # documentation for mmioAscend function).
                    if (sz & 1) == 1:
                        f.read(1)
                    while True:
                        if content.tell() == listSz - 4:
                            break
                        fcc = content.read(4)
                        if len(fcc) != 4:
                            return []
                        sz = struct.unpack("<L", content.read(4))[0]
                        if fcc == b"icon":
                            icon = _readwinicon(io.BytesIO(content.read(sz)))
                            if (sz & 1) == 1:
                                content.read(1)
                            ret.append(icon)
                        else:
                            content.seek(f.tell() + sz + (sz & 1))
                    if len(ret) != anih[1]:
                        raise ValueError
                    if seq:
                        ret = [_dup(ret[frame]) for frame in seq]
                    return ret
                else:
                    f.seek(f.tell() + sz - 4 + (sz & 1))
            elif fcc == b"anih":
                if haveAnih:
                    return ret
                haveAnih = True
                if sz != 0x24:
                    raise ValueError
                anih = struct.unpack("<LLLLLLLLL", f.read(0x24))
                if anih[0] != 0x24:
                    raise ValueError
                # anih[1] = images
                # anim[2] = frames
            elif fcc == b"seq ":
                if seq or not haveAnih:
                    return ret
                seq = []
                if sz < 4 or sz % 4 != 0:
                    raise ValueError
                for i in range(sz // 4):
                    frame = struct.unpack("<L", f.read(4))[0]
                    if frame >= anih[1]:
                        raise ValueError
                    seq.append(frame)
            else:
                f.seek(f.tell() + sz + (sz & 1))
    finally:
        f.close()

# Reads images from a Windows icon or cursor file.  The return value
# has the same format returned by the 'reados2icon' method.
def readwinicon(infile):
    f = open(infile, "rb")
    try:
        return readwinicon(f)
    finally:
        f.close()

def _readwinicon(f):
    ft = f.tell()
    newheader = struct.unpack("<HHH", f.read(6))
    isicon = newheader[1] == 1
    iscursor = newheader[1] == 2
    if newheader[0] != 0 or ((not isicon) and (not iscursor)):
        return []
    entries = []
    for i in range(newheader[2]):
        tag = f.read(16)
        if len(tag) < 16:
            entries.append(None)
            continue
        dirent = struct.unpack("<BBBBHHLL", tag)
        width = 256 if dirent[0] == 0 else dirent[0]
        height = 256 if dirent[1] == 0 else dirent[1]
        colorcount = dirent[2]
        if iscursor:
            if dirent[4] == 0xFFFF and dirent[5] == 0xFFFF:
                _errprint("no hot spot?")
            elif dirent[4] > width or dirent[5] > height:
                if i < 20:
                    _errprint(
                        "hot spot out of bounds: %d/%d %d/%d"
                        % (dirent[4], width, dirent[5], height)
                    )
                entries.append(None)
                continue
        elif isicon:
            # colorcount is supposed to equal 2^(planes*bitcount),
            # or equal 0 if bitcount is 8 or greater.
            # But some icons can have a colorcount of 0 in practice.
            # Reference: Raymond Chen, "The evolution of the ICO file format,
            # part 1: Monochrome beginnings", The Old New Thing, Oct. 18, 2010.
            # ---
            # Apparently, planes and bit count can be 0.
            if dirent[3] != 0:
                _errprint("unsupported reserved value")
                entries.append(None)
                continue
            if dirent[4] != 0 and dirent[4] != 1:
                _errprint("unsupported planes")
                entries.append(None)
                continue
            if dirent[5] >= 8 and colorcount != 0:
                _errprint(
                    "unsupported bit count and color count: %d, %d"
                    % (dirent[5], colorcount)
                )
                entries.append(None)
                continue
            if (
                dirent[5] != 0
                and dirent[5] != 1
                and dirent[5] != 2
                and dirent[5] != 4
                and dirent[5] != 8
                and dirent[5] != 24
            ):
                _errprint("unsupported bit count")
                entries.append(None)
                continue
        entries.append(
            [width, height, colorcount, dirent[5], dirent[6], dirent[7] + ft, dirent[4]]
        )
    for i in range(len(entries)):
        if not entries[i]:
            continue
        f.seek(entries[i][5])
        # print("%04X" %(entries[i][5]))
        entries[i] = _readwiniconcore(
            f,
            entries[i],
            newheader[1] == 1,
            [entries[i][6], entries[i][3]] if iscursor else None,
            entries[i][4],
        )
        if entries[i] and len(entries[i]) < 5:
            raise ValueError
    return entries

def _maskToLeftShift(mask):
    if mask == 0:
        return 0
    while (mask & 1) == 0:
        mask >>= 1
    shift = 0
    while (mask & 1) != 0:
        mask >>= 1
        shift += 1
    return 8 - shift

def _maskToRightShift(mask):
    if mask == 0:
        return 0
    shift = 0
    while (mask & 1) == 0:
        mask >>= 1
        shift += 1
    return shift

def _readicon(f, packedWinBitmap=False):
    unusual = False
    isColor = False
    isIcon = False
    isPointer = False
    isBitmap = False
    hotspotX = 0
    hotspotY = 0
    if not packedWinBitmap:
        tag = f.read(2)
        if len(tag) < 0:
            raise ValueError
        if (
            tag != b"CI"
            and tag != b"CP"
            and tag != b"IC"
            and tag != b"PT"
            and tag != b"BM"
        ):
            _errprint("unrecognized tag: %s" % (tag))
            return None
        isColor = tag == b"CI" or tag == b"CP"  # color icon or color pointer
        isIcon = tag == b"CI" or tag == b"IC"
        isPointer = tag == b"CP" or tag == b"PT"
        isBitmap = tag == b"BM"
        andmaskinfo = struct.unpack("<LHHL", f.read(0x0C))
        # The meaning of this field differs in Windows and Presentation Manager bitmaps
        offsetToImage = andmaskinfo[3]
        if not isBitmap:
            hotspotX = andmaskinfo[1]  # hot spot is valid for icons and pointers
            hotspotY = andmaskinfo[2]  # hot spot is valid for icons and pointers
    else:
        isBitmap = True
    # Read info on the AND mask or bitmap
    andmask = None
    andmaskcolors = None
    colormask = None
    colormaskscan = 0
    colormaskcolors = None
    andmaskhdr = struct.unpack("<L", f.read(4))
    andpalette = 0
    andcompression = 0
    andsizeImage = 0
    andcolormasks = None
    andalphamask = None
    andTopdown = False
    bitfields = None
    andmaskextra = None
    if andmaskhdr[0] == 0x0C:
        # BITMAPCOREHEADER from OS/2 Presentation Manager
        fr = f.read(8)
        if len(fr) < 8:
            return None
        andmaskhdr += struct.unpack("<HHHH", fr)
        if andmaskhdr[4] <= 8:
            andpalette = 1 << andmaskhdr[4]
    elif andmaskhdr[0] < 0x10:
        _errprint("unsupported header size")
        return None
    elif andmaskhdr[0] >= 40:
        fr = f.read(36)
        if len(fr) < 36:
            return None
        andmaskhdr += struct.unpack("<llHHLLllLL", fr)
        slack = f.read(andmaskhdr[0] - 40)
        andmaskextra = slack
        andsizeImage = andmaskhdr[6]
        if andmaskhdr[4] <= 8:
            andpalette = 1 << andmaskhdr[4]
        if (
            andmaskhdr[4] <= 8 or andmaskhdr[4] == 16 or andmaskhdr[4] == 32
        ) and andmaskhdr[
            9
        ] != 0:  # biClrUsed
            andpalette = min(andpalette, andmaskhdr[9])
        andcompression = andmaskhdr[5]
        if andcompression > 4:
            _errprint("unsupported compression: %d" % (andcompression))
            return None
        if (
            (andcompression == 1 and andmaskhdr[4] != 8)
            or (andcompression == 2 and andmaskhdr[4] != 4)
            or (andcompression == 4 and andmaskhdr[4] != 24)
            or (
                andcompression == 3
                and andmaskhdr[4] != 1
                and andmaskhdr[4] != 16
                and andmaskhdr[4] != 32
            )
        ):
            _errprint("unsupported compression: %d" % (andcompression))
            return None
        if andmaskhdr[7] != 0 or andmaskhdr[8] != 0:
            # resolutions seen include 3622 &times; 3622 pixels per meter (about 92 dpi)
            # Also seen: 2833 &times; 2833; 2834 &times; 2834; 2667 &times; 2667; 2667 &times; 2000 (EGA); 2667 &times; 1111 (CGA)
            # _errprint(
            #    "nonzero compression or resolution: %d %d %d"
            #    % (andmaskhdr[5], andmaskhdr[7], andmaskhdr[8])
            # )
            pass
        allzeros = True
        if andmaskhdr[0] >= 0x6C:
            if len(andmaskextra) < 68:
                _errprint(["header not long enough"])
                return None
            extrainfo = struct.unpack("<LLLLLLLLLLLLLLLLL", andmaskextra[0:68])
            for i in range(5, 5 + 12):
                if slack[i] != 0:
                    allzeros = False
            andalphamask = [
                extrainfo[3],
                _maskToLeftShift(extrainfo[3]),
                _maskToRightShift(extrainfo[3]),
            ]
            if andalphamask[1] < 0 or (andalphamask[0] >> andalphamask[2]) > 255:
                _errprint(["unsupported alpha mask", andalphamask])
                return None
        if andmaskhdr[0] >= 0x7C:
            if len(andmaskextra) + 0x28 < andmaskhdr[0]:
                _errprint(
                    "size of extras plus original header is smaller than declared header size: %d, %d"
                    % (
                        len(andmaskextra),
                        andmaskhdr[0],
                    )
                )
                return None
            extrainfo = struct.unpack("<LLLLLLLLLLLLLLLLLLLLL", andmaskextra[0:84])
            for i in range(5, 5 + 12):
                if slack[i] != 0:
                    allzeros = False
            for i in range(13, 16):
                if slack[i] != 0:
                    allzeros = False
        else:
            for i in range(len(slack)):
                if slack[i] != 0:
                    allzeros = False
        if not allzeros:
            # andmaskhdr[0] == 0x6c indicates BITMAPV4HEADER
            # andmaskhdr[0] == 0x7c indicates BITMAPV5HEADER
            _errprint("nonzero slack; ignore the slack")
    elif andmaskhdr[0] >= 0x10:
        fr = f.read(12)
        if len(fr) < 12:
            _errprint("too short")
            return None
        andmaskhdr += struct.unpack("<llHH", fr)
        if andmaskhdr[4] <= 8:
            andpalette = 1 << andmaskhdr[4]
        slack = f.read(andmaskhdr[0] - 0x10)
        if len(fr) < andmaskhdr[0] - 0x10:
            _errprint("too short")
            return None
        allzeros = True
        for i in range(len(slack)):
            if slack[i] != 0:
                allzeros = False
        if not allzeros:
            _errprint("nonzero slack")
            return None
    if andmaskhdr[2] < 0 and not (
        isBitmap
        and (
            andcompression == 0
            or (andcompression == 3 and (andmaskhdr[4] == 16 or andmaskhdr[4] == 32))
        )
    ):
        if isBitmap:
            _errprint("top-down bitmaps not supported for this kind of bitmap")
        else:
            _errprint(
                "top-down bitmaps not supported for Presentation Manager icons and cursors"
            )
        return None
    if andmaskhdr[1] == 0 or andmaskhdr[2] == 0:
        _errprint("zero image size not supported")
        return None
    if (isIcon or isPointer) and abs(andmaskhdr[2]) % 2 != 0:
        raise ValueError("mask height is odd")
    if andmaskhdr[3] != 1:
        _errprint("unsupported no. of planes")
        return None
    if isBitmap:
        if (
            andmaskhdr[4] != 1
            and andmaskhdr[4] != 4
            # support 2-bit-per-pixel bitmaps only if header's size is
            # that of BITMAPINFOHEADER and only if uncompressed;
            # such bitmaps are a Windows CE peculiarity
            and not (andmaskhdr[4] == 2 and andmaskhdr[0] == 40 and andcompression == 0)
            and andmaskhdr[4] != 8
            and andmaskhdr[4] != 16
            and andmaskhdr[4] != 24
            and andmaskhdr[4] != 32
        ):
            _errprint("unsupported bits per pixel: %d" % (andmaskhdr[4]))
            return None
    else:
        if andmaskhdr[4] != 1:  # Only 1-bpp AND/XOR masks are supported
            raise ValueError("unsupported bits per pixel: %d" % (andmaskhdr[4]))
        if andpalette != 2:
            _errprint("unusual palette size: %d" % (andpalette))
            unusual = None
    if andmaskhdr[1] < 0:
        _errprint("negative width")
        return None
    andcolortable = f.tell()
    f.seek(andcolortable + andpalette * (3 if andmaskhdr[0] <= 0x0C else 4))
    if packedWinBitmap:
        offsetToImage = f.tell()
    w = andmaskhdr[1]
    h = abs(andmaskhdr[2])
    andmaskscan = ((w * andmaskhdr[4] + 31) >> 5) << 2
    andmaskbits = andmaskscan * h
    if isColor:
        # Read info on the color mask
        newtag = f.read(2)
        if newtag != tag:
            raise ValueError
        colormaskinfooffset = f.tell()
        colormaskinfo = struct.unpack("<LHHL", f.read(0x0C))
        if (not isBitmap) and hotspotX != colormaskinfo[1]:
            raise ValueError
        if (not isBitmap) and hotspotY != colormaskinfo[2]:
            raise ValueError
        o = f.tell()
        colorcompression = 0
        colorpalette = 0
        colorsizeImage = 0
        colormaskhdr = struct.unpack("<L", f.read(4))
        if colormaskhdr[0] == 0x0C:
            colormaskhdr += struct.unpack("<HHHH", f.read(8))
            if colormaskhdr[4] <= 8:
                colorpalette = 1 << colormaskhdr[4]
        elif colormaskhdr[0] < 0x10:
            _errprint("unsupported header size")
            return None
        elif colormaskhdr[0] >= 40:
            colormaskhdr += struct.unpack("<llHHLLllLL", f.read(36))
            slack = f.read(colormaskhdr[0] - 40)
            colorsizeImage = colormaskhdr[6]
            colorcompression = colormaskhdr[5]
            if colormaskhdr[4] <= 8:
                colorpalette = 1 << colormaskhdr[4]
            if colormaskhdr[4] <= 8 and colormaskhdr[9] != 0:  # biClrUsed
                colorpalette = min(colorpalette, colormaskhdr[9])
            if colorcompression > 4:
                _errprint("unsupported compression: %d" % (colorcompression))
                return None
            if (
                (colorcompression == 1 and colormaskhdr[4] != 8)
                or (colorcompression == 2 and colormaskhdr[4] != 4)
                or (colorcompression == 4 and colormaskhdr[4] != 24)
                or (colorcompression == 3 and colormaskhdr[4] != 1)
            ):
                _errprint("unsupported compression: %d" % (colorcompression))
                return None
            if colormaskhdr[7] != 0 or colormaskhdr[8] != 0:
                # _errprint(
                #    "nonzero compression or resolution: %d %d %d"
                #    % (colormaskhdr[5], colormaskhdr[7], colormaskhdr[8])
                # )
                pass
            allzeros = True
            for i in range(len(slack)):
                if slack[i] != 0:
                    allzeros = False
            if not allzeros:
                _errprint("nonzero slack")
                return None
        elif colormaskhdr[0] >= 0x10:
            colormaskhdr += struct.unpack("<llHH", f.read(12))
            slack = f.read(colormaskhdr[0] - 0x10)
            allzeros = True
            for i in range(len(slack)):
                if slack[i] != 0:
                    allzeros = False
            if not allzeros:
                _errprint("nonzero slack")
                return None
        if colormaskhdr[1] < 0:
            return None
        colorbpp = colormaskhdr[4]
        if colormaskhdr[2] < 0:
            _errprint(
                "top-down color mask is not supported for Presentation Manager icons and cursors"
            )
            return None
        if colorbpp == 3:
            # NOTE: A 3 BPP color icon was attested, but it is unclear whether
            # Presentation Manager supports such 3 BPP icons.
            _errprint("3 bits per pixel not supported")
            return None
        if colormaskhdr[1] == 0 or colormaskhdr[2] == 0:
            _errprint("zero image size not supported")
            return None
        if colormaskhdr[1] != andmaskhdr[1]:
            raise ValueError("unsupported width")
        if colormaskhdr[2] * 2 != abs(andmaskhdr[2]):
            raise ValueError("unsupported height")
        if colormaskhdr[3] != 1:
            _errprint("unsupported no. of planes")
            return None
        if colorbpp != 1 and colorbpp != 4 and colorbpp != 8 and colorbpp != 24:
            _errprint("unsupported bits per pixel: %d" % (colorbpp))
            return None
        colorpalette = 0
        if colorbpp <= 8:
            colorpalette = 1 << colorbpp
        colorcolortable = f.tell()
        w = colormaskhdr[1]
        h = colormaskhdr[2]
        colormaskscan = ((w * colorbpp + 31) >> 5) << 2
        colormaskbits = colormaskscan * h
    realHeight = abs(andmaskhdr[2] if isBitmap else andmaskhdr[2] // 2)
    # hot spot Y counts from the lower left row up, so adjust
    # for top-down convention
    if not isBitmap:
        hotspotY = realHeight - 1 - hotspotY
        if hotspotY < 0 or hotspotY >= realHeight:
            # hot spot outside image
            if isPointer:
                raise ValueError
        if hotspotX < 0 or hotspotX >= andmaskhdr[1]:
            # hot spot outside image
            if isPointer:
                raise ValueError
    tablesize = (1 << andmaskhdr[4]) if andpalette > 0 else 0
    # The palette of icons' and pointers' AND/XOR mask
    # is effectively fixed at black and white (that is,
    # (0,0,0) and (255,255,255), respectively).
    # It may be, but I am not sure, that OS/2 Presentation Manager
    # ignores the color table of icons' and pointers' AND/XOR mask.
    andmaskcolors = []
    if not (isIcon or isPointer):
        # Gather bitmap's color table if not an icon or pointer
        tablesize = 2
        if andcompression == 3 and (andmaskhdr[4] == 16 or andmaskhdr[4] == 32):
            # BI_BITFIELDS
            if andmaskhdr[0] < 0x6C:  # smaller than BITMAPV4HEADER
                f.seek(andcolortable)
                masks = f.read(12)
            else:
                masks = andmaskextra[0:12]
                # if andalphamask!=None and andalphamask[0]!=0:
                #    _errprint(["alpha mask not yet supported", masks,andalphamask])
                #    return None
            if len(masks) < 12:
                _errprint(["unsupported color masks: len=%d", len(masks)])
                return None
            masks = struct.unpack("<LLL", masks)
            # NOTE: Windows 95, 98, and Me support a bitmap with compression mode
            # BI_BITFIELDS only if the color masks are as follows:
            # 16 bpp: [0x7c00,0x3e0,0x1f] (5/5/5); [0xf800,0x7e0,0x1f] (5/6/5).
            # 32 bpp: [0xff0000,0xff00,0xff] (8/8/8).
            # This is according to "Windows 95/98/Me Graphics Device Interface".
            bitfields = [[m, _maskToLeftShift(m), _maskToRightShift(m)] for m in masks]
            for bf in bitfields:
                if bf[1] < 0 or (bf[0] >> bf[2]) > 255:
                    _errprint(["unsupported color masks", masks])
                    return None
            if packedWinBitmap:
                offsetToImage += 12
        if andpalette > 0:
            f.seek(andcolortable)
            cts = 3 if andmaskhdr[0] <= 0x0C else 4
            for i in range(andpalette):
                clr = f.read(3)  # BGR color
                andmaskcolors.append(clr)
                if len(clr) != 3:
                    _errprint(["color table can't be read"])
                    return None
                if cts > 3:
                    f.read(cts - 3)
            for i in range((1 << andmaskhdr[4]) - andpalette):
                clr = bytes([0, 0, 0])
                andmaskcolors.append(clr)
    # Offset from the beginning of the file, not necessarily
    # from the beginning of the bitmap/icon/cursor header.
    # If packedWinBitmap is true, this is instead the offset
    # immediately after the header and color table.
    # _errprint(["offsetToImage",offsetToImage])
    f.seek(offsetToImage)
    sz = andsizeImage if andsizeImage > 0 and andcompression > 0 else andmaskbits
    # _errprint(["andSizeImage", andsizeImage, "andmaskbits", andmaskbits])
    try:
        andmask = f.read(sz)
    except:
        _errprint("can't read whole image")
        return None
    if len(andmask) != sz:
        _errprint("Failure: %d %d [%d]" % (len(andmask), sz, andcompression))
        return None
    if andcompression > 0 and not bitfields:
        deco = [0 for i in range(andmaskbits)]
        if andcompression == 1 and not _rle8decompress(
            andmask, deco, andmaskhdr[1], andmaskhdr[2]
        ):
            _errprint("Failed to decompress")
            return None
        elif andcompression == 2 and not _rle4decompress(
            andmask, deco, andmaskhdr[1], andmaskhdr[2]
        ):
            _errprint("Failed to decompress")
            return None
        elif (
            andcompression == 3
            and andmaskhdr[4] == 1
            and not _huffmandecompress(andmask, deco, andmaskhdr[1], andmaskhdr[2])
        ):
            _errprint("Failed to decompress")
            return None
        elif andcompression == 4 and not _rle24decompress(
            andmask, deco, andmaskhdr[1], andmaskhdr[2]
        ):
            _errprint("Failed to decompress")
            return None
        andmask = bytes(deco)
    if len(andmask) != andmaskbits:
        _errprint("Failure: %d %d" % (len(andmask), andmaskbits))
        return None
    bitspixel = andmaskhdr[4]
    if isColor:
        if colorpalette > 0:
            f.seek(colorcolortable)
            colormaskcolors = []
            cts = 3 if colormaskhdr[0] <= 0x0C else 4
            for i in range(colorpalette):
                clr = f.read(3)  # BGR color
                colormaskcolors.append(clr)
                if len(clr) != 3:
                    raise ValueError
                if cts > 3:
                    f.read(cts - 3)
            for i in range((1 << colorbpp) - colorpalette):
                clr = f.read(bytes([0, 0, 0]))
                colormaskcolors.append(clr)
        # Offset from the beginning of the file, not necessarily
        # from the beginning of the bitmap/icon/cursor header.
        f.seek(colormaskinfo[3])
        sz = colorsizeImage if colorsizeImage > 0 else colormaskbits
        colormask = f.read(sz)
        if len(colormask) != sz:
            _errprint("Failure: %d %d" % (len(andmask), sz))
            return None
        if colorcompression > 0:
            deco = [0 for i in range(colormaskbits)]
            if colorcompression == 1 and not _rle8decompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                _errprint("Failed to decompress")
                return None
            elif colorcompression == 2 and not _rle4decompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                _errprint("Failed to decompress")
                return None
            elif colorcompression == 3 and not _huffmandecompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                _errprint("Failed to decompress")
                return None
            elif colorcompression == 4 and not _rle24decompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                _errprint("Failed to decompress")
                return None
            colormask = bytes(deco)
        if len(colormask) != colormaskbits:
            _errprint("Failure: %d %d" % (len(colormask), colormaskbits))
            return None
    width = 0
    height = 0
    ret = None
    if isBitmap:
        # Presentation Manager or Windows bitmap
        cw = andmaskhdr[1]
        ch = abs(andmaskhdr[2])
        bpp = andmaskhdr[4]
        ci = dw.blankimage(cw, ch, alpha=True)
        alpha1 = bytes([255])
        for y in range(ch):
            for x in range(cw):
                yy = ch - 1 - y if andmaskhdr[2] < 0 else y
                if bitfields:
                    col = _readBitmapAsColorBitfields(
                        andmask, andmaskscan, ch, bpp, x, yy, bitfields
                    )
                else:
                    col = _readBitmapAsColorBGR(
                        andmask, andmaskscan, ch, bpp, x, yy, andmaskcolors
                    )
                alpha = (
                    _readBitmapAsAlphaBitfields(
                        andmask, andmaskscan, ch, bpp, x, yy, andalphamask
                    )
                    if andalphamask and andalphamask != 0
                    else alpha1
                )
                try:
                    dw.setpixelbgralpha(ci, cw, ch, x, y, col + alpha)
                except:
                    _errprint("failure to set pixel")
                    return None
        ret = ci
        width = cw
        height = ch
    elif isColor:
        # Presentation Manager color icon
        cw = colormaskhdr[1]
        ch = colormaskhdr[2]
        bpp = colormaskhdr[4]
        bl = dw.blankimage(cw, ch, alpha=True)
        white = bytes([255, 255, 255])
        black = bytes([0, 0, 0])
        alpha0 = bytes([0])
        alpha1 = bytes([255])
        for y in range(ch):
            for x in range(cw):
                bitand = _read1bppBitmap(andmask, andmaskscan, andmaskhdr[2], x, y)
                bitxor = _read1bppBitmap(andmask, andmaskscan, andmaskhdr[2], x, y + ch)
                # Windows color icons employ a simpler 2-mask system (an AND mask and
                # an XOR mask) than Presentation Manager (PM) color icons (AND/XOR mask and color mask).
                # The XOR mask for Windows icons is the same as the PM icon's
                # color mask except that, where the PM icon's AND mask bit (in the upper
                # half of the AND/XOR mask) is 1, the Windows icon's XOR mask bits are:
                # - all ones where the PM icon's XOR mask bit (in the lower half of the
                # AND/XOR mask) is 1, or
                # - all zeros where the PM icon's XOR mask bit is 0.
                # See "Bitmap File Format", in the _Presentation Manager Programming
                # Guide and Reference_.
                # However, the presence of nonzero values in a PM icon's or PM cursor's
                # XOR mask is unusual for color icons and pointers.
                # Moreover, PNGs don't support color inversions.
                px = (
                    white
                    if (bitand & bitxor) == 1
                    else (
                        black
                        if bitand == 1 and bitxor == 0
                        else _readBitmapAsColorBGR(
                            colormask, colormaskscan, ch, bpp, x, y, colormaskcolors
                        )
                    )
                ) + ((alpha1) if bitand == 0 else alpha0)
                try:
                    dw.setpixelbgralpha(bl, cw, ch, x, y, px)
                except:
                    _errprint("failure to set pixel")
                    return None
        width = cw
        height = ch
        ret = bl
    else:
        # Presentation Manager two-color icon
        trueheight = andmaskhdr[2] // 2
        bl = dw.blankimage(andmaskhdr[1], trueheight, alpha=True)
        blackalpha0 = [0, 0, 0, 0]
        whitealpha0 = [255, 255, 255, 0]
        blackalpha1 = [0, 0, 0, 255]
        whitealpha1 = [255, 255, 255, 255]
        for y in range(trueheight):
            for x in range(andmaskhdr[1]):
                bitand = _read1bppBitmap(andmask, andmaskscan, andmaskhdr[2], x, y)
                bitxor = _read1bppBitmap(
                    andmask, andmaskscan, andmaskhdr[2], x, y + trueheight
                )
                px = (
                    (whitealpha1 if bitand == 0 else whitealpha0)
                    if bitxor == 1
                    else (blackalpha1 if bitand == 0 else blackalpha0)
                )
                dw.setpixelalpha(bl, andmaskhdr[1], trueheight, x, y, px)
        width = andmaskhdr[1]
        height = trueheight
        ret = bl
    return [ret, width, height, hotspotX, hotspotY]

# Saves a video file by converting the image to grayscale, animating the pixel intensities, and
# replacing the intensities with the color values from the specified color table.
# Image has the same format returned by the _desktopwallpaper_ module's blankimage() method with alpha=False.
def colorTableAnimation(image, width, height, colorTable, destAnimation, fps=15):
    images = []
    i = 0
    while i < 256:
        gm = dw.graymap(
            [x for x in image],
            width,
            height,
            [colorTable[(i + j) % 256] for j in range(len(colorTable))],
        )
        images.append(gm)
        i += 2
    writeavi(destAnimation, images, width, height, fps=fps)

# Image has the same format returned by the _desktopwallpaper_ module's blankimage() method with alpha=False.
# NOTE: Currently, there must be 256 or fewer unique colors used in the image
# for this method to be successful.
def parallaxAvi(
    image,
    width,
    height,
    destAVI,
    widthReverse=False,
    heightReverse=False,
    interlacing=False,
    numframes=32,
    fps=15,
):
    if not image:
        raise ValueError
    if numframes <= 0:
        raise ValueError
    outputHeight = height // 2 if interlacing else height
    images = [dw.blankimage(width, height) for i in range(numframes)]
    for i in range(numframes):
        dw.imageblit(
            images[i],
            width,
            height,
            width - width * i // numframes if widthReverse else width * i // numframes,
            (
                height - height * i // numframes
                if heightReverse
                else height * i // numframes
            ),
            image,
            width,
            height,
        )
        if interlacing:
            # interlace at half the height
            a, b = dw.interlace(images[i], width, height)
            images[i] = a if i % 2 == 0 else b
        if len(images[i]) != width * outputHeight * 3:
            raise ValueError
    writeavi(destAVI, images, width, outputHeight, fps=fps)

# Generates an AVI video file consisting of images arranged
# in a row or column and writes the file to the path given by
# 'destAVI'.  Each frame's width and height are determined
# as follows.
# - If the source image's width is greater than its height,
#   then each frame is 'crossSize' &times; (source height).
# - If the source image's width is less than its height,
#   then each frame is (source width) &times; 'crossSize'.
# If 'crossSize' is None, which is the default, then 'crossSize'
# is the source's width or the source's height, whichever is smaller.
# Raises an error if 'crossSize' is not None and the source image's
# width equals its height.
# The source image has the same format returned by the
# _desktopwallpaper_ module's blankimage() method with alpha=False.
# NOTE: Currently, there must be 256 or fewer unique colors used in the image
# for this method to be successful.
def animationBitmap(
    image, width, height, destAVI, firstFrame=0, fps=15, crossSize=None
):
    frameSize = min(width, height)
    if frameSize <= 0:
        raise ValueError
    if crossSize:
        if crossSize <= 0 or width == height:
            return ValueError
        frameSize = crossSize
    animWidth = frameSize if width > height else width
    animHeight = frameSize if height > width else height
    images = []
    for i in range(firstFrame, max(width, height) // frameSize):
        dst = dw.blankimage(animWidth, animHeight)
        dw.imageblitex(
            dst,
            animWidth,
            animHeight,
            0,
            0,
            animWidth,
            animHeight,
            image,
            width,
            height,
            i * frameSize if width > height else 0,
            i * frameSize if height > width else 0,
        )
        images.append(dst)
    writeavi(destAVI, images, animWidth, animHeight, fps=fps)

def _icnspalette256():
    ret = []
    for i in range(215):
        i2 = 216 - 1 - i
        ret.append([(i2 // 36) * 51, ((i2 // 6) % 6) * 51, (i2 % 6) * 51])
    s = [14, 13, 11, 10, 8, 7, 5, 4, 2, 1]
    for v in s:
        ret.append([v + (v << 4), 0, 0])
    for v in s:
        ret.append([0, v + (v << 4), 0])
    for v in s:
        ret.append([0, 0, v + (v << 4)])
    for v in s:
        ret.append([v + (v << 4), v + (v << 4), v + (v << 4)])
    ret.append([0, 0, 0])
    return ret

# Reads icon images from a file in the GEM icon resource format. The return value
# has the same format returned by the reados2icon() method.
def readicn(infile):
    f = open(infile, "rb")
    ret = [None for i in range(72)]
    try:
        addrs = struct.unpack(">HH", f.read(4))
        iconblks = [None for i in range(72)]
        iconwidth = 0
        iconheight = 0
        maxicon = 0
        for i in range(72):
            iconblks[i] = struct.unpack("<LLLBBHHHHHHHHHH", f.read(34))
            maxmask = max(iconblks[i][0], iconblks[i][1])
            if maxmask >= 144:
                raise ValueError
            fgcolor = (iconblks[i][4] >> 4) & 0x0F
            bgcolor = (iconblks[i][4] >> 4) & 0x0F
            if iconblks[i][4] != 0x10:
                raise ValueError("Nonblack/white colors not supported")
            print([fgcolor, bgcolor])
            width = iconblks[i][9]
            height = iconblks[i][10]
            if width % 16 != 0 or width == 0:
                raise ValueError("Unsupported width")
            if height == 0:
                raise ValueError("Unsupported height")
            if i == 0:
                iconwidth = width
            if i == 0:
                iconheight = height
        iconsize = 2 * ((iconwidth + 15) // 16) * iconheight
        iconoffset = f.tell()
        for i in range(72):
            rowsize = 2 * ((iconwidth + 15) // 16)
            iconmask = [None, None]
            for k in range(2):
                f.seek(iconoffset + iconblks[i][k] * iconsize)
                img = dw.blankimage(iconwidth, iconheight)
                for y in range(iconheight):
                    icon = f.read(rowsize)
                    if len(icon) < rowsize:
                        raise ValueError
                    c = rowsize - 2
                    x = iconwidth - 16
                    while c >= 0:
                        word = (icon[c + 1] << 8) | icon[c]
                        for j in range(16):
                            if (word & (1 << (15 - j))) != 0:
                                dw.setpixel(
                                    img, iconwidth, iconheight, x + j, y, [0, 0, 0]
                                )
                            else:
                                dw.setpixel(
                                    img,
                                    iconwidth,
                                    iconheight,
                                    x + j,
                                    y,
                                    [255, 255, 255],
                                )
                        x -= 16
                        c -= 2
                iconmask[k] = img
            icon = dw.blankimage(iconwidth, iconheight, alpha=True)
            for y in range(iconheight):
                for x in range(iconwidth):
                    maskpixel = dw.getpixel(iconmask[0], iconwidth, iconheight, x, y)
                    iconpixel = dw.getpixel(iconmask[1], iconwidth, iconheight, x, y)
                    dw.setpixelalpha(
                        icon,
                        iconwidth,
                        iconheight,
                        x,
                        y,
                        [
                            iconpixel[0],
                            iconpixel[1],
                            iconpixel[2],
                            0 if maskpixel[0] != 0 else 255,
                        ],
                    )
            ret[i] = [icon, iconwidth, iconheight, 0, 0]
        if not ret:
            raise ValueError
        return ret
    except:
        if not ret:
            raise ValueError
        return ret
    finally:
        f.close()

# Reads icon images from a file in the Apple icon resource format (also known
# as icon family or icon suite), in the '.icns' format.  This format was
# introduced in Mac OS 8.5 (see Apple TN1142: "Mac OS 8.5").  The return value
# has the same format returned by the reados2icon() method.
def readicns(infile):
    f = open(infile, "rb")
    try:
        ret = []
        tag = f.read(4)
        if tag != b"icns":
            return ret
        size = struct.unpack(">L", f.read(4))[0]
        if size < 8:
            return ret
        lp = _LimitedIO(f, size - 8)
        return _readicns_core(lp, tag)
    finally:
        f.close()

def _readicns_core(lp, starttag):
    tag = lp.read(4)
    size = struct.unpack(">L", lp.read(4))[0]
    tags = {}
    ret = []
    variants = []
    if size < 8:
        return ret
    if tag == b"TOC " and starttag == b"icns":
        # Table of contents
        toc = lp.read(size - 8)
    else:
        lp.seek(0)
    index = 0
    while True:
        tag = lp.read(4)
        if len(tag) == 0:
            break
        # print(["readicns_core",tag,starttag])
        size = struct.unpack(">L", lp.read(4))[0]
        if size < 8:
            # Size too small for this tag
            return ret
        if tag in tags:
            # NOTE: Usually, icon tags are unique within an ICNS.
            # Can an ICNS have two or more icons of the same kind?
            # The same tag has occurred more than once in at least
            # one ICNS (in this case, 'il32' and 'l8mk').
            # Because of what's said in Apple TB30, "Multiple Resources
            # with the Same Type and ID", having multiple icons of the
            # same type in an ICNS is probably not supported.
            _errprint("tag already exists: %s" % (tag))
        else:
            tags[tag] = [lp.tell(), size - 8, index]
        ret.append(None)
        try:
            lp.seek(lp.tell() + size - 8)
        except ValueError:
            # Size too small for this tag
            return ret
        index += 1
    for tag in tags.keys():
        if (
            tag == b"ic07"
            or tag == b"ic08"
            or tag == b"ic09"
            or tag == b"ic10"
            or tag == b"ic11"
            or tag == b"ic12"
            or tag == b"ic13"
            or tag == b"ic14"
            or tag == b"ic04"
            or tag == b"ic05"
            or tag == b"icp4"
            or tag == b"icp5"
            or tag == b"icp6"
        ):
            info = tags[tag]
            lp.seek(info[0])
            imagebytes = lp.read(info[1])
            if (
                (tag == b"ic04" or tag == b"ic05")
                and len(imagebytes) > 4
                and imagebytes[0:4] == b"ARGB"
            ):
                width = 32 if tag == b"ic05" else 16
                height = width
                if len(imagebytes) - 4 == width * height * 4:
                    # uncompressed
                    icon = imagebytes[4:]
                else:
                    # compressed
                    icon = [0 for i in range(width * height * 4)]
                    if not _icnsrle24decode(io.BytesIO(imagebytes[4:]), icon, planes=4):
                        _errprint("decoding failed: %s" % (tag))
                        continue
                image = [0 for i in range(width * height * 4)]
                for i in range(width * height):
                    image[i * 4] = icon[i * 4 + 1]
                    image[i * 4 + 1] = icon[i * 4 + 2]
                    image[i * 4 + 2] = icon[i * 4 + 3]
                    image[i * 4 + 3] = icon[i * 4 + 0]
                ret[info[2]] = [image, width, height, 0, 0]
            else:
                iconimg, width, height = _pilReadImage(imagebytes)
                ret[info[2]] = [iconimg, width, height, 0, 0]
        elif tag == b"s8mk" or tag == b"l8mk" or tag == b"h8mk" or tag == b"t8mk":
            info = tags[tag]
            ret[info[2]] = True
        elif starttag == b"icns" and (
            tag == b"drop"
            or tag == b"open"
            or tag == b"odrp"
            or tag == b"over"
            or tag == b"tile"
        ):
            # icon variants: drop, open, open/drop, rollover, tile
            info = tags[tag]
            lp.seek(info[0])
            lp2 = _LimitedIO(lp, info[1])
            variants.append(_readicns_core(lp2, tag))
            lp.seek(info[0] + info[1])
            ret[info[2]] = True
        elif (
            tag == b"is32"
            or tag == b"il32"
            or tag == b"ih32"
            or tag == b"it32"
            or tag == b"ics#"
            or tag == b"ICN#"
            or tag == b"ich#"
            or tag == b"icm#"
            or tag == b"ics4"
            or tag == b"icl4"
            or tag == b"ich4"
            or tag == b"icm4"
            or tag == b"ics8"
            or tag == b"icl8"
            or tag == b"ich8"
            or tag == b"icm8"
            or tag == b"SICN"
            or tag == b"ICON"
        ):
            # NOTE: Usually, icon types that support masks must have an icon
            # of the corresponding mask type in the ICNS.  But at
            # least one ICNS was observed with an icon of a kind
            # covered here ('ich4') but not its corresponding mask ('ich#')
            # if _masktag(tag) not in tags and _masktag(tag) != b"":
            #    print([tags[tag],"%04X"%(tags[tag][0])])
            #    _errprint("mask tag not found: %s" % (tag))
            #    break
            info = tags[tag]
            width = _iconsize(tag)
            height = width if tag[3] != 0x23 else width * 2
            # NOTE: Observed at least one ICNS that incorrectly assumes
            # the mini size is 16 &times; 12, rather than 12 &times; 12 (see Technical
            # Note QD18: Drawing Icons the System 7 Way).
            if (
                (tag == b"icm#" and info[1] == 48)
                or (tag == b"icm4" and info[1] == 96)
                or (tag == b"icm8" and info[1] == 192)
            ):
                width = 16
                height = 12 if tag[3] != 0x23 else 24
            lp.seek(info[0])
            index = info[2]
            iconsize = (
                (width * height) // 8
                if tag[3] == 0x23 or tag == b"SICN" or tag == b"ICON"
                else (
                    (width * height) // 2
                    if tag[3] == 0x34
                    else ((width * height) if tag[3] == 0x38 else width * height * 3)
                )
            )
            isCompressed = iconsize != info[1]
            is32bit = False
            if tag[2] == 0x33 and tag[3] == 0x32 and width * height * 4 == info[1]:
                # ??32
                is32bit = True
                isCompressed = False
            if isCompressed:
                if (
                    tag[3] == 0x23
                    or tag[3] == 0x34
                    or tag[3] == 0x38
                    or tag == b"SICN"
                    or tag == b"ICON"
                ):
                    _errprint(
                        "compression unsupported: %s [iconsize=%d, req. size=%d]"
                        % (tag, iconsize, info[1])
                    )
                    continue
                icon = [0 for i in range(width * height * 4)]
                if not _icnsrle24decode(_LimitedIO(lp, info[1]), icon):
                    _errprint("decoding failed: %s" % (tag))
                    continue
            else:
                icon = lp.read(info[1])
            if tag[3] == 0x23:
                height //= 2
                halficonsize = width * height
                image = [0 for i in range(width * height * 4)]
                for i in range(width * height):
                    bit = (icon[i // 8] >> (7 - (i & 7))) & 1  # XOR mask
                    bit2 = (
                        icon[(i + halficonsize) // 8] >> (7 - (i & 7))
                    ) & 1  # AND mask
                    if bit == 0:
                        image[i * 4] = image[i * 4 + 1] = image[i * 4 + 2] = 0xFF
                    image[i * 4 + 3] = 0xFF if (bit2 == 1) else 0x00
            elif tag == b"SICN" or tag == b"ICON":
                image = [0 for i in range(width * height * 4)]
                for i in range(width * height):
                    bit = (icon[i // 8] >> (7 - (i & 7))) & 1
                    if bit == 0:
                        image[i * 4] = image[i * 4 + 1] = image[i * 4 + 2] = 0xFF
                    image[i * 4 + 3] = 0xFF
            elif tag[3] == 0x34:
                image = [0xFF for i in range(width * height * 4)]
                pal = [
                    [221, 8, 6],
                    [242, 8, 132],
                    [70, 0, 165],
                    [0, 0, 212],
                    [2, 171, 234],
                    [31, 183, 20],
                    [0, 100, 17],
                    [86, 44, 5],
                    [144, 113, 58],
                ]
                for i in range(width * height):
                    bit = (icon[i // 2] >> (4 - 4 * (i & 1))) & 0x0F
                    match bit:
                        case 0:
                            pass
                        case 1:
                            image[i * 4] = 252
                            image[i * 4 + 1] = 243
                            image[i * 4 + 2] = 5
                        case 2:
                            image[i * 4] = 255
                            image[i * 4 + 1] = 100
                            image[i * 4 + 2] = 2
                        case 12 | 13 | 14 | 15:
                            image[i * 4] = image[i * 4 + 1] = image[i * 4 + 2] = (
                                192 - (bit - 12) * 64
                            )
                        case _:
                            if bit - 3 < 0:
                                raise ValueError
                            if bit - 3 >= len(pal):
                                raise ValueError
                            image[i * 4] = pal[bit - 3][0]
                            image[i * 4 + 1] = pal[bit - 3][1]
                            image[i * 4 + 2] = pal[bit - 3][2]
            elif tag[3] == 0x38:
                pal = _icnspalette256()
                image = [0 for i in range(width * height * 4)]
                for i in range(width * height):
                    bit = icon[i]
                    image[i * 4] = pal[bit][0]
                    image[i * 4 + 1] = pal[bit][1]
                    image[i * 4 + 2] = pal[bit][2]
            elif is32bit:
                image = [0 for i in range(width * height * 4)]
                for i in range(width * height):
                    image[i * 4] = icon[i * 4 + 1]
                    image[i * 4 + 1] = icon[i * 4 + 2]
                    image[i * 4 + 2] = icon[i * 4 + 3]
                    image[i * 4 + 3] = icon[i * 4 + 0]
            else:
                if isCompressed:
                    image = icon
                else:
                    image = [0 for i in range(width * height * 4)]
                    for i in range(width * height):
                        image[i * 4] = icon[i * 3]
                        image[i * 4 + 1] = icon[i * 3 + 1]
                        image[i * 4 + 2] = icon[i * 3 + 2]
            # mask
            masktag = _masktag(tag)
            if masktag != b"" and masktag in tags:
                info = tags[masktag]
                lp.seek(info[0])
                masksize = (
                    (width * height * 2) // 8 if masktag[3] == 0x23 else width * height
                )
                if masksize != info[1]:
                    _errprint("compressed mask is unsupported")
                    continue
                mask = lp.read(info[1])
                if masktag[3] == 0x23:
                    halficonsize = width * height
                    for i in range(width * height):
                        bit2 = (
                            mask[(i + halficonsize) // 8] >> (7 - (i & 7))
                        ) & 1  # AND mask
                        image[i * 4 + 3] = 0xFF if (bit2 == 1) else 0x00
                else:
                    for i in range(width * height):
                        image[i * 4 + 3] = mask[i]
            ret[index] = [image, width, height, 0, 0]
        elif tag == b"icnV":
            info = tags[tag]
            if info[1] == 4:
                lp.seek(info[0])
                val = struct.unpack(">f", lp.read(info[1]))[0]
                # val appears to be a floating-point value such as
                # -1.0 or 120.0
                ret[info[2]] = True
            else:
                _errprint("unrecognized: %s" % (tag))
        elif tag == b"name":
            info = tags[tag]
            if info[1] == 4:
                lp.seek(info[0])
                str(lp.read(info[1]), "utf-8")
                # value appears to be a name string
                ret[info[2]] = True
            else:
                _errprint("unrecognized: %s" % (tag))
        elif tag == b"info":
            info = tags[tag]
            ret[info[2]] = True
        else:
            _errprint("unrecognized: %s" % (tag))
    ret2 = []
    for v in ret:
        if v is not True:
            ret2.append(v)
    for va in variants:
        for v in va:
            ret2.append(v)
    ret = ret2
    return ret

def _iconsize(icontag):
    if icontag == b"is32":
        return 16
    if icontag == b"SICN":  # s = small
        return 16
    if icontag == b"icm#":  # m = mini
        return 12
    if icontag == b"icm4":
        return 12
    if icontag == b"icm8":
        return 12
    if icontag == b"ics#":
        return 16
    if icontag == b"ics4":
        return 16
    if icontag == b"ics8":
        return 16
    if icontag == b"ICON":
        return 32
    if icontag == b"ICN#":
        return 32
    if icontag == b"icl4":  # l = large
        return 32
    if icontag == b"icl8":
        return 32
    if icontag == b"il32":
        return 32
    if icontag == b"ich#":  # h = huge
        return 48
    if icontag == b"ich4":
        return 48
    if icontag == b"ich8":
        return 48
    if icontag == b"ih32":
        return 48
    if icontag == b"it32":
        return 128
    raise ValueError

def _masktag(icontag):
    if icontag == b"SICN":
        return b""
    if icontag == b"ICON":
        return b""
    if icontag == b"ics#":
        return b""
    if icontag == b"ics4":
        return b"ics#"
    if icontag == b"ics8":
        return b"ics#"
    if icontag == b"icm#":
        return b""
    if icontag == b"icm4":
        return b"icm#"
    if icontag == b"icm8":
        return b"icm#"
    if icontag == b"ICN#":
        return b""
    if icontag == b"icl4":
        return b"ICN#"
    if icontag == b"icl8":
        return b"ICN#"
    if icontag == b"ich#":
        return b""
    if icontag == b"ich4":
        return b"ich#"
    if icontag == b"ich8":
        return b"ich#"
    if icontag == b"is32":
        return b"s8mk"
    if icontag == b"il32":
        return b"l8mk"
    if icontag == b"ih32":
        return b"h8mk"
    if icontag == b"it32":
        return b"t8mk"
    raise ValueError

def _icnsrle24decode(f, image, planes=3):
    ftell = f.tell()
    nulldata = f.read(4)
    if nulldata != b"\x00\x00\x00\x00":
        f.seek(ftell)
    for i in range(planes):
        pos = 0
        while True:
            if pos >= len(image):
                break
            b = f.read(1)
            if len(b) == 0:
                return False
            if (b[0] & 0x80) == 0:
                if (len(image) - pos) // 4 < b[0] + 1:
                    return False
                for j in range(b[0] + 1):
                    b = f.read(1)
                    if len(b) == 0:
                        return False
                    image[pos + i] = b[0]
                    pos += 4
            else:
                bb = (b[0] & 0x7F) + 3
                b = f.read(1)
                if len(b) == 0:
                    return False
                if (len(image) - pos) // 4 < bb:
                    return False
                for j in range(bb):
                    image[pos + i] = b[0]
                    pos += 4
    return True

# Gets the width and height of a PNG file from its
# header. 'f' is the file's filename.
# Returns a two-element array with the width
# and height, in that order, in pixels, or [0,0] if
# the file is not detected as
# a PNG file.  It bears mentioning that a positive value
# for the width and height is not a guarantee that the
# PNG file is well-formed.
def getpngwidthheight(f):
    ff = open(f, "rb")
    if not ff:
        return [0, 0]
    hdr = ff.read(8)
    if hdr != bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
        ff.close()
        return [0, 0]
    hdr = struct.unpack(">LLLL", ff.read(16))
    if hdr[0] != 0x0D or hdr[1] != 0x49484452:
        ff.close()
        return [0, 0]
    width = hdr[2]  # PNG width
    height = hdr[3]  # PNG height
    ff.close()
    return [width, height]

def _tiledSvg(imagedata, width, height, screenwidth, screenheight):
    dataurl = "data:image/png;base64," + str(base64.b64encode(imagedata), "utf-8")
    svgbytes = bytes(
        "<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>"
        + (
            "<pattern patternUnits='userSpaceOnUse' id='pattern' width='%d' height='%d'>"
        )
        % (width, height)
        + ("<image width='%d' height='%d' x='0' y='0' xlink:href='%s'/>")
        % (width, height, dataurl)
        + "</pattern><path style='stroke:none;fill:url(#pattern)' "
        + "d='M0 0 L0 %d L%d %d L%d 0 Z'/>"
        % (screenheight, screenwidth, screenheight, screenwidth)
        + "</svg>",
        "utf-8",
    )
    return svgbytes

def tiledSvgFromImage(
    image, width, height, alpha=False, screenwidth=1920, screenheight=1080
):
    return _tiledSvg(
        pngbytes(image, width, height, alpha=alpha),
        width,
        height,
        screenwidth,
        screenheight,
    )

def tiledSvgFromFile(pngFile, screenwidth=1920, screenheight=1080):
    ff = open(pngFile, "rb")
    hdr = ff.read(8)
    existingdata = hdr
    if hdr != bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
        ff.close()
        raise ValueError("not a PNG")
    hdr = ff.read(16)
    existingdata += hdr
    hdr = struct.unpack(">LLLL", hdr)
    if hdr[0] != 0x0D or hdr[1] != 0x49484452:
        ff.close()
        raise ValueError("not a valid PNG")
    width = hdr[2]  # PNG width
    height = hdr[3]  # PNG height
    if width == 0 or height == 0:
        ff.close()
        raise ValueError("not a valid PNG")
    imagedata = existingdata + ff.read()
    ff.close()
    return _tiledSvg(imagedata, width, height, screenwidth, screenheight)

def imageToSvg(image, width, height, alpha=False):
    pixelBytes = 4 if alpha else 3
    ret = "<svg xmlns='http://www.w3.org/2000/svg' " + (
        "viewBox='0 0 %d %d'>" % (width, height)
    )
    pos = 0
    uniques = {}
    for y in range(height):
        for x in range(width):
            if (not alpha) or image[pos + 3] > 0:
                col = (
                    image[pos],
                    image[pos + 1],
                    image[pos + 2],
                    image[pos + 3] if alpha else 255,
                )
                path = "M%d %dh1v1h-1Z" % (x, y)
                if col not in uniques:
                    uniques[col] = [path]
                else:
                    uniques[col].append(path)
            pos += pixelBytes
    for k in uniques:
        path = uniques[k]
        color = "#%02X%02X%02X" % (k[0], k[1], k[2])
        opacity = "" if (k[3] == 255) else ";fill-opacity:%.03f" % (k[3] / 255)
        ret += "<path style='stroke:none;fill:%s%s' d='%s'/>\n" % (
            color,
            opacity,
            "".join(path),
        )
    return bytes(ret + "</svg>", "utf-8")

class _BitArray:
    def __init__(self, count):
        self.bits = [0 for i in range((count + 31) // 32)]
        self.count = count

    def set(self, i, v):
        if v:
            self.bits[i >> 5] |= 1 << (i & 31)
        else:
            self.bits[i >> 5] &= ~(1 << (i & 31))

    def setAll(self, v):
        if v:
            for i in range(len(self.bits)):
                self.bits[i] = 0xFFFFFFFF
        else:
            for i in range(len(self.bits)):
                self.bits[i] = 0x00000000

    def get(self, i):
        return (self.bits[i >> 5] & (1 << (i & 31))) != 0

class SvgPath:
    def __init__(self):
        self.path = ""

    def MoveTo(self, x, y):
        if int(x) == x and int(y) == y:
            self.path += "M%d %d" % (x, y)
        else:
            self.path += "M%f %f" % (x, y)

    def LineTo(self, x, y):
        if int(x) == x and int(y) == y:
            self.path += "L%d %d" % (x, y)
        else:
            self.path += "L%f %f" % (x, y)

    def Close(self):
        self.path += "Z"

    def __str__(self):
        return self.path

def _isInside(rows, width, height, target, x, y):
    pos = (y * width + x) * 3
    # Right-hand side is true if the specified pixel is "black" (all zeros)
    return target == ((rows[pos] | rows[pos + 1] | rows[pos + 2]) == 0)

def _floodFillOuter(rows, width, height, rc, x, y, target, bits, fillbits):
    # four-neighbor flood fill
    w = rc[2] - rc[0]
    xLeft = x
    xRight = x
    yFromOrg = y - rc[1]
    xFromOrg = x - rc[0]
    curpos = yFromOrg * w + xFromOrg
    while True:
        bits.set(curpos, True)
        fillbits.set(curpos, True)
        curpos -= 1
        xLeft -= 1
        if not (
            xLeft >= rc[0]
            and _isInside(rows, width, height, target, xLeft, y)
            and not fillbits.get(curpos)
        ):
            break
    xLeft += 1
    curpos = yFromOrg * w + xFromOrg
    while True:
        bits.set(curpos, True)
        fillbits.set(curpos, True)
        curpos += 1
        xRight += 1
        if not (
            xRight < rc[2]
            and _isInside(rows, width, height, target, xRight, y)
            and not fillbits.get(curpos)
        ):
            break
    xRight -= 1
    curpos = yFromOrg - w + (xLeft - rc[0])
    for i in range(xLeft, xRight + 1):
        above = (yFromOrg - 1) * w + (i - rc[0])
        below = (yFromOrg + 1) * w + (i - rc[0])
        if (
            y > rc[1]
            and _isInside(rows, width, height, target, i, y - 1)
            and not fillbits.get(above)
        ):
            _floodFillOuter(rows, width, height, rc, i, y - 1, target, bits, fillbits)
        if (
            y < (rc[3] - 1)
            and _isInside(rows, width, height, target, i, y + 1)
            and not fillbits.get(below)
        ):
            _floodFillOuter(rows, width, height, rc, i, y + 1, target, bits, fillbits)

def _floodFillInner(rows, width, height, rc, x, y, target, bits, fillbits):
    # eight-neighbor flood fill
    w = rc[2] - rc[0]
    xLeft = x
    xRight = x
    yFromOrg = y - rc[1]
    xFromOrg = x - rc[0]
    curpos = yFromOrg * w + xFromOrg
    while True:
        bits.set(curpos, True)
        fillbits.set(curpos, True)
        curpos -= 1
        xLeft -= 1
        if not (
            xLeft >= rc[0]
            and _isInside(rows, width, height, target, xLeft, y)
            and not fillbits.get(curpos)
        ):
            break
    xLeft += 1
    curpos = yFromOrg * w + xFromOrg
    while True:
        bits.set(curpos, True)
        fillbits.set(curpos, True)
        curpos += 1
        xRight += 1
        if not (
            xRight < rc[2]
            and _isInside(rows, width, height, target, xRight, y)
            and not fillbits.get(curpos)
        ):
            break
    xRight -= 1
    curpos = yFromOrg - w + (xLeft - rc[0])
    for i in range(xLeft, xRight + 1):
        above = (yFromOrg - 1) * w + (i - rc[0])
        below = (yFromOrg + 1) * w + (i - rc[0])
        if y > rc[1]:
            if _isInside(rows, width, height, target, i, y - 1) and not fillbits.get(
                above
            ):
                _floodFillInner(
                    rows, width, height, rc, i, y - 1, target, bits, fillbits
                )
            if (
                i > rc[0]
                and _isInside(rows, width, height, target, i - 1, y - 1)
                and not fillbits.get(above - 1)
            ):
                _floodFillInner(
                    rows, width, height, rc, i - 1, y - 1, target, bits, fillbits
                )
            if (
                i < rc[2] - 1
                and _isInside(rows, width, height, target, i + 1, y - 1)
                and not fillbits.get(above + 1)
            ):
                _floodFillInner(
                    rows, width, height, rc, i + 1, y - 1, target, bits, fillbits
                )
        if y < (rc[3] - 1):
            if _isInside(rows, width, height, target, i, y + 1) and not fillbits.get(
                below
            ):
                _floodFillInner(
                    rows, width, height, rc, i, y + 1, target, bits, fillbits
                )
            if (
                i > rc[0]
                and _isInside(rows, width, height, target, i - 1, y + 1)
                and not fillbits.get(below - 1)
            ):
                _floodFillInner(
                    rows, width, height, rc, i - 1, y + 1, target, bits, fillbits
                )
            if (
                i < rc[2] - 1
                and _isInside(rows, width, height, target, i + 1, y + 1)
                and not fillbits.get(below + 1)
            ):
                _floodFillInner(
                    rows, width, height, rc, i + 1, y + 1, target, bits, fillbits
                )

# Returns an SVG path string of the outline traced by the
# black pixels in the specified image.  A black pixel has a red
# component, green component, and blue component of 0.
# Image has the same format returned by the _desktopwallpaper_ module's
# blankimage() method with alpha=False.
def pathFromBitmap(ibi, width, height):
    path = SvgPath()
    _pathFromBitmapEx(ibi, width, height, [0, 0, width, height], path, 1)
    return str(path)

def _pathFromBitmapEx(ibi, width, height, rcExtent, path, targetPixel):
    rows = None
    if not ibi:
        raise ValueError
    if not path:
        raise ValueError
    target = targetPixel != 0
    notTarget = targetPixel == 0
    rows = ibi
    rcClip = [0, 0, 0, 0]
    rcClip[0] = max(0, min(rcExtent[0], rcExtent[2]))
    rcClip[1] = max(0, min(rcExtent[1], rcExtent[3]))
    rcClip[2] = min(width, max(rcExtent[0], rcExtent[2]))
    rcClip[3] = min(height, max(rcExtent[1], rcExtent[3]))
    rc = rcExtent
    w = rc[2] - rc[0]
    h = rc[3] - rc[1]
    bits = _BitArray(w * h)
    fillbits = _BitArray(w * h)
    bitindex = 0
    for y in range(rc[1], rc[3]):
        for x in range(rc[0], rc[2]):
            if not bits.get(bitindex):
                if _isInside(rows, width, height, target, x, y):
                    _traceShape(rows, width, height, rc, x, y, target, bits, path)
                    fillbits.setAll(False)
                    _floodFillOuter(
                        rows, width, height, rc, x, y, target, bits, fillbits
                    )
                else:
                    if x == rc[0] or x == rc[2] - 1 or y == rc[1] or y == rc[3] - 1:
                        fillbits.setAll(False)
                        _floodFillInner(
                            rows, width, height, rc, x, y, notTarget, bits, fillbits
                        )
                    else:
                        point = [0, 0]
                        fillbits.setAll(False)
                        _floodFillInnerCheck(
                            rows, width, height, rc, x, y, notTarget, fillbits, point
                        )
                        if point[0] != rc[2] - 1 and point[1] != rc[3] - 1:
                            _traceShapeInner(
                                rows, width, height, rc, x, y, notTarget, bits, path
                            )
                        fillbits.setAll(False)
                        _floodFillInner(
                            rows, width, height, rc, x, y, notTarget, bits, fillbits
                        )
            bitindex += 1

_DIR_LEFT = 0
_DIR_RIGHT = 1
_DIR_UP = 2
_DIR_DOWN = 3

def _traceShape(rows, width, height, rc, x, y, target, bits, path):
    # Start from the right, then go clockwise around
    # the path
    direction = _DIR_RIGHT
    xBegin = x
    yBegin = y
    xLast = x
    yLast = y
    right1 = rc[2] - 1
    bottom1 = rc[3] - 1
    path.MoveTo(x, y)
    while True:
        if not (x >= rc[0]):
            raise ValueError
        if not (y >= rc[1]):
            raise ValueError
        if not (x <= rc[2]):
            raise ValueError
        if not (y <= rc[3]):
            raise ValueError
        # Console.WriteLine("%d | %d %d [%d
        # %d]",direction,xLast,yLast,xBegin,yBegin);
        if direction == _DIR_RIGHT:
            xLast = x + 1
            if not (x < rc[2]):
                raise ValueError
            if x != right1 and _isInside(rows, width, height, target, x + 1, y):
                if y != rc[1] and _isInside(rows, width, height, target, x + 1, y - 1):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_UP
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_DOWN
            x += 1
        elif direction == _DIR_LEFT:
            xLast = x - 1
            if not (x > rc[0]):
                raise ValueError
            if (
                x > rc[0] + 1
                and y != rc[1]
                and _isInside(rows, width, height, target, x - 2, y - 1)
            ):
                if y != rc[3] and _isInside(rows, width, height, target, x - 2, y):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_DOWN
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_UP
            x -= 1
        elif direction == _DIR_DOWN:
            yLast = y + 1
            if not (x > rc[0]):
                raise ValueError
            if y != bottom1 and _isInside(rows, width, height, target, x - 1, y + 1):
                if x != rc[2] and _isInside(rows, width, height, target, x, y + 1):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_RIGHT
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_LEFT
            y += 1
        elif direction == _DIR_UP:
            yLast = y - 1
            if not (x < rc[2]):
                raise ValueError
            if y > rc[1] + 1 and _isInside(rows, width, height, target, x, y - 2):
                if x != rc[0] and _isInside(rows, width, height, target, x - 1, y - 2):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_LEFT
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_RIGHT
            y -= 1
        if not (x != xBegin or y != yBegin):
            break
    path.Close()

def _floodFillInnerCheck(rows, width, height, rc, x, y, target, fillbits, point):
    # eight-neighbor flood fill
    w = rc[2] - rc[0]
    xLeft = x
    xRight = x
    yFromOrg = y - rc[1]
    xFromOrg = x - rc[0]
    curpos = yFromOrg * w + xFromOrg
    while True:
        fillbits.set(curpos, True)
        point[0] = max(point[0], xLeft)
        point[1] = max(point[1], y)
        curpos -= 1
        xLeft -= 1
        if not (
            xLeft >= rc[0]
            and _isInside(rows, width, height, target, xLeft, y)
            and not fillbits.get(curpos)
        ):
            break
    xLeft += 1
    curpos = yFromOrg * w + xFromOrg
    while True:
        fillbits.set(curpos, True)
        point[0] = max(point[0], xRight)
        point[1] = max(point[1], y)
        curpos += 1
        xRight += 1
        if not (
            xRight < rc[2]
            and _isInside(rows, width, height, target, xRight, y)
            and not fillbits.get(curpos)
        ):
            break
    xRight -= 1
    curpos = yFromOrg - w + (xLeft - rc[0])
    for i in range(xLeft, xRight + 1):
        above = (yFromOrg - 1) * w + (i - rc[0])
        below = (yFromOrg + 1) * w + (i - rc[0])
        if y > rc[1]:
            if _isInside(rows, width, height, target, i, y - 1) and not fillbits.get(
                above
            ):
                _floodFillInnerCheck(
                    rows, width, height, rc, i, y - 1, target, fillbits, point
                )
            if (
                i > rc[0]
                and _isInside(rows, width, height, target, i - 1, y - 1)
                and not fillbits.get(above - 1)
            ):
                _floodFillInnerCheck(
                    rows, width, height, rc, i - 1, y - 1, target, fillbits, point
                )
            if (
                i < rc[2] - 1
                and _isInside(rows, width, height, target, i + 1, y - 1)
                and not fillbits.get(above + 1)
            ):
                _floodFillInnerCheck(
                    rows, width, height, rc, i + 1, y - 1, target, fillbits, point
                )
        if y < (rc[3] - 1):
            if _isInside(rows, width, height, target, i, y + 1) and not fillbits.get(
                below
            ):
                _floodFillInnerCheck(
                    rows, width, height, rc, i, y + 1, target, fillbits, point
                )
            if (
                i > rc[0]
                and _isInside(rows, width, height, target, i - 1, y + 1)
                and not fillbits.get(below - 1)
            ):
                _floodFillInnerCheck(
                    rows, width, height, rc, i - 1, y + 1, target, fillbits, point
                )
            if (
                i < rc[2] - 1
                and _isInside(rows, width, height, target, i + 1, y + 1)
                and not fillbits.get(below + 1)
            ):
                _floodFillInnerCheck(
                    rows, width, height, rc, i + 1, y + 1, target, fillbits, point
                )

def _traceShapeInner(rows, width, height, rc, x, y, target, bits, path):
    # Start down, then go clockwise around
    # the path
    direction = _DIR_DOWN
    xBegin = x
    yBegin = y
    xLast = x
    yLast = y
    right1 = rc[2] - 1
    bottom1 = rc[3] - 1
    path.MoveTo(x, y)
    while True:
        if not (x >= rc[0]):
            raise ValueError
        if not (y >= rc[1]):
            raise ValueError
        if not (x <= rc[2]):
            raise ValueError
        if not (y <= rc[3]):
            raise ValueError
        if direction == _DIR_RIGHT:
            xLast = x + 1
            if not (x < rc[2]):
                raise ValueError
            if (
                x != right1
                and y != rc[1]
                and _isInside(rows, width, height, target, x + 1, y - 1)
            ):
                if y != rc[3] and _isInside(rows, width, height, target, x + 1, y):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_DOWN
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_UP
            x += 1
        elif direction == _DIR_LEFT:
            xLast = x - 1
            if not (x > rc[0]):
                raise ValueError
            if (
                x > rc[0] + 1
                and y != rc[3]
                and _isInside(rows, width, height, target, x - 2, y)
            ):
                if y != rc[1] and _isInside(rows, width, height, target, x - 2, y - 1):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_UP
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_DOWN
            x -= 1
        elif direction == _DIR_DOWN:
            yLast = y + 1
            if not (x > rc[0]):
                raise ValueError
            if (
                y != bottom1
                and x != rc[2]
                and _isInside(rows, width, height, target, x, y + 1)
            ):
                if x != rc[0] and _isInside(rows, width, height, target, x - 1, y + 1):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_LEFT
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_RIGHT
            y += 1
        elif direction == _DIR_UP:
            yLast = y - 1
            if not (x < rc[2]):
                raise ValueError
            if (
                y > rc[1] + 1
                and x != rc[0]
                and _isInside(rows, width, height, target, x - 1, y - 2)
            ):
                if x != rc[2] and _isInside(rows, width, height, target, x, y - 2):
                    path.LineTo(xLast, yLast)
                    direction = _DIR_RIGHT
            else:
                path.LineTo(xLast, yLast)
                direction = _DIR_LEFT
            y -= 1
        if not (x != xBegin or y != yBegin):
            break
    path.Close()
