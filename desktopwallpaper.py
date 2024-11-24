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
# to the public domain or under the Unlicense) to generate tileable—
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
import io

def _listdir(p):
    return [os.path.abspath(p + "/" + x) for x in os.listdir(p)]

_DitherMatrix4x4 = [  # Bayer 4x4 ordered dither matrix
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

_DitherMatrix = [  # Bayer 8x8 ordered dither matrix
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

# Returns an array of the 216 colors of the "safety palette", also known as the
# "Web safe" palette.  The "safety palette" consists of 216 colors that are
# uniformly spaced in the red&ndash;green&ndash;blue color cube.  Robert Hess's
# article "[The Safety Palette](https://learn.microsoft.com/en-us/previous-versions/ms976419(v=msdn.10))",
# 1996, described the advantage that images that use only colors in this palette
# won't dither when displayed by Web browsers on displays that can show up to 256
# colors at once. (See also [**Wikipedia**](http://en.wikipedia.org/wiki/Web_colors).
# Dithering is the scattering of colors in a limited set to simulate colors
# outside that set.)
# Each element in the return value is a color in the form of a 3-element array of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
def websafecolors():
    colors = []
    for r in range(6):
        for g in range(6):
            for b in range(6):
                colors.append([r * 51, g * 51, b * 51])
    return colors

# Returns an array of the 64 colors displayable by EGA (extended graphics adapter) displays
# Each element in the return value is a color in the form of a 3-element array of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
def egacolors():
    colors = []
    for r in range(4):
        for g in range(4):
            for b in range(4):
                colors.append([r * 85, g * 85, b * 85])
    return colors

# Canonical 16-color CGA palette
# see also: https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/
# Each element in the return value is a color in the form of a 3-element array of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
def cgacolors():
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

# 16-color VGA palette
def classiccolors():
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

# 8-color palette where each color opponent is 0 or 255
# Each element in the return value is a color in the form of a 3-element array of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
def ega8colors():
    return [
        [0, 0, 0],
        [255, 0, 0],
        [0, 255, 0],
        [0, 0, 255],
        [255, 0, 255],
        [0, 255, 255],
        [255, 255, 0],
        [255, 255, 255],
    ]

# Colors in classiccolors() and their "half-and-half" versions.
# Each element in the return value is a color in the form of a 3-element array of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
def classiccolors2():
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

# Returns an array containing the colors in the given palette plus their
# "half-and half" versions.
# Each element in the return value is a color in the form of a 3-element array of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
def paletteandhalfhalf(palette):
    ret = [
        [k & 0xFF, (k >> 8) & 0xFF, (k >> 16) & 0xFF]
        for k in _getdithercolors(palette).keys()
    ]
    ret.sort()
    return ret

# Gets the "half-and half" versions of colors in the given palette.
def _getdithercolors(palette):
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
    cdcolors = _getdithercolors(palette)
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
# palette to a gradient starting at rgb1 for grayscale level 0 (a 3-element array of the red,
# green, and blue components in that order; e.g., [2,10,255] where each
# component is from 0 through 255) and ending at rgb2 for grayscale level 255 (same format as rgb1).
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

# ImageMagick command for clearing an image with a solid color.
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

# ImageMagick command.
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

# ImageMagick command.
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

# ImageMagick command to render an input image described in 'versatilePattern' in an unavailable appearance.
# If 'buttonShadow' is darker than 'buttonHighlight' (as is the default), then this method will result in
# the image's appearing engraved, that is, sunken onto the background, given the existence of a light
# source that shines from the upper left corner.
# If 'buttonShadow' is lighter than 'buttonHighlight', the image instead appears embossed, that is, raised above the
# background, given the light source just described.
# If 'drawShiftedImageOver' is True, the image drawn in the 'buttonShadow' color is drawn above the
# image drawn in the 'buttonHighlight' color.
def unavailable(
    bgColor=None, buttonShadow=None, buttonHighlight=None, drawShiftedImageOver=False
):
    if not bgColor:
        bgColor = [192, 192, 192]
    if not buttonShadow:
        buttonShadow = [128, 128, 128]
    if not buttonHighlight:
        buttonHighlight = [255, 255, 255]
    mpre = "mpr:engrave"
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

# ImageMagick command to emboss an input image described in 'versatilePattern' into a 3-color (black/gray/white) image.
# If 'fgColor' is lighter than 'hiltColor' (as is the default), then embossing an outline will result in its
# appearing raised above the background, given the existence of a light source that shines from the upper
# left corner.
# If 'fgColor' is darker than 'hiltColor', the outline instead appears engraved, that is, sunken into the
# background, given the light source just described.
# In this description, lower-intensity values are generally "darker", higher-intensity values "lighter".
def emboss(bgColor=None, fgColor=None, hiltColor=None):
    return unavailable(
        bgColor if bgColor else [128, 128, 128],
        hiltColor if hiltColor else [255, 255, 255],
        fgColor if fgColor else [0, 0, 0],
        True,
    )

# ImageMagick command.
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

# ImageMagick command for setting a foreground pattern, whose black parts
# are set in the given foreground color, on a background that can optionally
# be colored.
# 'fgcolor' and 'bgcolor' are the foreground and background color, respectively.
# The input image this command will be applied to is assumed to be an SVG file
# which must be black (all zeros) in the nontransparent areas (given that ImageMagick renders the
# SVG, by default, on a background colored white, or (255,255,255)) or a raster image with only
# gray tones, where the closer the gray level is to 0, the less transparent.
# 'bgcolor' can be None so that an alpha
# background is used.  Each color is a
# 3-element array of the red, green, and blue components in that order; e.g.,
# [2,10,255] where each component is from 0 through 255.
# Inspired by the technique for generating backgrounds in heropatterns.com.
def versatilePattern(fgcolor, bgcolor=None):
    return [
        "-negate",
        "-background",
        "#%02x%02x%02x" % (int(fgcolor[0]), int(fgcolor[1]), int(fgcolor[2])),
        "-alpha",
        "shape",
    ] + backgroundColorUnder(bgcolor)

# ImageMagick command for setting a light gray (192,192,192) foreground pattern on a white (255,255,255) background.
def lightmodePattern():
    return versatilePattern([192, 192, 192], [255, 255, 255])

# ImageMagick command for setting a gray (128,128,128) foreground pattern on a black (0,0,0) background.
def darkmodePattern():
    return versatilePattern([128, 128, 128], [0, 0, 0])

# ImageMagick command.
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

# ImageMagick command.
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

# ImageMagick command to generate a Pmm wallpaper group tiling pattern.
# This command can be applied to arbitrary images to render them
# tileable.
# NOTE: "-append" is a vertical append; "+append" is a horizontal append;
# "-flip" reverses the row order; "-flop" reverses the column order.
def tileable():
    return (
        ["(", "+clone", "-flip"]
        + _chopBeforeVAppendArray()
        + [")", "-append", "(", "+clone", "-flop"]
        + _chopBeforeHAppendArray()
        + [")", "+append"]
    )

# ImageMagick command to generate a P2 wallpaper group tiling pattern.
# For best results, the command should be applied to images whose
# last row's first half is a mirror of its second half.
def groupP2():
    return (
        ["(", "+clone", "-flip", "-flop"] + _chopBeforeVAppendArray() + [")", "-append"]
    )

# ImageMagick command to generate a Pm wallpaper group tiling pattern.
def groupPm():
    return ["(", "+clone", "-flop"] + _chopBeforeHAppendArray() + [")", "+append"]

# ImageMagick command to generate a Pg wallpaper group tiling pattern.
# For best results, the command should be applied to images whose
# last column's first half is a mirror of its second half.
def groupPg():
    return ["(", "+clone", "-flip"] + _chopBeforeVAppendArray() + [")", "-append"]

# ImageMagick command to generate a Pgg wallpaper group tiling pattern.
# For best results, the command should be applied to images whose
# last row's and last column's first half is a mirror of its
# second half.
def groupPgg():
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

# ImageMagick command to generate a Cmm wallpaper group tiling pattern.
# For best results, the command should be applied to images whose
# last row's and last column's first half is a mirror of its
# second half.
def groupCmm():
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

# ImageMagick command to put a background color behind the input image.
# 'bgcolor' is the background color,
# either None or a 3-element array of the red,
# green, and blue components in that order; e.g., [2,10,255] where each
# component is from 0 through 255; default is None, or no background color.
def backgroundColorUnder(bgcolor=None):
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

# ImageMagick command to generate a diamond tiling pattern (or a brick tiling
# pattern if the image the command is applied to has only its top half
# or its bottom half drawn).  For best results, the command should be applied
# to images with an even width and height.
def diamondTiling():
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

# kind=0: image drawn in middle and padded
# kind=1: brick drawn at top
# kind=2: brick drawn at left
def diamondTiled(bgcolor=None, kind=0):
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

# ImageMagick command to generate a Pmg wallpaper group tiling pattern.
# For best results, the command should be applied to images whose
# last column's first half is a mirror of its
# second half.
def groupPmg():
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

# ImageMagick command to generate a brushed metal texture from a noise image.
# A brushed metal texture was featured in Mac OS X Panther and
# Tiger (10.3, 10.4) and other Apple products
# around the time of either OS's release.
def brushedmetal():
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
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

# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
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

# Images have the same format returned by the _blankimage_ method with alpha=True.
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
    newimages = [splitmask(img, width, height) for img in images]
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

# Images have the same format returned by the _blankimage_ method with alpha=False.
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

# Reads an OS/2 icon, mouse pointer (cursor), bitmap, or bitmap array.
# OS/2 icons have the '.ico' file extension; OS/2 cursors, '.ptr'; and
# OS/2 bitmaps, '.bmp'.
# Returns a list of five-element lists, representing the decoded images
# in the order in which they were read.  If an icon, pointer, or
# bitmap could not be read, the value None takes the place of the
# corresponding five-element list.
# Each five-element list in the returned list contains the image,
# its width, its height, its hot spot X coordinate, and its hot spot
# Y coordinate in that order. The image has the same format returned by the
# _blankimage_ method with alpha=True. (The hot spot is the point in the image
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

# Returns a list of the unique colors in an image (disregarding
# the alpha channel, if any).  The return value has the same
# format returned in the _reados2palette_ function.
def uniquecolors(image, width, height, alpha=False):
    colors = {}
    bytesperpixel = 4 if alpha else 3
    for i in range(width * height):
        c = (
            image[i * bytesperpixel]
            | (image[i * bytesperpixel + 1] << 8)
            | (image[i * bytesperpixel + 2] << 16)
        )
        colors[c] = True
    ck = [[k & 0xFF, (k >> 8) & 0xFF, (k >> 16) & 0xFF] for k in colors.keys()]
    ck.sort()
    return ck

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
    bl = blankimage(width, height, alpha=True)
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
            setpixelbgralpha(bl, width, height, x, y, px)
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
        ci = blankimage(cw, ch, alpha=True)
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
                setpixelbgralpha(ci, cw, ch, x, y, col + alpha)
        ret = ci
        width = cw
        height = ch
    elif isColor:
        cw = colormaskhdr[1]
        ch = colormaskhdr[2]
        bpp = colormaskhdr[4]
        bl = blankimage(cw, ch, alpha=True)
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
                setpixelbgralpha(bl, cw, ch, x, y, px)
        width = cw
        height = ch
        ret = bl
    else:
        trueheight = andmaskhdr[2] // 2
        bl = blankimage(andmaskhdr[1], trueheight, alpha=True)
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
                setpixelalpha(bl, andmaskhdr[1], trueheight, x, y, px)
        width = andmaskhdr[1]
        height = trueheight
        ret = bl
    return [ret, width, height, hotspotX, hotspotY]

# Image has the same format returned by the _blankimage_ method with alpha=False.
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
    images = [blankimage(width, height) for i in range(32)]
    for i in range(32):
        imageblit(
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
            a, b = interlace(images[i], width, height)
            images[i] = a if i % 2 == 0 else b
        if len(images[i]) != width * outputHeight * 3:
            raise ValueError
    writeavi(destParallax, images, width, outputHeight, fps=fps)

# Generates an AVI video file consisting of images arranged
# in a row or column.  If the source image's width
# is greater than its height, then each frame's height
# is the same as the source image's; if less, each
# frame's width.
# The source image has the same format returned by the
# _blankimage_ method with alpha=False.
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
        dst = blankimage(animWidth, animHeight)
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

def simplebox(image, width, height, color, x0, y0, x1, y1, wraparound=True):
    borderedbox(
        image, width, height, None, color, color, x0, y0, x1, y1, wraparound=wraparound
    )

# Draw a wraparound hatched box on an image.
# Image has the same format returned by the _blankimage_ method with alpha=False.
# 'color' is the color of the hatch, drawn on every "black" pixel (defined below)
# in the pattern's tiling.
# 'pattern' is an 8-element array with integers in the interval [0,255].
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

# Apply a binary raster operation to two 8-bit source and destination
# color channels.
# 'dst' and 'src' are each 8-bit integers (from 0 through 255).
# 'rop' is a 4-bit binary raster operation (from 0 through 15).
def _applyrop(dst, src, rop):
    # Assuming the source and destination
    # images are black-and-white (where 0-bits represent black,
    # and 1-bits white), the result of
    # each raster operation is as follows:
    match rop:
        case 12:
            # Also known as "source copy".
            # Copy source to destination.
            return src
        case 10:
            # Also known as "no-op".
            # Leave destination unchanged.
            return dst
        case 0:
            # Turn destination black.
            return 0
        case 1:
            # Also known as "not source erase" or "not merge pen".
            # Inversion of operation code 14.
            # Result's white area is the intersection of black areas
            # of the source and destination.  That is, the result pixel
            # is white only if both the source and destination
            # pixels are black.  Alternatively, the black area is
            # the union of white areas of the source and destination.
            # Alternatively, if the source is black-and-white and the
            # destination is colored: The white area of the source is
            # copied to the destination and turned black there, and
            # if the source pixel is black, the destination color is
            # inverted.
            return (dst | src) ^ 0xFF
        case 2:
            # Also known as "mask not pen".
            # Inversion of operation code 13.
            # The result pixel is white only if the source pixel is black
            # and the destination pixel is white.
            # The result pixel is black only if the source pixel is white,
            # the destination pixel is black, or both.
            return dst & (src ^ 0xFF)
        case 3:
            # Also known as "not source copy" or "not copy pen".
            # Copy inverted source colors to destination.
            # If source and destination are black-and-white:
            # If source pixel is black, white is copied
            # to the destination, and vice versa.
            return src ^ 0xFF
        case 4:
            # Also known as "source erase" or "mask pen not".
            # Inversion of operation code 11.
            # The result pixel is white only if the source pixel is white
            # and the destination pixel is black.
            # The result pixel is black only if the source pixel is black,
            # the destination pixel is white, or both.
            return src & (dst ^ 0xFF)
        case 5:
            # Also known as "destination invert".
            # Invert colors of destination.
            # If destination is black-and-white, turns
            # white destination pixels black and vice versa.
            return dst ^ 0xFF
        case 6:
            # Also known as "source invert" or "XOR pen".
            # The result pixel is white if the source pixel is black
            # and the destination pixel is white or vice versa, and the result
            # pixel is black if the source and destination pixels are
            # the same.  Alternatively, if the source and destination
            # are colored: Where the source color is black, the destination
            # is left unchanged, and where the _destination_ color is
            # black, the source color is copied to the destination.
            return dst ^ src
        case 7:
            # Also known as "not mask pen".
            # Result's white area is the intersection of white areas
            # of the source and destination.  That is, the result pixel
            # is white only if the source and destination pixels are
            # both white.  Alternatively, the black area is the union
            # of black areas of the source and destination.
            # Alternatively, if the source is black-and-white and the
            # destination is colored, the black area of the source is
            # copied to the destination and turned white there, and where
            # the source pixel color is white, the destination color is
            # inverted.
            return (dst & src) ^ 0xFF
        case 8:
            # Also known as "source AND".
            # Result's white area is the intersection of white areas
            # of the source and destination.  That is, the result pixel
            # is white only if the source and destination pixels are
            # both white.  Alternatively, the black area is the union
            # of black areas of the source and destination.
            # Alternatively, if the source is black-and-white and the
            # destination is colored, the black area of the source is
            # copied to the destination (and left black there).
            return dst & src
        case 9:
            # Also known as "not XOR pen".
            # Inversion of operation code 6.
            # The result pixel is black if the source pixel is black
            # and the destination is white or vice versa, and the result
            # pixel is white if the source and destination pixels are
            # the same. Alternatively, if the source and destination
            # are colored: Where the source color is white, the destination
            # is left unchanged, and where the _destination_ color is
            # white, the source color is copied to the destination.
            return (dst ^ src) ^ 0xFF
        case 11:
            # Also known as "merge paint" or "merge not pen".
            # Inversion of operation code 4.
            # The result pixel is black only if the source pixel is white
            # and the destination pixel is black.
            # The result pixel is white only if the source pixel is black,
            # the destination pixel is white, or both.
            return (src & (dst ^ 0xFF)) ^ 0xFF
        case 13:
            # Also known as "merge pen not".
            # Inversion of operation code 2.
            # The result pixel is black only if the source pixel is black
            # and the destination pixel is white.
            # The result pixel is white only if the source pixel is white,
            # the destination pixel is black, or both.
            return (dst & (src ^ 0xFF)) ^ 0xFF
        case 14:
            # Also known as "source paint" or "merge pen".
            # Result's white area is the union of white areas
            # of the source and destination.  That is, the result pixel
            # is white only if the source pixel, the destination
            # pixel, or both are white.  Alternatively, the black area is
            # the intersection of black areas of the source and destination.
            # Alternatively, if the source is black-and-white and the
            # destination is colored, the white area of the source is
            # copied to the destination (and left white there).
            return dst | src
        case 15:
            # Turn destination white.
            return 0xFF
        case _:
            # Undefined raster operation.
            return 0

# Draw a wraparound copy of an image on another image.
# 'dstimage' and 'srcimage' are the destination and source images.
# 'pattern' is a brush pattern image (also known as a stipple).
# 'srcimage', 'maskimage', and 'patternimage' are optional.
# 'dstimage', 'srcimage', 'patternimage', and 'maskimage', to the extent given,
# have the same format returned by the _blankimage_ method with the given value of 'alpha'.
# The default value for 'alpha' is False, and the alpha channel of the images, if any, is ignored,
# so that the images are treated as having no transparent or translucent (semitransparent) pixels.
# (Windows's graphical device interface [GDI] supports transparent
# pixels in brush patterns, but only for brushes
# with predefined hatch patterns and only in the gaps between hatch marks; in
# bit block transfer operations such as BitBlt, these transparent pixels are
# filled with the background color whether the background mode is
# transparent or opaque; in line and shape drawing operations (which this
# method doesn't belong in), if the background mode is transparent, only
# the nontransparent pixels are drawn and affected by raster operations.)
# 'patternOrgX' and 'patternOrgY' are offsets from the destination's top left
# corner where the top left corner of the brush pattern image would
# be drawn if a repetition of the brush pattern were to be drawn across the
# whole destination image.  The default for both parameters is 0.
# 'x0src' and 'y0src' are offsets from the destination image's top left corner
# where the source image's top left corner will be drawn.
# 'x0mask' and 'y0mask' are offsets from the source image's top left corner
# and correspond to pixels in the source image.
# 'ropForeground' is a foreground ternary raster operation between the bits of the
# destination, those of the source, and those of the brush pattern; the low 4 bits give the binary raster
# operation used where the pattern bit is 0 or there is no pattern or an empty pattern;
# the high 4 bits, where the pattern
# bit is 1. 'ropForeground' is used where the mask bit is 1 or there is no mask
# or an empty mask. 'ropBackground' is the same as 'ropForeground', but for the
# background (used where the mask bit is 0 rather than 1).
# In turn, a binary raster operation is a 4-bit value that tells how to combine
# the bits of the destination with those of the source; the low 2 bits give the unary
# raster operation used where the source bit is 0 or there is no source or an empty
# source; the high 2 bits, where the source
# bit is 1.  In turn, a unary raster operation tells how to change each bit
# of the destination: if the operation is 0, the result is 0; if 1, the destination
# bit is inverted (the result is 1 if the destination bit is 0, and vice versa);
# if 2, the result is the destination bit (the destination is left unchanged);
# if 3, the result is 1. For example, suppose the source and
# destination images are black-and-white (where 0-bits represent black, and 1-bits white), and
# suppose the binary raster operation is 6 (or the ternary raster operation is 0x66).
# Then, where the source is white (source bit is 1), the destination color is inverted
# (since the high 2 bits give 1), and where the source is black (source bit is 0), the
# destination is left unchanged (since the low 2 bits give 2).
# The default for 'ropForeground' is 0xCC (copy the source to the destination), and the
# default for 'ropBackground' is 0xAA (leave destination unchanged).
# 'maskimage' is ideally a monochrome image (every pixel's bits are either all zeros
# [black] or all ones [white]), but it doesn't have to be.
# 'dstimage' may be the same as 'srcimage', 'patternimage', or 'maskimage',
# and the source and destination rectangles may overlap.
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
    alpha=False,
):
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
        # Destination left unchanged
        return
    if srcimage is dstimage or patternimage is dstimage or maskimage is dstimage:
        # Avoid overlapping source/pattern/mask with destination
        return imageblitex(
            dstimage,
            dstwidth,
            dstheight,
            (
                srcimage
                if srcimage is not dstimage
                else ([x for x in srcimage] if srcimage else None)
            ),
            srcwidth,
            srcheight,
            x0src,
            y0src,
            transcolor,
            (
                patternimage
                if patternimage is not dstimage
                else ([x for x in patternimage] if patternimage else None)
            ),
            patternwidth,
            patternheight,
            patternOrgX,
            patternOrgY,
            (
                maskimage
                if maskimage is not dstimage
                else ([x for x in maskimage] if maskimage else None)
            ),
            maskwidth,
            maskheight,
            x0mask,
            y0mask,
            ropForeground,
            ropBackground,
            wraparound,
            alpha=alpha,
        )
    pixelsize = 4 if alpha else 3
    for y in range(y1 - y0):
        dy = y0 + y
        if wraparound:
            dy %= dstheight
        if (not wraparound) and dy < 0 or dy >= dstheight:
            continue
        sy = (y0src + y) * srcwidth * pixelsize if srcimage else 0
        paty = (
            (((dy - patternOrgY) % patternheight) * patternwidth * pixelsize)
            if patternimage
            else 0
        )
        masky = (y0mask + y) * maskwidth * pixelsize if maskimage else 0
        dy = dy * dstwidth * pixelsize
        for x in range(x1 - x0):
            dx = x0 + x
            if wraparound:
                dx %= dstwidth
            if (not wraparound) and dx < 0 or dx >= dstwidth:
                continue
            dstpos = dy + dx * pixelsize
            srcpos = sy + (x0src + x) * pixelsize
            patpos = (
                (paty + ((dx - patternOrgX) % patternwidth) * pixelsize)
                if patternimage
                else 0
            )
            maskpos = masky + (x0mask + x) * pixelsize if maskimage else 0
            for i in range(3):
                s1 = srcimage[srcpos + i] if srcimage else 0
                d1 = dstimage[dstpos + i] if dstimage else 0
                p1 = patternimage[patpos + i] if patternimage else 0
                m1 = maskimage[maskpos + i] if maskimage else 0
                sdl = _applyrop(d1, s1, ropForeground & 0xF)
                sdh = _applyrop(d1, s1, (ropForeground >> 4) & 0xF)
                sdp = (p1 & sdh) ^ ((~p1) & sdl)
                if maskimage:
                    sdl = _applyrop(d1, s1, ropBackground & 0xF)
                    sdh = _applyrop(d1, s1, (ropBackground >> 4) & 0xF)
                    sdpb = (p1 & sdh) ^ ((~p1) & sdl)
                    sdp = (m1 & sdp) ^ ((~m1) & sdpb)
                dstimage[dstpos + i] = sdp

# All images have the same format returned by the _blankimage_ method with the given value of 'alpha'.
# The default value for 'alpha' is False, and the alpha channel of the images, if any, is ignored,
# so that the images are treated as having no transparent or translucent (semitransparent) pixels.
# 'ropForeground' and 'ropBackground' are as in imageblitex, except that
# 'ropForeground' is used where the source color (in its red, green, and blue components) is not 'transcolor' or if
# 'transcolor' is None; 'ropBackground' is used elsewhere.
# The default for 'ropForeground' is 0xCC (copy the source to the destination), and the
# default for 'ropBackground' is 0xAA (leave destination unchanged).
# For more on raster operations, see the documentation for 'imageblitex'.
# 'dstimage' may be the same as 'srcimage' or 'patternimage',
# and the source and destination rectangles may overlap.
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
    alpha=False,
):
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
            alpha=alpha,
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
        # Destination left unchanged
        return
    if srcimage is dstimage or patternimage is dstimage:
        # Avoid overlapping source/pattern with destination
        return imagetransblit(
            dstimage,
            dstwidth,
            dstheight,
            (
                srcimage
                if srcimage is not dstimage
                else ([x for x in srcimage] if srcimage else None)
            ),
            srcwidth,
            srcheight,
            x0src,
            y0src,
            (
                patternimage
                if patternimage is not dstimage
                else ([x for x in patternimage] if patternimage else None)
            ),
            patternwidth,
            patternheight,
            patternOrgX,
            patternOrgY,
            ropForeground,
            ropBackground,
            wraparound,
        )
    pixelsize = 4 if alpha else 3
    for y in range(y1 - y0):
        dy = y0 + y
        if wraparound:
            dy %= dstheight
        if (not wraparound) and dy < 0 or dy >= dstheight:
            continue
        sy = (y0src + y) * srcwidth * pixelsize
        paty = ((dy + patternOrgY) % patternheight) * pixelsize if patternimage else 0
        dy = dy * dstwidth * pixelsize
        for x in range(x1 - x0):
            dx = x0 + x
            if wraparound:
                dx %= dstwidth
            if (not wraparound) and dx < 0 or dx >= dstwidth:
                continue
            dstpos = dy + dx * pixelsize
            srcpos = sy + (x0src + x) * pixelsize
            patpos = (
                paty + ((dx + patternOrgX) % patternwidth) * pixelsize
                if patternimage
                else 0
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
                sdh = _applyrop(d1, s1, (ropForeground >> 4) & 0xF)
                sdp = (p1 & sdh) ^ ((~p1) & sdl)
                sdl = _applyrop(d1, s1, ropBackground & 0xF)
                sdh = _applyrop(d1, s1, (ropBackground >> 4) & 0xF)
                sdpb = (p1 & sdh) ^ ((~p1) & sdl)
                sdp = (m1 & sdp) ^ ((~m1) & sdpb)
                dstimage[dstpos + i] = sdp

# 'dstimage' and 'srcimage' have the same format returned by the _blankimage_ method with alpha=False.
# 'rasterOp' is a binary raster operation between the bits of the
# destination and those of the source.  For more on binary raster
# operations, see the documentation for _imageblitex_.
def imageblit(
    dstimage,
    dstwidth,
    dstheight,
    x0,
    y0,
    srcimage,
    srcwidth,
    srcheight,
    wraparound=True,
    rasterOp=12,
):
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

# 'srcimage' has the same format returned by the _blankimage_ method with alpha=False.
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
                x * srcwidth,
                y * srcheight,
                srcimage,
                srcwidth,
                srcheight,
                wraparound=False,
            )
    return image

# Images in 'sourceImages' have the same format returned by the _blankimage_ method with alpha=False.
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
                x * srcwidth,
                y * srcheight,
                random.choice(sourceImages),
                srcwidth,
                srcheight,
            )
    return image

