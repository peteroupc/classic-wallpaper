# This Python script helps generate interesting variations on desktop
# wallpapers based on existing image files.  Because they run on the CPU
# and are implemented in pure Python, the methods are intended for
# relatively small images that are suitable as tileable desktop wallpaper
# patterns, especially with dimensions 256x256 or smaller.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under the Unlicense: https://unlicense.org/
#
# NOTES:
#
# 1. Animation of tilings composed from a wallpaper image can be implemented by
# shifting, with each frame, the starting position for drawing the top left
# corner of the wallpaper tiling (e.g., from the top left corner of the image
# to some other position in the image).
# 2. In Windows, if both an 8x8 monochrome pattern and a centered wallpaper
# are set as the desktop background, both the pattern and the wallpaper
# will be drawn on the desktop, the latter appearing above the former.
# The nonblack areas of the monochrome pattern are filled with the desktop
# color.
# 3. I would welcome it if readers could contribute computer code (released
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
import zlib

def _listdir(p):
    return [os.path.abspath(p + "/" + x) for x in os.listdir(p)]

DitherMatrix4x4 = [  # Bayer 4x4 ordered dither matrix
    0,
    8,
    2,
    10,
    12,
    4,
    14,
    6,
    3,
    11,
    1,
    9,
    15,
    7,
    13,
    5,
]

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
    if width <= 0 or height <= 0 or not palette:
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

def solidfill(bg=[192, 192, 192]):
    if bg == None or len(bg) < 3:
        raise ValueError
    bc = "#%02x%02x%02x" % (int(bg[0]), int(bg[1]), int(bg[2]))
    return ["-size", "%wx%h", "xc:" + bc, "-delete", "-2"]

def solid(bg=[192, 192, 192]):
    if bg == None or len(bg) < 3:
        raise ValueError
    bc = "#%02x%02x%02x" % (int(bg[0]), int(bg[1]), int(bg[2]))
    # Fred Weinhaus suggested the following to me, which avoids
    # having to know the input image size in advance:
    # https://github.com/ImageMagick/ImageMagick/discussions/7423
    # return ["(", "+clone", "-fill", "xc:" + bc, "-colorize", "100", ")"]
    # another solution that works better with alpha channel images
    return ["(", "+clone", "-size", "%wx%h", "xc:" + bc, "-delete", "-2", ")"]

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
        " -grayscale Rec709Luma -channel RGB -threshold 51%% +channel -write mpr:z "
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

def shiftwrap(xOrigin, yOrigin):
    return [
        "(",
        "+clone",
        ")",
        "-append",
        "(",
        "+clone",
        ")",
        "+append",
        "-crop",
        "50%%x50%%%s%d%s%d"
        % ("+" if xOrigin >= 0 else "", xOrigin, "+" if yOrigin >= 0 else "", yOrigin),
    ]

def unavailable(
    bgColor=None, buttonShadow=None, buttonHighlight=None, drawShiftedImageOver=False
):
    # Emboss an input image described in 'versatilePattern' for an unavailable appearance
    if not bgColor:
        bgColor = [192, 192, 192]
    if not buttonShadow:
        buttonShadow = [128, 128, 128]
    if not buttonHighlight:
        buttonHighlight = [255, 255, 255]
    mpre = "mpr:emboss"
    return (
        ["-grayscale", "Rec709Luma", "-write", mpre, "-delete", "0", "(", mpre]
        + versatilePattern(buttonHighlight, None)
        + [")", "(", mpre]
        + versatilePattern(buttonShadow, None)
        + shiftwrap(1, 1)
        + [
            ")",
            "-alpha",
            "on",
            "-compose",
            "DstOver" if drawShiftedImageOver else "Over",
            "-composite",
        ]
        + backgroundColorUnder(bgColor)
    )

def emboss(bgColor=None, fgColor=None, hiltColor=None):
    # Emboss an input image described in 'versatilePattern' into a 3-color (black/gray/white) image
    return unavailable(
        bgColor if bgColor else [128, 128, 128],
        hiltColor if hiltColor else [255, 255, 255],
        fgColor if fgColor else [0, 0, 0],
        True,
    )

def versatileForeground(foregroundImage):
    return [
        "-negate",
        "-write",
        "mpr:vfg",
        "-delete",
        "-1",
        "tile:" + foregroundImage,
        "mpr:vfg",
        "-alpha",
        "Off",
        "-compose",
        "copyopacity",
        "-composite",
    ]

def versatilePattern(fgcolor, bgcolor=None):
    # ImageMagick command for setting a foreground pattern, whose black parts
    # are set in the given foreground color, on a background that can optionally
    # be colored.
    # 'fgcolor' and 'bgcolor' are the foreground and background color, respectively.
    # The input image this command will be applied to is assumed to be an SVG file
    # which must be black in the nontransparent areas (given that ImageMagick renders the
    # SVG on a white background by default) or a raster image with only
    # gray tones, where the blacker, the less transparent.
    # 'bgcolor' can be None so that an alpha
    # background is used.  Each color is a
    # 3-item array of the red, green, and blue components in that order; e.g.,
    # [2,10,255] where each component is from 0 through 255.
    # Inspired by the technique for generating backgrounds in heropatterns.com.
    return [
        "-negate",
        "-background",
        "#%02x%02x%02x" % (int(fgcolor[0]), int(fgcolor[1]), int(fgcolor[2])),
        "-alpha",
        "shape",
    ] + backgroundColorUnder(bgcolor)

def lightmodePattern():
    return versatilePattern([192, 192, 192], [255, 255, 255])

