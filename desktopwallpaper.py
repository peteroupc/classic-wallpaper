# This Python script helps generate interesting variations on desktop
# wallpapers based on existing image files.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under Creative Commons Zero (CC0).
#
# NOTE: Animation of tilings composed from a wallpaper
# image can be implemented by shifting, with each frame, the starting
# position for drawing the top left corner of the wallpaper tiling
# (e.g., from the top left corner of the image
# to some other position in the image).
#
# NOTE: In Windows, if both an 8x8 monochrome pattern and a centered wallpaper
# are set as the desktop background, both the pattern and the wallpaper
# will be drawn on the desktop, the latter appearing above the former.
#
# NOTE: I would welcome it if readers could contribute computer code (released
# to the public domain or under Creative Commons Zero) to generate tileable—
# - noise,
# - procedural textures or patterns, or
# - arrangements of symbols or small images with partial transparency,
# without artificial intelligence, with a limited color palette and a small
# resolution, as long as the resulting images do not employ
# trademarks and are suitable for all ages.  For details on the color and
# resolution options as well as a broader challenge to generate tileable
# classic wallpapers, see:
#
# https://github.com/peteroupc/classic-wallpaper
#

import os
import math
import random
import struct

def _listdir(p):
    return [os.path.abspath(p + "/" + x) for x in os.listdir(p)]

DitherMatrix = [  # Bayer 8x8 ordered dither matrix
    0,
    32,
    8,
    40,
    2,
    34,
    10,
    42,
    48,
    16,
    56,
    24,
    50,
    18,
    58,
    26,
    12,
    44,
    4,
    36,
    14,
    46,
    6,
    38,
    60,
    28,
    52,
    20,
    62,
    30,
    54,
    22,
    3,
    35,
    11,
    43,
    1,
    33,
    9,
    41,
    51,
    19,
    59,
    27,
    49,
    17,
    57,
    25,
    15,
    47,
    7,
    39,
    13,
    45,
    5,
    37,
    63,
    31,
    55,
    23,
    61,
    29,
    53,
    21,
]

def _bayerdither(a, b, t, x, y):
    # 't' is such that 0<=t<=1; closer to 1 means closer to 'b';
    # closer to 0 means closer to 'a'.
    # 'x' and 'y' are a pixel position.
    bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
    if bdither < t * 64:
        return b
    else:
        return a

def websafecolors():
    colors = []
    for r in range(6):
        for g in range(6):
            for b in range(6):
                colors.append([r * 51, g * 51, b * 51])
    return colors

def egacolors():
    # 64 colors displayable by EGA displays
    colors = []
    for r in range(4):
        for g in range(4):
            for b in range(4):
                colors.append([r * 85, g * 85, b * 85])
    return colors

def cgacolors():
    # Canonical 16-color CGA palette
    # see also: https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/
    return [
        [0, 0, 0],
        [0, 0, 170],
        [0, 170, 0],
        [0, 170, 170],
        [170, 0, 0],
        [170, 0, 170],
        [170, 85, 0],  # [170, 170, 0] is another variant, given
        # that exact color values for CGA's 16 colors
        # are unstandardized beyond the notion of 'RGBI'.
        [170, 170, 170],
        [85, 85, 85],
        [85, 85, 255],
        [85, 255, 85],
        [85, 255, 255],
        [255, 85, 85],
        [255, 85, 255],
        [255, 255, 85],
        [255, 255, 255],
    ]

def classiccolors():
    # 16-color VGA palette
    return [
        [0, 0, 0],
        [128, 128, 128],
        [192, 192, 192],
        [255, 0, 0],
        [128, 0, 0],
        [0, 255, 0],
        [0, 128, 0],
        [0, 0, 255],
        [0, 0, 128],
        [255, 0, 255],
        [128, 0, 128],
        [0, 255, 255],
        [0, 128, 128],
        [255, 255, 0],
        [128, 128, 0],
        [255, 255, 255],
    ]

def classiccolors2():
    # colors in classiccolors() and their "half-and-half" versions
    colors = []
    for a in [0, 64, 128, 192]:
        for b in [0, 64, 128, 192]:
            for c in [0, 64, 128, 192]:
                cij = [a, b, c]
                if cij not in colors:
                    colors.append(cij)
    for a in [0, 128, 255]:
        for b in [0, 128, 255]:
            for c in [0, 128, 255]:
                cij = [a, b, c]
                if cij not in colors:
                    colors.append(cij)
    for a in [96, 160]:
        for b in [96, 160]:
            for c in [96, 160]:
                cij = [a, b, c]
                if cij not in colors:
                    colors.append(cij)
    for a in [96, 224]:
        for b in [96, 224]:
            for c in [96, 224]:
                cij = [a, b, c]
                if cij not in colors:
                    colors.append(cij)
    return colors

def paletteandhalfhalf(palette):
    ret = [
        [k & 0xFF, (k >> 8) & 0xFF, (k >> 16) & 0xFF]
        for k in getdithercolors(palette).keys()
    ]
    ret.sort()
    return ret