# Draws a box filled with a transparent vertical hatch pattern.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def verthatchedbox(image, width, height, color, x0, y0, x1, y1):
    pattern = [0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA]
    hatchedbox(image, width, height, color, pattern, x0, y0, x1, y1)

# Draws a box filled with a transparent horizontal hatch pattern.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def horizhatchedbox(image, width, height, color, x0, y0, x1, y1):
    pattern = [0xFF, 0, 0xFF, 0, 0xFF, 0, 0xFF, 0]
    hatchedbox(image, width, height, color, pattern, x0, y0, x1, y1)

# Image has the same format returned by the _blankimage_ method with alpha=False.
def shadowedborderedbox(
    image, width, height, border, shadow, color1, color2, x0, y0, x1, y1
):
    # Draw box's shadow
    pattern = [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55]
    hatchedbox(image, width, height, shadow, pattern, x0 + 4, y0 + 4, x1 + 4, y1 + 4)
    borderedbox(image, width, height, border, color1, color2, x0, y0, x1, y1)

# Creates a brush pattern (also known as a stipple) with width 2 and height equal to 'spacing'*2.
# The image returned by this method has the same format returned by the _blankimage_ method with alpha=False.
# Each color occurs equally in the image.
# Designed for drawing filled, unstroked, opaque vector paths,
# generally vector paths of an abstract design or symbol.
# 'spacing' is the spacing from the beginning of one horizontal hatch
# to the beginning of the next. Hatches are colored with color1.  Default is 3.
# 'hatchsize' is the thickness of each hatch line. Default is 1.
def styledbrush1(color1, color2, color3, spacing=3, hatchsize=1):
    if hatchsize < 0 or spacing <= 0:
        raise ValueError
    width = 2
    height = spacing * 2
    ret = blankimage(width, height)
    for y in range(height):
        for x in range(width):
            if y % spacing < hatchsize:
                setpixel(ret, width, height, x, y, color1)  # hatch
            elif (x + y) % 2 == 0:
                setpixel(ret, width, height, x, y, color2)  # dither color 1
            else:
                setpixel(ret, width, height, x, y, color3)  # dither color 2
    return ret

