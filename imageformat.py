# This Python script implements the reading of writing
# of certain classic bitmap, icon, and cursor formats,
# and the writing of certain animation formats.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under the Unlicense: https://unlicense.org/

import os
import math
import random
import struct
import zlib
import io

import desktopwallpaper as dw


# Image has the same format returned by the _desktopwallpaper_ module's _blankimage_ method with alpha=False.
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


# Image has the same format returned by the _desktopwallpaper_ module's _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def writepng(f, image, width, height, raiseIfExists=False, alpha=False):
    if not image:
        raise ValueError
    if width < 0 or height < 0:
        raise ValueError
    if len(image) != width * height * (4 if alpha else 3):
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    fd = open(f, "xb" if raiseIfExists else "wb")
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
    fd.close()


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
            and colortable[3] == colortable[4]
            and colortable[3] == colortable[5]
            and (colortable[3] == 0 or colortable[3] == 255)
        )
    )


# Images have the same format returned by the _desktopwallpaper_ module's _blankimage_ method with alpha=True.
# Note that, for mouse pointers (cursors), 32x32 pixels are the standard width and height.
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


# Images have the same format returned by the _desktopwallpaper_ module's _blankimage_ method with alpha=False.
def writeavi(
    f, images, width, height, raiseIfExists=False, singleFrameAsBmp=False, fps=20
):
    # NOTE: 20 fps or higher is adequate for fluid animations
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
            print("AVI writing in more than 256 colors is not supported")
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
        if bpp == 2:
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
                    fd.write(scan)
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
                    fd.write(scan)
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
                    fd.write(scan)
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
                                # if index==0 and sindex==height-1: print(["cnt",bytes([realcnt, lastbyte])])
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
                                #  print(rc)
                                #  print([realcnt*runMult,"spc",scanPixelCount,"i",i,"li",lastIndex,"lr",lastRun])
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
                            # if index==0 and sindex==height-1: print([runMult,"spc",scanPixelCount,"i",i,"li",lastIndex,"lr",lastRun])
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
                                # if index==0 and sindex==height-1: print(bytes([realcnt, lastbyte]))
                                scanPixelCount += realcnt
                                # if index==0 and sindex==height-1: print(["run",realcnt, "spc", scanPixelCount,"i", i,"li",lastIndex,"lr", lastRun])
                                cnt -= realcnt
                            if (len(nb) & 1) != 0:
                                raise ValueError
                            # if index==0 and sindex==height-1: print(nb)
                            newbytes += nb
                            lastIndex = i
                            isConsecutive = True
                        lastRun = i
                    if i < len(imagebytes):
                        lastbyte = imagebytes[i]
                # if index==0 and sindex==height-1:
                #   print(imagebytes)
                #   print(newbytes[nbindex:len(newbytes)])
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
    linesz = ((width * 8 + 31) >> 5) << 2  # bytes per scanline
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
    linesz = ((width * 24 + 31) >> 5) << 2  # bytes per scanline
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
    linesz = ((width + 31) >> 5) << 2  # bytes per scanline
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
    linesz = ((width + 31) >> 5) << 2  # bytes per scanline
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
    linesz = ((width * 4 + 31) >> 5) << 2  # bytes per scanline
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