def getdithercolors(palette):
    # Gets the "half-and half" versions of colors in the given palette.
    if (not palette) or (len(palette) > 256):  # too long palettes not supported
        raise ValueError
    colors = {}
    for c in palette:
        cij = c[0] | (c[1] << 8) | (c[2] << 16)
        if cij not in colors:
            colors[cij] = [cij, cij]
    for i in range(len(palette)):
        for j in range(i + 1, len(palette)):
            ci = palette[i]
            cj = palette[j]
            ci1 = ci[0] | (ci[1] << 8) | (ci[2] << 16)
            cj1 = cj[0] | (cj[1] << 8) | (cj[2] << 16)
            cij = (
                ((ci[0] + cj[0] + 1) // 2)
                | (((ci[1] + cj[1] + 1) // 2) << 8)
                | (((ci[2] + cj[2] + 1) // 2) << 16)
            )
            if cij not in colors:
                colors[cij] = [ci1, cj1]
    return colors

def halfhalfditherimage(image, width, height, palette):
    if width <= 0 or height <= 0:
        raise ValueError
    cdcolors = getdithercolors(palette)
    for y in range(height):
        yd = y * width
        for x in range(width):
            xp = yd + x
            col = image[xp * 3] | (image[xp * 3 + 1] << 8) | (image[xp * 3 + 2] << 16)
            cd = cdcolors[col]
            if not cd:
                raise ValueError
            col = cd[0] if (x + y) % 2 == 0 else cd[1]
            image[xp * 3] = col & 0xFF
            image[xp * 3 + 1] = (col >> 8) & 0xFF
            image[xp * 3 + 2] = (col >> 16) & 0xFF

def _isqrtceil(i):
    r = math.isqrt(i)
    return r if r * r == i else r + 1

# Returns an ImageMagick filter string to generate a desktop background from an image, in three steps.
# 1. If rgb1 and rgb2 are not nil, converts the input image to grayscale, then translates the grayscale
# palette to a gradient starting at rgb1 for black (a 3-item array of the red,
# green, and blue components in that order; e.g., [2,10,255] where each
# component is from 0 through 255) and ending at rgb2 for white (same format as rgb1).
# Raises an error if rgb1 or rgb2 has a length less than 3.
# The output image is the input for the next step.
# 2. If hue is not 0, performs a hue shift, in degrees (-180 to 180), of the input image.
# The output image is the input for the next step.
# 3. If basecolors is not nil, ensures that that the image used only the colors
# given in 'basecolors', which is a list
# of colors (each color is of the same format as rgb1 and rgb2).  If 'dither' is also True, the
# image's colors are then scattered so that they appear close to the original colors.
# Raises an error if 'basecolors' has a length greater than 256.
def magickgradientditherfilter(
    rgb1=None, rgb2=None, basecolors=None, hue=0, dither=True
):
    if hue < -180 or hue > 180:
        raise ValueError
    if rgb1 and len(rgb1) < 3:
        raise ValueError
    if rgb2 and len(rgb2) < 3:
        raise ValueError
    if basecolors:
        if len(basecolors) > 256:
            raise ValueError
        for k in basecolors:
            if (not k) or len(k) < 3:
                raise ValueError
    ret = []
    huemod = (hue + 180) * 100.0 / 180.0
    if rgb1 != None and rgb2 != None:
        r1 = "#%02x%02x%02x" % (int(rgb1[0]), int(rgb1[1]), int(rgb1[2]))
        r2 = "#%02x%02x%02x" % (int(rgb2[0]), int(rgb2[1]), int(rgb2[2]))
        ret += [
            "(",
            "+clone",
            "-grayscale",
            "Rec709Luma",
            ")",
            "(",
            "-size",
            "1x256",
            "gradient:%s-%s" % (r1, r2),
            ")",
            "-delete",
            "0",
            "-clut",
        ]
    if hue != 0:
        ret += ["-modulate", "100,100,%.02f" % (huemod)]
    if basecolors and len(basecolors) > 0:
        bases = ["xc:#%02X%02X%02X" % (k[0], k[1], k[2]) for k in basecolors]
        # ImageMagick command to generate the palette image
        ret += (
            ["(", "-size", "1x1"]
            + bases
            + ["+append", "-write", "mpr:z", "+delete", ")"]
        )
        # Apply Floyd-Steinberg error diffusion dither.
        # NOTE: For abstractImage = True, ImageMagick's ordered 8x8 dithering
        # algorithm ("-ordered-dither 8x8") is by default a per-channel monochrome
        # (2-level) dither, not a true color dithering approach that takes much
        # account of the color palette.
        # As a result, for example, dithering a grayscale image with the algorithm will
        # lead to an image with only black and white pixels, even if the palette contains,
        # say, ten shades of gray.  The number after "8x8" is the number of color levels
        # per color channel in the ordered dither algorithm, and this number is taken
        # as the square root of the palette size, rounded up, minus 1, but not less
        # than 2.
        # ditherkind = (
        #    "-ordered-dither 8x8,%d" % (min(2, _isqrtceil(len(basecolors)) - 1))
        #    if abstractImage
        #    else "-dither FloydSteinberg"
        # )
        # "+dither" disables dithering
        if dither:
            ret += ["-dither", "FloydSteinberg"]
        else:
            ret += ["+dither"]
        ret += ["-remap", "mpr:z"]
    return ret

def _magickgradientditherfilter(
    rgb1=None, rgb2=None, basecolors=None, hue=0, dither=True
):
    return (
        " "
        + (" ".join(magickgradientditherfilter(rgb1, rgb2, basecolors, hue, dither)))
        + " "
    )

def solid(bg=[192, 192, 192], w=64, h=64):
    if bg == None or len(bg) < 3:
        raise ValueError
    bc = "#%02x%02x%02x" % (int(bg[0]), int(bg[1]), int(bg[2]))
    return ["-size", "%dx%d" % (w, h), "xc:%s" % (bc)]

def hautrelief(bg=[192, 192, 192], highlight=[255, 255, 255], shadow=[0, 0, 0]):
    if bg == None or len(bg) < 3:
        raise ValueError
    if highlight == None or len(highlight) < 3:
        raise ValueError
    if shadow == None or len(shadow) < 3:
        raise ValueError
    bc = "#%02x%02x%02x" % (int(bg[0]), int(bg[1]), int(bg[2]))
    hc = "#%02x%02x%02x" % (int(highlight[0]), int(highlight[1]), int(highlight[2]))
    sc = "#%02x%02x%02x" % (int(shadow[0]), int(shadow[1]), int(shadow[2]))
    return (
        " -grayscale Rec709Luma -channel RGB -threshold 51%% -write mpr:z "
        + '\\( -clone 0 -morphology Convolve "3:0,0,0 0,0,0 0,0,1" -write mpr:z1 \\) '
        + '\\( -clone 0 -morphology Convolve "3:1,0,0 0,0,0 0,0,0" -write mpr:z2 \\) -delete 0 '
        + "-compose Multiply -composite "
        + "\\( mpr:z1 mpr:z2 -compose Screen -composite -negate \\) -compose Plus -composite "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a1 -delete 0 "
        + 'mpr:z1 \\( mpr:z -negate -morphology Convolve "3:1,0,0 0,0,0 0,0,0" \\) -compose Multiply -composite '
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a2 -delete 0 "
        + '\\( mpr:z -negate -morphology Convolve "3:0,0,0 0,0,0 0,0,1" \\) mpr:z2 -compose Multiply -composite '
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut mpr:a2 -compose Plus -composite mpr:a1 -compose Plus -composite "
    ) % (bc, hc, sc)

def emboss():
    # Emboss a two-color black and white image into a 3-color (black/gray/white) image
    return [
        "(",
        "+clone",
        "(",
        "+clone",
        ")",
        "-append",
        "(",
        "+clone",
        ")",
        "+append",
        "-crop",
        "50%x50%+1+1",
        "(",
        "-size",
        "1x2",
        "gradient:#FFFFFF-#808080",
        ")",
        "-clut",
        ")",
        "-compose",
        "Multiply",
        "-composite",
    ]

def basrelief(bg=[192, 192, 192], highlight=[255, 255, 255], shadow=[0, 0, 0]):
    if bg == None or len(bg) < 3:
        raise ValueError
    if highlight == None or len(highlight) < 3:
        raise ValueError
    if shadow == None or len(shadow) < 3:
        raise ValueError
    bc = "#%02x%02x%02x" % (int(bg[0]), int(bg[1]), int(bg[2]))
    hc = "#%02x%02x%02x" % (int(highlight[0]), int(highlight[1]), int(highlight[2]))
    sc = "#%02x%02x%02x" % (int(shadow[0]), int(shadow[1]), int(shadow[2]))
    return (
        " -grayscale Rec709Luma -channel RGB -threshold 51%% -write mpr:z "
        + '\\( -clone 0 -morphology Convolve "3:0,0,0 0,0,0 0,0,1" -write mpr:z1 \\) '
        + '\\( -clone 0 -morphology Convolve "3:1,0,0 0,0,0 0,0,0" -write mpr:z2 \\) -delete 0--1 '
        + "mpr:z2 \\( mpr:z -negate \\) -compose Multiply -composite -write mpr:a10 "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a2 -delete 0 "
        + "\\( mpr:z -negate \\) mpr:z1 -compose Multiply -composite -write mpr:a20 "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a1 -delete 0 "
        + "mpr:a10 mpr:a20 -compose Plus -composite -negate "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut mpr:a2 -compose Plus -composite "
        + "mpr:a1 -compose Plus -composite "
    ) % (sc, hc, bc)

def magickgradientditherfilterrandom():
    rgb1 = None
    rgb2 = None
    hue = 0
    basecolors = None
    while rgb1 == None and rgb2 == None and hue == 0 and basecolors == None:
        if random.randint(0, 99) == 1:
            return magickgradientditherfilter()
        rgb1 = None
        rgb2 = None
        hue = 0
        basecolors = None
        if random.randint(0, 9) < 6:
            rgb1 = [0, 0, 0]
            rgb2 = [
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            ]
        if random.randint(0, 9) < 3:
            hue = random.randint(0, 50) - 180
        r = random.randint(0, 9)
        if r < 3:
            basecolors = classiccolors()
        elif r < 6:
            basecolors = websafecolors()
        elif r < 8 and rgb1 != None:
            basecolors = [rgb1, rgb2]
    return magickgradientditherfilter(rgb1, rgb2, basecolors, hue=hue)

def _chopBeforeHAppend():
    return " " + (" ".join(_chopBeforeHAppendArray())) + " "

def _chopBeforeHAppendArray(withFarEnd=True):
    if withFarEnd:
        # Remove the left and right column
        return [
            "+repage",  # If absent, chop might fail
            "-gravity",
            "West",
            "-chop",
            "1x0",
            "-gravity",
            "East",
            "-chop",
            "1x0",
            "+gravity",
        ]
    # Remove the left column
    return ["+repage", "-gravity", "West", "-chop", "1x0", "+gravity"]

def _chopBeforeVAppend():
    return " " + (" ".join(_chopBeforeVAppendArray())) + " "

def _chopBeforeVAppendArray(withFarEnd=True):
    if withFarEnd:
        # Remove the top and bottom row
        return [
            "+repage",  # If absent, chop might fail
            "-gravity",
            "North",
            "-chop",
            "0x1",
            "-gravity",
            "South",
            "-chop",
            "0x1",
            "+gravity",
        ]
    # Remove the top row
    return ["+repage", "-gravity", "North", "-chop", "0x1", "+gravity"]

def tileable():
    # ImageMagick command to generate a Pmm wallpaper group tiling pattern.
    # This command can be applied to arbitrary images to render them
    # tileable.
    # NOTE: "-append" is a vertical append; "+append" is a horizontal append;
    # "-flip" reverses the row order; "-flop" reverses the column order.
    return (
        ["(", "+clone", "-flip"]
        + _chopBeforeVAppendArray()
        + [")", "-append", "(", "+clone", "-flop"]
        + _chopBeforeHAppendArray()
        + [")", "+append"]
    )

def groupP2():
    # ImageMagick command to generate a P2 wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last row's first half is a mirror of its second half.
    return (
        ["(", "+clone", "-flip", "-flop"] + _chopBeforeVAppendArray() + [")", "-append"]
    )

def groupPm():
    # ImageMagick command to generate a Pm wallpaper group tiling pattern.
    return ["(", "+clone", "-flop"] + _chopBeforeHAppendArray() + [")", "+append"]

def groupPg():
    # ImageMagick command to generate a Pg wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last column's first half is a mirror of its second half.
    return ["(", "+clone", "-flip"] + _chopBeforeVAppendArray() + [")", "-append"]

def groupPgg():
    # ImageMagick command to generate a Pgg wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last row's and last column's first half is a mirror of its
    # second half.
    return (
        [
            "-write",
            "mpr:wpgroup",
            "-delete",
            "0",
            "(",
            "mpr:wpgroup",
            "(",
            "mpr:wpgroup",
            "-flip",
            "-flop",
        ]
        + _chopBeforeHAppendArray()
        + [
            ")",
            "+append",
            ")" "(",
            "(",
            "mpr:wpgroup",
            "-flip",
            "-flop",
            ")",
            "(",
            "mpr:wpgroup",
        ]
        + _chopBeforeHAppendArray()
        + [")", "+append"]
        + _chopBeforeVAppendArray()
        + [")", "-append"]
    )

def groupCmm():
    # ImageMagick command to generate a Cmm wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last row's and last column's first half is a mirror of its
    # second half.
    return (
        " \\( +clone -flip \\) -append -write mpr:wpgroup -delete 0 "
        + "\\( mpr:wpgroup \\( mpr:wpgroup -flop "
        + _chopBeforeHAppend()
        + " \\) +append \\) "
        + "\\( \\( mpr:wpgroup -flop \\) \\( mpr:wpgroup "
        + _chopBeforeHAppend()
        + " \\) +append "
        + _chopBeforeVAppend()
        + "\\) "
        + "-append "
    )

def diamondTiling(bgcolor=None):
    # ImageMagick command to generate a diamond tiling pattern (or a brick tiling
    # pattern if the image the command is applied to has only its top half
    # or its bottom half drawn).  For best results, the command should be applied
    # to images with an even width and height. 'bgcolor' is the background color,
    # either None or a 3-item array of the red,
    # green, and blue components in that order; e.g., [2,10,255] where each
    # component is from 0 through 255; default is None, or no background color.
    bc = ""
    if bgcolor:
        bc = " \\( -size 100%x100%"
        bc += " xc:#%02x%02x%02x \\) -compose DstOver -composite " % (
            int(bg[0]),
            int(bg[1]),
            int(bg[2]),
        )
    return (
        " \\( +clone \\( +clone \\) -append \\( +clone \\) +append -chop "
        + "25%x25% \\) -compose Over -composite "
        + bc
    )

def groupPmg():
    # ImageMagick command to generate a Pmg wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last column's first half is a mirror of its
    # second half.
    return (
        " -write mpr:wpgroup -delete 0 "
        + "\\( mpr:wpgroup \\( mpr:wpgroup -flip -flop "
        + _chopBeforeHAppend()
        + "\\) +append \\) "
        + "\\( \\( mpr:wpgroup -flip \\) \\( mpr:wpgroup -flop "
        + _chopBeforeHAppend()
        + "\\) +append "
        + _chopBeforeVAppend()
        + "\\) "
        + "-append "
    )

def writeppm(f, image, width, height, raiseIfExists=False):
    if not image:
        raise ValueError
    if len(image) != width * height * 3:
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    fd = open(f, "xb" if raiseIfExists else "wb")
    fd.write(bytes("P6\n%d %d\n255\n" % (width, height), "utf-8"))
    fd.write(bytes(image))
    fd.close()

def _simplebox(image, width, height, color, x0, y0, x1, y1):
    borderedbox(image, width, height, None, color, color, x0, y0, x1, y1)

def hatchedbox(
    image,
    width,
    height,
    color,
    pattern,
    x0,
    y0,
    x1,
    y1,
    msbfirst=True,
    drawborder=False,
):
    # Draw a wraparound hatched box on an image.
    # 'color' is the color of the hatch, drawn on every "black" pixel
    # in the pattern's tiling.
    # 'pattern' and 'msbfirst' have the same meaning as in the _monopattern_
    # method.
    # 'drawborder' means to draw the box's border with the hatch color;
    # default is False.
    if x0 < 0 or y0 < 0 or x1 < x0 or y1 < y0:
        raise ValueError
    if width <= 0 or height <= 0:
        raise ValueError
    if (not color) or len(color) != 3:
        raise ValueError
    if x0 == x1 or y0 == y1:
        return
    cr = color[0] & 0xFF
    cg = color[1] & 0xFF
    cb = color[2] & 0xFF
    for y in range(y0, y1):
        ypp = y % height
        yp = ypp * width * 3
        for x in range(x0, x1):
            xp = x % width
            c = (
                ((pattern[ypp & 7] >> (7 - (xp & 7))) & 1)
                if msbfirst
                else ((pattern[ypp & 7] >> (xp & 7)) & 1)
            )
            if (
                drawborder and (y == y0 or y == y1 - 1 or x == x0 or x == x1 - 1)
            ) or c == 1:
                # Draw hatch color
                image[yp + xp * 3] = cr
                image[yp + xp * 3 + 1] = cg
                image[yp + xp * 3 + 2] = cb

def shadowedborderedbox(
    image, width, height, border, shadow, color1, color2, x0, y0, x1, y1
):
    if shadow:
        # Draw box's shadow
        pattern = [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55]
        hatchedbox(
            image, width, height, shadow, pattern, x0 + 4, y0 + 4, x1 + 4, y1 + 4
        )
    borderedbox(image, width, height, border, color1, color2, x0, y0, x1, y1)

def borderedbox(image, width, height, border, color1, color2, x0, y0, x1, y1):
    # Draw a wraparound dither-colored box on an image.
    # 'border' is the color of the 1-pixel-thick border. Can be None (so
    # that no border is drawn)
    # 'color1' and 'color2' are the dithered
    # versions of the inner color. 'color1' and 'color2' can't be None.
    if x0 < 0 or y0 < 0 or x1 < x0 or y1 < y0:
        raise ValueError
    if width <= 0 or height <= 0:
        raise ValueError
    if (not color1) or (not image) or (not color2):
        raise ValueError
    if x0 == x1 or y0 == y1:
        return
    for y in range(y0, y1):
        ypp = y % height
        yp = ypp * width * 3
        for x in range(x0, x1):
            xp = x % width
            if border and (y == y0 or y == y1 - 1 or x == x0 or x == x1 - 1):
                # Draw border color
                image[yp + xp * 3] = border[0]
                image[yp + xp * 3 + 1] = border[1]
                image[yp + xp * 3 + 2] = border[2]
            elif ypp % 2 == xp % 2:
                # Draw first color
                image[yp + xp * 3] = color1[0]
                image[yp + xp * 3 + 1] = color1[1]
                image[yp + xp * 3 + 2] = color1[2]
            else:
                # Draw second color
                image[yp + xp * 3] = color2[0]
                image[yp + xp * 3 + 1] = color2[1]
                image[yp + xp * 3 + 2] = color2[2]

def _blankimage(width, height, color=None):
    if color and len(color) < 3:
        raise ValueError
    image = [255 for i in range(width * height * 3)]  # default background is white
    if color:
        _simplebox(image, width, height, color, 0, 0, width, height)
    return image

def checkerboardimage(width, height, darkcolor, lightcolor, hatchColor=None):
    image = _blankimage(width, height, lightcolor)
    _simplebox(image, width, height, darkcolor, 0, 0, width // 2, height // 2)
    _simplebox(image, width, height, darkcolor, width // 2, height // 2, width, height)
    if hatchColor:
        # hatch=[0x88,0x44,0x22,0x11,0x88,0x44,0x22,0x11] # denser diagonal hatch
        # revhatch=[0x22,0x44,0x88,0x11,0x22,0x44,0x88,0x11] # denser diagonal hatch
        hatch = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]
        revhatch = [0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x01]
        hatchedbox(
            image, width, height, hatchColor, hatch, 0, 0, width // 2, height // 2
        )
        hatchedbox(
            image,
            width,
            height,
            hatchColor,
            revhatch,
            width // 2,
            height // 2,
            width,
            height,
        )
    return image

def _isdark(c):
    r = c & 0xFF
    g = (c >> 8) & 0xFF
    b = (c >> 16) & 0xFF
    return (r * 0.3 + g * 0.5 + b * 0.2) < 127.5

def _nearest(pal, c):
    best = -1
    ret = 0
    r = c & 0xFF
    g = (c >> 8) & 0xFF
    b = (c >> 16) & 0xFF
    for i in range(len(pal)):
        cr = pal[i] & 0xFF
        cg = (pal[i] >> 8) & 0xFF
        cb = (pal[i] >> 16) & 0xFF
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if i == 0 or dist < best:
            ret = i
            best = dist
    return ret

def _darker(c):
    cr = c & 0xFF
    cg = (c >> 8) & 0xFF
    cb = (c >> 16) & 0xFF
    return (cr // 2) + ((cg // 2) << 8) + ((cb // 2) << 16)

def _p2a(c):
    # packed to array
    r = c & 0xFF
    g = (c >> 8) & 0xFF
    b = (c >> 16) & 0xFF
    return [r, g, b]

def randomboxeslightdark(width, height, palette):
    # Generate two portable pixelmaps (PPM) of a tileable pattern
    # with random boxes, namely a light version and a dark version,
    # using only the colors in the given palette.
    if width <= 0 or int(width) != width:
        raise ValueError
    if height <= 0 or int(height) != height:
        raise ValueError
    if (not palette) or len(palette) <= 0 or len(palette) > 512:
        # too long palette not supported
        raise ValueError
    cdkeys = [k[0] | (k[1] << 8) | (k[2] << 16) for k in palette]
    cdkeys.sort()
    darkest = _p2a(_nearest(cdkeys, 0x000000))
    lightimage = _blankimage(width, height, darkest)
    darkimage = _blankimage(width, height, darkest)
    paletteSize = len(palette)
    darkkeys = [cdkeys[_nearest(cdkeys, _darker(cd))] for cd in cdkeys]
    for i in range(45):
        x0 = random.randint(0, width - 1)
        x1 = x0 + random.randint(3, max(3, width * 3 // 4))
        y0 = random.randint(0, height - 1)
        y1 = y0 + random.randint(3, max(3, height * 3 // 4))
        border1 = random.randint(0, 5)
        border2 = random.randint(0, paletteSize - 1)
        color = random.randint(0, paletteSize - 1)
        border = border2 if border1 == 0 else 0
        c1 = _p2a(cdkeys[color])
        shadowedborderedbox(
            lightimage, width, height, darkest, None, c1, c1, x0, y0, x1, y1
        )
        c1 = _p2a(darkkeys[color])
        shadowedborderedbox(
            darkimage, width, height, darkest, None, c1, c1, x0, y0, x1, y1
        )
    return {"light": lightimage, "dark": darkimage}

def randomboxes(width, height, palette):
    # Generate a portable pixelmap (PPM) of a tileable pattern with random boxes,
    # using only the colors in the given palette
    return randomboxeslightdark(width, height, palette)["light"]

def crosshatch(
    hhatchdist=8, vhatchdist=8, hhatchthick=1, vhatchthick=1, fgcolor=None, bgcolor=None
):
    # Generate a portable pixelmap (PPM) of a horizontal and/or vertical hatch
    # pattern.
    # hhatchdist - distance from beginning of one horizontal hash line to the
    # beginning of the next, in pixels.
    # hhatchthick - thickness in pixels of each horizontal hash line.
    # Similar for vhatchdist and vhatchthick, with vertical hash lines.
    # fgcolor -  foreground color.  If None, default is black.
    # bgcolor -  background color.  If None, default is white.
    if hhatchdist <= 0 or hhatchthick < 0 or hhatchthick > hhatchdist:
        raise ValueError
    if vhatchdist <= 0 or vhatchthick < 0 or vhatchthick > vhatchdist:
        raise ValueError
    if fgcolor and len(fgcolor) != 3:
        raise ValueError
    if bgcolor and len(bgcolor) != 3:
        raise ValueError
    if not fgcolor:
        fgcolor = [0, 0, 0]
    width = vhatchdist * 4
    height = hhatchdist * 4
    image = _blankimage(width, height, bgcolor)
    for i in range(4):
        _simplebox(
            image,
            width,
            height,
            fgcolor,
            0,
            hhatchdist * i,
            width,
            hhatchdist * i + hhatchthick,
        )
        _simplebox(
            image,
            width,
            height,
            fgcolor,
            vhatchdist * i,
            0,
            vhatchdist * i + vhatchthick,
            height,
        )
    return {
        "image": image,
        "width": width,
        "height": height,
    }

def verthatch(hatchdist=8, hatchthick=1, fgcolor=None, bgcolor=None):
    # Generate a portable pixelmap (PPM) of a vertical hatch pattern.
    return crosshatch(1, hatchdist, 0, hatchthick, fgcolor=fgcolor, bgcolor=bgcolor)

def horizhatch(hatchdist=8, hatchthick=1, fgcolor=None, bgcolor=None):
    # Generate a portable pixelmap (PPM) of a horizontal hatch pattern.
    return crosshatch(hatchdist, 1, hatchthick, 0, fgcolor=fgcolor, bgcolor=bgcolor)

def _drawdiagstripe(image, width, height, stripesize, reverse, fgcolor=None, offset=0):
    if stripesize > max(width, height) or stripesize < 0:
        raise ValueError
    if fgcolor and len(fgcolor) != 3:
        raise ValueError
    xpstart = -(stripesize // 2)
    for y in range(height):
        yp = y * width * 3
        for x in range(stripesize):
            xp = x + xpstart + offset
            while xp < 0:
                xp += width
            while xp >= width:
                xp -= width
            if reverse:  # drawing reverse stripe
                xp = width - 1 - xp
            imagepos = yp + xp * 3
            if fgcolor:
                image[imagepos] = fgcolor[0] & 0xFF
                image[imagepos + 1] = fgcolor[1] & 0xFF
                image[imagepos + 2] = fgcolor[2] & 0xFF
            else:
                # default foreground color is black
                image[imagepos] = 0
                image[imagepos + 1] = 0
                image[imagepos + 2] = 0
        xpstart += 1

def diagcrosshatch(
    wpsize=64, stripesize=32, revstripesize=32, fgcolor=None, bgcolor=None
):
    # Generate a portable pixelmap (PPM) of a diagonal stripe pattern
    # 'wpsize': image width and height, in pixels
    # 'stripesize': thickness of stripe (running from top left to bottom
    # right assuming the image's first row is the top row), in pixels
    # 'revstripesize': thickness of stripe (running from top right to bottom
    # left), in pixels
    # 'fgcolor': foreground color.  If None, default is black.
    # 'bgcolor': background color.  If None, default is white.
    if stripesize > wpsize or stripesize < 0:
        raise ValueError
    if revstripesize > wpsize or revstripesize < 0:
        raise ValueError
    if wpsize <= 0 or int(wpsize) != wpsize:
        raise ValueError
    if fgcolor and len(fgcolor) != 3:
        raise ValueError
    width = wpsize
    height = wpsize
    image = _blankimage(width, height, bgcolor)
    # Draw the stripes
    _drawdiagstripe(image, width, height, stripesize, False, fgcolor=fgcolor)
    _drawdiagstripe(image, width, height, revstripesize, True, fgcolor=fgcolor)
    return image

def diaghatch(wpsize=64, stripesize=32, fgcolor=None, bgcolor=None):
    return diagcrosshatch(wpsize, stripesize, 0, fgcolor, bgcolor)

def diagrevhatch(wpsize=64, stripesize=32, fgcolor=None, bgcolor=None):
    return diagcrosshatch(wpsize, 0, stripesize, fgcolor, bgcolor)

def dithertograyimage(image, width, height, grays):
    for y in range(height):
        yp = y * width * 3
        for x in range(width):
            xp = yp + x * 3
            c = (image[xp] * 2126 + image[xp + 1] * 7152 + image[xp + 2] * 722) // 10000
            image[xp] = image[xp + 1] = image[xp + 2] = _dithergray(c, x, y, grays)

def _dithergray(r, x, y, grays):
    if grays == 4:
        # Dither to the four VGA grays
        bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
        if r <= 128:
            r = 128 if bdither < r * 64 // 128 else 0
        elif r <= 192:
            r = 192 if bdither < (r - 128) else 128
        else:
            r = 255 if bdither < (r - 192) * 64 // 63 else 192
    if grays == -4:
        # Dither to the four canonical CGA grays
        bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
        rmod = r % 0x55
        r = (r - rmod) + 0x55 if bdither < r * 64 // 0x55 else (r - rmod)
    elif grays == 3:
        # Dither to three grays
        bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
        if r <= 128:
            r = 128 if bdither < r * 64 // 128 else 0
        else:
            r = 255 if bdither < (r - 128) * 64 // 127 else 128
    elif grays == 2:
        # Dither to black and white
        bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
        r = 255 if bdither < r * 64 // 255 else 0
    elif grays == 6:
        # Dither to the six grays in the "Web safe" palette
        bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
        rmod = r % 51
        r = (r - rmod) + 51 if bdither < r * 64 // 51 else (r - rmod)
    return r

def diaggradient(size=32):
    # Generate a portable pixelmap (PPM) of a diagonal linear gradient
    if size <= 0 or int(size) != size:
        raise ValueError
    image = []
    for y in range(size):
        row = [0 for i in range(size * 3)]
        for x in range(size):
            r = abs(x - (size - 1 - y)) * 255 // (size - 1)
            row[x * 3] = r
            row[x * 3 + 1] = r
            row[x * 3 + 2] = r
        image.append(row)
    return [px for row in image for px in row]

def colorizegrayimage(image, width, height, c0, c1):
    cr0 = c0[0] & 0xFF
    cg0 = c0[1] & 0xFF
    cb0 = c0[2] & 0xFF
    cr1 = c1[0] & 0xFF
    cg1 = c1[1] & 0xFF
    cb1 = c1[2] & 0xFF
    for y in range(height):
        yp = y * width * 3
        for x in range(width):
            xp = yp + x * 3
            if image[xp] != image[xp + 1] or image[xp] != image[xp + 2]:
                raise ValueError
            gray = image[xp]
            image[xp] = cr0 + (cr1 - cr0) * gray // 255
            image[xp + 1] = cg0 + (cg1 - cg0) * gray // 255
            image[xp + 2] = cb0 + (cb1 - cb0) * gray // 255

def noiseppm(width=64, height=64):
    # Generate a portable pixelmap (PPM) of noise
    if width <= 0 or int(width) != width:
        raise ValueError
    if height <= 0 or int(height) != height:
        raise ValueError
    rarr = [0, 255, 192, 192, 192, 192, 192, 192, 128]
    image = []
    for y in range(height):
        row = [0 for i in range(width * 3)]
        for x in range(width):
            r = rarr[random.randint(0, len(rarr) - 1)]
            row[x * 3] = r
            row[x * 3 + 1] = r
            row[x * 3 + 2] = r
        image.append(row)
    return [px for row in image for px in row]

def whitenoiseppm(width=64, height=64):
    # Generate a portable pixelmap (PPM) of noise
    if width <= 0 or int(width) != width:
        raise ValueError
    if height <= 0 or int(height) != height:
        raise ValueError
    image = []
    for y in range(height):
        row = [0 for i in range(width * 3)]
        for x in range(width):
            r = random.randint(0, 255)
            row[x * 3] = r
            row[x * 3 + 1] = r
            row[x * 3 + 2] = r
        image.append(row)
    return [px for row in image for px in row]

def _join(ls):
    ret = ""
    for i in range(len(ls)):
        if i > 0:
            ret += ","
        ret += str(ls[i])
    return ret

def brushedmetal():
    # ImageMagick command to generate a brushed metal texture from a noise image.
    # A brushed metal texture was featured in Mac OS X Panther and
    # Tiger (10.3, 10.4) and other Apple products
    # around the time of either OS's release.
    return [
        "+clone",
        "+append",
        "-morphology",
        "Convolve",
        "50x1+49+0:" + _join([1 / 50 for i in range(50)]),
        "-crop",
        "50%x0+0+0",
    ]

# What follows are methods for generating scalable vector graphics (SVGs) of
# classic OS style borders and button controls.  Although the SVGs are scalable
# by definition, they are pixelated just as they would appear in classic OSs.
#
# NOTE: A more flexible approach for this kind of drawing
# is to prepare an SVG defining the frame of a user interface element
# with five different parts (in the form of 2D shapes): an "upper outer part", a
# "lower outer part", an "upper inner part", a "lower inner part", and a "middle part".
# Each of these five parts can be colored separately or filled with a pattern.

class ImageWraparoundRectDraw:
    def __init__(self, image, width, height):
        self.image = image
        self.width = width
        self.height = height

    def rect(self, x0, y0, x1, y1, c):
        _simplebox(self.image, self.width, self.height, c, x0, y0, x1, y1)

    def __str__(self):
        pass

class SvgRectDraw:
    def __init__(self):
        self.svg = ""

    def rect(self, x0, y0, x1, y1, c):
        if x0 >= x1 or y0 >= y1:
            return ""
        self.svg += (
            "<path style='stroke:none;fill:%s' d='M%d %dL%d %dL%d %dL%d %dZ'/>"
            % (
                c,
                x0,
                y0,
                x1,
                y0,
                x1,
                y1,
                x0,
                y1,
            )
        )

    def __str__(self):
        return self.svg

# helper for edge drawing (top left edge "dominates")
# hilt = upper part of edge, dksh = lower part of edge
def _drawedgetopdom(helper, x0, y0, x1, y1, hilt, dksh=None, edgesize=1):
    if x1 - x0 < edgesize * 2 or y1 - y0 < edgesize * 2:  # too narrow and short
        _drawedgebotdom(helper, x0, y0, x1, y1, hilt, dksh, edgesize)
    else:
        helper.rect(x0, y0, x0 + edgesize, y1, hilt)  # left edge
        helper.rect(x0 + edgesize, y0, x1, y0 + edgesize, hilt)  # top edge
        helper.rect(x1 - edgesize, y0 + edgesize, x1, y1, dksh)  # right edge
        helper.rect(
            x0 + edgesize, y1 - edgesize, x1 - edgesize, y1, dksh
        )  # bottom edge

def _drawface(helper, x0, y0, x1, y1, face, edgesize=1):
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        return
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y0 + edgesize, x1, y0 - edgesize, face)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y1, face)
    else:
        helper.rect(x0 + edgesize, y0 + edgesize, x1 - edgesize, y1 - edgesize, face)

# helper for edge drawing (bottom right edge "dominates")
# hilt = upper part of edge, dksh = lower part of edge
def _drawedgebotdom(helper, x0, y0, x1, y1, hilt, dksh=None, edgesize=1):
    if hilt and (dksh is None):
        dksh = hilt
    if dksh and (hilt is None):
        hilt = dksh
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        helper.rect(x0, y0, x1, y1, dksh)
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y0, x1, y0 + edgesize, hilt)
        helper.rect(x0, y0 + edgesize, x1, y0 - edgesize, hilt)
        helper.rect(x0, y1 - edgesize, x1, y1, dksh)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0, y0, x0 + edgesize, y1, dksh)
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y1, hilt)
        helper.rect(x1 - edgesize, y0, x1, y1, dksh)
    else:
        helper.rect(x0, y0, x0 + edgesize, y1 - edgesize, hilt)  # left edge
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y0 + edgesize, hilt)  # top edge
        helper.rect(x1 - edgesize, y0, x1, y1, dksh)  # right edge
        helper.rect(x0, y1 - edgesize, x1 - edgesize, y1, dksh)  # bottom edge

# hilt = upper part of edge, dksh = lower part of edge
def _drawroundedge(helper, x0, y0, x1, y1, hilt, dksh=None, edgesize=1):
    if hilt and (dksh is None):
        dksh = hilt
    if dksh and (hilt is None):
        hilt = dksh
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        return
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y0 + edgesize, x1, y0 - edgesize, hilt)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y1, hilt)
    else:
        helper.rect(x0, y0 + edgesize, x0 + edgesize, y1 - edgesize, hilt)  # left edge
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y0 + edgesize, hilt)  # top edge
        helper.rect(
            x1 - edgesize,
            y0 + edgesize,
            x1,
            y1 - edgesize,
            hilt if dksh is None else dksh,
        )  # right edge
        helper.rect(
            x0 + edgesize,
            y1 - edgesize,
            x1 - edgesize,
            y1,
            hilt if dksh is None else dksh,
        )  # bottom edge

def _drawinnerface(helper, x0, y0, x1, y1, face):
    if face:
        edgesize = 1
        _drawface(
            helper,
            x0 + edgesize,
            y0 + edgesize,
            x1 - edgesize,
            y1 - edgesize,
            face,
            edgesize=edgesize,
        )

def drawindentborder(
    helper, x0, y0, x1, y1, hilt, sh, frame, outerBorderSize=1, innerBorderSize=1
):
    if innerBorderSize < 0:
        raise ValueError
    for i in range(outerBorderSize):
        _drawedgebotdom(helper, x0, y0, x1, y1, sh, hilt)
        x0 += 1
        y0 += 1
        x1 -= 1
        y1 -= 1
    _drawedgebotdom(helper, x0 + 1, y1 + 1, x1 - 1, y1 - 1, frame, frame)
    x0 += 1
    y0 += 1
    x1 -= 1
    y1 -= 1
    for i in range(innerBorderSize):
        _drawedgebotdom(helper, x0, y0, x1, y1, hilt, sh)
        x0 += 1
        y0 += 1
        x1 -= 1
        y1 -= 1

# highlight color, light color, shadow color, dark shadow color
def drawraisedouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    _drawedgebotdom(helper, x0, y0, x1, y1, lt, dksh)

def drawraisedinner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    _drawedgebotdom(
        helper,
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        hilt,  # draw the "upper part" with this color
        sh,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

def drawsunkenouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    return _drawedgebotdom(helper, x0, y0, x1, y1, sh, hilt)

def drawsunkeninner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    return _drawedgebotdom(
        helper,
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        dksh,  # draw the "upper part" with this color
        lt,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

# button edges (also known as "soft" edges)
def drawraisedouterbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    return _drawedgebotdom(helper, x0, y0, x1, y1, hilt, dksh)

def drawraisedinnerbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    return _drawedgebotdom(
        helper,
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        lt,  # draw the "upper part" with this color
        sh,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

def drawsunkenouterbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    return _drawedgebotdom(helper, x0, y0, x1, y1, dksh, hilt)

def drawsunkeninnerbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    return _drawedgebotdom(
        helper,
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        sh,  # draw the "upper part" with this color
        lt,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

def monoborder(  # "Monochrome" flat border
    helper,
    x0,
    y0,
    x1,
    y1,
    clientAreaColor,  # draw the inner and middle parts with this color
    windowFrameColor,  # draw the outer parts with this color
):
    drawraisedouter(  # upper and lower outer parts
        helper,
        x0,
        y0,
        x1,
        y1,
        windowFrameColor,
        windowFrameColor,
        windowFrameColor,
        windowFrameColor,
    )
    drawraisedinner(  # upper and lower inner parts
        helper,
        x0,
        y0,
        x1,
        y1,
        clientAreaColor,
        clientAreaColor,
        clientAreaColor,
        clientAreaColor,
    )
    _drawinnerface(  # middle
        helper,
        x0,
        y0,
        x1,
        y1,
        clientAreaColor,
        clientAreaColor,
        clientAreaColor,
        clientAreaColor,
    )

def flatborder(  # Flat border
    helper,
    x0,
    y0,
    x1,
    y1,
    sh,  # draw the outer parts with this color
    buttonFace,  # draw the inner and middle parts with this color
):
    drawraisedouter(helper, x0, y0, x1, y1, sh, sh, sh, sh)
    drawraisedinner(
        helper, x0, y0, x1, y1, buttonFace, buttonFace, buttonFace, buttonFace
    )
    _drawinnerface(
        helper, x0, y0, x1, y1, buttonFace, buttonFace, buttonFace, buttonFace
    )

def windowborder(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,  # highlight color
    lt,  # light color
    sh,  # shadow color
    dksh,  # dark shadow color
    face=None,  # face color
):
    face = face if face else lt
    drawraisedouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    _drawinnerface(helper, x0, y0, x1, y1, face)

def buttonup(
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    sh,
    dksh,
    face=None,
    drawFace=True,
):
    face = face if face else lt
    drawraisedouterbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinnerbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    if drawFace:
        _drawinnerface(helper, x0, y0, x1, y1, face)

def buttondown(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    sh,
    dksh,
    face=None,
    drawFace=True,
):
    face = face if face else lt
    drawsunkenouterbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawsunkeninnerbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    if drawFace:
        _drawinnerface(helper, x0, y0, x1, y1, face)

def fieldbox(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    sh,
    dksh,
    face=None,  # Usually the textbox face color if unpressed, button face if pressed
    pressed=False,
):
    face = face if face else (lt if pressed else hilt)
    drawsunkenouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawsunkeninner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    _drawinnerface(helper, x0, y0, x1, y1, face)

def wellborder(helper, x0, y0, x1, y1, hilt, windowText):
    face = face if face else (lt if pressed else hilt)
    drawsunkenouter(helper, x0, y0, x1, y1, hilt, hilt, hilt, hilt)
    drawsunkeninner(
        helper, x0, y0, x1, y1, windowText, windowText, windowText, windowText
    )
    drawsunkenouter(
        helper,
        x0 - 1,
        y0 - 1,
        x1 + 1,
        y1 + 1,
        windowText,
        windowText,
        windowText,
        windowText,
    )

def groupingbox(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    sh,
    dksh,
    face=None,
):
    face = face if face else lt
    drawsunkenouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    _drawinnerface(helper, x0, y0, x1, y1, face)

def statusfieldbox(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    sh,
    dksh,
    face=None,
):
    face = face if face else lt
    drawsunkenouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    _drawinnerface(helper, x0, y0, x1, y1, face)

def _drawrsedge(helper, x0, y0, x1, y1, lt, sh, squareFrame=False):
    if squareFrame:
        _drawedgebotdom(helper, x0, y0, x1, y1, lt, sh)
    else:
        _drawroundedge(helper, x0, y0, x1, y1, lt, sh)

def _dither(helper, face, hilt, hiltIsScrollbarColor=False):
    if hiltIsScrollbarColor:
        helper.rect(0, 0, 2, 2, hilt)
    # elif 256 or more colors and hilt is not white:
    #    helper.rect(0, 0, 2, 2, mix(face, hilt))
    else:
        helper.rect(0, 0, 1, 1, hilt)
        helper.rect(1, 1, 2, 2, hilt)
        helper.rect(0, 1, 1, 2, face)
        helper.rect(1, 0, 2, 1, face)

# Generate SVG code for an 8x8 monochrome pattern.
# 'idstr' is a string identifying the pattern in SVG.
# 'pattern' is an 8-item array with integers in the interval [0,255].
# The first integer represents the first row from the top;
# the second, the second row, etc.
# For each integer, the eight bits from most to least significant represent
# the column from left to right (right to left if 'msbfirst' is False).
# If a bit is set, the corresponding position
# in the pattern is filled with 'black'; if clear, with 'white'.
# 'black' is the black color (or pattern color), and 'white' is the white color
# (or user-selected background color).
# Either can be set to None to omit pixels of that color in the pattern
# 'msbfirst' is the bit order for each integer in 'pattern'.  If True,
# the Windows convention is used; if False, the X pixmap convention is used.
# 'originX' and 'originY' give the initial offset of the monochrome pattern, from
# the top left corner of the image.  The default for both parameters is 0.
def monopattern(
    idstr, pattern, black="black", white="white", msbfirst=True, originX=0, originY=0
):
    if pattern is None or len(pattern) < 8:
        raise ValueError
    if black is None and white is None:
        return ""
    ret = (
        "<pattern patternUnits='userSpaceOnUse' id='"
        + idstr
        + (
            "' width='8' height='8' patternTransform='translate(%d %d)'>"
            % (4 - originX, 4 - originY)
        )
    )
    bw = [white, black]
    helper = SvgRectDraw.new()
    for y in range(8):
        for x in range(8):
            c = (
                bw[(pattern[y] >> (7 - x)) & 1]
                if msbfirst
                else bw[(pattern[y] >> x) & 1]
            )
            if c is None:
                continue
            helper.rect(x, y, x + 1, y + 1, c)
    return str(helper) + "</pattern>"

def _ditherbg(idstr, face, hilt, hiltIsScrollbarColor=False):
    if hiltIsScrollbarColor:
        return hilt
    if "'" in idstr:
        raise ValueError
    if '"' in idstr:
        raise ValueError
    helper = SvgRectDraw.new()
    _dither(helper, face, hilt, hiltIsScrollbarColor)
    return (
        "<pattern patternUnits='userSpaceOnUse' id='"
        + idstr
        + "' width='2' height='2' patternTransform='translate(1 1)'>"
        + str(helper)
        + "</pattern>"
    )

def drawbuttonpush(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    sh,
    dksh,
    btn,  # button face color
    frame,
    squareFrame=True,
    isDefault=False,  # whether the button is a default button
    drawFace=True,
):
    if lt == None:
        lt = btn
    if dksh == None:
        dksh = sh
    if isDefault:
        _drawedgebotdom(helper, x0, y0, x1, y1, frame, frame)
        _drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, sh, sh)
        if drawFace:
            _drawinnerface(helper, x0 + 2, y0 + 2, x1 - 2, y1 - 2, btn)
    else:
        edge = 1 if isDefault else 0
        buttondown(
            helper,
            x0 + edge,
            y0 + edge,
            x1 - edge,
            y1 - edge,
            hilt,
            lt,
            sh,
            dksh,
            btn,
            drawFace=drawFace,
        )

def drawbutton(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    sh,
    dksh,
    btn,  # button face color
    frame,
    squareFrame=True,
    isDefault=False,  # whether the button is a default button
    drawFace=True,
):
    if lt == None:
        lt = btn
    if dksh == None:
        dksh = sh
    # If isDefault is True, no frame is drawn and no room is left for the frame
    edge = 1 if isDefault else 0
    buttonup(
        helper,
        x0 + edge,
        y0 + edge,
        x1 - edge,
        y1 - edge,
        hilt,
        lt,
        sh,
        dksh,
        btn,
        drawFace=drawFace,
    )
    if isDefault:
        _drawrsedge(helper, x0, y0, x1, y1, frame, frame, squareFrame)

# Draws a pressed button in 16-bit style
def draw16buttonpush(
    helper,
    x0,
    y0,
    x1,
    y1,
    lt,
    sh,
    btn,  # button face color
    frame=None,  # optional frame color
    squareFrame=False,
    isDefault=False,  # whether the button is a default button
    drawFace=True,
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    _drawedgetopdom(helper, x0 + edge, y0 + edge, x1 - edge, y1 - edge, sh, btn)
    if drawFace:
        helper.rect(x0 + edge + 1, y0 + edge + 1, x1 - edge - 1, y1 - edge - 1, btn)
    if frame:
        _drawrsedge(helper, x0, y0, x1, y1, frame, frame, squareFrame)
        if isDefault:
            _drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)

# Draws a button in 16-bit style
def draw16button(
    helper,
    x0,
    y0,
    x1,
    y1,
    lt,
    sh,
    btn,  # button face color
    frame=None,  # optional frame color
    squareFrame=False,
    isDefault=False,
    drawFace=True,
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    _drawedgebotdom(helper, x0 + edge, y0 + edge, x1 - edge, y1 - edge, lt, sh)
    _drawedgebotdom(
        helper, x0 + edge + 1, y0 + edge + 1, x1 - edge - 1, y1 - edge - 1, lt, sh
    )
    if drawFace:
        helper.rect(x0 + edge + 2, y0 + edge + 2, x1 - edge - 2, y1 - edge - 2, btn)
    if frame:
        _drawrsedge(helper, x0, y0, x1, y1, frame, frame, squareFrame)
        if isDefault:
            _drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)

def makesvg():
    image = _blankimage(64, 64)
    helper = ImageWraparoundRectDraw(image, 64, 64)
    draw16button(
        helper,
        0,
        32,
        64,
        64,
        [255, 255, 255],
        [128, 128, 128],
        [192, 192, 192],
        [0, 0, 0],
        squareFrame=True,
        drawFace=True,
    )
    draw16button(
        helper,
        32,
        0,
        96,
        32,
        [255, 255, 255],
        [128, 128, 128],
        [192, 192, 192],
        [0, 0, 0],
        squareFrame=True,
        drawFace=True,
    )

# random wallpaper generation

def randomhatchimage(palette=None):
    # Generates a random hatch image using the given palette
    # (default is the palette in classiccolors2)
    pal = palette if palette else classiccolors2()
    if random.randint(0, 99) < 50:
        w = random.randint(40, 96)
        w -= w % 2  # make even
        image = diagcrosshatch(
            w,
            random.randint(0, 16),
            random.randint(0, 16),
            bgcolor=random.choice(pal),
            fgcolor=random.choice(pal),
        )
        return {"image": image, "width": w, "height": w}
    else:
        hhatch = random.randint(0, 7)
        vhatch = random.randint(0, 7)
        return crosshatch(
            hhatch + random.randint(4, 32),
            vhatch + random.randint(4, 32),
            hhatch,
            vhatch,
            bgcolor=random.choice(pal),
            fgcolor=random.choice(pal),
        )

def randomboxesimage(palette=None):
    # Generates a random boxes image using the given palette
    # (default is the palette in classiccolors2)
    pal = palette if palette else classiccolors2()
    w = random.randint(180, 320)
    w -= w % 2  # make even
    h = random.randint(140, 240)
    h -= h % 2  # make even
    image = randomboxes(w, h, pal)
    return {"image": image, "width": w, "height": h}

def randomcheckimage(palette=None):
    # Generates a random checkerboard pattern image using the given palette
    # (default is the palette in classiccolors2)
    pal = palette if palette else classiccolors2()
    w = random.randint(16, 128)
    w -= w % 2  # make even
    h = random.randint(16, 128)
    h -= h % 2  # make even
    hatch = None if random.randint(0, 1) == 0 else random.choice(pal)
    image = checkerboardimage(w, h, random.choice(pal), random.choice(pal), hatch)
    return {"image": image, "width": w, "height": h}

# palette generation

def _writeu16(ff, x):
    ff.write(bytes([(x >> 8) & 0xFF, (x) & 0xFF]))

def _writeu32(ff, x):
    ff.write(bytes([(x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, (x) & 0xFF]))

def _writef32(ff, x):
    ff.write(struct.pack(">f", x))

def _utf16len(strval):
    b = bytes(strval, "utf-16be")
    if len(b) % 2 == 1:
        raise ValueError
    return 4 + len(b)

def _writeutf16(ff, strval):
    b = bytes(strval, "utf-16be")
    if len(b) % 2 == 1:
        raise ValueError
    _writeu16(ff, len(b) // 2 + 1)
    ff.write(b)
    _writeu16(ff, 0)

def _setup_rgba_to_colorname_hash():
    ncs = (
        "aliceblue,f0f8ff,antiquewhite,faebd7,aqua,00ffff,aquamarine,7fffd4,azure,f0ffff,beige,f5f5dc,bisque,ffe4c4,black,000000,blanchedalmond,ffebcd,blue,0000ff,"
        + "blueviolet,8a2be2,brown,a52a2a,burlywood,deb887,cadetblue,5f9ea0,chartreuse,7fff00,chocolate,d2691e,coral,ff7f50,cornflowerblue,6495ed,cornsilk,fff8dc,"
        + "crimson,dc143c,cyan,00ffff,darkblue,00008b,darkcyan,008b8b,darkgoldenrod,b8860b,darkgray,a9a9a9,darkgreen,006400,darkkhaki,bdb76b,darkmagenta,8b008b,"
        + "darkolivegreen,556b2f,darkorange,ff8c00,darkorchid,9932cc,darkred,8b0000,darksalmon,e9967a,darkseagreen,8fbc8f,darkslateblue,483d8b,darkslategray,2f4f4f,"
        + "darkturquoise,00ced1,darkviolet,9400d3,deeppink,ff1493,deepskyblue,00bfff,dimgray,696969,dodgerblue,1e90ff,firebrick,b22222,floralwhite,fffaf0,forestgreen,"
        + "228b22,fuchsia,ff00ff,gainsboro,dcdcdc,ghostwhite,f8f8ff,gold,ffd700,goldenrod,daa520,gray,808080,green,008000,greenyellow,adff2f,honeydew,f0fff0,hotpink,"
        + "ff69b4,indianred,cd5c5c,indigo,4b0082,ivory,fffff0,khaki,f0e68c,lavender,e6e6fa,lavenderblush,fff0f5,lawngreen,7cfc00,lemonchiffon,fffacd,lightblue,add8e6,"
        + "lightcoral,f08080,lightcyan,e0ffff,lightgoldenrodyellow,fafad2,lightgray,d3d3d3,lightgreen,90ee90,lightpink,ffb6c1,lightsalmon,ffa07a,lightseagreen,20b2aa,"
        + "lightskyblue,87cefa,lightslategray,778899,lightsteelblue,b0c4de,lightyellow,ffffe0,lime,00ff00,limegreen,32cd32,linen,faf0e6,magenta,ff00ff,maroon,800000,"
        + "mediumaquamarine,66cdaa,mediumblue,0000cd,mediumorchid,ba55d3,mediumpurple,9370d8,mediumseagreen,3cb371,mediumslateblue,7b68ee,mediumspringgreen,"
        + "00fa9a,mediumturquoise,48d1cc,mediumvioletred,c71585,midnightblue,191970,mintcream,f5fffa,mistyrose,ffe4e1,moccasin,ffe4b5,navajowhite,ffdead,navy,"
        + "000080,oldlace,fdf5e6,olive,808000,olivedrab,6b8e23,orange,ffa500,orangered,ff4500,orchid,da70d6,palegoldenrod,eee8aa,palegreen,98fb98,paleturquoise,"
        + "afeeee,palevioletred,d87093,papayawhip,ffefd5,peachpuff,ffdab9,peru,cd853f,pink,ffc0cb,plum,dda0dd,powderblue,b0e0e6,purple,800080,rebeccapurple,663399,red,ff0000,rosybrown,"
        + "bc8f8f,royalblue,4169e1,saddlebrown,8b4513,salmon,fa8072,sandybrown,f4a460,seagreen,2e8b57,seashell,fff5ee,sienna,a0522d,silver,c0c0c0,skyblue,87ceeb,"
        + "slateblue,6a5acd,slategray,708090,snow,fffafa,springgreen,00ff7f,steelblue,4682b4,tan,d2b48c,teal,008080,thistle,d8bfd8,tomato,ff6347,turquoise,40e0d0,violet,"
        + "ee82ee,wheat,f5deb3,white,ffffff,whitesmoke,f5f5f5,yellow,ffff00,yellowgreen,9acd32"
    )
    nc = ncs.split(",")
    __color_to_rgba_namedColors = {}
    i = 0
    while i < len(nc):
        __color_to_rgba_namedColors["#" + nc[i + 1]] = nc[i]
        i += 2
    return __color_to_rgba_namedColors

_rgba_to_colorname_hash = _setup_rgba_to_colorname_hash()

def _colorname(c):
    cname = "#%02x%02x%02x" % (c[0], c[1], c[2])
    if cname in _rgba_to_colorname_hash:
        return _rgba_to_colorname_hash[cname] + " " + cname
    return cname

def writepalette(f, palette, name=None, checkIfExists=False):
    if "\n" in name:
        raise ValueError
    if (not palette) or len(palette) > 512:
        raise ValueError
    # GIMP palette
    ff = open(f + ".gpl", "xb" if checkIfExists else "wb")
    ff.write(bytes("GIMP Palette\n", "utf-8"))
    if name:
        ff.write(bytes("# Name: %s\n" % (name), "utf-8"))
    ff.write(bytes("# Colors: %d\n" % (len(palette)), "utf-8"))
    for c in palette:
        ff.write(
            bytes(
                "%d %d %d %s\n" % (c[0], c[1], c[2], _colorname(c)),
                "utf-8",
            )
        )
    ff.close()
    # Adobe color swatch format
    ff = open(f + ".aco", "xb" if checkIfExists else "wb")
    _writeu16(ff, 1)
    _writeu16(ff, len(palette))
    for i in range(len(palette)):
        c = palette[i]
        _writeu16(ff, 0)
        _writeu16(ff, c[0] * 0xFFFF // 255)
        _writeu16(ff, c[1] * 0xFFFF // 255)
        _writeu16(ff, c[2] * 0xFFFF // 255)
        _writeu16(ff, 0)
    _writeu16(ff, 2)
    _writeu16(ff, len(palette))
    for c in palette:
        _writeu16(ff, 0)
        _writeu16(ff, c[0] * 0xFFFF // 255)
        _writeu16(ff, c[1] * 0xFFFF // 255)
        _writeu16(ff, c[2] * 0xFFFF // 255)
        _writeu16(ff, 0)
        _writeu16(ff, 0)
        _writeutf16(ff, _colorname(c))
    ff.close()
    # Adobe swatch exchange format
    ff = open(f + ".ase", "xb" if checkIfExists else "wb")
    ff.write(bytes("ASEF", "utf-8"))
    _writeu16(ff, 1)
    _writeu16(ff, 0)
    _writeu32(ff, len(palette) + 1)
    for i in range(len(palette)):
        c = palette[i]
        _writeu16(ff, 1)
        colorname = _colorname(c)
        _writeu32(ff, _utf16len(colorname) + 18)
        _writeutf16(ff, colorname)
        ff.write(bytes("RGB ", "utf-8"))
        _writef32(ff, c[0] / 255.0)
        _writef32(ff, c[1] / 255.0)
        _writef32(ff, c[2] / 255.0)
        _writeu16(ff, 0)

if __name__ == "__main__":
    try:
        os.mkdir("palettes")
    except FileExistsError:
        pass
    writepalette("palettes/2color", [[0, 0, 0], [255, 255, 255]], "Two Colors")
    writepalette(
        "palettes/3gray", [[0, 0, 0], [128, 128, 128], [255, 255, 255]], "Three Grays"
    )
    writepalette(
        "palettes/4gray",
        [[0, 0, 0], [128, 128, 128], [192, 192, 192], [255, 255, 255]],
        "Four Grays",
    )
    writepalette(
        "palettes/6gray", [[x * 51, x * 51, x * 51] for x in range(6)], "Six Grays"
    )
    writepalette(
        "palettes/16gray",
        [[x * 0x11, x * 0x11, x * 0x11] for x in range(16)],
        "16 Grays",
    )
    writepalette(
        "palettes/64gray",
        [[x * 255 // 63, x * 255 // 63, x * 255 // 63] for x in range(64)],
        "64 Grays",
    )
    writepalette("palettes/256gray", [[x, x, x] for x in range(256)], "256 Grays")
    writepalette(
        "palettes/cga-canonical", cgacolors(), "Canonical 16-Color CGA Palette"
    )
    writepalette(
        "palettes/cga-with-halfmixtures",
        paletteandhalfhalf(cgacolors()),
        "Canonical CGA Palette with Half-and-Half Mixtures",
    )
    writepalette("palettes/vga", classiccolors(), "VGA (Windows) 16-Color Palette")
    writepalette("palettes/16color", classiccolors(), "VGA (Windows) 16-Color Palette")
    writepalette("palettes/ega", egacolors(), "Colors Displayable by EGA Monitors")
    writepalette("palettes/websafe", websafecolors(), '"Web Safe" Colors')
    writepalette(
        "palettes/websafe-and-vga",
        websafecolors()
        + [
            [128, 128, 128],
            [192, 192, 192],
            [128, 0, 0],
            [0, 128, 0],
            [0, 0, 128],
            [128, 0, 128],
            [0, 128, 128],
            [128, 128, 0],
        ],
        '"Web Safe" and VGA Colors',
    )
    writepalette(
        "palettes/windows-20",
        classiccolors()
        + [[192, 220, 192], [160, 160, 164], [255, 251, 240], [166, 202, 240]],
        "Windows 20-Color Palette",
    )
    writepalette(
        "palettes/vga-with-halfmixtures",
        paletteandhalfhalf(classiccolors()),
        "VGA Palette with Half-and-Half Mixtures",
    )