# Creates a brush pattern (also known as a stipple) with width 2 and height 8.
# color1 occurs on 1/2 the brush pattern; the other
# colors on 1/4 each.
# The image returned by this method has the same format returned by the _blankimage_ method with alpha=False.
# Designed for drawing filled, unstroked, opaque vector paths,
# generally vector paths of an abstract design or symbol.
def styledbrush2(color1, color2, color3):
    return styledbrush1(color1, color2, color3, spacing=4, hatchsize=2)

# Image has the same format returned by the _blankimage_ method with alpha=False.
# Draw a wraparound box in a gradient fill on an image.
# 'border' is the color of the 1-pixel-thick border. Can be None (so
# that no border is drawn)
# 'gradient' is a list of 256 colors for mapping the 256 possible shades
# of the gradient fill.
def borderedgradientbox(
    image, width, height, border, gradient, contour, x0, y0, x1, y1, wraparound=True
):
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
# Draw a wraparound box in a two-color dithered gradient fill on an image.
# 'border' is the color of the 1-pixel-thick border. Can be None (so
# that no border is drawn)
# 'color1' and 'color2' are the dithered
# versions of the inner color. 'color1' and 'color2' can't be None.
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
                bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                if bdither < c:
                    image[yp + xp * 3] = color2[0]
                    image[yp + xp * 3 + 1] = color2[1]
                    image[yp + xp * 3 + 2] = color2[2]
                else:
                    image[yp + xp * 3] = color1[0]
                    image[yp + xp * 3 + 1] = color1[1]
                    image[yp + xp * 3 + 2] = color1[2]