# Reads an OS/2 icon, mouse pointer (cursor), bitmap, or bitmap array,
# or a Windows icon or cursor.
# OS/2 and Windows icons have the '.ico' file extension; OS/2 cursors, '.ptr';
# OS/2 bitmaps, '.bmp'; and Windows cursors, '.cur'.
# Returns a list of five-element lists, representing the decoded images
# in the order in which they were read.  If an icon, pointer, or
# bitmap could not be read, the value None takes the place of the
# corresponding five-element list.
# Each five-element list in the returned list contains the image,
# its width, its height, its hot spot X coordinate, and its hot spot
# Y coordinate in that order. The image has the same format returned by the
# _desktopwallpaper_ module's _blankimage_ method with alpha=True. (The hot spot is the point in the image
# that receives the system's mouse position when that image is
# drawn on the screen.  The hot spot makes sense only for mouse pointers;
# the hot spot X and Y coordinates are each 0 if the image relates to
# an icon or bitmap, rather than a pointer.)
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
                print(chunk)
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
        offsets = [0x0E]
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
            # include 640x200 (CGA, usually with half-height
            # icons), 640x350 (EGA), 640x480, 1024x768.
            endInfo = f.tell()
            infos.append(info)
            if info[1] == 0:
                break
            else:
                contentSize = info[1] - endInfo
                if contentSize < 2:
                    raise ValueError("unsupported content size")
                offsets.append(0x0E + info[1])
                f.seek(info[1])
        ret = []
        for i in range(len(offsets)):
            f.seek(offsets[i])
            ret.append(_readicon(f))
        return ret
    elif tag == bytes([0, 0]):
        # Windows icon
        f.seek(ft)
        return _readwinicon(f)
    else:
        f.seek(ft)
        return [_readicon(f)]


# Reads the color table from an OS/2 or Windows palette file.
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
            haveAnih = True
            if sz < 4:
                raise ValueError
            info = struct.unpack("<HH", f.read(4))
            if info[0] != 0x300 or info[1] * 4 + 4 != sz:
                raise ValueError
            for i in range(info[1]):
                color = struct.unpack("<BBBB", f.read(4))
                ret.append(color[0], color[1], color[2])
            return ret
        else:
            f.seek(f.tell() + sz)


# Reads the bitmaps, icons, and pointers in an OS/2 theme resource file.
# An OS/2 theme resource file is a collection of OS/2 resources
# such as bitmaps, icons, pointers, and text string tables.
# These theme resource files have the extensions .itr, .cmr, .ecr,
# .inr, .mmr, and .pmr.
# Returns a list of elements, each of which has the format described
# in the _reados2icon_ method.
def readitr(infile):
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
            st0 = (st[0] << 8) | st[1]
            st1 = (st[2] << 8) | st[3]
            size = st[5]
            if size < 2:
                raise ValueError("unsupported content size")
            pos = f.tell()
            data = f.read(size)
            if len(data) != size:
                raise ValueError
            nextpos = f.tell()
            tag = data[0:2]
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
            f.seek(pos)
            ret.append(reados2iconcore(f))
            i += 1
    finally:
        f.close()


def _read1bppBitmap(byteData, scanSize, height, x, y):
    # Reads the bit value of an array of bottom-up 1-bit-per-pixel
    # Windows or OS/2 bitmap data.
    return (byteData[scanSize * (height - 1 - y) + (x >> 3)] >> (7 - (x & 7))) & 1


def _read4bppBitmap(byteData, scanSize, height, x, y):
    # Reads the bit value of an array of bottom-up 4-bit-per-pixel
    # Windows or OS/2 bitmap data.
    return (
        byteData[scanSize * (height - 1 - y) + (x >> 1)] >> (4 * (1 - (x & 1)))
    ) & 0x0F


def _readBitmapAlpha(byteData, scanSize, height, bpp, x, y):
    # Reads the alpha value at the given pixel position of a bitmap image,
    # represented by an array of bottom-up Windows or OS/2 bitmap data.
    # Returns 255 if bpp is not 32.
    if bpp == 32:
        row = scanSize * (height - 1 - y)
        return byteData[row + x * 4 + 3]
    else:
        return 255


def _readBitmapAsColorBGR(byteData, scanSize, height, bpp, x, y, palette):
    # Reads the pixel color value at the given position of a bitmap image,
    # represented by an array of bottom-up Windows or OS/2 bitmap data.
    # The color value is returned as an array containing the blue, green,
    # and red components, in that order.
    match bpp:
        case 1:
            return palette[_read1bppBitmap(byteData, scanSize, height, x, y)]
        case 4:
            return palette[_read4bppBitmap(byteData, scanSize, height, x, y)]
        case 8:
            return palette[byteData[scanSize * (height - 1 - y) + x]]
        case 24:
            row = scanSize * (height - 1 - y)
            return byteData[row + x * 3 : row + x * 3 + 3]
        case 32:
            row = scanSize * (height - 1 - y)
            return byteData[row + x * 4 : row + x * 4 + 3]
        case _:
            raise ValueError("Bits per pixel not supported")