def darkmodePattern():
    return versatilePattern([128, 128, 128], [0, 0, 0])

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
        [
            "(",
            "+clone",
            "-flip",
            ")",
            "-append",
            "-write",
            "mpr:wpgroup",
            "-delete",
            "0",
            "(",
            "mpr:wpgroup",
            "(",
            "mpr:wpgroup",
            "-flop",
        ]
        + _chopBeforeHAppendArray()
        + [
            ")",
            "+append",
            ")",
            "(",
            "(",
            "mpr:wpgroup",
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

def backgroundColorUnder(bgcolor=None):
    # 'bgcolor' is the background color,
    # either None or a 3-item array of the red,
    # green, and blue components in that order; e.g., [2,10,255] where each
    # component is from 0 through 255; default is None, or no background color.
    return (
        solid(bgcolor)
        + [
            "-compose",
            "DstOver",
            "-composite",
        ]
        if bgcolor
        else []
    )

def diamondTiling():
    # ImageMagick command to generate a diamond tiling pattern (or a brick tiling
    # pattern if the image the command is applied to has only its top half
    # or its bottom half drawn).  For best results, the command should be applied
    # to images with an even width and height.
    ret = [
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
        "-chop",
        "25%x25%",
        ")",
        "-compose",
        "Over",
        "-composite",
    ]
    return ret

def _bottomPadding():
    return [
        "-background",
        "transparent",
        "+repage",
        "-gravity",
        "SouthEast",
        "-splice",
        "0x%h",
        "+gravity",
        "+repage",
    ]

def _rightPadding():
    return [
        "-background",
        "transparent",
        "+repage",
        "-gravity",
        "NorthEast",
        "-splice",
        "%wx0",
        "+gravity",
        "+repage",
    ]

def diamondTiledSize(width, height, kind):
    if kind == 1:
        return (width, height * 2)
    if kind == 2:
        return (width * 2, height)
    return (width + (width // 2) * 2, height + (height // 2) * 2)

def diamondTiled(bgcolor=None, kind=0):
    # kind=0: image drawn in middle and padded
    # kind=1: brick drawn at top
    # kind=2: brick drawn at left
    return (
        (
            _bottomPadding()
            if kind == 1
            else (
                _rightPadding()
                if kind == 2
                else [
                    "+repage",
                    "-bordercolor",
                    "transparent",
                    # Don't allow whatever '-compose'
                    # setting there is to leak into
                    # the '-border' option
                    "-compose",
                    "Over",
                    "-border",
                    "50%x50%",
                    "-bordercolor",
                    "white",
                ]
            )
        )
        + diamondTiling()
        + backgroundColorUnder(bgcolor)
    )

def groupPmg():
    # ImageMagick command to generate a Pmg wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last column's first half is a mirror of its
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
            ")",
            "(",
            "(",
            "mpr:wpgroup",
            "-flip",
            ")",
            "(",
            "mpr:wpgroup",
            "-flop",
        ]
        + _chopBeforeHAppendArray()
        + [")", "+append"]
        + _chopBeforeVAppendArray()
        + [")", "-append"]
    )

def brushedmetal():
    # ImageMagick command to generate a brushed metal texture from a noise image.
    # A brushed metal texture was featured in Mac OS X Panther and
    # Tiger (10.3, 10.4) and other Apple products
    # around the time of either OS's release.
    return [
        "(",
        "+clone",
        ")",
        "+append",
        "-morphology",
        "Convolve",
        "50x1+49+0:" + (",".join([str(1 / 50) for i in range(50)])),
        "+repage",
        "-crop",
        "50%x0+0+0",
        "+repage",
    ]

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

def writeavi(f, images, width, height, raiseIfExists=False):
    if not images:
        raise ValueError
    if width < 0 or height < 0 or width > 0x7FFF or height > 0x7FFF:
        raise ValueError
    for image in images:
        if not image:
            raise ValueError
        if len(image) != width * height * 3:
            raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    fps = 20
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
    uniquecolors = {}
    colortable = [0 for i in range(1024)]
    numuniques = 0
    for image in images:
        pos = 0
        for y in range(height * width):
            c = image[pos] | (image[pos + 1] << 8) | (image[pos + 2] << 16)
            if c not in uniquecolors:
                uniquecolors[c] = numuniques
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
    dowriteavi = len(images) > 1
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
    support2color = (compressionMode == 0) and (
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
    if bpp <= 8:
        bitmapinfo += bytes([colortable[i] for i in range(numuniques * 4)])
    fd = open(f, "xb" if raiseIfExists else "wb")
    if compressionMode == 0 and not dowriteavi:
        bmsize = 14 + len(bitmapinfo) + sizeImage
        bmoffset = 14 + len(bitmapinfo)
        chunk = b"BM" + struct.pack("<LhhL", bmsize, 0, 0, bmoffset)
        fd.write(chunk)
        fd.write(bitmapinfo)
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
                        scan[x] |= uniquecolors[
                            image[pp] | (image[pp + 1] << 8) | (image[pp + 2] << 16)
                        ] << (7 - i)
                if width % 8 != 0:
                    x = width // 8
                    for i in range(width % 8):
                        pp = pos + x * 24 + i * 3
                        scan[x] |= uniquecolors[
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
                        uniquecolors[
                            image[pos + x * 6]
                            | (image[pos + x * 6 + 1] << 8)
                            | (image[pos + x * 6 + 2] << 16)
                        ]
                        << 4
                    ) | (
                        uniquecolors[
                            image[pos + x * 6 + 3]
                            | (image[pos + x * 6 + 4] << 8)
                            | (image[pos + x * 6 + 5] << 16)
                        ]
                    )
                if width % 2 != 0:
                    x = width // 2
                    scan[x] = (
                        uniquecolors[
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
                        uniquecolors[
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
        bitmapinfo = b"strf" + struct.pack("<L", len(bitmapinfo)) + bitmapinfo
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
        bmsize = 14 + len(bitmapinfo) + sum(len(img) for img in imagedatas)
        bmoffset = 14 + len(bitmapinfo)
        chunk = b"BM" + struct.pack("<LhhL", bmsize, 0, 0, bmoffset)
        fd.write(chunk)
        fd.write(bitmapinfo)
        for img in imagedatas:
            fd.write(img)
    fd.close()

def writebmp(f, image, width, height, raiseIfExists=False):
    return writeavi(f, [image], width, height, raiseIfExists=raiseIfExists)

def simplebox(image, width, height, color, x0, y0, x1, y1, wraparound=True):
    borderedbox(
        image, width, height, None, color, color, x0, y0, x1, y1, wraparound=wraparound
    )

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
    wraparound=True,
):
    # Draw a wraparound hatched box on an image.
    # 'color' is the color of the hatch, drawn on every "black" pixel
    # in the pattern's tiling.
    # 'pattern' is an 8-item array with integers in the interval [0,255].
    # The first integer represents the first row from the top;
    # the second, the second row, etc.
    # For each integer, the eight bits from most to least significant represent
    # the column from left to right (right to left if 'msbfirst' is False).
    # If a bit is set, the corresponding position
    # in the pattern is a "black" pixel; if clear, a "white" pixel.
    # Either can be set to None to omit pixels of that color in the pattern
    # 'msbfirst' is the bit order for each integer in 'pattern'.  If True,
    # the Windows convention is used; if False, the X pixmap convention is used.
    # Default is True.
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
    if not wraparound:
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, width)
        y1 = min(y1, height)
        if x0 >= x1 or y0 >= y1:
            return
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

def _applyrop(a, b, rop):
    # apply a binary raster operation
    if rop == 12:
        return b
    elif rop == 10:
        return a
    elif rop == 0:
        return 0
    elif rop == 1:
        return (a | b) ^ 0xFF
    elif rop == 2:
        return a & (b ^ 0xFF)
    elif rop == 3:
        return b ^ 0xFF
    elif rop == 4:
        return b & (a ^ 0xFF)
    elif rop == 5:
        return a ^ 0xFF
    elif rop == 6:
        return a ^ b
    elif rop == 7:
        return (a & b) ^ 0xFF
    elif rop == 8:
        return a & b
    elif rop == 9:
        return (a ^ b) ^ 0xFF
    elif rop == 11:
        return (b & (a ^ 0xFF)) ^ 0xFF
    elif rop == 13:
        return (a & (b ^ 0xFF)) ^ 0xFF
    elif rop == 14:
        return a | b
    elif rop == 15:
        return 0xFF
    return 0

def imageblitex(
    dstimage,
    dstwidth,
    dstheight,
    x0,
    y0,
    x1,
    y1,
    srcimage,
    srcwidth,
    srcheight,
    x0src=0,
    y0src=0,
    patternimage=None,
    patternwidth=0,
    patternheight=0,
    patternOrgX=0,
    patternOrgY=0,
    maskimage=None,
    maskwidth=0,
    maskheight=0,
    x0mask=0,
    y0mask=0,
    ropForeground=0xCC,
    ropBackground=0xAA,
    wraparound=True,
):
    # Draw a wraparound copy of an image on another image.
    # 'dstimage' and 'srcimage' are the destination and source images.
    # 'pattern' is a brush pattern image.
    # 'srcimage', 'maskimage', and 'patternimage' are optional.
    # All images are flat arrays with the same format returned by the blankimage
    # function.  Thus none of them can include transparency in whole or in part.
    # (Windows's graphical device interface [GDI] supports transparent
    # parts in brush patterns only for brushes
    # with predefined hatch patterns, and then only if the background mode is
    # transparent and only in the gaps between hatch marks.)
    # 'patternOrgX' and 'patternOrgY' are offsets from the destination's top left
    # corner where the top left corner of the brush pattern image would
    # be drawn if a repetition of the brush pattern were to be drawn across the
    # whole destination image.  The default for both parameters is 0.
    # 'x0src' and 'y0src' are offsets from the destination image's top left corner
    # where the source image's top left corner will be drawn.
    # 'x0mask' and 'y0mask' are offsets from the source image's top left corner
    # and correspond to pixels in the source image.
    # 'ropForeground' is a foreground ternary raster operation between the bits of the
    # destination and those of the source; the low 4 bits is the binary raster
    # operation used where the pattern bit is 0; the high 4 bits, where the pattern
    # bit is 1. 'ropForeground' is used where the mask bit is 1 or there is no mask
    # or an empty mask. 'ropBackground' is the same as 'ropForeground', but for the
    # background (used where the mask bit is 0 rather than 1).
    # 'maskimage' is ideally a monochrome image (every pixel is either all zeros
    # (black) or all ones (white), but it doesn't have to be.
    if ropForeground < 0 or ropForeground >= 256:
        raise ValueError
    if ropBackground < 0 or ropBackground >= 256:
        raise ValueError
    if ropForeground == ropBackground or maskwidth == 0 or maskheight == 0:
        maskimage = None
    if (
        (
            ((ropForeground >> 4) & 15) == ((ropForeground) & 15)
            and ((ropBackground >> 4) & 15) == ((ropBackground) & 15)
        )
        or patternwidth == 0
        or patternheight == 0
    ):
        patternimage = None
    if maskimage != None and (maskwidth < 0 or maskheight < 0):
        raise ValueError
    if patternimage != None and (patternwidth < 0 or patternheight < 0):
        raise ValueError
    if dstimage == None or dstwidth < 0 or dstheight < 0:
        raise ValueError
    if x0 > x1 or y0 > y1:
        raise ValueError
    x1src = x0src + (x1 - x0)
    y1src = y0src + (y1 - y0)
    x1mask = x0mask + (x1 - x0)
    y1mask = y0mask + (y1 - y0)
    if maskimage and (
        x0mask < 0
        or x0mask > maskwidth
        or y0mask < 0
        or y0mask > maskheight
        or x1mask < 0
        or x1mask > maskwidth
        or y1mask < 0
        or y1mask > maskheight
    ):
        raise ValueError
    if srcimage and (
        x0src < 0
        or x0src > srcwidth
        or y0src < 0
        or y0src > srcheight
        or x1src < 0
        or x1src > srcwidth
        or y1src < 0
        or y1src > srcheight
    ):
        raise ValueError
    if not maskimage:
        ropBackground = ropForeground
    if ropForeground == 0xAA and ropBackground == 0xAA:
        return
    for y in range(y1 - y0):
        dy = y0 + y
        if wraparound:
            dy %= dstheight
        if (not wraparound) and dy < 0 or dy >= dstheight:
            continue
        dy = dy * dstwidth * 3
        sy = (y0src + y) * srcwidth * 3 if srcimage else 0
        paty = (
            ((dy - patternOrgY) % patternheight) * patternwidth * 3
            if patternimage
            else 0
        )
        masky = (y0mask + y) * maskwidth * 3 if maskimage else 0
        for x in range(x1 - x0):
            dx = x0 + x
            if wraparound:
                dx %= dstwidth
            if (not wraparound) and dx < 0 or dx >= dstwidth:
                continue
            dstpos = dy + dx * 3
            srcpos = sy + x * 3
            patpos = (
                paty + ((dx - patternOrgX) % patternwidth) * 3 if patternimage else 0
            )
            maskpos = masky + (x0mask + y) * 3 if maskimage else 0
            for i in range(3):
                s1 = srcimage[srcpos + i] if srcimage else 0
                d1 = dstimage[dstpos + i] if dstimage else 0
                p1 = patternimage[patpos + i] if patternimage else 0
                m1 = maskimage[maskpos + i] if maskimage else 0
                sdl = _applyrop(d1, s1, ropForeground & 0xF)
                sdh = _applyrop(d1, s1, (ropForeground >> 8) & 0xF)
                sdp = (p1 & sdh) ^ ((~p1) & sdl)
                if maskimage:
                    sdl = _applyrop(d1, s1, ropBackground & 0xF)
                    sdh = _applyrop(d1, s1, (ropBackground >> 8) & 0xF)
                    sdpb = (p1 & sdh) ^ ((~p1) & sdl)
                    sdp = (m1 & sdp) ^ ((~m1) & sdpb)
                dstimage[dstpos + i] = sdp

def imagetransblit(
    dstimage,
    dstwidth,
    dstheight,
    x0,
    y0,
    x1,
    y1,
    srcimage,
    srcwidth,
    srcheight,
    x0src=0,
    y0src=0,
    transcolor=None,
    patternimage=None,
    patternwidth=0,
    patternheight=0,
    patternOrgX=0,
    patternOrgY=0,
    ropForeground=0xCC,
    ropBackground=0xAA,
    wraparound=True,
):
    # 'ropForeground' and 'ropBackground' are as in imageblitex, except that
    # 'ropForeground' is used where the source color is not 'transcolor' or if
    # 'transcolor' is None; 'ropBackground' is used elsewhere.
    if transcolor == None:
        imageblitex(
            dstimage,
            dstwidth,
            dstheight,
            x0,
            y0,
            x1,
            y1,
            srcimage,
            srcwidth,
            srcheight,
            x0src,
            y0src,
            patternimage,
            patternwidth,
            patternheight,
            patternOrgX=patternOrgX,
            patternOrgY=patternOrgY,
            ropForeground=ropForeground,
            ropBackground=ropBackground,
            wraparound=wraparound,
        )
    if ropForeground < 0 or ropForeground >= 256:
        raise ValueError
    if ropBackground < 0 or ropBackground >= 256:
        raise ValueError
    if len(transcolor) < 3:
        raise ValueError
    if ropForeground == ropBackground:
        maskimage = None
    if (
        (
            ((ropForeground >> 4) & 15) == ((ropForeground) & 15)
            and ((ropBackground >> 4) & 15) == ((ropBackground) & 15)
        )
        or patternwidth == 0
        or patternheight == 0
    ):
        patternimage = None
    if patternimage != None and (patternwidth < 0 or patternheight < 0):
        raise ValueError
    if dstimage == None or dstwidth < 0 or dstheight < 0:
        raise ValueError
    if x0 > x1 or y0 > y1:
        raise ValueError
    x1src = x0src + (x1 - x0)
    y1src = y0src + (y1 - y0)
    if srcimage and (
        x0src < 0
        or x0src > srcwidth
        or y0src < 0
        or y0src > srcheight
        or x1src < 0
        or x1src > srcwidth
        or y1src < 0
        or y1src > srcheight
    ):
        raise ValueError
    if ropForeground == 0xAA and ropBackground == 0xAA:
        return
    for y in range(y1 - y0):
        dy = y0 + y
        if wraparound:
            dy %= dstheight
        if (not wraparound) and dy < 0 or dy >= dstheight:
            continue
        dy = dy * dstwidth * 3
        sy = (y0src + y) * srcwidth * 3
        paty = ((dy + patternOrgY) % patternheight) * 3 if patternimage else 0
        for x in range(x1 - x0):
            dx = x0 + x
            if wraparound:
                dx %= dstwidth
            if (not wraparound) and dx < 0 or dx >= dstwidth:
                continue
            dstpos = dy + dx * 3
            srcpos = sy + x * 3
            patpos = (
                paty + ((dx + patternOrgX) % patternwidth) * 3 if patternimage else 0
            )
            m1 = (
                0x00
                if (
                    srcimage[srcpos] == transcolor[0]
                    and srcimage[srcpos + 1] == transcolor[1]
                    and srcimage[srcpos + 2] == transcolor[2]
                )
                else 0xFF
            )
            for i in range(3):
                s1 = srcimage[srcpos + i] if srcimage else 0
                d1 = dstimage[dstpos + i] if dstimage else 0
                p1 = patternimage[patpos + i] if patternimage else 0
                sdl = _applyrop(d1, s1, ropForeground & 0xF)
                sdh = _applyrop(d1, s1, (ropForeground >> 8) & 0xF)
                sdp = (p1 & sdh) ^ ((~p1) & sdl)
                sdl = _applyrop(d1, s1, ropBackground & 0xF)
                sdh = _applyrop(d1, s1, (ropBackground >> 8) & 0xF)
                sdpb = (p1 & sdh) ^ ((~p1) & sdl)
                sdp = (m1 & sdp) ^ ((~m1) & sdpb)
                dstimage[dstpos + i] = sdp

def imageblit(
    dstimage,
    dstwidth,
    dstheight,
    srcimage,
    srcwidth,
    srcheight,
    x0,
    y0,
    wraparound=True,
    rasterOp=12,
):
    # 'rasterOp' is a binary raster operation between the bits of the
    # destination and those of the source.
    if rasterOp < 0 or rasterOp >= 16:
        raise ValueError
    return imageblitex(
        dstimage,
        dstwidth,
        dstheight,
        x0,
        y0,
        x0 + srcwidth,
        y0 + srcheight,
        srcimage,
        srcwidth,
        srcheight,
        0,
        0,
        wraparound=wraparound,
        ropForeground=rasterOp | (rasterOp << 4),
    )

def tiledImage(srcimage, srcwidth, srcheight, dstwidth, dstheight):
    if srcwidth < 0 or srcheight < 0 or dstwidth < 0 or dstheight < 0:
        raise ValueError
    image = blankimage(dstwidth, dstheight)
    if dstheight <= 0 or dstwidth <= 0 or srcwidth <= 0 or srcheight <= 0:
        return image
    columns = -((-dstwidth) // srcwidth)  # ceiling trick
    rows = -((-dstheight) // srcheight)
    for y in range(rows):
        for x in range(columns):
            imageblit(
                image,
                dstwidth,
                dstheight,
                srcimage,
                srcwidth,
                srcheight,
                x * srcwidth,
                y * srcheight,
                wraparound=False,
            )
    return image

def randomtiles(columns, rows, sourceImages, srcwidth, srcheight):
    if srcwidth <= 0 or srcheight <= 0:
        raise ValueError
    if (not sourceImages) or len(sourceImages) == 0:
        raise ValueError
    width = columns * srcwidth
    height = rows * srcheight
    image = blankimage(width, height)
    for y in range(rows):
        for x in range(columns):
            imageblit(
                image,
                width,
                height,
                random.choice(sourceImages),
                srcwidth,
                srcheight,
                x * srcwidth,
                y * srcheight,
            )
    return image

def verthatchedbox(image, width, height, color, x0, y0, x1, y1):
    pattern = [0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA]
    hatchedbox(image, width, height, color, pattern, x0, y0, x1, y1)

def horizhatchedbox(image, width, height, color, x0, y0, x1, y1):
    pattern = [0xFF, 0, 0xFF, 0, 0xFF, 0, 0xFF, 0]
    hatchedbox(image, width, height, color, pattern, x0, y0, x1, y1)

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

def borderedgradientbox(
    image, width, height, border, gradient, contour, x0, y0, x1, y1, wraparound=True
):
    # Draw a wraparound box in a gradient fill on an image.
    # 'border' is the color of the 1-pixel-thick border. Can be None (so
    # that no border is drawn)
    # 'gradient' is a list of 256 colors for mapping the 256 possible shades
    # of the gradient fill.
    if x1 < x0 or y1 < y0:
        raise ValueError
    if width <= 0 or height <= 0:
        raise ValueError
    if (not gradient) or (not image) or (not contour):
        raise ValueError
    if x0 == x1 or y0 == y1:
        return
    if not wraparound:
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, width)
        y1 = min(y1, height)
        if x0 >= x1 or y0 >= y1:
            return
    for y in range(y0, y1):
        ypp = y % height
        yv = (y - y0) / (y1 - y0)
        yp = ypp * width * 3
        for x in range(x0, x1):
            xp = x % width
            if border and (y == y0 or y == y1 - 1 or x == x0 or x == x1 - 1):
                # Draw border color
                image[yp + xp * 3] = border[0]
                image[yp + xp * 3 + 1] = border[1]
                image[yp + xp * 3 + 2] = border[2]
            else:
                xv = (x - x0) / (x1 - x0)
                c = _togray255(contour(xv, yv))
                color = gradient[c]
                image[yp + xp * 3] = color[0]
                image[yp + xp * 3 + 1] = color[1]
                image[yp + xp * 3 + 2] = color[2]

def bordereddithergradientbox(
    image,
    width,
    height,
    border,
    color1,
    color2,
    contour,
    x0,
    y0,
    x1,
    y1,
    wraparound=True,
):
    # Draw a wraparound box in a two-color dithered gradient fill on an image.
    # 'border' is the color of the 1-pixel-thick border. Can be None (so
    # that no border is drawn)
    # 'color1' and 'color2' are the dithered
    # versions of the inner color. 'color1' and 'color2' can't be None.
    if x1 < x0 or y1 < y0:
        raise ValueError
    if width <= 0 or height <= 0:
        raise ValueError
    if (not color1) or (not image) or (not color2) or (not contour):
        raise ValueError
    if x0 == x1 or y0 == y1:
        return
    if not wraparound:
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, width)
        y1 = min(y1, height)
        if x0 >= x1 or y0 >= y1:
            return
    for y in range(y0, y1):
        ypp = y % height
        yv = (y - y0) / (y1 - y0)
        yp = ypp * width * 3
        for x in range(x0, x1):
            xp = x % width
            if border and (y == y0 or y == y1 - 1 or x == x0 or x == x1 - 1):
                # Draw border color
                image[yp + xp * 3] = border[0]
                image[yp + xp * 3 + 1] = border[1]
                image[yp + xp * 3 + 2] = border[2]
            else:
                xv = (x - x0) / (x1 - x0)
                c = _togray64(contour(xv, yv))
                bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
                if bdither < c:
                    image[yp + xp * 3] = color2[0]
                    image[yp + xp * 3 + 1] = color2[1]
                    image[yp + xp * 3 + 2] = color2[2]
                else:
                    image[yp + xp * 3] = color1[0]
                    image[yp + xp * 3 + 1] = color1[1]
                    image[yp + xp * 3 + 2] = color1[2]

def ditheralpha(image, width, height):
    # Dither 256-level alpha channel to two levels (opaque
    # and transparent)
    i = 0
    for y in range(height):
        for x in range(width):
            a = image[i + 3]
            if a != 0 and a != 255:
                bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
                a = 255 if bdither < a * 64 // 255 else 0
                image[i + 3] = a
            i += 4

def borderedbox(
    image, width, height, border, color1, color2, x0, y0, x1, y1, wraparound=True
):
    # Draw a wraparound dither-colored box on an image.
    # 'border' is the color of the 1-pixel-thick border. Can be None (so
    # that no border is drawn)
    # 'color1' and 'color2' are the dithered
    # versions of the inner color. 'color1' and 'color2' can't be None.
    if x1 < x0 or y1 < y0:
        raise ValueError
    if width <= 0 or height <= 0:
        raise ValueError
    if (not color1) or (not image) or (not color2):
        raise ValueError
    if x0 == x1 or y0 == y1:
        return
    if not wraparound:
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, width)
        y1 = min(y1, height)
        if x0 >= x1 or y0 >= y1:
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

def blankimage(width, height, color=None):
    if color and len(color) < 3:
        raise ValueError
    image = [255 for i in range(width * height * 3)]  # default background is white
    if color:
        simplebox(image, width, height, color, 0, 0, width, height)
    return image

def argyle(foregroundImage, backgroundImage, width, height, expo=1, shiftImageBg=False):
    # Generates a tileable argyle pattern from two images of the
    # same size.  'backgroundImage' must be tileable if shiftImageBg=False;
    # 'foregroundImage' need not be tileable.
    if shiftImageBg:
        i2 = blankimage(width, height)
        imageblit(
            i2, width, height, backgroundImage, width, height, width // 2, height // 2
        )
        return argyle(foregroundImage, i2, width, height, expo, shiftImageBg=False)
    ret = blankimage(width, height)
    pos = 0
    for y in range(height):
        yp = (y / height) * 2 - 1
        for x in range(width):
            xp = (x / width) * 2 - 1
            if abs(xp) ** expo + abs(yp) ** expo <= 1:
                # image 1 is inside the diamond
                ret[pos] = foregroundImage[pos]
                ret[pos + 1] = foregroundImage[pos + 1]
                ret[pos + 2] = foregroundImage[pos + 2]
            else:
                # image 2 is outside the diamond
                ret[pos] = backgroundImage[pos]
                ret[pos + 1] = backgroundImage[pos + 1]
                ret[pos + 2] = backgroundImage[pos + 2]
            pos += 3
    return ret

def checkerboardtile(upperLeftImage, otherImage, width, height, columns=2, rows=2):
    # Generates a tileable checkerboard pattern using two images of the same size;
    # each tile is the whole of one of the source images, and the return value's
    # width in pixels is width*columns; its height is height*rows.
    # The two images should be tileable.
    # The number of columns and of rows must be even and positive.
    if rows <= 0 or columns <= 0 or rows % 2 == 1 or columns % 2 == 1:
        raise ValueError
    ret = blankimage(width * columns, height * rows)
    for y in range(rows):
        for x in range(columns):
            imageblit(
                ret,
                width * columns,
                height * rows,
                upperLeftImage if (y + x) % 2 == 0 else otherImage,
                width,
                height,
                x * width,
                y * height,
            )
    return ret

def checkerboard(upperLeftImage, otherImage, width, height, columns=2, rows=2):
    # Generates a tileable checkerboard pattern made of parts of two images of the same size;
    # the return value has the same width and height as the source images.
    # The two images should be tileable.
    # The number of columns and of rows must be even and positive.
    if rows <= 0 or columns <= 0 or rows % 2 == 1 or columns % 2 == 1:
        raise ValueError
    ret = blankimage(width, height)
    pos = 0
    for y in range(height):
        yp = y * rows // height
        for x in range(width):
            xp = x * columns // width
            if (yp + xp) % 2 == 0:
                ret[pos] = upperLeftImage[pos]
                ret[pos + 1] = upperLeftImage[pos + 1]
                ret[pos + 2] = upperLeftImage[pos + 2]
            else:
                ret[pos] = otherImage[pos]
                ret[pos + 1] = otherImage[pos + 1]
                ret[pos + 2] = otherImage[pos + 2]
            pos += 3
    return ret

def simpleargyle(fgcolor, bgcolor, linecolor, w, h):
    fg = blankimage(w, h, fgcolor)
    bg = blankimage(w, h, bgcolor)
    bg = argyle(fg, bg, w, h)
    linedraw(bg, w, h, linecolor, 0, 0, w, h)
    linedraw(bg, w, h, linecolor, 0, h, w, 0)
    return bg

def doubleargyle(fgcolor1, fgcolor2, bgcolor, linecolor1, linecolor2, w, h):
    f1 = simpleargyle(fgcolor1, bgcolor, linecolor1, w, h)
    f2 = simpleargyle(fgcolor2, bgcolor, linecolor2, w, h)
    return checkerboardtile(f1, f2, w, h)

def simpleargyle2(fgcolor, bgcolor, linecolor, w, h):
    fg = blankimage(w, h, fgcolor)
    bg = blankimage(w, h, bgcolor)
    bg = argyle(fg, bg, w, h)
    linedraw(bg, w, h, linecolor, 2, 0, w + 2, h, wraparound=True)
    linedraw(bg, w, h, linecolor, -2, 0, w - 2, h, wraparound=True)
    linedraw(bg, w, h, linecolor, 2, h, w + 2, 0, wraparound=True)
    linedraw(bg, w, h, linecolor, -2, h, w - 2, 0, wraparound=True)
    return bg

def hatchoverlay(image, width, height, hatchColor, rows=2):
    if not hatchColor:
        raise ValueError
    # hatch=[0x88,0x44,0x22,0x11,0x88,0x44,0x22,0x11] # denser diagonal hatch
    # revhatch=[0x22,0x44,0x88,0x11,0x22,0x44,0x88,0x11] # denser diagonal hatch
    hatch = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]
    revhatch = [0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x01]
    for y in range(rows):
        y0 = height * y // rows
        y1 = height * (y + 1) // rows
        hatchedbox(
            image,
            width,
            height,
            hatchColor,
            hatch if y % 2 == 0 else revhatch,
            0,
            y0,
            width,
            y1,
        )

def _nearest_rgb3(pal, r, g, b):
    best = -1
    ret = 0
    for i in range(len(pal)):
        cr = pal[i][0]
        cg = pal[i][1]
        cb = pal[i][2]
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if i == 0 or dist < best:
            ret = i
            best = dist
    return ret

def _nearest_rgb(pal, rgb):
    return _nearest_rgb3(pal, rgb[0], rgb[1], rgb[2])

def drawhatchcolumns(image, width, height, hatchdist=8, hatchthick=1, fgcolor=None):
    # hatchdist - distance from beginning of one vertical hash line to the
    # beginning of the next, in pixels.
    # hatchthick - thickness in pixels of each vertical hash line.
    if hatchdist <= 0 or hatchthick < 0 or hatchthick > hatchdist:
        raise ValueError
    if fgcolor and len(fgcolor) != 3:
        raise ValueError
    if not fgcolor:
        fgcolor = [0, 0, 0]
    pos = 0
    while pos < width:
        simplebox(
            image,
            width,
            height,
            fgcolor,
            pos,
            0,
            min(width, pos + hatchthick),
            height,
        )
        pos += hatchdist

def drawhatchrows(image, width, height, hatchdist=8, hatchthick=1, fgcolor=None):
    if hatchdist <= 0 or hatchthick < 0 or hatchthick > hatchdist:
        raise ValueError
    if fgcolor and len(fgcolor) != 3:
        raise ValueError
    if not fgcolor:
        fgcolor = [0, 0, 0]
    pos = 0
    while pos < height:
        simplebox(
            image,
            width,
            height,
            fgcolor,
            0,
            pos,
            width,
            min(height, pos + hatchthick),
        )
        pos += hatchdist

def drawdiagstripe(image, width, height, stripesize, reverse, fgcolor=None):
    # 'stripesize' is in pixels
    # reverse=false: stripe runs from top left to bottom
    # right assuming the image's first row is the top row
    # reverse=true: stripe runs from top right to bottom
    # left
    if stripesize > max(width, height) or stripesize < 0:
        raise ValueError
    if fgcolor and len(fgcolor) != 3:
        raise ValueError
    # default foreground color is black
    if not fgcolor:
        fgcolor = [0, 0, 0]
    xpstart = -(stripesize // 2)
    xpend = xpstart + stripesize
    xIsLong = width >= height
    longStart = 0
    shortStart = 0
    longEnd = (width - 1) if xIsLong else (height - 1)
    shortEnd = (height - 1) if xIsLong else (width - 1)
    u = 2 * (shortEnd - shortStart)
    dlong = longEnd - longStart
    v = u - 2 * dlong
    z = u - dlong
    shortCoord = shortStart
    for longCoord in range(longStart, longEnd + 1):
        if longCoord == longEnd:
            shortCoord = shortEnd
        elif longCoord > longStart:
            if z < 0:
                z += u
            else:
                shortCoord += 1
                z += v
        if xIsLong:
            xc = width - 1 - longCoord if reverse else longCoord
            simplebox(
                image,
                width,
                height,
                fgcolor,
                xc,
                shortCoord + xpstart,
                xc + 1,
                shortCoord + xpend,
            )
        else:
            xc = width - 1 - shortCoord if reverse else shortCoord
            simplebox(
                image,
                width,
                height,
                fgcolor,
                xc + xpstart,
                longCoord,
                xc + xpend,
                longCoord + 1,
            )

def getgrays(palette):
    grays = 0
    for p in palette:
        if p[0] >= 256 or p[0] < 0:
            raise ValueError
        if p[0] == p[1] and p[1] == p[2]:
            grays |= 1 << p[0]
    ret = []
    for i in range(256):
        if (grays & (1 << i)) != 0:
            ret.append(i)
    return ret  # return a sorted list of gray tones in the given palette

def dithertograyimage(image, width, height, grays):
    if not grays:
        return graymap(image, width, height)
    if len(grays) < 2:
        raise ValueError
    for i in range(1, len(grays)):
        # Grays must be sorted
        if grays[i] < 0 or grays[i] < grays[i - 1] or (grays[i] - grays[i - 1]) > 255:
            raise ValueError
    for y in range(height):
        yp = y * width * 3
        for x in range(width):
            xp = yp + x * 3
            c = (image[xp] * 2126 + image[xp + 1] * 7152 + image[xp + 2] * 722) // 10000
            r = 0
            bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
            for i in range(1, len(grays)):
                if c >= grays[i - 1] and c <= grays[i]:
                    r = (
                        grays[i]
                        if bdither
                        < (c - grays[i - 1]) * 64 // (grays[i] - grays[i - 1])
                        else grays[i - 1]
                    )
                    break
            image[xp] = image[xp + 1] = image[xp + 2] = r
    return image

def graymap(image, width, height, colors=None):
    # Converts the image to grayscale and maps the resulting gray tones
    # to colors in the given colors array.  If 'colors' is None, the default,
    # the mapping step is skipped.
    for y in range(height):
        yp = y * width * 3
        for x in range(width):
            xp = yp + x * 3
            c = image[xp]
            if c != image[xp + 1] or image[xp + 1] != image[xp + 2]:
                # Not a gray pixel, so find gray value
                c = (
                    image[xp] * 2126 + image[xp + 1] * 7152 + image[xp + 2] * 722
                ) // 10000
            if colors:
                col = colors[c]
                if not col:
                    # No color defined at this index
                    raise ValueError
                image[xp] = col[0]
                image[xp + 1] = col[1]
                image[xp + 2] = col[2]
            else:
                image[xp] = image[xp + 1] = image[xp + 2] = c
    return image

def getpixel(image, width, height, x, y):
    pos = y * width * 3 + x * 3
    return image[pos : pos + 3]

def setpixel(image, width, height, x, y, c):
    pos = y * width * 3 + x * 3
    image[pos] = c[0]
    image[pos + 1] = c[1]
    image[pos + 2] = c[2]

def imagetranspose(image, width, height):
    image2 = blankimage(height, width)
    for y in range(height):
        for x in range(width):
            setpixel(image2, height, width, y, x, getpixel(image, width, height, x, y))
    return image2

def _ditherstyle(image, width, height, bgcolor=None):
    # Create a twice-as-wide image inspired by the style used
    # to generate MARBLE.BMP
    image2 = blankimage(width * 2, height)
    if not bgcolor:
        bgcolor = [192, 192, 192]
    for y in range(height):
        for x in range(width):
            c = getpixel(image, width, height, x, y)
            setpixel(image2, width * 2, height, x * 2, y, c if y % 2 == 0 else bgcolor)
            setpixel(
                image2, width * 2, height, x * 2 + 1, y, bgcolor if y % 2 == 0 else c
            )
    return image2

def tograyditherstyle(image, width, height, palette=None, light=False):
    im = [x for x in image]
    graymap(im, width, height)
    if palette:
        grays = getgrays(palette)
        if len(grays) == 0:
            raise ValueError("palette has no gray tones")
        dithertograyimage(im, width, height, grays)
    if light:
        # Variant used in background of WINLOGO.BMP
        colors = [[i, i, i] for i in range(256)]
        colors[192] = [255, 255, 255]
        colors[128] = [192, 192, 192]
        colors[0] = [128, 128, 128]
        graymap(im, width, height, colors)
    return _ditherstyle(im, width, height)

def websafeDither(image, width, height):
    # Dithering for the color palette returned by websafecolors()
    for y in range(height):
        yp = y * width * 3
        for x in range(width):
            xp = yp + x * 3
            for i in range(3):
                c = image[xp + i]
                cm = c % 51
                bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
                image[xp + i] = (c - cm) + 51 if bdither < cm * 64 // 51 else c - cm
    return image

def patternDither(image, width, height, palette):
    # Dithering for arbitrary color palettes
    # Derived from Adobe's pattern dithering algorithm, described by J. Yliluoma at:
    # https://bisqwit.iki.fi/story/howto/dither/jy/
    candidates = [[] for i in range(len(DitherMatrix))]
    paletteLum = [
        (can[0] * 2126 + can[1] * 7152 + can[2] * 722) // 10000 for can in palette
    ]
    trials = {}
    numtrials = 0
    numskips = 0
    for y in range(height):
        yp = y * width * 3
        for x in range(width):
            xp = yp + x * 3
            e = [0, 0, 0]
            exact = False
            for i in range(len(DitherMatrix)):
                ir = image[xp]
                ig = image[xp + 1]
                ib = image[xp + 2]
                # "// 4" is equiv. to "* 0.25" where 0.25
                # is the dithering strength
                t0 = ir + e[0] // 4
                if t0 < 0:
                    t0 = 0
                if t0 > 255:
                    t0 = 255
                t1 = ig + e[1] // 4
                if t1 < 0:
                    t1 = 0
                if t1 > 255:
                    t1 = 255
                t2 = ib + e[2] // 4
                if t2 < 0:
                    t2 = 0
                if t2 > 255:
                    t2 = 255
                t = t0 | (t1 << 8) | (t2 << 16)
                canvalue = None
                numtrials += 1
                if t in trials:
                    numskips += 1
                    canvalue = trials[t]
                else:
                    canindex = _nearest_rgb3(
                        palette,
                        t0,
                        t1,
                        t2,
                    )
                    can = palette[canindex]
                    trials[t] = canvalue = [
                        paletteLum[canindex],
                        canindex,
                    ]  # sort key consisting of gray value then color
                candidates[i] = canvalue
                cv1 = palette[canvalue[1]]
                e[0] += ir - cv1[0]
                e[1] += ig - cv1[1]
                e[2] += ib - cv1[2]
            if exact:
                continue
            candidates.sort()
            bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
            fcan = candidates[bdither][1]
            fcan = palette[fcan]
            image[xp] = fcan[0]
            image[xp + 1] = fcan[1]
            image[xp + 2] = fcan[2]
    return image

def colorgradient(blackColor, whiteColor):
    if (
        (not blackColor)
        or (not whiteColor)
        or len(blackColor) != 3
        or len(whiteColor) != 3
    ):
        raise ValueError
    return [
        [blackColor[i] + (whiteColor[i] - blackColor[i]) * j // 255 for i in range(3)]
        for j in range(256)
    ]

def noiseimage(width=64, height=64):
    # Generate an image of noise
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

def whitenoiseimage(width=64, height=64):
    # Generate an image of white noise
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

def circledraw(image, width, height, c, cx, cy, r, wraparound=True):
    # Draws a wraparound circle
    stride = width * 3
    fullstride = stride * height
    # midpoint circle algorithm
    z = -r
    x = r
    y = 0
    while y < x:
        octs = [[x, y], [-x, -y], [x, -y], [-x, y], [y, x], [-y, -x], [y, -x], [-y, x]]
        for xx, yy in octs:
            px = cx + xx
            py = cy + yy
            if wraparound:
                px = px % width
                py = py % height
            if wraparound or (px >= 0 and py >= 0 and px < width and py < height):
                pos = stride * py + px * 3
                image[pos] = c[0]
                image[pos + 1] = c[1]
                image[pos + 2] = c[2]
        z += 1 + y + y
        y += 1
        if z >= 0:
            z -= x + x - 1
            x -= 1

def linedraw(
    image, width, height, c, x0, y0, x1, y1, drawEndPoint=False, wraparound=True
):
    # Draws a wraparound line
    stride = width * 3
    fullstride = stride * height
    # Bresenham's algorithm
    dx = x1 - x0
    dy = y1 - y0
    wrap = wraparound and (
        x0 < 0
        or x1 < 0
        or y0 < 0
        or y1 < 0
        or x0 >= width
        or x1 >= width
        or y0 >= height
        or y1 >= height
    )
    # Starting point
    if wraparound or (y0 >= 0 and x0 >= 0 and x0 < width and y0 < height):
        imgpos = (
            (y0 % height) * stride + (x0 % width) * 3 if wrap else y0 * stride + x0 * 3
        )
        image[imgpos] = c[0]
        image[imgpos + 1] = c[1]
        image[imgpos + 2] = c[2]
    # Ending point
    if drawEndPoint:
        if wraparound or (y1 >= 0 and x1 >= 0 and x1 < width and y1 < height):
            imgpos = (
                (y1 % height) * stride + (x1 % width) * 3
                if wrap
                else y1 * stride + x1 * 3
            )
            image[imgpos] = c[0]
            image[imgpos + 1] = c[1]
            image[imgpos + 2] = c[2]
    if abs(dy) > abs(dx):
        if y1 < y0:
            dy = abs(dy)
            dx = -dx
            t = y0
            y0 = y1
            y1 = t
            t = x0
            x0 = x1
            x1 = t
        a = abs(dx + dx)
        z = a - dy
        b = z - dy
        y = y0
        x = x0
        if wrap:
            y %= height
            x %= width
        pos = y * stride + x * 3
        stridechange = -3 if dx < 0 else 3
        coordchange = -1 if dx < 0 else 1
        for i in range(1, y1 - y0):
            pos += stride
            y += 1
            if wrap and y == height:
                y = 0
                pos -= fullstride
            if z < 0:
                z += a
            else:
                z += b
                pos = pos + stridechange
                x += coordchange
                if wrap and x < 0:
                    pos += stride
                    x += width
                elif wrap and x >= width:
                    pos -= stride
                    x -= width
            if wraparound or (y >= 0 and x >= 0 and x < width and y < height):
                image[pos] = c[0]
                image[pos + 1] = c[1]
                image[pos + 2] = c[2]
    else:
        if x1 < x0:
            dx = abs(dx)
            dy = -dy
            t = y0
            y0 = y1
            y1 = t
            t = x0
            x0 = x1
            x1 = t
        a = abs(dy + dy)
        z = a - dx
        b = z - dx
        y = y0
        x = x0
        if wrap:
            y %= height
            x %= width
        pos = y * stride + x * 3
        stridechange = -stride if dy < 0 else stride
        coordchange = -1 if dy < 0 else 1
        for i in range(1, x1 - x0):
            pos += 3
            x += 1
            if wrap and x == width:
                x = 0
                pos -= stride
            if z < 0:
                z += a
            else:
                z += b
                pos = pos + stridechange
                y += coordchange
                if wrap and y < 0:
                    pos += fullstride
                    y += height
                elif wrap and y >= height:
                    pos -= fullstride
                    y -= height
            if wraparound or (y >= 0 and x >= 0 and x < width and y < height):
                image[pos] = c[0]
                image[pos + 1] = c[1]
                image[pos + 2] = c[2]

def brushednoise(width, height, tileable=True):
    image = blankimage(width, height, [192, 192, 192])
    for i in range(max(width, height) * 5):
        c = random.choice([128, 128, 128, 128, 0, 255])
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        x1 = x + random.randint(0, width // 2)
        simplebox(image, width, height, [c, c, c], x, y, x1, y + 1, wraparound=tileable)
    return image

def brushednoise2(width, height, tileable=True):
    image = blankimage(width, height, [192, 192, 192])
    for i in range(max(width, height) * 5):
        c = random.choice([128, 128, 128, 128, 0, 255])
        x = random.randint(0, width)
        y = random.randint(0, height)
        x1 = x + (-1 if random.randint(0, 1) == 0 else 1) * random.randint(
            0, width // 2
        )
        y1 = y + (-1 if random.randint(0, 1) == 0 else 1) * random.randint(
            0, height // 2
        )
        linedraw(image, width, height, [c, c, c], x, y, x1, y1, wraparound=tileable)
    return image

def brushednoise3(width, height, tileable=True):
    image = blankimage(width, height, [192, 192, 192])
    for i in range(max(width, height) * 3):
        c = random.choice([128, 128, 128, 128, 0, 255])
        if random.randint(0, 2) == 0:
            # circle
            x = random.randint(0, width)
            y = random.randint(0, height)
            x1 = random.randint(0, width // 2)
            circledraw(image, width, height, [c, c, c], x, y, x1, wraparound=tileable)
        else:
            x = random.randint(0, width)
            y = random.randint(0, height)
            x1 = x + (-1 if random.randint(0, 1) == 0 else 1) * random.randint(
                0, width // 2
            )
            y1 = y + (-1 if random.randint(0, 1) == 0 else 1) * random.randint(
                0, height // 2
            )
            linedraw(image, width, height, [c, c, c], x, y, x1, y1, wraparound=tileable)
    return image

def imagerotatecolumn(image, width, height, x, offset=0):
    # Rotates a column of the image by the given downward offset in pixels, which may be negative or not.
    if x < 0 or x >= width or width < 0 or height < 0:
        raise ValueError
    if height == 0 or width == 0:
        return image
    offset %= height
    if offset == 0:
        return image
    pixels = [
        image[(y * width + x) * 3 : (y * width + x + 1) * 3] for y in range(height)
    ]
    y = 0
    for i in range(height - offset, height):
        image[(y * width + x) * 3 : (y * width + x + 1) * 3] = pixels[i]
        y += 1
    for i in range(0, height - offset):
        image[(y * width + x) * 3 : (y * width + x + 1) * 3] = pixels[i]
        y += 1
    return image

def imagerotaterow(image, width, height, y, offset=0):
    # Rotates a row of the image by the given rightward offset in pixels, which may be negative or not.
    if y < 0 or y >= height or width < 0 or height < 0:
        raise ValueError
    if height == 0 or width == 0:
        return image
    offset %= width
    if offset == 0:
        return image
    image[y * width * 3 : (y + 1) * width * 3] = (
        image[(y * width + (width - offset)) * 3 : (y + 1) * width * 3]
        + image[y * width * 3 : (y * width + (width - offset)) * 3]
    )
    return image

def imagereversecolumnorder(image, width, height):
    for y in range(height):
        pixels = [
            image[(y * width + x) * 3 : (y * width + x + 1) * 3] for x in range(width)
        ]
        pixels.reverse()
        image[y * width * 3 : (y + 1) * width * 3] = [
            c for pixel in pixels for c in pixel
        ]
    return image

def imagereverseroworder(image, width, height):
    halfHeight = height // 2  # floor of half height; don't care about middle row
    for y in range(halfHeight):
        row = image[y * width * 3 : (y + 1) * width * 3]
        otherRow = image[(height - 1 - y) * width * 3 : (height - y) * width * 3]
        image[y * width * 3 : (y + 1) * width * 3] = otherRow
        image[(height - 1 - y) * width * 3 : (height - y) * width * 3] = row
    return image

def endingColumnsAreMirrored(image, width, height):
    # Returns True if width or height is 0 or if:
    # - The image's first column's first half is a mirror
    # of its second half, and...
    # - The image's last column's first half is a mirror
    # of its second half.
    if width < 0 or height < 0:
        raise ValueError
    if width == 0 or height == 0:
        return True
    halfHeight = (height + 1) // 2  # ceiling of half height
    stride = width * 3
    lastPixel = stride - 3
    for i in range(halfHeight):
        oi = height - 1 - i  # other 'i'
        if (
            image[i * stride] != image[oi * stride]
            or image[i * stride + 1] != image[oi * stride + 1]
            or image[i * stride + 2] != image[oi * stride + 2]
        ):
            return False
        if (
            image[i * stride + lastPixel] != image[oi * stride + lastPixel]
            or image[i * stride + lastPixel + 1] != image[oi * stride + lastPixel + 1]
            or image[i * stride + lastPixel + 2] != image[oi * stride + lastPixel + 2]
        ):
            return False
    return True

def endingRowsAreMirrored(image, width, height):
    # Returns True if width or height is 0 or if:
    # - The image's first row's first half is a mirror
    # of its second half, and...
    # - The image's last row's first half is a mirror
    # of its second half.
    if width < 0 or height < 0:
        raise ValueError
    if width == 0 or height == 0:
        return True
    halfWidth = (width + 1) // 2  # ceiling of half width
    lastRow = (height - 1) * width * 3
    for i in range(halfWidth):
        oi = width - 1 - i  # other 'i'
        if (
            image[i * 3] != image[oi * 3]
            or image[i * 3 + 1] != image[oi * 3 + 1]
            or image[i * 3 + 2] != image[oi * 3 + 2]
        ):
            return False
        if (
            image[i * 3 + lastRow] != image[oi * 3 + lastRow]
            or image[i * 3 + lastRow + 1] != image[oi * 3 + lastRow + 1]
            or image[i * 3 + lastRow + 2] != image[oi * 3 + lastRow + 2]
        ):
            return False
    return True

def randomTruchetTiles(image, width, height, columns, rows):
    # "Truchet" means Sébastien Truchet
    if endingRowsAreMirrored(image, width, height):
        altImage = imagereversecolumnorder([x for x in image], width, height)
        return randomtiles(columns, rows, [image, altImage], width, height)
    elif endingColumnsAreMirrored(image, width, height):
        altImage = imagereverseroworder([x for x in image], width, height)
        return randomtiles(columns, rows, [image, altImage], width, height)
    else:
        raise ValueError("ending rows and ending columns are not mirrored")

import math

def affine(
    dstimage, dstwidth, dstheight, srcimage, srcwidth, srcheight, m1, m2, m3, m4
):
    for y in range(dstheight):
        yp = y / srcheight
        for x in range(dstwidth):
            xp = x / srcwidth
            tx = int((xp * m1 + yp * m2) * srcwidth) % srcwidth
            ty = int((xp * m3 + yp * m4) * srcheight) % srcheight
            dstindex = (y * dstwidth + x) * 3
            srcindex = (ty * srcwidth + tx) * 3
            if dstindex < 0 or dstindex > len(dstimage):
                raise ValueError([x, y, tx, ty])
            if srcindex < 0 or srcindex > len(srcimage):
                raise ValueError([x, y, tx, ty])
            dstimage[dstindex : dstindex + 3] = srcimage[srcindex : srcindex + 3]
    return dstimage

def horizskew(image, width, height, skew):
    if skew < -1 or skew > 1:
        raise ValueError
    for i in range(height):
        p = i / height
        imagerotaterow(image, width, height, i, int(skew * p * width))
    return image

def vertskew(image, width, height, skew):
    if skew < -1 or skew > 1:
        raise ValueError
    for i in range(width):
        p = i / width
        imagerotatecolumn(image, width, height, i, int(skew * p * height))
    return image

def randomRotated(image, width, height):
    # Do the rotation rarely
    if random.randint(0, 6) > 0:
        return [image, width, height]
    # A rotated but still tileable version of the given image
    stretch = 2  # must be an integer
    slant = int(math.hypot(width * stretch, height))
    size = width
    image2width = int(slant * (width / size))
    image2height = int(slant * (height / size))
    image2 = blankimage(image2width, image2height)
    r1 = random.choice([1, -1])  # normally 1
    r2 = random.choice([-1, 1])  # normally -1
    return [
        affine(
            image2,
            image2width,
            image2height,
            image,
            width,
            height,
            (size * stretch / slant),
            r1 * (size / slant),
            r2 * (size / slant),
            (size * stretch / slant),
        ),
        image2width,
        image2height,
    ]

def _radialmask(width, height, x, y):
    vx = abs((x / width) * 2.0 - 1.0)
    vy = abs((y / height) * 2.0 - 1.0)
    return min(1, (vx**2 + vy**2) ** 0.5)

def _linearmask(width, height, x, y):
    vx = abs((x / width) * 2.0 - 1.0)
    vy = abs((y / height) * 2.0 - 1.0)
    return max(vx, vy)

def maketileable(image, width, height):
    # Use tiling method described by Paul Bourke,
    # Tiling Textures on the Plane (Part 1)
    # https://paulbourke.net/geometry/tiling/
    ret = blankimage(width, height)
    for y in range(height):
        yp = (y + height // 2) % height
        for x in range(width):
            xp = (x + width // 2) % width
            m1 = 1 - _linearmask(width, height, x, y)
            m2 = 1 - _linearmask(width, height, xp, yp)
            m1 = max(0.001, m1)
            m2 = max(0.001, m2)
            o1 = getpixel(image, width, height, x, y)
            o2 = getpixel(image, width, height, xp, yp)
            t = [
                m1 * ov1 / (m1 + m2) + m2 * ov2 / (m1 + m2) for ov1, ov2 in zip(o1, o2)
            ]
            t = [max(0, min(255, int(v))) for v in t]
            setpixel(ret, width, height, x, y, t)
    return ret

# What follows are methods for generating scalable vector graphics (SVGs)
# and raster graphics of classic OS style borders and button controls.
# Although the SVGs are scalable
# by definition, they are pixelated just as they would appear in classic OSs.
#
# NOTE: A more flexible approach for this kind of drawing
# is to prepare an SVG defining the frame of a user interface element
# with five different parts (in the form of 2D shapes): an "upper outer part", a
# "lower outer part", an "upper inner part", a "lower inner part", and a "middle part".
# Each of these five parts can be colored separately or filled with a pattern.

def svgimagepattern(idstr, image, width, height, transcolor=None, originX=0, originY=0):
    if not image:
        raise ValueError
    if idstr:
        raise ValueError
    ret = (
        "<pattern patternUnits='userSpaceOnUse' id='"
        + idstr.replace("'", "&apos;")
        + (
            "' width='%s' height='%s' patternTransform='translate(%d %d)'>"
            % (width / 2 - originX, height / 2 - originY)
        )
    )
    helper = SvgDraw()
    for y in range(height):
        yp = y * width * 3
        for x in range(width):
            c = [image[yp + x * 3], image[yp + x * 3 + 1], image[yp + x * 3 + 2]]
            if transcolor and c != transcolor:
                helper.rect(x, y, x + 1, y + 1, c)
    return str(helper) + "</pattern>"

class ImageWraparoundDraw:
    def __init__(self, image, width, height):
        self.image = image
        self.width = width
        self.height = height

    def rect(self, x0, y0, x1, y1, c):
        if len(c) == 2:
            borderedbox(image, width, height, None, c[0], c[1], x0, y0, x1, y1)
        else:
            simplebox(self.image, self.width, self.height, c, x0, y0, x1, y1)

class SvgDraw:
    def __init__(self):
        self.svg = ""
        self.patterns = []

    def _tocolor(self, c):
        if isinstance(c, list) and len(c) == 3:
            return "rgb(%d,%d,%d)" % (c[0], c[1], c[2])
        if isinstance(c, list) and len(c) == 2:
            return self._ensurepattern(c[0], c[1])
        return c

    def _ditherbg(self, idstr, face, hilt, hiltIsScrollbarColor=False):
        # 'face' is the button face color
        # 'hilt' is the button highlight color
        if hiltIsScrollbarColor:
            return hilt
        if "'" in idstr:
            raise ValueError
        if '"' in idstr:
            raise ValueError
        image = blankimage(2, 2)
        helper = ImageWraparoundDraw(image, 2, 2)
        if hiltIsScrollbarColor:
            helper.rect(0, 0, 2, 2, hilt)
        # elif 256 or more colors and hilt is not white:
        #    helper.rect(0, 0, 2, 2, [(a+b)//2 for a,b in zip(face, hilt)])
        else:
            helper.rect(0, 0, 1, 1, hilt)
            helper.rect(1, 1, 2, 2, hilt)
            helper.rect(0, 1, 1, 2, face)
            helper.rect(1, 0, 2, 1, face)
        return svgimagepattern(idstr, image, 2, 2)

    def _ensurepattern(self, c1, c2):
        if not c1 or not c2 or len(c1) != 3 or len(c2) != 3:
            raise ValueError
        for pattern in self.patterns:
            if pattern[0] == c1 and pattern[1] == c2:
                return "url(#" + pattern[c2] + ")"
        patid = "pat%d" % (len(self.patterns))
        patsvg = self._ditherbg(patid, c1, c2)
        self.patterns.append([[x for x in c1], [x for x in c2], patid, patsvg])
        return "url(#" + patid + ")"

    def rect(self, x0, y0, x1, y1, c):
        if x0 >= x1 or y0 >= y1:
            return ""
        self.svg += (
            "<path style='stroke:none;fill:%s' d='M%d %dL%d %dL%d %dL%d %dZ'/>"
            % (
                self._tocolor(c),
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

    def toSvg(self, width, height):
        return "<svg width='%dpx' height='%dpx' viewBox='0 0 %d %d'" % (
            width,
            height,
            width,
            height,
        )
        +" xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>"
        +str(self) + "</svg>"

    def __str__(self):
        return ("".join(x[3] for x in self.patterns)) + self.svg

def _createPenIndirect(color):
    cref = (
        (color[0] & 0xFF) | ((color[1] & 0xFF) << 8) | ((color[2] & 0xFF) << 16)
        if color
        else 0
    )
    return struct.pack("<LHHHHL", 8, 0x2FA, 0 if color else 5, 0, 0, cref)

def _createBrushIndirect(color):
    cref = (
        (color[0] & 0xFF) | ((color[1] & 0xFF) << 8) | ((color[2] & 0xFF) << 16)
        if color
        else 0
    )
    return struct.pack("<LHHLh", 7, 0x2FC, 0 if color else 1, cref, 0)

def _selectObject(index):
    if index < 0 or index > 0x7FFF:
        raise ValueError
    return struct.pack("<LHH", 4, 0x12D, index & 0xFFFF)

def _deleteObject(index):
    if index < 0 or index > 0x7FFF:
        raise ValueError
    return struct.pack("<LHH", 4, 0x1F0, index & 0xFFFF)

def _polygonMetafile(points):
    if len(points) > 32767:
        raise ValueError
    size = 4 + len(points) * 2
    ret = struct.pack("<LHH", size, 0x324, len(points))
    for pt in points:
        if pt[0] < -32768 or pt[0] > 32767:
            raise ValueError
        if pt[1] < -32768 or pt[1] > 32767:
            raise ValueError
        ret += struct.pack("<hh", pt[0], pt[1])
    return ret

def _rectangleMetafile(x0, y0, x1, y1):
    if x0 < -32768 or x0 > 32767:
        raise ValueError
    if x1 < -32768 or x1 > 32767:
        raise ValueError
    if y0 < -32768 or y0 > 32767:
        raise ValueError
    if y1 < -32768 or y1 > 32767:
        raise ValueError
    if abs(x1 - x0) >= 32767:
        raise ValueError
    if abs(y1 - y0) >= 32767:
        raise ValueError
    if abs(x1 - x0) <= 2 or abs(y1 - y0) <= 2:
        return _polygonMetafile([[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]])
    return struct.pack("<LHhhhh", 7, 0x41B, y1, x1, y0, x0)

class WindowsMetafileDraw:
    def __init__(self):
        self.colorbrushes = {}
        self.colorpens = {}
        self.handles = []
        self.records = []
        self.selectedPen = -1
        self.selectedBrush = -1
        self.bbox = None

    def _tocref(self, color):
        if not color:
            return -1
        return (color[0] & 0xFF) | ((color[1] & 0xFF) << 8) | ((color[2] & 0xFF) << 16)

    def _ensurePen(self, color):
        if color and len(color) != 3:
            raise ValueError
        cref = self._tocref(color)
        if cref in self.colorpens:
            sel = self.colorpens[cref]
            if self.selectedPen != sel:
                self.records.append(_selectObject(sel))
        else:
            record = _createPenIndirect(color)
            handle = len(self.handles)
            self.records.append(record)
            self.handles.append(record)
            self.colorpens[cref] = handle
            self.records.append(_selectObject(handle))
        self.selectedPen = self.colorpens[cref]

    def _ensureBrush(self, color):
        if color and len(color) != 3:
            raise ValueError
        cref = self._tocref(color)
        if cref in self.colorbrushes:
            sel = self.colorbrushes[cref]
            if self.selectedBrush != sel:
                self.records.append(_selectObject(sel))
        else:
            record = _createBrushIndirect(color)
            handle = len(self.handles)
            self.records.append(record)
            self.handles.append(record)
            self.colorbrushes[cref] = handle
            self.records.append(_selectObject(handle))
        self.selectedBrush = self.colorbrushes[cref]

    def _ensurePoint(self, x, y):
        if not self.bbox:
            self.bbox = [x, y, x, y]
        else:
            self.bbox = [
                min(self.bbox[0], x),
                min(self.bbox[1], y),
                max(self.bbox[2], x),
                max(self.bbox[3], y),
            ]

    def rect(self, x0, y0, x1, y1, c):
        self._ensurePen(None)
        self._ensureBrush(c)
        self._ensurePoint(x0, y0)
        self._ensurePoint(x1, y1)
        self.records.append(_rectangleMetafile(x0, y0, x1, y1))

    def toMetafile(self):
        bbox = self.bbox if self.bbox else [0, 0, 0, 0]
        deletionRecords = [_deleteObject(i) for i in range(len(self.handles))]
        # Windows adds the following "final" metafile record to metafiles it generates
        deletionRecords.append(struct.pack("<LH", 3, 0))
        startingRecords = []
        # SetMapMode(MM_TEXT)
        startingRecords.append(struct.pack("<LHh", 4, 0x103, 1))
        # SetWindowOrg(0,0)
        startingRecords.append(struct.pack("<LHhh", 5, 0x20B, 0, 0))
        # SetWindowExt(right,bottom)
        startingRecords.append(
            struct.pack("<LHHH", 5, 0x20C, (bbox[3] & 0xFFFF), (bbox[2] & 0xFFFF))
        )
        recs = startingRecords + self.records + deletionRecords
        numRecords = len(recs)
        largestRecord = 0 if numRecords == 0 else max(len(r) for r in (recs)) // 2
        size = 9 + (0 if numRecords == 0 else sum(len(r) for r in (recs)) // 2)
        if (
            size > 0xFFFFFFFF
            or largestRecord > 0xFFFFFFFF
            or len(self.handles) > 0xFFFF
        ):
            raise ValueError
        header = b""
        header += struct.pack(
            "<HHHLHLH", 1, 9, 0x300, size, len(self.handles), largestRecord, 0
        )
        return header + b"".join(recs)

# helper for upper edge drawing
def _drawupperedge(helper, x0, y0, x1, y1, color, edgesize=1):
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        helper.rect(x0, y0, x1, y1, color)
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y0, x1, y0 + edgesize, color)
        helper.rect(x0, y0 + edgesize, x1, y1, color)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0, y0, x0 + edgesize, y1, color)
        helper.rect(x0 + edgesize, y0, x1, y1, color)
    else:
        helper.rect(x0, y0, x0 + edgesize, y1, color)  # left edge
        helper.rect(x0 + edgesize, y0, x1, y0 + edgesize, color)  # top edge

# helper for lower edge drawing
def _drawloweredge(helper, x0, y0, x1, y1, color, edgesize=1):
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        helper.rect(x0, y0, x1, y1, color)
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y1 - edgesize, x1, y1, color)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0, y0, x0 + edgesize, y1, color)
        helper.rect(x1 - edgesize, y0, x1, y1, color)
    else:
        helper.rect(x1 - edgesize, y0, x1, y1, color)  # right edge
        helper.rect(x0, y1 - edgesize, x1 - edgesize, y1, color)  # bottom edge

# helper for button face drawing
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
        helper.rect(x0, y0 + edgesize, x1, y1 - edgesize, hilt)
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
    drawFace=True,
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
    if drawFace:
        _drawinnerface(helper, x0, y0, x1, y1, clientAreaColor)  # middle

def flatborder(  # Flat border
    helper,
    x0,
    y0,
    x1,
    y1,
    sh,  # draw the outer parts with this color
    buttonFace,  # draw the inner and middle parts with this color
    drawFace=True,
):
    drawraisedouter(helper, x0, y0, x1, y1, sh, sh, sh, sh)
    drawraisedinner(
        helper, x0, y0, x1, y1, buttonFace, buttonFace, buttonFace, buttonFace
    )
    if drawFace:
        _drawinnerface(helper, x0, y0, x1, y1, buttonFace)

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
    drawFace=True,
):
    face = face if face else lt
    drawraisedouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    if drawFace:
        _drawinnerface(helper, x0, y0, x1, y1, face)

def buttonup(
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
    drawFace=True,
):
    face = face if face else (lt if pressed else hilt)
    drawsunkenouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawsunkeninner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    if drawFace:
        _drawinnerface(helper, x0, y0, x1, y1, face)

def wellborder(helper, x0, y0, x1, y1, hilt, windowText):
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
    drawFace=True,
):
    face = face if face else lt
    drawsunkenouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinner(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    if drawFace:
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
    drawFace=True,
):
    face = face if face else lt
    drawsunkenouter(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    if drawFace:
        _drawinnerface(helper, x0, y0, x1, y1, face)

def _drawrsedge(helper, x0, y0, x1, y1, lt, sh, squareFrame=False):
    if squareFrame:
        _drawedgebotdom(helper, x0, y0, x1, y1, lt, sh)
    else:
        _drawroundedge(helper, x0, y0, x1, y1, lt, sh)

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
    hilt,  # button highlight color
    sh,  # button shadow color
    btn,  # button face color
    frame=None,  # optional frame color
    squareFrame=False,
    isDefault=False,  # whether the button is a default button
    drawFace=True,
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    _drawupperedge(helper, x0 + edge, y0 + edge, x1 - edge, y1 - edge, sh)
    if drawFace:
        helper.rect(x0 + edge + 1, y0 + edge + 1, x1 - edge, y1 - edge, btn)
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
    hilt,  # button highlight color
    sh,  # button shadow color
    btn,  # button face color
    frame=None,  # optional frame color
    squareFrame=False,
    isDefault=False,
    drawFace=True,
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    _drawedgebotdom(helper, x0 + edge, y0 + edge, x1 - edge, y1 - edge, hilt, sh)
    _drawedgebotdom(
        helper, x0 + edge + 1, y0 + edge + 1, x1 - edge - 1, y1 - edge - 1, hilt, sh
    )
    if drawFace:
        helper.rect(x0 + edge + 2, y0 + edge + 2, x1 - edge - 2, y1 - edge - 2, btn)
    if frame:
        _drawrsedge(helper, x0, y0, x1, y1, frame, frame, squareFrame)
        if isDefault:
            _drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)

def makesvg():
    image = blankimage(64, 64)
    helper = ImageWraparoundDraw(image, 64, 64)
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
        drawFace=False,
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
        drawFace=False,
    )
    return image

# random wallpaper generation

def _togray255(x):
    return int(abs(max(-1, min(1, x))) * 255.0)

def _togray64(x):
    return int(abs(max(-1, min(1, x))) * 64.0)

def _diagcontour(x, y):
    if x > 1 or x < -1:
        raise ValueError(x)
    if y > 1 or y < -1:
        raise ValueError(y)
    c = abs(x + y) % 2.0
    return 2 - c if c > 1.0 else c

def _horizcontour(x, y):
    return y

def _vertcontour(x, y):
    return x

def _argyle(x, y, v):
    x = x * 2.0 - 1
    y = y * 2.0 - 1
    return min(1, abs(x) ** v + abs(y) ** v)

def _square(x, y):
    x = abs(x * 2.0 - 1)
    y = abs(y * 2.0 - 1)
    return min(1, max(x, y))

def _reversediagcontour(x, y):
    return _diagcontour(1 - x, y)

def _halfandhalf(x, y):
    return 0.5

def _whole(x, y):
    return 1.0

def _horizcontourwrap(x, y):
    return y * 2.0 - 1

def _vertcontourwrap(x, y):
    return x * 2.0 - 1

def _diagcontourwrap(x, y):
    return _diagcontour(x * 2.0 - 1, y * 2.0 - 1)

def _reversediagcontourwrap(x, y):
    return _diagcontourwrap(1 - x, y)

def _mindiagwrap(x, y):
    return min(_diagcontourwrap(x, y), _reversediagcontourwrap(x, y))

def _randomgradientfillex(width, height, palette, contour):
    image = blankimage(width, height)
    grad = randomColorization()
    borderedgradientbox(image, width, height, None, grad, contour, 0, 0, width, height)
    if palette:
        patternDither(image, width, height, palette)
    return image

def _randomcontour(tileable=True, includeWhole=False):
    contours = []
    r = random.choice([0.5, 2.0 / 3, 1, 1.5, 2])
    if tileable:
        contours = [
            _horizcontourwrap,
            _vertcontourwrap,
            _diagcontourwrap,
            _reversediagcontourwrap,
            _mindiagwrap,
            _square,
            lambda x, y: _argyle(x, y, r),
        ]
    else:
        contours = [
            _horizcontourwrap,
            _vertcontourwrap,
            _diagcontourwrap,
            _reversediagcontourwrap,
            _mindiagwrap,
            _horizcontour,
            _vertcontour,
            _diagcontour,
            _square,
            lambda x, y: _argyle(x, y, r),
        ]
    if includeWhole:
        contours.append(_whole)
    return random.choice(contours)

def _randomgradientfill(width, height, palette, tileable=True):
    return _randomgradientfillex(width, height, palette, _randomcontour(tileable))

def randommaybemonochrome(image, width, height):
    r = random.randint(0, 99)
    if r < 8:
        image = dithertograyimage([x for x in image], width, height, [0, 128, 255])
        return random.choice(
            [x for x in vgaVariantsFromThreeGrays(image, width, height).values()]
        )
    elif r < 16:
        image = dithertograyimage([x for x in image], width, height, [0, 128, 192, 255])
        return random.choice(
            [x for x in vgaVariantsFromFourGrays(image, width, height).values()]
        )
    else:
        return image

def _randomdither(image, width, height, palette):
    grays = getgrays(palette) if palette else None
    if ((not palette) or len(grays) >= 2) and random.randint(0, 99) < 10:
        # Convert to the grays in the palette
        dithertograyimage(image, width, height, grays if palette else None)
    elif palette:
        # Dither away from half-and-half colors
        halfhalfditherimage(
            image,
            width,
            height,
            palette,
        )
    return image

def _randombackground(w, h, palette, tileable=True):
    r = random.randint(0, 100)
    if r < 25:
        return _randombrushednoiseimage(w, h, palette, tileable=tileable)
    elif r < 80:
        return _randomgradientfill(w, h, palette, tileable=tileable)
    else:
        image = blankimage(w, h)
        c0 = []
        c1 = []
        if palette:
            c0 = random.choice(palette)
            c1 = random.choice(palette)
        else:
            c0 = c1 = [random.randint(0, 255) for i in range(3)]
        borderedbox(
            image,
            w,
            h,
            None,
            c0,
            c1,
            0,
            0,
            w,
            h,
            wraparound=tileable,
        )
        return image

def randomhatchimage(w, h, palette=None, tileable=True):
    # Generates a random hatch image (using the given palette, if any)
    expandedpal = paletteandhalfhalf(palette) if palette else []
    if random.randint(0, 99) < 50:
        # Diagonal hatch
        fgcolor = (
            random.choice(expandedpal)
            if palette
            else [random.randint(0, 255) for i in range(3)]
        )
        image = _randombackground(w, h, palette, tileable=tileable)
        drawdiagstripe(
            image, w, h, random.randint(0, min(4, w // 8)), False, fgcolor=fgcolor
        )
        drawdiagstripe(
            image, w, h, random.randint(0, min(4, w // 8)), True, fgcolor=fgcolor
        )
        return _randomdither(
            image,
            w,
            h,
            palette,
        )
    else:
        # Horizontal and vertical hatch
        distx = w // 4
        disty = h // 4
        thickx = random.randint(0, min(7, distx))
        thicky = random.randint(0, min(7, disty))
        image = _randombackground(w, h, palette, tileable=tileable)
        fgcolor = (
            random.choice(expandedpal)
            if palette
            else [random.randint(0, 255) for i in range(3)]
        )
        drawhatchcolumns(image, w, h, distx, thickx, fgcolor)
        drawhatchrows(image, w, h, disty, thicky, fgcolor)
        return _randomdither(
            image,
            w,
            h,
            palette,
        )

def _randomboxesimage(width, height, palette=None, tileable=True, fancy=True):
    # Generates a random boxes image (using the given palette, if any)
    expandedpal = paletteandhalfhalf(palette) if palette else None
    darkest = palette[_nearest_rgb3(palette, 0, 0, 0)] if palette else []
    image = blankimage(width, height, darkest if palette else [0, 0, 0])
    contours = [
        _horizcontour,
        _vertcontour,
        _diagcontour,
        _reversediagcontour,
        _horizcontourwrap,
        _vertcontourwrap,
        _diagcontourwrap,
        _reversediagcontourwrap,
        _mindiagwrap,
        _square,
        lambda x, y: _argyle(x, y, 1),
        _halfandhalf,
        _halfandhalf,
    ]
    for i in range(45):
        x0 = random.randint(0, width - 1)
        x1 = x0 + random.randint(3, max(3, width * 3 // 4))
        y0 = random.randint(0, height - 1)
        y1 = y0 + random.randint(3, max(3, height * 3 // 4))
        c1 = (
            (
                random.choice(expandedpal)
                if random.randint(0, 1) == 0
                else random.choice(palette)
            )
            if palette
            else [random.randint(0, 255) for i in range(3)]
        )
        c2 = (
            (
                random.choice(expandedpal)
                if random.randint(0, 1) == 0
                else random.choice(palette)
            )
            if palette
            else [random.randint(0, 255) for i in range(3)]
        )
        if not palette:
            if fancy:
                borderedgradientbox(
                    image,
                    width,
                    height,
                    [0, 0, 0],
                    colorgradient(c1, c2),
                    random.choice(contours),
                    x0,
                    y0,
                    x1,
                    y1,
                    wraparound=tileable,
                )
            else:
                borderedbox(
                    image,
                    width,
                    height,
                    [0, 0, 0],
                    c1,
                    c1,
                    x0,
                    y0,
                    x1,
                    y1,
                    wraparound=tileable,
                )
        else:
            bordereddithergradientbox(
                image,
                width,
                height,
                darkest,
                c1,
                c2,
                random.choice(contours) if fancy else _halfandhalf,
                x0,
                y0,
                x1,
                y1,
                wraparound=tileable,
            )
    return _randomdither(image, width, height, palette) if palette else image

def _randomshadedboxesimage(w, h, palette=None, tileable=True):
    r = 0
    if w <= 32 or h <= 32:
        r = random.randint(3, 6)
    else:
        r = random.randint(6, 10)  # number of rows and number of columns
    image = blankimage(w, h)
    origColor = [random.randint(0, 255) for i in range(3)]
    contour = _randomcontour(tileable=tileable, includeWhole=True)
    for y in range(r):
        for x in range(r):
            x0 = x * w // r
            x1 = (x + 1) * w // r
            y0 = y * h // r
            y1 = (y + 1) * h // r
            gx = (x0 + (x1 - x0) // 2) * 1.0 / w
            gy = (y0 + (y1 - y0) // 2) * 1.0 / h
            cr = random.randint(0, 128) - 64
            cont = _togray64(contour(gx, gy))
            cr = cr * cont // 64
            newColor = []
            if cr < 0:
                newColor = [x - x * abs(cr) // 255 for x in origColor]
            else:
                newColor = [x + (255 - x) * abs(cr) // 255 for x in origColor]
            borderedbox(
                image,
                w,
                h,
                None,
                newColor,
                newColor,
                x0,
                y0,
                x1,
                y1,
                wraparound=tileable,
            )
    if palette:
        patternDither(image, w, h, palette)
    return image

def _randombrushednoiseimage(w, h, palette=None, tileable=True):
    transpose = random.randint(0, 1) == 0
    ww = h if transpose else w
    hh = w if transpose else h
    r = random.randint(0, 2)
    if r == 0:
        image = brushednoise(ww, hh, tileable=tileable)
    elif r == 1:
        image = brushednoise2(ww, hh, tileable=tileable)
    else:
        image = brushednoise3(ww, hh, tileable=tileable)
    if transpose:
        image = imagetranspose(image, ww, hh)
    graymap(
        image,
        w,
        h,
        colorgradient([0, 0, 0], [random.randint(0, 255) for i in range(3)]),
    )
    if palette:
        patternDither(image, w, h, palette)
    return image

def randomcheckimage(w, h, palette=None, tileable=True):
    # Generates a random checkerboard pattern image (using the given palette, if any)
    expandedpal = paletteandhalfhalf(palette) if palette else []
    hatch = (
        None
        if random.randint(0, 1) == 0
        else (
            random.choice(expandedpal)
            if palette
            else [random.randint(0, 255) for i in range(3)]
        )
    )
    if w >= 64 and h >= 64:
        rows = random.choice([2, 2, 2, 4, 6, 8])
        columns = random.choice([2, 2, 2, 4, 6, 8])
    else:
        rows = 2
        columns = 2
    otherImage = _randombackground(w, h, palette, tileable=tileable)
    upperLeftImage = _randombackground(w, h, palette, tileable=tileable)
    if hatch:
        hatchoverlay(upperLeftImage, w, h, hatch, rows=rows)
    image = checkerboard(upperLeftImage, otherImage, w, h, rows=rows, columns=columns)
    return _randomdither(image, w, h, palette)

def _randomsimpleargyle(w, h, palette, tileable=True):
    expandedpal = paletteandhalfhalf(palette) if palette else []
    bg = (
        random.choice(expandedpal)
        if palette
        else [random.randint(0, 255) for i in range(3)]
    )
    fg = (
        random.choice(expandedpal)
        if palette
        else [random.randint(0, 255) for i in range(3)]
    )
    linecolor = (
        random.choice(expandedpal)
        if palette
        else [random.randint(0, 255) for i in range(3)]
    )
    image3 = simpleargyle(fg, bg, linecolor, w, h)
    if palette:
        halfhalfditherimage(image3, w, h, palette)
    return image3

def randombackgroundimage(w, h, palette=None, tileable=True):
    r = random.randint(0, 6)
    if r == 0:
        return randomhatchimage(w, h, palette, tileable=tileable)
    elif r == 1:
        return randomcheckimage(w, h, palette, tileable=tileable)
    elif r == 2:
        return _randomboxesimage(
            w, h, palette, tileable=tileable, fancy=(random.randint(0, 3) != 0)
        )
    elif r == 3:
        return _randomgradientfill(w, h, palette, tileable=tileable)
    elif r == 4:
        return _randomsimpleargyle(w, h, palette, tileable=tileable)
    elif r == 5:
        return _randomshadedboxesimage(w, h, palette, tileable=tileable)
    else:
        return _randombrushednoiseimage(w, h, palette, tileable=tileable)

def monochromeFromThreeGrays(image, width, height):
    # Input image uses only three colors: (0,0,0),(128,128,128),(255,255,255)
    # Turns the image into a black-and-white image, with middle gray dithered.
    image = [x for x in image]
    dithertograyimage(image, width, height, [0, 255])
    return image

def randomPalettedFromThreeGrays(image, width, height, palette=None):
    # Input image uses only three colors: (0,0,0),(128,128,128),(255,255,255)
    # Default for palette is VGA palette (classiccolors())
    image = [x for x in image]
    if not palette:
        palette = classiccolors()
    cc = paletteandhalfhalf(palette)
    endColor = random.choice(palette)  # choose color in 'palette' at random
    r = random.randint(0, 99)
    colors = [[] for i in range(256)]
    # Random beginning color
    if r < 40:
        colors[0] = palette[_nearest_rgb(palette, [0, 0, 0])]
    elif r < 80:
        colors[0] = palette[_nearest_rgb(palette, [255, 255, 255])]
    else:
        colors[0] = random.choice(palette)
    middleColor = cc[
        _nearest_rgb(cc, [(a + b) // 2 for a, b in zip(colors[0], endColor)])
    ]
    colors[128] = middleColor
    colors[255] = endColor
    graymap(image, width, height, colors)
    halfhalfditherimage(image, width, height, palette)
    return image

def randomColorization(palette=None):
    # Generates a random colorization gradient
    # Random beginning color.  Palette is optional;
    # if not None (the default), the beginning and end colors are limited
    # to those in the given palette.
    colors = [[] for i in range(256)]
    r = random.randint(0, 99)
    if r < 40:
        colors[0] = palette[_nearest_rgb(palette, [0, 0, 0])] if palette else [0, 0, 0]
    elif r < 80:
        colors[0] = (
            palette[_nearest_rgb(palette, [255, 255, 255])]
            if palette
            else [255, 255, 255]
        )
    else:
        colors[0] = (
            random.choice(palette)
            if palette
            else [random.randint(0, 255) for i in range(3)]
        )
    # Random end color
    colors[255] = (
        random.choice(palette)
        if palette
        else [random.randint(0, 255) for i in range(3)]
    )
    for i in range(1, 255):
        colors[i] = [a + ((b - a) * i // 255) for a, b in zip(colors[0], colors[255])]
    return colors

def vgaVariantsFromThreeGrays(image, width, height):
    # Input image uses only three colors: (0,0,0),(128,128,128),(255,255,255)
    colors = [[] for i in range(256)]
    colors[0] = [0, 0, 0]
    colors[128] = [128, 0, 0]
    colors[255] = [255, 0, 0]
    red = graymap([x for x in image], width, height, colors)
    colors[128] = [0, 128, 0]
    colors[255] = [0, 255, 0]
    green = graymap([x for x in image], width, height, colors)
    colors[128] = [0, 0, 128]
    colors[255] = [0, 0, 255]
    blue = graymap([x for x in image], width, height, colors)
    colors[128] = [128, 128, 0]
    colors[255] = [255, 255, 0]
    yellow = graymap([x for x in image], width, height, colors)
    colors[128] = [0, 128, 128]
    colors[255] = [0, 255, 255]
    cyan = graymap([x for x in image], width, height, colors)
    colors[128] = [128, 0, 128]
    colors[255] = [255, 0, 255]
    magenta = graymap([x for x in image], width, height, colors)
    colors[0] = [0, 0, 0]
    colors[128] = [192, 192, 192]
    colors[255] = [255, 255, 255]
    lightgray = graymap([x for x in image], width, height, colors)
    colors[0] = [128, 128, 128]
    colors[128] = [192, 192, 192]
    colors[255] = [255, 255, 255]
    light = graymap([x for x in image], width, height, colors)
    colors[0] = [0, 0, 0]
    colors[128] = [128, 128, 128]
    colors[255] = [192, 192, 192]
    dark = graymap([x for x in image], width, height, colors)
    return {
        "gray": [x for x in image],
        "red": red,
        "green": green,
        "blue": blue,
        "yellow": yellow,
        "cyan": cyan,
        "magenta": magenta,
        "lightgray": lightgray,
        "light": light,
        "dark": dark,
    }

def vgaVariantsFromFourGrays(image, width, height):
    # Input image uses only four colors: (0,0,0),(128,128,128),(192,192,192),(255,255,255)
    colors = [[] for i in range(256)]
    colors[0] = [0, 0, 0]
    colors[255] = [255, 255, 255]
    colors[128] = [128, 0, 0]
    colors[192] = [255, 0, 0]
    red = graymap([x for x in image], width, height, colors)
    colors[128] = [0, 128, 0]
    colors[192] = [0, 255, 0]
    green = graymap([x for x in image], width, height, colors)
    colors[128] = [0, 0, 128]
    colors[192] = [0, 0, 255]
    blue = graymap([x for x in image], width, height, colors)
    colors[128] = [128, 128, 0]
    colors[192] = [255, 255, 0]
    yellow = graymap([x for x in image], width, height, colors)
    colors[128] = [0, 128, 128]
    colors[192] = [0, 255, 255]
    cyan = graymap([x for x in image], width, height, colors)
    colors[128] = [128, 0, 128]
    colors[192] = [255, 0, 255]
    magenta = graymap([x for x in image], width, height, colors)
    colors[0] = [128, 128, 128]
    colors[128] = [192, 192, 192]
    colors[192] = [255, 255, 255]
    colors[255] = [255, 255, 255]
    light = graymap([x for x in image], width, height, colors)
    return {
        "gray": [x for x in image],
        "red": red,
        "green": green,
        "blue": blue,
        "yellow": yellow,
        "cyan": cyan,
        "magenta": magenta,
        "light": light,
    }

# palette generation

def _writeu16(ff, x):  # big endian write of 16-bit value
    ff.write(bytes([(x >> 8) & 0xFF, (x) & 0xFF]))

def _writeu32(ff, x):  # big endian write of 32-bit value
    ff.write(bytes([(x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, (x) & 0xFF]))

def _writeu16le(ff, x):  # little endian write of 16-bit value
    ff.write(bytes([(x) & 0xFF, (x >> 8) & 0xFF]))

def _writeu32le(ff, x):  # big endian write of 32-bit value
    ff.write(bytes([(x) & 0xFF, (x >> 8) & 0xFF, (x >> 16) & 0xFF, (x >> 24) & 0xFF]))

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
    if name and "\n" in name:
        raise ValueError
    if (not palette) or len(palette) > 512:
        raise ValueError
    # Microsoft palette
    ff = open(f + ".pal", "xb" if checkIfExists else "wb")
    ff.write(bytes("RIFF", "utf-8"))
    size = 4 * len(palette) + 0x10
    _writeu32le(ff, size)
    ff.write(bytes("PAL ", "utf-8"))
    ff.write(bytes("data", "utf-8"))
    size = 4 * len(palette) + 4
    _writeu32le(ff, size)
    _writeu16le(ff, 0x300)
    _writeu16le(ff, len(palette))
    for c in palette:
        ff.write(bytes([c[0] & 0xFF, c[1] & 0xFF, c[2] & 0xFF, 2]))
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