# Modifies the given 4-byte-per-pixel image by
# converting its 256-level alpha channel to two levels (opaque
# and transparent). Reducing the alpha channel
# this way is also known as stippled or screen-door
# transparency.
# Image has the same format returned by the _blankimage_ method with alpha=True.
# If 'dither' is True, the conversion is done by dithering, that
# is, by scattering opaque and transparent pixels to simulate
# pixels between the two extremes.  If False, the conversion is
# done by thresholding: alpha values 127 or below become 0, and
# alpha values 128 or higher become 255.  Default is False
def alphaToTwoLevel(image, width, height, dither=False):
    i = 0
    for y in range(height):
        for x in range(width):
            a = image[i + 3]
            if a != 0 and a != 255:
                if dither:
                    bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                    a = 255 if bdither < a * 64 // 255 else 0
                    image[i + 3] = a
                else:
                    image[i + 3] = 0 if a <= 127 else 255
            i += 4
    return image

# Splits a 4-byte-per pixel image (four elements per pixel) into a
# color mask and an (inverted) alpha mask, in that order.
# Image has the same format returned by the _blankimage_ method with alpha=True.
# Returns a list of two elements, the color mask and the alpha mask, both
# with the same format returned by the _blankimage_ method with alpha=False.
def splitmask(image, width, height):
    if width * height * 4 != len(image):
        raise ValueError
    img = [0 for _ in range(width * height * 3)]
    mask = [0 for _ in range(width * height * 3)]
    for i in range(width * height):
        if image[i * 4 + 3] == 0:
            # Set color to black for every transparent pixel,
            # to ease the color mask's use as an XOR mask
            # (when every pixel in the alpha mask's bits are all zeros or all ones)
            img[i * 3] = img[i * 3 + 1] = img[i * 3 + 2] = 0
            mask[i * 3] = mask[i * 3 + 1] = mask[i * 3 + 2] = 255
        else:
            img[i * 3] = image[i * 4]
            img[i * 3 + 1] = image[i * 4 + 1]
            img[i * 3 + 2] = image[i * 4 + 2]
            # Invert alpha channel to ease the alpha mask's use as an AND mask
            # (when the bits of every pixel in the mask are all zeros or all ones)
            mask[i * 3] = mask[i * 3 + 1] = mask[i * 3 + 2] = 255 - image[i * 4 + 3]
    return [img, mask]

# Draws a 3D outline over a 4-byte-per-pixel image with transparent
# pixels, assuming a light source from the upper left.
# Image has the same format returned by the _blankimage_ method with alpha=True.
# 'lt' is the light color.  If not given, is [128,128,128].
# 'sh' is the shadow color.  If not given, is [0,0,0].
def outlineimage(image, width, height, lt=None, sh=None):
    for y in range(height):
        for x in range(width):
            xp = (y * width + x) * 4
            # Draw upper left outline gray
            if (
                image[xp + 3] == 255
                and (x == 0 or image[(xp - 4) + 3] != 255)
                or (y == 0 or image[(xp - width * 4) + 3] != 255)
            ):
                image[xp] = lt[0] if lt else 0x80
                image[xp + 1] = lt[1] if lt else 0x80
                image[xp + 2] = lt[2] if lt else 0x80
            # "Then" draw bottom right outline black
            if (
                image[xp + 3] == 255
                and (x == width - 1 or image[(xp + 4) + 3] != 255)
                or (y == height - 1 or image[(xp + width * 4) + 3] != 255)
            ):
                image[xp] = sh[0] if sh else 0x00
                image[xp + 1] = sh[1] if sh else 0x00
                image[xp + 2] = sh[2] if sh else 0x00

# Draw a wraparound dither-colored box on an image.
# Image has the same format returned by the _blankimage_ method with alpha=False.
# 'border' is the color of the 1-pixel-thick border. Can be None (so
# that no border is drawn)
# 'color1' and 'color2' are the dithered
# versions of the inner color. 'color1' and 'color2' can't be None.
def borderedbox(
    image, width, height, border, color1, color2, x0, y0, x1, y1, wraparound=True
):
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