def _readwiniconcore(f, entry, isicon, hotspot):
    bmih = struct.unpack("<LllHHLLllLL", f.read(0x28))
    if bmih[0] != 0x28:
        print("unsupported header size")
        return False
    bitcount = bmih[4]
    colortablesize = 1 << bitcount if bitcount <= 8 else 0
    if colortablesize > 0 and bmih[9] != 0:
        if bmih[9] > colortablesize:
            print("bad biClrUsed")
            return None
        colortablesize = min(colortablesize, bmih[9])
    if bmih[7] != 0 or bmih[8] != 0:
        print("unusual: resolution given")
    if entry and (bmih[1] != entry[0] or bmih[2] != entry[1] * 2):
        print("bad header")
        return None
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
        print(["bad header", bmih])
        return None
    # if entry and isicon and entry[3]!=bmih[4]:
    #   # non-matching bit count
    #   return False
    sizeImage = bmih[6]
    width = bmih[1]
    if bmih[2] % 2 != 0:
        print("odd height value")
        return None
    height = bmih[2] // 2
    if (
        bitcount != 1
        and bitcount != 4
        and bitcount != 8
        and bitcount != 24
        and bitcount != 32
    ):
        print("unsupported bit count")
        return None
    xormaskscan = ((width * bitcount + 31) >> 5) << 2
    andmaskscan = ((width * 1 + 31) >> 5) << 2
    xormaskbytes = xormaskscan * height
    andmaskbytes = andmaskscan * height
    if isicon and bitcount <= 8 and entry and entry[2] > colortablesize:
        print("too few colors")
        return None
    totalsize = colortablesize * 4 + xormaskbytes + andmaskbytes + 0x28
    if entry and totalsize != entry[4]:
        print("bad overall image size: %d %d" % (totalsize, entry[4]))
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
        print("color table read failed")
        return None
    xormask = f.read(xormaskbytes)
    if len(xormask) != xormaskbytes:
        return None
    andmask = f.read(andmaskbytes)
    if len(andmask) != andmaskbytes:
        return None
    bl = dw.blankimage(width, height, alpha=True)
    alpha1 = bytes([0xFF])
    alpha0 = bytes([0])
    for y in range(height):
        for x in range(width):
            bitand = _read1bppBitmap(andmask, andmaskscan, height, x, y)
            pxalpha = _readBitmapAlpha(xormask, xormaskscan, height, bitcount, x, y)
            px = _readBitmapAsColorBGR(
                xormask, xormaskscan, height, bitcount, x, y, colortable
            ) + (
                (bytes([pxalpha]) if pxalpha != 255 else alpha1)
                if bitand == 0
                else alpha0
            )
            dw.setpixelbgralpha(bl, width, height, x, y, px)
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
    return [([[z for z in y[0]], y[1], y[2]] if y else None) for y in x]


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
        endpos = f.tell() + sz
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
                    while True:
                        if content.tell() == listSz - 4:
                            break
                        fcc = content.read(4)
                        sz = struct.unpack("<L", content.read(4))[0]
                        if fcc == b"icon":
                            ret.append(_readwinicon(io.BytesIO(content.read(sz))))
                        else:
                            content.seek(f.tell() + sz)
                    if len(ret) != anih[1]:
                        raise ValueError
                    if seq:
                        ret = [_dup(ret[frame]) for frame in seq]
                    return ret
                else:
                    f.seek(f.tell() + sz - 4)
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
                f.seek(f.tell() + sz)
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
    if newheader[0] != 0 or ((not isicon) and (not iscurosr)):
        return []
    entries = []
    for i in range(newheader[2]):
        dirent = struct.unpack("<BBBBHHLL", f.read(16))
        width = 256 if dirent[0] == 0 else dirent[0]
        height = 256 if dirent[1] == 0 else dirent[1]
        colorcount = dirent[2]
        if iscursor:
            if dirent[4] == 0xFFFF and dirent[5] == 0xFFFF:
                print("no hotspot?")
            elif dirent[4] > width or dirent[5] > height:
                print(
                    "hotspot out of bounds: %d/%d %d/%d"
                    % (dirent[4], width, dirent[5], height)
                )
                entries.append(None)
                continue
        elif isicon:
            # Apparently, planes and bit count are ignored and can be 0.
            # if dirent[4]!=1:
            # print("unsupported planes")
            # entries.append(None); continue
            # if dirent[5]!=1 and dirent[5]!=4 and dirent[5]!=8 and \
            # dirent[5]!=24:
            # print("unsupported bit count")
            # entries.append(None); continue
            pass
        entries.append(
            [width, height, colorcount, dirent[5], dirent[6], dirent[7] + ft, dirent[4]]
        )
    for i in range(len(entries)):
        if not entries[i]:
            continue
        f.seek(entries[i][5])
        entries[i] = _readwiniconcore(
            f,
            entries[i],
            newheader[1] == 1,
            [entries[i][6], entries[i][3]] if iscursor else None,
        )
    return entries


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
            print("unrecognized tag: %s" % (tag))
            return None
        isColor = tag == b"CI" or tag == b"CP"  # color icon or color pointer
        isIcon = tag == b"CI" or tag == b"IC"
        isPointer = tag == b"CP" or tag == b"PT"
        isBitmap = tag == b"BM"
        andmaskinfo = struct.unpack("<LHHL", f.read(0x0C))
        offsetToImage = andmaskinfo[3]
        if not isBitmap:
            hotspotX = andmaskinfo[1]  # hotspot is valid for icons and pointers
            hotspotY = andmaskinfo[2]  # hotspot is valid for icons and pointers
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
    if andmaskhdr[0] == 0x0C:
        andmaskhdr += struct.unpack("<HHHH", f.read(8))
        if andmaskhdr[4] <= 8:
            andpalette = 1 << andmaskhdr[4]
    elif andmaskhdr[0] < 0x10:
        print("unsupported header size")
        return None
    elif andmaskhdr[0] >= 40:
        andmaskhdr += struct.unpack("<llHHLLllLL", f.read(36))
        slack = f.read(andmaskhdr[0] - 40)
        andsizeImage = andmaskhdr[6]
        if andmaskhdr[4] <= 8:
            andpalette = 1 << andmaskhdr[4]
        if andmaskhdr[4] <= 8 and andmaskhdr[9] != 0:  # biClrUsed
            andpalette = min(andpalette, andmaskhdr[9])
        andcompression = andmaskhdr[5]
        if andcompression > 4:
            print("unsupported compression: %d" % (andcompression))
            return None
        if (
            (andcompression == 1 and andmaskhdr[4] != 8)
            or (andcompression == 2 and andmaskhdr[4] != 4)
            or (andcompression == 4 and andmaskhdr[4] != 24)
            or (andcompression == 3 and andmaskhdr[4] != 1)
        ):
            print("unsupported compression: %d" % (andcompression))
            return None
        if andmaskhdr[7] != 0 or andmaskhdr[8] != 0:
            # resolutions seen include 3622x3622 pixels per meter (about 92 dpi)
            # Also seen: 2833x2833; 2834x2834; 2667x2667; 2667x2000 (EGA); 2667x1111 (CGA)
            # print(
            #    "nonzero compression or resolution: %d %d %d"
            #    % (andmaskhdr[5], andmaskhdr[7], andmaskhdr[8])
            # )
            pass
        allzeros = True
        for i in range(len(slack)):
            if slack[i] != 0:
                allzeros = False
        if not allzeros:
            print("nonzero slack")
            return None
    elif andmaskhdr[0] >= 0x10:
        andmaskhdr += struct.unpack("<llHH", f.read(12))
        if andmaskhdr[4] <= 8:
            andpalette = 1 << andmaskhdr[4]
        slack = f.read(andmaskhdr[0] - 0x10)
        allzeros = True
        for i in range(len(slack)):
            if slack[i] != 0:
                allzeros = False
        if not allzeros:
            print("nonzero slack")
            return None
    if andmaskhdr[2] < 0:
        print("top-down bitmaps not supported")
        return None
    if andmaskhdr[1] == 0 or andmaskhdr[2] == 0:
        print("zero image size not supported")
        return None
    if (isIcon or isPointer) and andmaskhdr[2] % 2 != 0:
        raise ValueError("mask height is odd")
    if andmaskhdr[3] != 1:
        print("unsupported no. of planes")
        return None
    if isBitmap:
        if (
            andmaskhdr[4] != 1
            and andmaskhdr[4] != 4
            and andmaskhdr[4] != 8
            and andmaskhdr[4] != 24
            and andmaskhdr[4] != 32
        ):
            print("unsupported bits per pixel: %d" % (andmaskhdr[4]))
            return None
    else:
        if andmaskhdr[4] != 1:  # Only 1-bpp AND/XOR masks are supported
            raise ValueError("unsupported bits per pixel: %d" % (andmaskhdr[4]))
        if andpalette != 2:
            print("unusual palette size: %d" % (andpalette))
            unusual = None
    if andmaskhdr[1] < 0:
        return None
    andcolortable = f.tell()
    f.seek(andcolortable + andpalette * (3 if andmaskhdr[0] <= 0x0C else 4))
    if packedWinBitmap:
        offsetToImage = f.tell()
    w = andmaskhdr[1]
    h = andmaskhdr[2]
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
            print("unsupported header size")
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
                print("unsupported compression: %d" % (colorcompression))
                return None
            if (
                (colorcompression == 1 and colormaskhdr[4] != 8)
                or (colorcompression == 2 and colormaskhdr[4] != 4)
                or (colorcompression == 4 and colormaskhdr[4] != 24)
                or (colorcompression == 3 and colormaskhdr[4] != 1)
            ):
                print("unsupported compression: %d" % (andcompression))
                return None
            if colormaskhdr[7] != 0 or colormaskhdr[8] != 0:
                # print(
                #    "nonzero compression or resolution: %d %d %d"
                #    % (colormaskhdr[5], colormaskhdr[7], colormaskhdr[8])
                # )
                pass
            allzeros = True
            for i in range(len(slack)):
                if slack[i] != 0:
                    allzeros = False
            if not allzeros:
                print("nonzero slack")
                return None
        elif colormaskhdr[0] >= 0x10:
            colormaskhdr += struct.unpack("<llHH", f.read(12))
            slack = f.read(colormaskhdr[0] - 0x10)
            allzeros = True
            for i in range(len(slack)):
                if slack[i] != 0:
                    allzeros = False
            if not allzeros:
                print("nonzero slack")
                return None
        if colormaskhdr[1] < 0:
            return None
        colorbpp = colormaskhdr[4]
        if colormaskhdr[2] < 0:
            print("top-down bitmaps not supported")
            return None
        if colorbpp == 3:
            # NOTE: A 3 BPP color icon was attested, but it is unclear whether
            # OS/2 supports such 3 BPP icons.
            print("3 bits per pixel not supported")
            return None
        if colormaskhdr[1] == 0 or colormaskhdr[2] == 0:
            print("zero image size not supported")
            return None
        if colormaskhdr[1] != andmaskhdr[1]:
            raise ValueError("unsupported width")
        if colormaskhdr[2] * 2 != andmaskhdr[2]:
            raise ValueError("unsupported height")
        if colormaskhdr[3] != 1:
            print("unsupported no. of planes")
            return None
        if colorbpp != 1 and colorbpp != 4 and colorbpp != 8 and colorbpp != 24:
            print("unsupported bits per pixel: %d" % (colorbpp))
            return None
        colorpalette = 0
        if colorbpp <= 8:
            colorpalette = 1 << colorbpp
        colorcolortable = f.tell()
        w = colormaskhdr[1]
        h = colormaskhdr[2]
        colormaskscan = ((w * colorbpp + 31) >> 5) << 2
        colormaskbits = colormaskscan * h
    realHeight = andmaskhdr[2] if isBitmap else andmaskhdr[2] // 2
    # hot spot Y counts from the bottom left row up, so adjust
    # for top-down convention
    if not isBitmap:
        hotspotY = realHeight - 1 - hotspotY
        if hotspotY < 0 or hotspotY >= realHeight:
            # hotspot outside of image
            if isPointer:
                raise ValueError
        if hotspotX < 0 or hotspotX >= andmaskhdr[1]:
            # hotspot outside of image
            if isPointer:
                raise ValueError
    tablesize = (1 << andmaskhdr[4]) if andpalette > 0 else 0
    # The palette of icons' and pointers' AND/XOR mask
    # is effectively fixed at black and white (that is,
    # (0,0,0) and (255,255,255), respectively).
    # It may be, but I am not sure, that OS/2
    # ignores the color table of icons' and pointers' AND/XOR mask.
    andmaskcolors = []
    if not (isIcon or isPointer):
        # Gather bitmap's color table if not an icon or pointer
        tablesize = 2
        if andpalette > 0:
            f.seek(andcolortable)
            cts = 3 if andmaskhdr[0] <= 0x0C else 4
            for i in range(andpalette):
                clr = f.read(3)  # BGR color
                andmaskcolors.append(clr)
                if len(clr) != 3:
                    raise ValueError
                if cts > 3:
                    f.read(cts - 3)
            for i in range((1 << andmaskhdr[4]) - andpalette):
                clr = bytes([0, 0, 0])
                andmaskcolors.append(clr)
    # Offset from the beginning of the file, not necessarily
    # from the beginning of the bitmap/icon/cursor header.
    # If packedWinBitmap is true, this is instead the offset
    # immediately after the header and color table.
    # print(["offsetToImage",offsetToImage])
    f.seek(offsetToImage)
    sz = andsizeImage if andsizeImage > 0 and andcompression > 0 else andmaskbits
    # print(["andSizeImage",andsizeImage,"andmaskbits",andmaskbits])
    andmask = f.read(sz)
    if len(andmask) != sz:
        print("Failure: %d %d [%d]" % (len(andmask), sz, andcompression))
        return None
    if andcompression > 0:
        deco = [0 for i in range(andmaskbits)]
        if andcompression == 1 and not _rle8decompress(
            andmask, deco, andmaskhdr[1], andmaskhdr[2]
        ):
            print("Failed to decompress")
            return None
        elif andcompression == 2 and not _rle4decompress(
            andmask, deco, andmaskhdr[1], andmaskhdr[2]
        ):
            print("Failed to decompress")
            return None
        elif andcompression == 3 and not _huffmandecompress(
            andmask, deco, andmaskhdr[1], andmaskhdr[2]
        ):
            print("Failed to decompress")
            return None
        elif andcompression == 4 and not _rle24decompress(
            andmask, deco, andmaskhdr[1], andmaskhdr[2]
        ):
            print("Failed to decompress")
            return None
        andmask = bytes(deco)
    if len(andmask) != andmaskbits:
        print("Failure: %d %d" % (len(andmask), andmaskbits))
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
            print("Failure: %d %d" % (len(andmask), sz))
            return None
        if colorcompression > 0:
            deco = [0 for i in range(colormaskbits)]
            if colorcompression == 1 and not _rle8decompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                print("Failed to decompress")
                return None
            elif colorcompression == 2 and not _rle4decompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                print("Failed to decompress")
                return None
            elif colorcompression == 3 and not _huffmandecompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                print("Failed to decompress")
                return None
            elif colorcompression == 4 and not _rle24decompress(
                colormask, deco, colormaskhdr[1], colormaskhdr[2]
            ):
                print("Failed to decompress")
                return None
            colormask = bytes(deco)
        if len(colormask) != colormaskbits:
            print("Failure: %d %d" % (len(colormask), colormaskbits))
            return None
    width = 0
    height = 0
    ret = None
    if isBitmap:
        cw = andmaskhdr[1]
        ch = andmaskhdr[2]
        bpp = andmaskhdr[4]
        ci = dw.blankimage(cw, ch, alpha=True)
        alpha1 = bytes([255])
        for y in range(ch):
            for x in range(cw):
                col = _readBitmapAsColorBGR(
                    andmask, andmaskscan, ch, bpp, x, y, andmaskcolors
                )
                alpha = (
                    alpha1
                    if bpp
                    else bytes(_readBitmapAlpha(andmask, andmaskscan, ch, bpp, x, y))
                )
                dw.setpixelbgralpha(ci, cw, ch, x, y, col + alpha)
        ret = ci
        width = cw
        height = ch
    elif isColor:
        cw = colormaskhdr[1]
        ch = colormaskhdr[2]
        bpp = colormaskhdr[4]
        bl = dw.blankimage(cw, ch, alpha=True)
        white = bytes([255, 255, 255])
        alpha0 = bytes([0])
        alpha1 = bytes([255])
        for y in range(ch):
            for x in range(cw):
                bitand = _read1bppBitmap(andmask, andmaskscan, andmaskhdr[2], x, y)
                bitxor = _read1bppBitmap(andmask, andmaskscan, andmaskhdr[2], x, y + ch)
                # Windows color icons employ a simpler 2-mask system (an AND mask and
                # an XOR mask) than OS/2 color icons (AND/XOR mask and color mask).
                # The XOR mask for Windows icons is the same as the OS/2 icon's
                # color mask except that, where the OS/2 icon's XOR mask bit (in the bottom
                # half of the AND/XOR mask) and its AND mask bit (in the top half) are 1,
                # the Windows icon's XOR mask bits are all ones.
                # See "Bitmap File Format", in the _Presentation Manager Programming
                # Guide and Reference_.
                # However, the presence of nonzero values in an OS/2 icon's or OS/2 cursor's
                # XOR mask is unusual for color icons and pointers.
                # Moreover, PNGs don't support color inversions.
                px = (
                    white
                    if (bitand & bitxor) == 1
                    else _readBitmapAsColorBGR(
                        colormask, colormaskscan, ch, bpp, x, y, colormaskcolors
                    )
                ) + (
                    (
                        alpha1
                        if bpp
                        else bytes(
                            _readBitmapAlpha(colormask, colormaskscan, ch, bpp, x, y)
                        )
                    )
                    if bitand == 0
                    else alpha0
                )
                dw.setpixelbgralpha(bl, cw, ch, x, y, px)
        width = cw
        height = ch
        ret = bl
    else:
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