# Split an image into two interlaced versions with half the height.
# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
# The first image should be displayed at even-numbered frames; the second,
# odd-numbered.
def interlace(image, width, height, alpha=False):
    if height % 2 != 0:
        raise ValueError("height must be even")
    bypp = 4 if alpha else 3
    image1 = listsum(
        image[(y * 2) * width * bypp : (y * 2 + 1) * width * bypp]
        for y in range(height // 2)
    )
    image2 = listsum(
        image[(y * 2 + 1) * width * bypp : (y * 2 + 2) * width * bypp]
        for y in range(height // 2)
    )
    return [image1, image2]

# Creates a blank image with 3 or 4 bytes per pixel and the given width, height,
# and fill color.  The image is in the form of a list with a number of
# elements equal to width*height*3 (or width*height*4 if 'alpha' is True).  The
# array is divided into 'height' many rows running from top to bottom. Each row
# is divided into 'width' many pixels (one pixel for each column from left to
# right), with three elements per pixel (or four elements if 'alpha' is True).
# In each pixel, which represents a color at the given row and column, the
# first element is the color's red component; the second, its blue component;
# the third, its red component; the fourth, if present, is the color's alpha
# component or _opacity_ (0 if the color is transparent; 255 if opaque; otherwise,
# the color is translucent or semitransparent).  Each component is an integer
# from 0 through 255.  In this format, lower-intensity values are
# generally "darker", higher-intensity values "lighter", so that [0,0,0,255] (4 bytes per pixel)
# or [0,0,0] (3 bytes per pixel) is "black", and [255,255,255,255] or [255,255,255] is "white".
# If 'color' is None, uses [255,255,255,255], or white.
# If 'alpha' is True, generates a 4-byte-per-pixel image; if False, generates a
# 3-byte-per-pixel image.  The default is False.
def blankimage(width, height, color=None, alpha=False):
    if color and len(color) < (4 if alpha else 3):
        raise ValueError
    # default background is white; default alpha is 255
    image = [255 for i in range(width * height * (4 if alpha else 3))]
    if color:
        for i in range(height * width):
            image[i * 3] = color[0]
            image[i * 3 + 1] = color[1]
            image[i * 3 + 2] = color[2]
            if alpha:
                image[i * 3 + 3] = color[3]
    return image

# Generates a tileable argyle pattern from two images of the
# same size.  The images have the same format returned by the _blankimage_
# method with the given value of 'alpha' (default value for 'alpha' is False).  'backgroundImage' must be tileable if shiftImageBg=False;
# 'foregroundImage' need not be tileable.
# 'expo' is a parameter that determines the shape in the middle of the image,
# and can be any number greater than 0. If 1, the shape resembles a
# diamond; if 2, an ellipse.  Default is 1.
def argyle(foregroundImage, backgroundImage, width, height, expo=1, shiftImageBg=False):
    if expo <= 0:
        raise ValueError
    if shiftImageBg:
        i2 = blankimage(width, height)
        imageblit(
            i2, width, height, width // 2, height // 2, backgroundImage, width, height
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

# Generates a tileable checkerboard pattern using two images of the same size;
# each tile is the whole of one of the source images, and the return value's
# width in pixels is width*columns; its height is height*rows.
# The two images should be tileable.
# The images have the same format returned by the _blankimage_ method with alpha=False.
# The number of columns and of rows must be even and positive.
def checkerboardtile(upperLeftImage, otherImage, width, height, columns=2, rows=2):
    if rows <= 0 or columns <= 0 or rows % 2 == 1 or columns % 2 == 1:
        raise ValueError
    ret = blankimage(width * columns, height * rows)
    for y in range(rows):
        for x in range(columns):
            imageblit(
                ret,
                width * columns,
                height * rows,
                x * width,
                y * height,
                upperLeftImage if (y + x) % 2 == 0 else otherImage,
                width,
                height,
            )
    return ret

# Generates a tileable checkerboard pattern made of parts of two images of the same size;
# the return value has the same width and height as the source images.
# The two images should be tileable.
# The images have the same format returned by the _blankimage_ method with alpha=False.
# The number of columns and of rows must be even and positive.
def checkerboard(upperLeftImage, otherImage, width, height, columns=2, rows=2):
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

# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
def simpleargyle(fgcolor, bgcolor, linecolor, w, h):
    fg = blankimage(w, h, fgcolor)
    bg = blankimage(w, h, bgcolor)
    bg = argyle(fg, bg, w, h)
    linedraw(bg, w, h, linecolor, 0, 0, w, h)
    linedraw(bg, w, h, linecolor, 0, h, w, 0)
    return bg

# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
def doubleargyle(fgcolor1, fgcolor2, bgcolor, linecolor1, linecolor2, w, h):
    f1 = simpleargyle(fgcolor1, bgcolor, linecolor1, w, h)
    f2 = simpleargyle(fgcolor2, bgcolor, linecolor2, w, h)
    return checkerboardtile(f1, f2, w, h)

# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
def simpleargyle2(fgcolor, bgcolor, linecolor, w, h):
    fg = blankimage(w, h, fgcolor)
    bg = blankimage(w, h, bgcolor)
    bg = argyle(fg, bg, w, h)
    linedraw(bg, w, h, linecolor, 2, 0, w + 2, h, wraparound=True)
    linedraw(bg, w, h, linecolor, -2, 0, w - 2, h, wraparound=True)
    linedraw(bg, w, h, linecolor, 2, h, w + 2, 0, wraparound=True)
    linedraw(bg, w, h, linecolor, -2, h, w - 2, 0, wraparound=True)
    return bg

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

# Image has the same format returned by the _blankimage_ method with alpha=False.
# hatchdist - distance from beginning of one vertical hash line to the
# beginning of the next, in pixels.
# hatchthick - thickness in pixels of each vertical hash line.
def drawhatchcolumns(image, width, height, hatchdist=8, hatchthick=1, fgcolor=None):
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
# 'stripesize' is in pixels
# reverse=false: stripe runs from top left to bottom
# right assuming the image's first row is the top row
# reverse=true: stripe runs from top right to bottom
# left
def drawdiagstripe(image, width, height, stripesize, reverse, fgcolor=None):
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

# Finds the gray tones in the given color palette and returns
# a sorted list of them.
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

# Converts the image to grayscale and dithers the resulting image
# to the gray tones given.
# Image has the same format returned by the _blankimage_ method with the
# given value of 'alpha' (default value for 'alpha' is False).
# 'grays' is a sorted list of gray tones.  Each gray tone must be an integer
# from 0 through 255.  The list must have a length of 2 or greater.
# If 'ignoreNonGrays' is True, just dither the gray tones and leave the other
# colors in the image unchanged.  Default is False.
def dithertograyimage(image, width, height, grays, alpha=False, ignoreNonGrays=False):
    if not grays:
        return graymap(image, width, height)
    if len(grays) < 2:
        raise ValueError
    for i in range(1, len(grays)):
        # Grays must be sorted
        if (
            grays[i] < 0
            or grays[i] > 255
            or grays[i] < grays[i - 1]
            or (grays[i] - grays[i - 1]) > 255
        ):
            raise ValueError
    pixelSize = 4 if alpha else 3
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            c = image[xp]
            if ignoreNonGrays:
                if image[xp] != image[xp + 1] or image[xp + 1] != image[xp + 2]:
                    continue
            else:
                c = (
                    image[xp] * 2126 + image[xp + 1] * 7152 + image[xp + 2] * 722
                ) // 10000
            r = 0
            bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
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

# Converts the image to grayscale and maps the resulting gray tones
# to colors in the given colors array.  If 'colors' is None (the default),
# the mapping step is skipped.
# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
# If 'ignoreNonGrays' is True, leave colors other than gray tones
# colors in the image unchanged.  Default is False.
def graymap(image, width, height, colors=None, alpha=False, ignoreNonGrays=False):
    pixelSize = 4 if alpha else 3
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            c = image[xp]
            if c != image[xp + 1] or image[xp + 1] != image[xp + 2]:
                if ignoreNonGrays:
                    continue
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
# Returns a list describing a color; its elements are the red, green, and blue
# components, in that order.
def getpixel(image, width, height, x, y):
    pos = (y * width + x) * 3
    return image[pos : pos + 3]

# Image has the same format returned by the _blankimage_ method with alpha=False.
# Returns a list describing a color; its elements are the blue, green, and red
# components, in that order.
def getpixelbgr(image, width, height, x, y):
    r = getpixel(image, width, height, x, y)
    return [r[2], r[1], r[0]]

# Image has the same format returned by the _blankimage_ method with alpha=False.
# Returns a list describing a color; its elements are the blue, green, red, and alpha
# components, in that order.
def getpixelbgralpha(image, width, height, x, y):
    r = getpixelalpha(image, width, height, x, y)
    return [r[2], r[1], r[0], r[3]]

# Image has the same format returned by the _blankimage_ method with alpha=False.
# 'c' is a list describing a color; its elements are the red, green, and blue
# components, in that order.
def setpixel(image, width, height, x, y, c):
    pos = (y * width + x) * 3
    image[pos] = c[0]
    image[pos + 1] = c[1]
    image[pos + 2] = c[2]

# Image has the same format returned by the _blankimage_ method with alpha=False.
# 'c' is a list describing a color; its elements are the blue, green, and
# red components, in that order.
def setpixelbgr(image, width, height, x, y, c):
    pos = (y * width + x) * 3
    image[pos] = c[2]
    image[pos + 1] = c[1]
    image[pos + 2] = c[0]

# Image has the same format returned by the _blankimage_ method with alpha=True.
# Returns a list describing a color; its elements are the red, green, blue, and
# alpha components, in that order.
def getpixelalpha(image, width, height, x, y):
    pos = (y * width + x) * 4
    return image[pos : pos + 4]

# Image has the same format returned by the _blankimage_ method with alpha=True.
# 'c' is a list describing a color; its elements are the red, green, blue, and
# alpha components, in that order.
def setpixelalpha(image, width, height, x, y, c):
    pos = (y * width + x) * 4
    image[pos] = c[0]
    image[pos + 1] = c[1]
    image[pos + 2] = c[2]
    image[pos + 3] = c[3]

# Image has the same format returned by the _blankimage_ method with alpha=True.
# 'c' is a list describing a color; its elements are the blue, green, red, and
# alpha components, in that order.
def setpixelbgralpha(image, width, height, x, y, c):
    pos = (y * width + x) * 4
    image[pos] = c[2]
    image[pos + 1] = c[1]
    image[pos + 2] = c[0]
    image[pos + 3] = c[3]

# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def imagetranspose(image, width, height, alpha=False):
    image2 = blankimage(height, width, alpha=alpha)
    if alpha:
        for y in range(height):
            for x in range(width):
                setpixelalpha(
                    image2,
                    height,
                    width,
                    y,
                    x,
                    getpixelalpha(image, width, height, x, y),
                )
    else:
        for y in range(height):
            for x in range(width):
                setpixel(
                    image2,
                    height,
                    width,
                    y,
                    x,
                    getpixel(image, width, height, x, y),
                )
    return image2

# Create a twice-as-wide image inspired by the style used
# to generate MARBLE.BMP.
def _ditherstyle(image, width, height, bgcolor=None, alpha=False):
    image2 = blankimage(width * 2, height, alpha=alpha)
    if not bgcolor:
        bgcolor = [192, 192, 192, 255]
    if len(bgcolor) == 3 and alpha:
        bgcolor = bgcolor[0:3] + [255]
    gp = getpixelalpha if alpha else getpixel
    sp = setpixelalpha if alpha else setpixel
    for y in range(height):
        for x in range(width):
            c = gp(image, width, height, x, y)
            sp(image2, width * 2, height, x * 2, y, c if y % 2 == 0 else bgcolor)
            sp(image2, width * 2, height, x * 2 + 1, y, bgcolor if y % 2 == 0 else c)
    return image2

# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def tograyditherstyle(image, width, height, palette=None, light=False, alpha=False):
    im = [x for x in image]
    graymap(im, width, height, alpha=alpha)
    if palette:
        grays = getgrays(palette)
        if len(grays) == 0:
            raise ValueError("palette has no gray tones")
        dithertograyimage(im, width, height, grays, alpha=alpha)
    if light:
        # Variant used in background of WINLOGO.BMP
        colors = [[i, i, i] for i in range(256)]
        colors[192] = [255, 255, 255]
        colors[128] = [192, 192, 192]
        colors[0] = [128, 128, 128]
        graymap(im, width, height, colors, alpha=alpha)
    return _ditherstyle(im, width, height, alpha=alpha)

# Dithers in place the given image to the colors in color palette returned by websafecolors().
# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
# If 'includeVga' is True, leave unchanged any colors in the colorpalette returned by classiccolors(). Default is False.
def websafeDither(image, width, height, alpha=False, includeVga=False):
    pixelSize = 4 if alpha else 3
    if len(image) < width * height * pixelSize:
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            if includeVga:
                # Leave unchanged any colors in the VGA palette
                # but not in the "safety palette".
                c0 = image[xp]
                if c0 == 0xC0:
                    if image[xp + 1] == 0xC0 and image[xp + 2] == 0xC0:
                        continue
                elif c0 == 0x80 or c0 == 0:
                    if (image[xp + 1] == 0 or image[xp + 1] == 0x80) and (
                        image[xp + 2] == 0 or image[xp + 2] == 0x80
                    ):
                        continue
            for i in range(3):
                c = image[xp + i]
                cm = c % 51
                bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                image[xp + i] = (c - cm) + 51 if bdither < cm * 64 // 51 else c - cm
    return image

# Dithers in place the given image to the colors in an 8-bit color palette returned by ega8colors().
# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def eightColorDither(image, width, height, alpha=False):
    pixelSize = 4 if alpha else 3
    if width < 0 or height < 0:
        raise ValueError
    if width == 0 or height == 0:
        return
    if len(image) < width * height * pixelSize:
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            for i in range(3):
                c = image[xp + i]
                cm = c
                bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                image[xp + i] = (c - cm) + 255 if bdither < cm * 64 // 255 else c - cm
    return image

# Converts each color in the given image to the nearest color (in ordinary red&ndash;green&ndash;blue
# space) in the given color palette.
# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def posterize(image, width, height, palette, alpha=False):
    pixelSize = 4 if alpha else 3
    if len(image) < width * height * pixelSize:
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            canindex = _nearest_rgb3(
                palette,
                image[xp],
                image[xp + 1],
                image[xp + 2],
            )
            can = palette[canindex]
            image[xp] = can[0]
            image[xp + 1] = can[1]
            image[xp + 2] = can[2]
    return image

# Dithers in place the given image to the colors in an arbitrary color palette.
# Derived from Adobe's pattern dithering algorithm, described by J. Yliluoma at:
# https://bisqwit.iki.fi/story/howto/dither/jy/
# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def patternDither(image, width, height, palette, alpha=False):
    pixelSize = 4 if alpha else 3
    candidates = [[] for i in range(len(_DitherMatrix))]
    paletteLum = [
        (can[0] * 2126 + can[1] * 7152 + can[2] * 722) // 10000 for can in palette
    ]
    trials = {}
    numtrials = 0
    numskips = 0
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            e = [0, 0, 0]
            exact = False
            ir = image[xp]
            ig = image[xp + 1]
            ib = image[xp + 2]
            for i in range(len(_DitherMatrix)):
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
            bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
            fcan = candidates[bdither][1]
            fcan = palette[fcan]
            image[xp] = fcan[0]
            image[xp + 1] = fcan[1]
            image[xp + 2] = fcan[2]
    return image

# Returns a 256-element color gradient starting at 'blackColor' and ending at 'whiteColor'.
# 'blackColor' and 'whiteColor' are each three-element lists identifying colors.
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

def _gradient(stops, count=256):
    # NOTE: Assumes gradient stops are sorted by position
    if len(stops) == 0 or count <= 1:
        raise ValueError
    for s in stops:
        if not s[1] or len(s[1]) != 3:
            raise ValueError
    minStop = stops[0][0]
    maxStop = stops[len(stops) - 1][0]
    if minStop < 0 or maxStop > 255 or minStop > maxStop:
        raise ValueError
    ret = [None for i in range(count)]
    for i in range(count):
        p = i
        if p <= minStop:
            ret[i] = [x for x in stops[0][1]]
        elif p >= maxStop:
            ret[i] = [x for x in stops[len(stops) - 1][1]]
        else:
            for j in range(len(stops) - 1):
                if p >= stops[j][0] and p <= stops[j + 1][0]:
                    if stops[j][0] == stops[j + 1][0]:
                        ret[i] = [x for x in stops[j][1]]
                    else:
                        sx = stops[j][0]
                        sy = stops[j + 1][0]
                        pos = (p - sx) / (sy - sx)
                        ret[i] = [
                            int(x + (y - x) * pos)
                            for x, y in zip(stops[j][1], stops[j + 1][1])
                        ]
    return ret

# Returns a 256-element color gradient for coloring user interface elements (for example,
# using the 'graymap' function).
# The parameters are all
# three-element lists identifying colors.  Each parameter can be None.
def uicolorgradient(
    hilightColor=None, lightColor=None, shadowColor=None, darkShadowColor=None
):
    return _gradient(
        [
            [0, darkShadowColor if darkShadowColor else [0, 0, 0]],
            [128, shadowColor if shadowColor else [128, 128, 128]],
            [192, lightColor if lightColor else [192, 192, 192]],
            [255, hilightColor if hilightColor else [255, 255, 255]],
        ]
    )

# Returns a 256-element color gradient for coloring user interface elements (for example,
# using the 'graymap' function), given a desired button face color.  The parameters are all
# three-element lists identifying colors.  Each parameter can be None.
#
# Example 1: Suppose 'img' is the image of a custom drawn button in grayscale,
# with the button face colored light gray (192, 192, 192) and highlights
# and shadows colored in other gray tones.  Then the following code colors
# the gray tones of the button image and saves the resulting image to a file.
#
#  grad = dw.uicolorgradient2([220, 200, 150])
#  img256 = dw.graymap([x for x in img], w, h, grad, ignoreNonGrays=True)
#  dw.writepng("uielement.png", img, w, h)
#
# Example 2: Same as the previous example, but the image is first dithered
# to have at most four gray tones, including possibly light gray.
#
#  img = dw.dithertograyimage(
#    [x for x in img], w, h, [0, 128, 192, 255], ignoreNonGrays=True
#  )
#  grad = dw.uicolorgradient2([220, 200, 150])
#  img256 = dw.graymap([x for x in img], w, h, grad, ignoreNonGrays=True)
#  dw.writepng("uielement.png", img, w, h)
def uicolorgradient2(btnface=None):
    if not btnface:
        btnface = [192, 192, 192]
    return uicolorgradient(
        hilightColor=[255, 255, 255],
        lightColor=btnface,
        shadowColor=[x * 2 // 3 for x in btnface],
        darkShadowColor=[0, 0, 0],
    )

# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
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

# Generate an image of white noise.
# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
def whitenoiseimage(width=64, height=64):
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

# Alternate way to generate an image of noise.
# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
def noiseimage2(width=64, height=64, bgcolor=None, noisecolor=None):
    if width <= 0 or int(width) != width:
        raise ValueError
    if height <= 0 or int(height) != height:
        raise ValueError
    if not bgcolor:
        bgcolor = [255, 255, 255]
    if not noisecolor:
        noisecolor = [0, 0, 0]
    image = []
    for y in range(height):
        row = [0 for i in range(width * 3)]
        for x in range(width):
            r = noisecolor if random.randint(0, 63) < 8 else bgcolor
            row[x * 3] = r[0]
            row[x * 3 + 1] = r[1]
            row[x * 3 + 2] = r[2]
        image.append(row)
    return [px for row in image for px in row]

# Draws a circle that optionally wraps around.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def circledraw(image, width, height, c, cx, cy, r, wraparound=True):
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

# Draws a line that optionally wraps around.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def linedraw(
    image, width, height, c, x0, y0, x1, y1, drawEndPoint=False, wraparound=True
):
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

# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
def brushednoise(width, height, tileable=True):
    image = blankimage(width, height, [192, 192, 192])
    for i in range(max(width, height) * 5):
        c = random.choice([128, 128, 128, 128, 0, 255])
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        x1 = x + random.randint(0, width // 2)
        simplebox(image, width, height, [c, c, c], x, y, x1, y + 1, wraparound=tileable)
    return image

# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
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

# Returns an image with the same format returned by the _blankimage_ method with alpha=False.
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

# Rotates in place a column of the image by the given downward offset in pixels,
# which may be negative or not.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def imagerotatecolumn(image, width, height, x, offset=0):
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

# Rotates in place a row of the image by the given rightward offset in pixels,
# which may be negative or not.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def imagerotaterow(image, width, height, y, offset=0):
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
def imagereverseroworder(image, width, height):
    halfHeight = height // 2  # floor of half height; don't care about middle row
    for y in range(halfHeight):
        row = image[y * width * 3 : (y + 1) * width * 3]
        otherRow = image[(height - 1 - y) * width * 3 : (height - y) * width * 3]
        image[y * width * 3 : (y + 1) * width * 3] = otherRow
        image[(height - 1 - y) * width * 3 : (height - y) * width * 3] = row
    return image

# Returns True if width or height is 0 or if:
# - The image's first column's first half is a mirror
# of its second half, and...
# - The image's last column's first half is a mirror
# of its second half.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def endingColumnsAreMirrored(image, width, height):
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

# Returns True if width or height is 0 or if:
# - The image's first row's first half is a mirror
# of its second half, and...
# - The image's last row's first half is a mirror
# of its second half.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def endingRowsAreMirrored(image, width, height):
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
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

# Images have the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def affine(
    dstimage,
    dstwidth,
    dstheight,
    srcimage,
    srcwidth,
    srcheight,
    m1,
    m2,
    m3,
    m4,
    alpha=False,
):
    bypp = 4 if alpha else 3
    for y in range(dstheight):
        yp = y / srcheight
        for x in range(dstwidth):
            xp = x / srcwidth
            tx = int((xp * m1 + yp * m2) * srcwidth) % srcwidth
            ty = int((xp * m3 + yp * m4) * srcheight) % srcheight
            dstindex = (y * dstwidth + x) * bypp
            srcindex = (ty * srcwidth + tx) * bypp
            if dstindex < 0 or dstindex > len(dstimage):
                raise ValueError([x, y, tx, ty])
            if srcindex < 0 or srcindex > len(srcimage):
                raise ValueError([x, y, tx, ty])
            dstimage[dstindex : dstindex + bypp] = srcimage[srcindex : srcindex + bypp]
    return dstimage

# Image has the same format returned by the _blankimage_ method with alpha=False.
def horizskew(image, width, height, skew):
    if skew < -1 or skew > 1:
        raise ValueError
    for i in range(height):
        p = i / height
        imagerotaterow(image, width, height, i, int(skew * p * width))
    return image

# Image has the same format returned by the _blankimage_ method with alpha=False.
def vertskew(image, width, height, skew):
    if skew < -1 or skew > 1:
        raise ValueError
    for i in range(width):
        p = i / width
        imagerotatecolumn(image, width, height, i, int(skew * p * height))
    return image

# Image has the same format returned by the _blankimage_ method with alpha=False.
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

# Image has the same format returned by the _blankimage_ method with the given value of 'alpha' (default value for 'alpha' is False).
def maketileable(image, width, height, alpha=False):
    # Use tiling method described by Paul Bourke,
    # Tiling Textures on the Plane (Part 1)
    # https://paulbourke.net/geometry/tiling/
    ret = blankimage(width, height, alpha=alpha)
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
            if alpha:
                t = [
                    m1 * ov1 / (m1 + m2) + m2 * ov2 / (m1 + m2)
                    for ov1, ov2 in zip(o1, o2)
                ]
                t[3] = o1[3]  # adopt source image's alpha
                t = [max(0, min(255, int(v))) for v in t]
                setpixelalpha(ret, width, height, x, y, t)
            else:
                t = [
                    m1 * ov1 / (m1 + m2) + m2 * ov2 / (m1 + m2)
                    for ov1, ov2 in zip(o1, o2)
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

# Image has the same format returned by the _blankimage_ method with alpha=False.
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
            if (not transcolor) or c != transcolor:
                helper.rect(x, y, x + 1, y + 1, c)
    return str(helper) + "</pattern>"

class ImageWraparoundDraw:
    # Image has the same format returned by the _blankimage_ method with alpha=False.
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
def _drawupperedgecore(helper, x0, y0, x1, y1, color, edgesize=1):
    if (not color) or x1 <= x0 or y1 <= y0:  # empty or negative
        return
    elif x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        helper.rect(x0, y0, x1, y1, color)
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y0, x1, y0 + edgesize, color)
        helper.rect(x0, y0 + edgesize, x1, y1, color)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0, y0, x0 + edgesize, y1, color)
        helper.rect(x0 + edgesize, y0, x1, y1, color)
    else:
        # left edge (includes bottom left and top left "pixels")
        helper.rect(x0, y0, x0 + edgesize, y1, color)
        # top edge (includes top right "pixel")
        helper.rect(x0 + edgesize, y0, x1, y0 + edgesize, color)

# helper for lower edge drawing
def _drawloweredgecore(helper, x0, y0, x1, y1, color, edgesize=1):
    if (not color) or x1 <= x0 or y1 <= y0:  # empty or negative
        return
    elif x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        helper.rect(x0, y0, x1, y1, color)
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y1 - edgesize, x1, y1, color)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0, y0, x0 + edgesize, y1, color)
        helper.rect(x1 - edgesize, y0, x1, y1, color)
    else:
        # left edge (includes top right and bottom right "pixels")
        helper.rect(x1 - edgesize, y0, x1, y1, color)  # right edge
        # bottom edge (includes bottom left "pixel")
        helper.rect(x0, y1 - edgesize, x1 - edgesize, y1, color)

# hilt = upper part of edge, dksh = lower part of edge
def _drawroundedgecore(helper, x0, y0, x1, y1, upper, lower, edgesize=1):
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        return
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y0 + edgesize, x1, y0 - edgesize, upper)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y1, upper)
    else:
        helper.rect(x0, y0 + edgesize, x0 + edgesize, y1 - edgesize, upper)  # left edge
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y0 + edgesize, upper)  # top edge
        helper.rect(
            x1 - edgesize,
            y0 + edgesize,
            x1,
            y1 - edgesize,
            lower,
        )  # right edge
        helper.rect(
            x0 + edgesize,
            y1 - edgesize,
            x1 - edgesize,
            y1,
            lower,
        )  # bottom edge

def drawpositiverect(helper, x0, y0, x1, y1, face):
    if x1 >= x0 or y1 >= y0:  # empty or negative
        return
    helper.rect(x0, y0, x1, y1, face)

def drawupperedge(helper, x0, y0, x1, y1, upper, edgesize=1, bordersize=1):
    for i in range(bordersize):
        _drawupperedgecore(helper, x0, y0, x1, y1, upper, edgesize=edgesize)
        x0 += edgesize
        y0 += edgesize

def drawloweredge(helper, x0, y0, x1, y1, lower, edgesize=1, bordersize=1):
    for i in range(bordersize):
        _drawloweredgecore(helper, x0, y0, x1, y1, lower, edgesize=edgesize)
        x1 -= edgesize
        y1 -= edgesize