# Image has the same format returned by the _desktopwallpaper_ module's _blankimage_ method with alpha=False.
# NOTE: Currently, there must be 256 or fewer unique colors used in the image
# for this method to be successful.
def parallaxAvi(
    image,
    width,
    height,
    destParallax,
    widthReverse=False,
    heightReverse=False,
    interlacing=False,
    fps=15,
):
    if not image:
        raise ValueError
    outputHeight = height // 2 if interlacing else height
    images = [dw.blankimage(width, height) for i in range(32)]
    for i in range(32):
        dw.imageblit(
            images[i],
            width,
            height,
            width - width * i // 32 if widthReverse else width * i // 32,
            height - height * i // 32 if heightReverse else height * i // 32,
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
    dw.writeavi(destParallax, images, width, outputHeight, fps=fps)


# Generates an AVI video file consisting of images arranged
# in a row or column.  If the source image's width
# is greater than its height, then each frame's height
# is the same as the source image's; if less, each
# frame's width.
# The source image has the same format returned by the
# _desktopwallpaper_ module's _blankimage_ method with alpha=False.
# NOTE: Currently, there must be 256 or fewer unique colors used in the image
# for this method to be successful.
def animationBitmap(image, width, height, destImage, firstFrame=0, fps=15):
    frameSize = min(width, height)
    if frameSize <= 0:
        raise ValueError
    animWidth = frameSize if width > height else width
    animHeight = frameSize if height > width else height
    images = []
    for i in range(firstFrame, max(width, height) // frameSize):
        dst = dw.blankimage(animWidth, animHeight)
        imageblitex(
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
    writeavi(destImage, images, animWidth, animHeight, fps=fps)