# helper for edge drawing (upper left edge "dominates")
def drawroundededge(helper, x0, y0, x1, y1, upper, lower, edgesize=1, bordersize=1):
    for i in range(bordersize):
        _drawroundededgecore(helper, x0, y0, x1, y1, upper, lower, edgesize=edgesize)
        x0 += edgesize
        y0 += edgesize
        x1 -= edgesize
        y1 -= edgesize

# helper for edge drawing (upper left edge "dominates")
def drawedgetopdom(helper, x0, y0, x1, y1, upper, lower, edgesize=1, bordersize=1):
    for i in range(bordersize):
        drawupperedge(helper, x0, y0, x1, y1, upper, edgesize=edgesize)
        drawloweredge(
            helper, x0 + edgesize, y0 + edgesize, x1, y1, lower, edgesize=edgesize
        )
        x0 += edgesize
        y0 += edgesize
        x1 -= edgesize
        y1 -= edgesize

# helper for edge drawing (bottom right edge "dominates")
def drawedgebotdom(helper, x0, y0, x1, y1, upper, lower, edgesize=1, bordersize=1):
    for i in range(bordersize):
        drawupperedge(
            helper, x0, y0, x1 - edgesize, y1 - edgesize, upper, edgesize=edgesize
        )
        drawloweredge(helper, x0, y0, x1, y1, lower, edgesize=edgesize)
        x0 += edgesize
        y0 += edgesize
        x1 -= edgesize
        y1 -= edgesize

# helper for edge drawing (neither edge "dominates")
def drawedgenodom(
    helper, x0, y0, x1, y1, upper, lower, corner, edgesize=1, bordersize=1
):
    for i in range(bordersize):
        drawupperedge(
            helper, x0, y0, x1 - edgesize, y1 - edgesize, upper, edgesize=edgesize
        )
        drawloweredge(
            helper, x0 + edgesize, y0 + edgesize, x1, y1, lower, edgesize=edgesize
        )
        drawpositiverect(helper, x1 - edgesize, y0, x1, y0 + edgesize, corner)
        drawpositiverect(helper, x1, y1 - edgesize, x1 + edgesize, y1, corner)
        x0 += edgesize
        y0 += edgesize
        x1 -= edgesize
        y1 -= edgesize

def drawindentborder(
    helper, x0, y0, x1, y1, hilt, sh, frame, outerbordersize=1, innerbordersize=1
):
    if innerbordersize < 0:
        raise ValueError
    if outerbordersize < 0:
        raise ValueError
    drawsunkenborderbotdom(
        helper, x0, y1, x1, y1, hilt, None, sh, None, bordersize=outerbordersize
    )
    drawedgebotdom(
        helper,
        x0 + outerbordersize,
        y1 + outerbordersize,
        x1 - outerbordersize,
        y1 - outerbordersize,
        frame,
        frame,
    )
    drawraisedborderbotdom(
        helper,
        x0 + outerbordersize + 1,
        y1 + outerbordersize + 1,
        x1 - outerbordersize - 1,
        y1 - outerbordersize - 1,
        hilt,
        None,
        sh,
        None,
        bordersize=innerbordersize,
    )
    c = 1 + outerbordersize + innerbordersize
    return [x0 + c, y0 + c, x0 - c, y0 - c]

# The following four functions draw window edges
# in raised or sunken style

# Draw an outer window edge in raised style.
def drawraisedouterwindow(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,  # highlight color
    lt,  # light color
    sh,  # shadow color
    dksh,  # dark shadow color
):
    drawedgebotdom(helper, x0, y0, x1, y1, lt, dksh)

# Draw an inner window edge in raised style.
def drawraisedinnerwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, hilt, sh)

# Draw an outer window edge in sunken style.
def drawsunkenouterwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, sh, hilt)

# Draw an outer window edge in sunken style.
def drawsunkeninnerwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, dksh, lt)

# The following four functions draw button edges (also known as "soft" edges)
# in raised or sunken style

# Draw an outer button edge (or "soft" edge) in raised style.
def drawraisedouterwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, hilt, dksh)

# Draw an inner button edge (or "soft" edge) in raised style.
def drawraisedinnerwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, lt, sh)

# Draw an outer button edge (or "soft" edge) in sunken style.
def drawsunkenouterwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, dksh, hilt)

# Draw an inner button edge (or "soft" edge) in sunken style.
def drawsunkeninnerwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, sh, lt)

####

# Raised border where the "top left dominates"
def drawraisedbordertopdom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgetopdom(helper, x0, y0, x1, y1, hilt, sh, bordersize=bordersize)

# Sunken border where the "top left dominates"
def drawsunkenbordertopdom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgetopdom(helper, x0, y0, x1, y1, sh, hilt, bordersize=bordersize)

# Raised border where neither edge "dominates"
def drawraisedbordernodom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgenodom(helper, x0, y0, x1, y1, hilt, sh, lt, bordersize=bordersize)

# Sunken border where neither edge "dominates"
def drawsunkenbordernodom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgenodom(helper, x0, y0, x1, y1, sh, hilt, lt, bordersize=bordersize)

# Raised border where the "bottom right dominates"
def drawraisedborderbotdom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgebotdom(helper, x0, y0, x1, y1, hilt, sh, bordersize=bordersize)

# Sunken border where the "bottom right dominates"
def drawsunkenborderbotdom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgebotdom(helper, x0, y0, x1, y1, sh, hilt, bordersize=bordersize)

####

def monoborder(  # "Monochrome" flat border
    helper,
    x0,
    y0,
    x1,
    y1,
    clientAreaColor,  # draw the inner and middle parts with this color
    windowFrameColor,  # draw the outer parts with this color
):
    drawedgebotdom(helper, x0, y0, x1, y1, windowFrameColor, windowFrameColor)
    drawedgebotdom(
        helper, x0 + 1, y0 + 1, x1 + 1, y1 + 1, clientAreaColor, clientAreaColor
    )
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, clientAreaColor]

def flatborder(  # Flat border
    helper,
    x0,
    y0,
    x1,
    y1,
    sh,  # draw the outer parts with this color
    buttonFace,  # draw the inner and middle parts with this color
):
    drawedgebotdom(helper, x0, y0, x1, y1, sh, sh)
    drawedgebotdom(helper, x0 + 1, y0 + 1, x1 + 1, y1 + 1, buttonFace, buttonFace)
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, buttonFace]

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
    # NOTE: Window border style is also used to draw Windows Help's
    # ">>" and "purple arrow" buttons within Help topics.
    face = face if face else lt
    drawraisedouterwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinnerwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, face]

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
):
    face = face if face else lt
    drawraisedouterwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinnerwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, face]

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
):
    face = face if face else lt
    drawsunkenouterwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawsunkeninnerwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, face]

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
    drawsunkenouterwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawsunkeninnerwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, face]

def wellborder(helper, x0, y0, x1, y1, hilt, windowText):
    drawsunkenouterwindow(helper, x0, y0, x1, y1, hilt, hilt, hilt, hilt)
    drawsunkeninnerwindow(
        helper, x0, y0, x1, y1, windowText, windowText, windowText, windowText
    )
    drawsunkenouterwindow(
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
    # Return upper left and lower right coordinates of button face rectangle
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2]

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
    drawsunkenouterwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    drawraisedinnerwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, face]

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
    drawsunkenouterwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh)
    # Return upper left and lower right coordinates of button face rectangle
    # along with the face background color
    return [x0 + 1, y0 + 1, x1 - 1, y1 - 1, face]

def drawRoundOrSquareEdge(helper, x0, y0, x1, y1, lt, sh, squareFrame=False):
    if squareFrame:
        drawedgebotdom(helper, x0, y0, x1, y1, lt, sh)
    else:
        drawroundedge(helper, x0, y0, x1, y1, lt, sh)

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
    squareFrame=True,  # whether to draw a square frame or a rounded frame
    isDefault=False,  # whether the button is a default button
):
    if lt == None:
        lt = btn
    if dksh == None:
        dksh = sh
    if isDefault:
        drawedgebotdom(helper, x0, y0, x1, y1, frame, frame)
        drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, sh, sh)
        # Return upper left and lower right coordinates of button face rectangle
        # along with the face background color
        return [x0 + 2, y0 + 2, x1 - 2, y1 - 2, btn]
    else:
        edge = 1 if isDefault else 0
        return buttondown(
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
):
    if lt == None:
        lt = btn
    if dksh == None:
        dksh = sh
    # If isDefault is True, no frame is drawn and no room is left for the frame
    edge = 1 if isDefault else 0
    ret = buttonup(
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
    )
    if isDefault:
        drawRoundOrSquareEdge(helper, x0, y0, x1, y1, frame, frame, squareFrame)
    return ret

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
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    if frame:
        drawRoundOrSquareEdge(helper, x0, y0, x1, y1, frame, frame, squareFrame)
        if isDefault:
            drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)
    drawupperedge(helper, x0 + edge, y0 + edge, x1 - edge, y1 - edge, sh)
    return [x0 + edge + 1, y0 + edge + 1, x1 - edge, y1 - edge, btn]

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
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    drawedgebotdom(helper, x0 + edge, y0 + edge, x1 - edge, y1 - edge, hilt, sh)
    drawedgebotdom(
        helper, x0 + edge + 1, y0 + edge + 1, x1 - edge - 1, y1 - edge - 1, hilt, sh
    )
    if frame:
        drawRoundOrSquareEdge(helper, x0, y0, x1, y1, frame, frame, squareFrame)
        if isDefault:
            drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)
    return [x0 + edge + 2, y0 + edge + 2, x1 - edge - 2, y1 - edge - 2, btn]

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

# Draws a smaller version of the contour in the interior.
# Preserves tileability.
def _insetbox(x, y, contour):
    if x * 6.0 < 1 or y * 6.0 < 1 or x * 6 > 5 or x * 6 > 5:
        return contour(x, y)
    x = min(1, max(0, 3 * x / 2 - 1 / 4))
    y = min(1, max(0, 3 * y / 2 - 1 / 4))
    return contour(x, y)

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
        # Tileable gradient contours
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
        # Not necessarily tileable gradient contours
        contours = [
            _horizcontourwrap,
            _vertcontourwrap,
            _diagcontourwrap,
            _reversediagcontourwrap,
            _mindiagwrap,
            _horizcontour,
            _vertcontour,
            _diagcontour,
            _reversediagcontour,
            _square,
            lambda x, y: _argyle(x, y, r),
        ]
    if includeWhole:
        contours.append(_whole)
    ret = random.choice(contours)
    if random.randint(0, 9) == 0:
        rr = ret
        ret = lambda x, y: _insetbox(x, y, rr)
    return ret

def _randomgradientfill(width, height, palette, tileable=True):
    return _randomgradientfillex(width, height, palette, _randomcontour(tileable))

# Image has the same format returned by the _blankimage_ method with alpha=False.
def randommaybemonochrome(image, width, height):
    r = random.randint(0, 99)
    if r < 8:
        # dither the input image to three grays from the VGA palette
        image = dithertograyimage([x for x in image], width, height, [0, 128, 255])
        r = random.randint(0, 6)
        colors = [
            [128, 128, 128],
            [192, 192, 192],
        ]  # dark gray and light gray from the VGA palette
        black = [0, 0, 0]
        white = [255, 255, 255]
        if r > 0:
            # use a "colored" dark gray and light gray from the VGA palette instead
            colors = [
                [(r & 1) * 0x80, ((r >> 1) & 1) * 0x80, ((r >> 2) & 1) * 0x80],
                [(r & 1) * 0xFF, ((r >> 1) & 1) * 0xFF, ((r >> 2) & 1) * 0xFF],
            ]
        minipal = random.choice(
            [
                [black, colors[0], colors[1]],  # dark
                [black, colors[0], white],  # gray
                [black, colors[1], white],  # light gray
                [colors[0], colors[1], white],  # light
            ]
        )
        # replace the grays with the colors
        gcolors = [[] for i in range(256)]
        gcolors[0] = minipal[0]
        gcolors[128] = minipal[1]
        gcolors[255] = minipal[2]
        return graymap([x for x in image], width, height, gcolors)
    elif r < 16:
        r = random.randint(0, 6)
        colors = [
            [128, 128, 128],
            [192, 192, 192],
        ]  # dark gray and light gray from the VGA palette
        black = [0, 0, 0]
        white = [255, 255, 255]
        if r > 0:
            # use a "colored" dark gray and light gray from the VGA palette instead
            colors = [
                [(r & 1) * 0x80, ((r >> 1) & 1) * 0x80, ((r >> 2) & 1) * 0x80],
                [(r & 1) * 0xFF, ((r >> 1) & 1) * 0xFF, ((r >> 2) & 1) * 0xFF],
            ]
        # dither the input image to four grays from the VGA palette
        image = dithertograyimage([x for x in image], width, height, [0, 128, 192, 255])
        # replace the grays with the colors
        gcolors = [[] for i in range(256)]
        gcolors[0] = black
        gcolors[128] = colors[0]
        gcolors[192] = colors[1]
        gcolors[255] = white
        return graymap([x for x in image], width, height, gcolors)
    else:
        return image

def _randomdither(image, width, height, palette):
    grays = getgrays(palette) if palette else None
    if ((not palette) or len(grays) >= 2) and random.randint(0, 99) < 10:
        # Convert to the grays in the palette
        dithertograyimage(image, width, height, grays)
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

# Image returned by this method has the same format returned by the _blankimage_ method with alpha=False.
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

def _hatchoverlay(image, width, height, hatchColor, rows=2):
    if not hatchColor:
        raise ValueError
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

# Generates a random checkerboard pattern image (using the given palette, if any)
# Image returned by this method has the same format returned by the _blankimage_ method with alpha=False.
def randomcheckimage(w, h, palette=None, tileable=True):
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
        _hatchoverlay(upperLeftImage, w, h, hatch, rows=rows)
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

# Image returned by this method has the same format returned by the _blankimage_ method with alpha=False.
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

# Input image uses only three colors: (0,0,0) or black,(128,128,128),(255,255,255) or white
# Turns the image into a black-and-white image, with middle gray dithered.
# Image has the same format returned by the _blankimage_ method with alpha=False.
def monochromeFromThreeGrays(image, width, height):
    image = [x for x in image]
    dithertograyimage(image, width, height, [0, 255])
    return image

# Input image uses only three colors: (0,0,0) or black,(128,128,128),(255,255,255) or white
# Default for palette is VGA palette (classiccolors())
# Image has the same format returned by the _blankimage_ method with alpha=False.
def randomPalettedFromThreeGrays(image, width, height, palette=None):
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

# Generates a random colorization gradient
# Random beginning color.  Palette is optional;
# if not None (the default), the beginning and end colors are limited
# to those in the given palette.
def randomColorization(palette=None):
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

def writepalette(f, palette, name=None, raiseIfExists=False):
    if name and "\n" in name:
        raise ValueError
    if (not palette) or len(palette) > 512:
        raise ValueError
    # GIMP palette
    ff = open(f + ".gpl", "xb" if raiseIfExists else "wb")
    ff.write(bytes("GIMP Palette\n", "utf-8"))
    ff.write(
        bytes("Name: " + (name.replace("\n", " ").replace("#", "_")) + "\n", "utf-8")
    )
    ff.write(bytes("Columns: 8\n", "utf-8"))
    for c in palette:
        col = [c[0] & 0xFF, c[1] & 0xFF, c[2] & 0xFF]
        ff.write(
            bytes("%d %d %d %s\n" % (col[0], col[1], col[2], _colorname(col)), "utf-8")
        )
    ff.close()
    # Microsoft palette
    ff = open(f + ".pal", "xb" if raiseIfExists else "wb")
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
        ff.write(bytes([c[0] & 0xFF, c[1] & 0xFF, c[2] & 0xFF, 0]))
    ff.close()
    # Adobe color swatch format
    ff = open(f + ".aco", "xb" if raiseIfExists else "wb")
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
    ff = open(f + ".ase", "xb" if raiseIfExists else "wb")
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
    writepalette("palettes/websafe", websafecolors(), '"Safety Palette"')
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
        '"Safety Palette" and VGA Colors',
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
