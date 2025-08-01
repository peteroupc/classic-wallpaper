# This Python script helps generate interesting variations on desktop
# wallpapers based on existing image files.  Because they run on the CPU
# and are implemented in pure Python, the methods are intended for
# relatively small images that are suitable as tileable desktop wallpaper
# patterns, especially with dimensions 256 &times; 256 or smaller.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under the Unlicense: https://unlicense.org/
#
# NOTES:
#
# 1. Animation of tilings composed from a wallpaper image can be implemented by
# shifting, with each frame, the starting position for drawing the upper left
# corner of the wallpaper tiling (for example, from the upper-left corner of the image
# to some other position in the image).
# 2. In Windows, if both an 8 &times; 8 two-level pattern and a centered wallpaper
# are set as the desktop background, a tiling of the pattern and the wallpaper
# will be drawn on the desktop, the latter appearing above the former.  Areas of the
# two-level pattern where the pixel is 1 are drawn as "black", and other areas are
# drawn as the desktop color.
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
import sys

def _listdir(p):
    return [os.path.abspath(p + "/" + x) for x in os.listdir(p)]

_DitherMatrix4x4 = [  # Bayer 4 &times; 4 ordered dither matrix
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

_DitherMatrix = [  # Bayer 8 &times; 8 ordered dither matrix
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
# Each element in the return value is a color in the form of a 3-element list of its red,
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
# Each element in the return value is a color in the form of a 3-element list of its red,
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
# Each element in the return value is a color in the form of a 3-element list of its red,
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
# Each element in the return value is a color in the form of a 3-element list of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
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
# Each element in the return value is a color in the form of a 3-element list of its red,
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
# Each element in the return value is a color in the form of a 3-element list of its red,
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

# Returns an array containing the colors in the specified palette plus their
# "half-and half" versions.
# Each element in the return value is a color in the form of a 3-element list of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
def paletteandhalfhalf(palette):
    ret = [
        [k & 0xFF, (k >> 8) & 0xFF, (k >> 16) & 0xFF]
        for k in _getdithercolors(palette).keys()
    ]
    ret.sort()
    return ret

# Gets the "half-and half" versions of colors in the specified palette.
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

# Returns a list of the unique colors in an image (disregarding
# the alpha channel, if any).
# Each element in the return value is a color in the form of a 3-element list of its red,
# green, and blue components in that order, where each
# component is an integer from 0 through 255.
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

def _isqrtceil(i):
    r = math.isqrt(i)
    return r if r * r == i else r + 1

# Returns an ImageMagick filter string to generate a desktop background from an image, in three steps.
# 1. If rgb1 and rgb2 are not nil, converts the input image to grayscale, then translates the grayscale
# palette to a gradient starting at rgb1 for grayscale level 0 (a 3-element list of the red,
# green, and blue components in that order; for example, [2,10,255] where each
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
        sz = 256
        ret += [
            "(",
            "+clone",
            "-grayscale",
            "Rec709Luma",
            ")",
            "(",
            "-size",
            "1x%d" % (sz),
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
        # NOTE: For abstractImage = True, ImageMagick's ordered 8 &times; 8 dithering
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
# source that shines from the upper-left corner.
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
# lower-left corner.
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
# are set in the specified foreground color, on a background that can optionally
# be colored.
# 'fgcolor' and 'bgcolor' are the foreground and background color, respectively.
# The input image this command will be applied to is assumed to be an SVG file
# which must be black (all zeros) in the nontransparent areas (given that ImageMagick renders the
# SVG, by default, on a background colored white, or (255,255,255)) or a raster image with only
# gray tones, where the closer the gray level is to 0, the less transparent.
# 'bgcolor' can be None so that an alpha
# background is used.  Each color is a
# 3-element list of the red, green, and blue components in that order; for example,
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
# bg is treated as [192, 192, 192] if None.
# highlight is treated as [255, 255, 255] if None.
# shadow is treated as [0, 0, 0] if None.
def basrelief(bg=None, highlight=None, shadow=None):
    if bg == None:
        bg = [192, 192, 192]
    if len(bg) < 3:
        raise ValueError
    if highlight == None:
        highlight = [255, 255, 255]
    if len(highlight) < 3:
        raise ValueError
    if shadow == None:
        shadow = [0, 0, 0]
    if len(shadow) < 3:
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
# seamlessly tileable.
# NOTE: "-append" is a vertical append; "+append" is a horizontal append;
# "-flip" reverses the row order; "-flop" reverses the column order.
# NOTE: Of the seventeen wallpaper groups, four can be
# applied to areas with arbitrary contents to create seamlessly tileable images:
# Pmm (1/4 of a rectangle is reflected and repeated).
# P4m (1/8 of a rectangle).
# P3m1 (1/6 of a hexagon).
# P6m (1/12 of a hexagon).
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
# For best results, the command should be applied to images whose
# last row's first half is a mirror of its second half.
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
# either None or a 3-element list of the red,
# green, and blue components in that order; for example, [2,10,255] where each
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
# around the time of either operating system's release.
def brushedmetal():
    sz = 50
    return [
        "(",
        "+clone",
        ")",
        "+append",
        "-morphology",
        "Convolve",
        ("%dx1+%d+0:" % (sz, sz - 1)) + (",".join([str(1 / sz) for i in range(sz)])),
        "+repage",
        "-crop",
        "50%x0+0+0",
        "+repage",
    ]

# Draw a wraparound simple box on an image.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
def simplebox(
    image, width, height, color, x0, y0, x1, y1, wraparound=True, alpha=False
):
    if (
        x0 >= 0
        and y0 >= 0
        and x1 <= width
        and y1 <= height
        and (not alpha)
        and x0 < x1
        and y1 == y0 + 1
    ):
        pos = (y0 * width + x0) * 3
        for x in range(x0, x1):
            image[pos] = color[0]
            image[pos + 1] = color[1]
            image[pos + 2] = color[2]
            pos += 3
        return
    borderedbox(
        image,
        width,
        height,
        None,
        color,
        color,
        x0,
        y0,
        x1,
        y1,
        wraparound=wraparound,
        alpha=alpha,
    )

# Draw a wraparound hatched box on an image.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
# 'color' is the color of the hatch, drawn on every "black" pixel (defined below)
# in the pattern's tiling.
# This method currently does no "alpha blending".
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
    alpha=False,
):
    if not wraparound:
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
    ca = (color[3] & 0xFF) if (alpha and len(color) > 3) else 0xFF
    ox = x0
    oy = y0
    pixelCount = 4 if alpha else 3
    if not wraparound:
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, width)
        y1 = min(y1, height)
        if x0 >= x1 or y0 >= y1:
            return
    for y in range(y0, y1):
        ypp = y % height
        yp = ypp * width * pixelCount
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
                pos = yp + xp * pixelCount
                image[pos] = cr
                image[pos + 1] = cg
                image[pos + 2] = cb
                if alpha:
                    image[pos + 3] = ca

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

# Draw a wraparound hatched box on an image.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False
def hatchedbox_alignorigins(
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
    wraparound=True,
    alpha=False,
):
    hand = blankimage(8, 8, [255, 255, 255], alpha=alpha)
    hatchedbox(
        hand, 8, 8, [0, 0, 0], pattern, 0, 0, 8, 8, msbfirst=msbfirst, alpha=alpha
    )
    hxor = blankimage(8, 8, [0, 0, 0], alpha=alpha)
    hatchedbox(hxor, 8, 8, color, pattern, 0, 0, 8, 8, msbfirst=msbfirst, alpha=alpha)
    imageblitex(
        image,
        width,
        height,
        x0,
        y0,
        x1,
        y1,
        hand,
        8,
        8,
        0,
        0,
        ropForeground=0x88,
        wraparound=wraparound,
        alpha=alpha,
    )
    imageblitex(
        image,
        width,
        height,
        x0,
        y0,
        x1,
        y1,
        hxor,
        8,
        8,
        0,
        0,
        ropForeground=0x66,
        wraparound=wraparound,
        alpha=alpha,
    )

# Draw a wraparound copy of an image on another image.
# 'dstimage' and 'srcimage' are the destination and source images.
# 'pattern' is a brush pattern image (also known as a stipple).
# 'srcimage', 'maskimage', and 'patternimage' are optional.
# 'dstimage', 'srcimage', 'patternimage', and 'maskimage', to the extent given,
# have the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False, and the alpha channel
# (opacity channel) of the images, if any, is
# subject to the image operation in the same way as the red, green, and blue channels.
# (Windows's graphical device interface [GDI] supports transparent
# pixels in brush patterns, but only for brushes
# with predefined hatch patterns and only in the gaps between hatch marks; in
# bit block transfer operations such as BitBlt, these transparent pixels are
# filled with the background color whether the background mode is
# transparent or opaque; in line and shape drawing operations (which this
# method doesn't belong in), if the background mode is transparent, only
# the nontransparent pixels are drawn and affected by raster operations.)
# 'patternOrgX' and 'patternOrgY' are offsets from the destination's upper left
# corner where the upper-left corner of the brush pattern image would
# be drawn if a repetition of the brush pattern were to be drawn across the
# whole destination image.  The default for both parameters is 0.
# 'x0src' and 'y0src' are offsets from the destination image's upper-left corner
# where the source image's upper-left corner will be drawn.
# 'x0mask' and 'y0mask' are offsets from the source image's upper-left corner
# and correspond to pixels in the source image.
#
# 'ropForeground' is a foreground ternary raster operation between the bits of the
# destination, those of the source, and those of the brush pattern; the low 4
# bits give the binary raster
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
#
# The following are commonly seen ternary raster operations:
# 0x00: Turn destination "black" (bits are all zeros).
# 0x11: "Not source erase", "not merge pen" ("pen" is understood as the source pixel).
# 0x22: "Mask not pen".
# 0x33: "Not source copy", "not copy pen".
# 0x44: "Source erase", "mask pen not".
# 0x55: "Destination invert".
# 0x66: "Source invert", "XOR pen".
# 0x77: "Not mask pen".
# 0x88: "Source AND".
# 0x99: "Not XOR pen".
# 0xAA: "No-op"; destination is left unchanged.
# 0xBB: "Merge paint", "merge not pen".
# 0xCC: "Source copy"; copy source to destination.
# 0xDD: "Merge pen not".
# 0xEE: "Source paint"; "merge pen not"; "source OR destination".
# 0xFF: Turn destination "white" (bits are all ones).
# 0x5A: Pattern invert.
# 0xC0: "Merge copy"; where pattern pixel's bits are all ones, copy the source to the
# destination; where pattern pixel's bits are all zeros, set the destination
# pixel's bits to all zeros.
# 0xF0: Pattern copy.
# 0xFB: "Pattern paint".
#
# 0xB8 is a useful ternary raster operation: if the source is a two-level image in which
# each pixel's bits are either all zeros ("black") or all ones ("white"), this operation fills,
# with the pattern, the areas where the source is 0 ("black").
#
# 'maskimage' is ideally a two-level image in which each pixel's bits are either all zeros
# ("black") or all ones ("white"), but it doesn't have to be.
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
        # No pattern needed
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
    needDestination = True
    if (
        (ropForeground & 0x03) != 1
        and ((ropForeground >> 2) & 0x03) != 1
        and ((ropForeground >> 4) & 0x03) != 1
        and ((ropForeground >> 6) & 0x03) != 1
        and (ropForeground & 0x03) != 2
        and ((ropForeground >> 2) & 0x03) != 2
        and ((ropForeground >> 4) & 0x03) != 2
        and ((ropForeground >> 6) & 0x03) != 2
        and (
            ropBackground == ropForeground
            or (
                (ropBackground & 0x03) != 1
                and ((ropBackground >> 2) & 0x03) != 1
                and ((ropBackground >> 4) & 0x03) != 1
                and ((ropBackground >> 6) & 0x03) != 1
                and (ropBackground & 0x03) != 2
                and ((ropBackground >> 2) & 0x03) != 2
                and ((ropBackground >> 4) & 0x03) != 2
                and ((ropBackground >> 6) & 0x03) != 2
            )
        )
    ):
        # No need to read from destination
        needDestination = False
    if srcimage is dstimage or patternimage is dstimage or maskimage is dstimage:
        # Avoid overlapping source/pattern/mask with destination
        return imageblitex(
            dstimage,
            dstwidth,
            dstheight,
            x0,
            y0,
            x1,
            y1,
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
            for i in range(pixelsize):
                s1 = srcimage[srcpos + i] if srcimage else 0
                d1 = dstimage[dstpos + i] if dstimage and needDestination else 0
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

# All images have the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False, and the alpha channel (opacity channel) of the images, if any, is
# subject to the image operation in the same way as the red, green, and blue channels.
# 'ropForeground' and 'ropBackground' are as in imageblitex(), except that
# 'ropForeground' is used where the source color is not 'transcolor' or if
# 'transcolor' is None (in this sense, if 'transcolor' has three elements and 'alpha' is True,
# the fourth element, the alpha component, is treated as 255 so that 'transcolor' is an opaque
# color); 'ropBackground' is used elsewhere.
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
    needDestination = True
    if (
        (ropForeground & 0x03) != 1
        and ((ropForeground >> 2) & 0x03) != 1
        and ((ropForeground >> 4) & 0x03) != 1
        and ((ropForeground >> 6) & 0x03) != 1
        and (ropForeground & 0x03) != 2
        and ((ropForeground >> 2) & 0x03) != 2
        and ((ropForeground >> 4) & 0x03) != 2
        and ((ropForeground >> 6) & 0x03) != 2
        and (
            ropBackground == ropForeground
            or (
                (ropBackground & 0x03) != 1
                and ((ropBackground >> 2) & 0x03) != 1
                and ((ropBackground >> 4) & 0x03) != 1
                and ((ropBackground >> 6) & 0x03) != 1
                and (ropBackground & 0x03) != 2
                and ((ropBackground >> 2) & 0x03) != 2
                and ((ropBackground >> 4) & 0x03) != 2
                and ((ropBackground >> 6) & 0x03) != 2
            )
        )
    ):
        # No need to read from destination
        needDestination = False
    if srcimage is dstimage or patternimage is dstimage:
        # Avoid overlapping source/pattern with destination
        return imagetransblit(
            dstimage,
            dstwidth,
            dstheight,
            x0,
            y0,
            x1,
            y1,
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
                    and (
                        (not alpha)
                        or len(transcolor) == 3
                        or srcimage[srcpos + 3] == transcolor[3]
                    )
                )
                else 0xFF
            )
            for i in range(pixelsize):
                s1 = srcimage[srcpos + i] if srcimage else 0
                d1 = dstimage[dstpos + i] if dstimage and needDestination else 0
                p1 = patternimage[patpos + i] if patternimage else 0
                sdl = _applyrop(d1, s1, ropForeground & 0xF)
                sdh = _applyrop(d1, s1, (ropForeground >> 4) & 0xF)
                sdp = (p1 & sdh) ^ ((~p1) & sdl)
                sdl = _applyrop(d1, s1, ropBackground & 0xF)
                sdh = _applyrop(d1, s1, (ropBackground >> 4) & 0xF)
                sdpb = (p1 & sdh) ^ ((~p1) & sdl)
                sdp = (m1 & sdp) ^ ((~m1) & sdpb)
                dstimage[dstpos + i] = sdp

def _porterduff8bitalpha(d, di, s, si, op, sa255, alpha=True):
    sa = sa255
    da = d[di + 3] if alpha else 255
    match op:
        case 0:  # source over
            den = da * (sa - 255) - 255 * sa
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = (da * d[di] * (sa - 255) - 255 * sa * s[si]) // den
                d[di + 1] = (da * d[di + 1] * (sa - 255) - 255 * sa * s[si + 1]) // den
                d[di + 2] = (da * d[di + 2] * (sa - 255) - 255 * sa * s[si + 2]) // den
                if alpha:
                    d[di + 3] = da + sa - da * sa // 255
        case 1:  # source in
            d[di] = s[si]
            d[di + 1] = s[si + 1]
            d[di + 2] = s[si + 2]
            if alpha:
                d[di + 3] = (da * sa) // 255
        case 2:  # source held out
            d[di] = s[si]
            d[di + 1] = s[si + 1]
            d[di + 2] = s[si + 2]
            if alpha:
                d[di + 3] = ((255 - da) * sa) // 255
        case 3:  # source atop
            d[di] = (sa * s[si] - d[di] * (sa - 255)) // 255
            d[di + 1] = (sa * s[si + 1] - d[di + 1] * (sa - 255)) // 255
            d[di + 2] = (sa * s[si + 2] - d[di + 2] * (sa - 255)) // 255
            if alpha:
                d[di + 3] = da
        case 4:  # destination over
            den = sa * (da - 255) - 255 * da
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = (sa * s[si] * (da - 255) - 255 * da * d[di]) // den
                d[di + 1] = (sa * s[si + 1] * (da - 255) - 255 * da * d[di + 1]) // den
                d[di + 2] = (sa * s[si + 2] * (da - 255) - 255 * da * d[di + 2]) // den
                if alpha:
                    d[di + 3] = sa + da - sa * da // 255
        case 5:  # destination in
            # Destination RGB left unchanged
            if alpha:
                d[di + 3] = (sa * da) // 255
        case 6:  # destination held out
            # Destination RGB left unchanged
            if alpha:
                d[di + 3] = ((255 - sa) * da) // 255
        case 7:  # destination atop
            d[di] = (da * d[di] - s[si] * (da - 255)) // 255
            d[di + 1] = (da * d[di + 1] - s[si + 1] * (da - 255)) // 255
            d[di + 2] = (da * d[di + 2] - s[si + 2] * (da - 255)) // 255
            if alpha:
                d[di + 3] = sa
        case 8:  # source
            d[di] = s[si]
            d[di + 1] = s[si + 1]
            d[di + 2] = s[si + 2]
            if alpha:
                d[di + 3] = sa
        case 9:  # destination
            pass
        case 10:  # clear
            d[di] = 0
            d[di + 1] = 0
            d[di + 2] = 0
            if alpha:
                d[di + 3] = 0
        case 11:  # XOR
            den = -2 * da * sa + 255 * (da + sa)
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = (
                    -da * d[di] * sa
                    + 255 * da * d[di]
                    - da * sa * s[si]
                    + 255 * sa * s[si]
                ) // den
                d[di + 1] = (
                    -da * d[di + 1] * sa
                    + 255 * da * d[di + 1]
                    - da * sa * s[si + 1]
                    + 255 * sa * s[si + 1]
                ) // den
                d[di + 2] = (
                    -da * d[di + 2] * sa
                    + 255 * da * d[di + 2]
                    - da * sa * s[si + 2]
                    + 255 * sa * s[si + 2]
                ) // den
                if alpha:
                    d[di + 3] = -2 * da * sa // 255 + da + sa
        case 12:  # plus
            den = da + sa
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = min(255, (da * d[di] + sa * s[si]) // den)
                d[di + 1] = min(255, (da * d[di + 1] + sa * s[si + 1]) // den)
                d[di + 2] = min(255, (da * d[di + 2] + sa * s[si + 2]) // den)
                if alpha:
                    d[di + 3] = min(255, den)
        case _:
            raise ValueError

def _porterduff16bitalpha(d, di, s, si, op, sa65025, alpha=True):
    sa = sa65025
    da = d[di + 3] if alpha else 255
    if sa == 65025:
        _porterduff8bitalpha(d, di, s, si, op, 255, alpha=alpha)
        return
    elif sa == 0:
        _porterduff8bitalpha(d, di, s, si, op, 0, alpha=alpha)
        return
    match op:
        case 0:  # source over
            den = da * (sa - 65025) - 255 * sa
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = (da * d[di] * (sa - 65025) - 255 * sa * s[si]) // den
                d[di + 1] = (
                    da * d[di + 1] * (sa - 65025) - 255 * sa * s[si + 1]
                ) // den
                d[di + 2] = (
                    da * d[di + 2] * (sa - 65025) - 255 * sa * s[si + 2]
                ) // den
                if alpha:
                    d[di + 3] = (da * 65025 + sa * 255 - da * sa) // 65025
        case 1:  # source in
            d[di] = s[si]
            d[di + 1] = s[si + 1]
            d[di + 2] = s[si + 2]
            if alpha:
                d[di + 3] = (da * sa) // 65025
        case 2:  # source held out
            d[di] = s[si]
            d[di + 1] = s[si + 1]
            d[di + 2] = s[si + 2]
            if alpha:
                d[di + 3] = ((255 - da) * sa) // 65025
        case 3:  # source atop
            d[di] = (sa * s[si] - d[di] * (sa - 65025)) // 65025
            d[di + 1] = (sa * s[si + 1] - d[di + 1] * (sa - 65025)) // 65025
            d[di + 2] = (sa * s[si + 2] - d[di + 2] * (sa - 65025)) // 65025
            if alpha:
                d[di + 3] = da
        case 4:  # destination over
            den = sa * (da - 255) - 65025 * da
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = (sa * s[si] * (da - 255) - 65025 * da * d[di]) // den
                d[di + 1] = (
                    sa * s[si + 1] * (da - 255) - 65025 * da * d[di + 1]
                ) // den
                d[di + 2] = (
                    sa * s[si + 2] * (da - 255) - 65025 * da * d[di + 2]
                ) // den
                if alpha:
                    d[di + 3] = (sa * 255 + da * 65025 - sa * da) // 65025
        case 5:  # destination in
            # Destination RGB left unchanged
            if alpha:
                d[di + 3] = (sa * da) // 65025
        case 6:  # destination held out
            # Destination RGB left unchanged
            if alpha:
                d[di + 3] = ((65025 - sa) * da) // 65025
        case 7:  # destination atop
            d[di] = (da * d[di] - s[si] * (da - 255)) // 255
            d[di + 1] = (da * d[di + 1] - s[si + 1] * (da - 255)) // 255
            d[di + 2] = (da * d[di + 2] - s[si + 2] * (da - 255)) // 255
            if alpha:
                d[di + 3] = sa // 255
        case 8:  # source
            d[di] = s[si]
            d[di + 1] = s[si + 1]
            d[di + 2] = s[si + 2]
            if alpha:
                d[di + 3] = sa // 255
        case 9:  # destination
            pass
        case 10:  # clear
            d[di] = 0
            d[di + 1] = 0
            d[di + 2] = 0
            if alpha:
                d[di + 3] = 0
        case 11:  # XOR
            den = -2 * da * sa + 65025 * da + 255 * sa
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = (
                    -da * d[di] * sa
                    + 65025 * da * d[di]
                    - da * sa * s[si]
                    + 255 * sa * s[si]
                ) // den
                d[di + 1] = (
                    -da * d[di + 1] * sa
                    + 65025 * da * d[di + 1]
                    - da * sa * s[si + 1]
                    + 255 * sa * s[si + 1]
                ) // den
                d[di + 2] = (
                    -da * d[di + 2] * sa
                    + 65025 * da * d[di + 2]
                    - da * sa * s[si + 2]
                    + 255 * sa * s[si + 2]
                ) // den
                if alpha:
                    d[di + 3] = (-2 * da * sa + sa * 255) // 255 + da
        case 12:  # plus
            den = 255 * da + sa
            if den == 0:
                d[di] = d[di + 1] = d[di + 2] = 0
                if alpha:
                    d[di + 3] = 0
            else:
                d[di] = min(255, (255 * da * d[di] + sa * s[si]) // den)
                d[di + 1] = min(255, (255 * da * d[di + 1] + sa * s[si + 1]) // den)
                d[di + 2] = min(255, (255 * da * d[di + 2] + sa * s[si + 2]) // den)
                if alpha:
                    d[di + 3] = min(255, den // 255)
        case _:
            raise ValueError

# Performs a source-over composition involving a source image with an alpha channel
# and a destination image without an alpha channel.  The destination rectangle
# begins at x0 and y0 and has width ('x1'-'x0') and height ('y1'-'y0'),
# and wraps around the destination if 'wraparound'
# is True.
# 'dstimage' has the same format returned by the blankimage() method with alpha=False; 'srcimage', with alpha=True.
# If 'srcimage' is None, a source image with all zeros and an alpha of 0 for all pixels is used as the source, even if
# 'alpha' is False.  The red, green, and blue components for 'srcimage' are assumed to be "nonpremultiplied", that
# is, not multiplied beforehand by the alpha component divided by 255.
# If 'screendoor' is True (default is 'False'), translucency (semitransparency) is
# simulated by scattering transparent and opaque pixels, or dithering (a process also known
# as stippled or screen-door transparency).
#
# Blending Note: Operations that involve the blending of two RGB (red-green-
# blue) colors work best if the RGB color space is linear.  This is not the case
# for the sRGB color space, which is the color space assumed for images created
# using the blankimage() method.  Moreover, converting an image from a nonlinear
# to a linear color space and back can lead to data loss especially if the image's color
# components are 8 bits or fewer in length (as with images returned by blankimage()).
# This function does not do any such conversion.  The Blending Note does not
# apply to this function if 'screendoor' is True or if both 'sourceAlpha' is 0 or 255 and
# the input images have only transparent and
# opaque pixels (the alpha component of each color is either 0 or 255); in that case,
# the images can be in a linear or nonlinear RGB color space.
def imagesrcover(
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
    wraparound=True,
    sourceAlpha=255,
    screendoor=False,
):
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
    if (not srcimage) or sourceAlpha == 0:
        return
    if srcimage is dstimage:
        # Avoid overlapping source/pattern with destination
        return imagesrcover(
            dstimage,
            dstwidth,
            dstheight,
            x0,
            y0,
            x1,
            y1,
            (
                srcimage
                if srcimage is not dstimage
                else ([x for x in srcimage] if srcimage else None)
            ),
            srcwidth,
            srcheight,
            x0src,
            y0src,
            wraparound=wraparound,
            sourceAlpha=sourceAlpha,
            screendoor=screendoor,
        )
    for y in range(y1 - y0):
        dy = y0 + y
        if wraparound:
            dy %= dstheight
        if (not wraparound) and dy < 0 or dy >= dstheight:
            continue
        sy = (y0src + y) * srcwidth * 4
        dypos = dy
        dy = dy * dstwidth * 3
        for x in range(x1 - x0):
            dx = x0 + x
            if wraparound:
                dx %= dstwidth
            if (not wraparound) and dx < 0 or dx >= dstwidth:
                continue
            dstpos = dy + dx * 3
            srcpos = sy + (x0src + x) * 4
            sa = srcimage[srcpos + 3]
            if sourceAlpha == 255 and not screendoor:
                dstimage[dstpos] = (
                    sa * srcimage[srcpos] - dstimage[dstpos] * (sa - 255)
                ) // 255
                dstimage[dstpos + 1] = (
                    sa * srcimage[srcpos + 1] - dstimage[dstpos + 1] * (sa - 255)
                ) // 255
                dstimage[dstpos + 2] = (
                    sa * srcimage[srcpos + 2] - dstimage[dstpos + 2] * (sa - 255)
                ) // 255
            else:
                sa *= sourceAlpha
                if screendoor:
                    bdither = _DitherMatrix[(dypos & 7) * 8 + (dx & 7)]
                    if bdither < sa * 64 // 65025:
                        dstimage[dstpos] = srcimage[srcpos]
                        dstimage[dstpos + 1] = srcimage[srcpos + 1]
                        dstimage[dstpos + 2] = srcimage[srcpos + 2]
                else:
                    dstimage[dstpos] = (
                        sa * srcimage[srcpos] - dstimage[dstpos] * (sa - 65025)
                    ) // 65025
                    dstimage[dstpos + 1] = (
                        sa * srcimage[srcpos + 1] - dstimage[dstpos + 1] * (sa - 65025)
                    ) // 65025
                    dstimage[dstpos + 2] = (
                        sa * srcimage[srcpos + 2] - dstimage[dstpos + 2] * (sa - 65025)
                    ) // 65025

# Performs an image composition involving a source image and a destination image.  The destination rectangle
# begins at x0 and y0 and has width ('x1'-'x0') and height ('y1'-'y0'), and
# wraps around the destination if 'wraparound'
# is True.  Unlike with the original Porter&ndash;Duff composition operators, areas of the destination outside
# the destination rectangle are left unchanged.
# 'dstimage' and 'srcimage' have the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is True.  If 'alpha' is False, this method behaves as though both images
# had an alpha channel with all pixel's alpha components set to 255 (so that the two images are treated as opaque).
# If 'srcimage' is None, a source image with all zeros and an alpha of 0 for all pixels is used as the source, even if
# 'alpha' is False.  The red, green, and blue components for each image are assumed to be "nonpremultiplied", that
# is, not multiplied beforehand by the alpha component divided by 255.
# 'porterDuffOp' is one of the following operators: 0 = source over;
# 1 = source in; 2 = source held out; 3 = source atop; 4 = destination over;
# 5 = destination in; 6 = destination held out; 7 = destination atop;
# 8 = copy source; 9 = copy destination; 10 = clear; 11 = XOR; 12 = plus.
# The default value is 0, source over.
# If 'screendoor' is True (default is 'False'), translucency (semitransparency) is simulated
# by scattering transparent and opaque pixels, or dithering (a process also known as stippled
# or screen-door transparency).
#
# Blending Note: Operations that involve the blending of two RGB (red-green-
# blue) colors work best if the RGB color space is linear.  This is not the case
# for the sRGB color space, which is the color space assumed for images created
# using the blankimage() method.  Moreover, converting an image from a nonlinear
# to a linear color space and back can lead to data loss especially if the image's color
# components are 8 bits or fewer in length (as with images returned by blankimage()).
# This function does not do any such conversion.  The Blending Note does not
# apply to this function if 'screendoor' is True or if both 'sourceAlpha' is 0 or 255 and
# the input images have only transparent and
# opaque pixels (the alpha component of each color is either 0 or 255); in that case,
# the images can be in a linear or nonlinear RGB color space.
def imagecomposite(
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
    porterDuffOp=0,
    wraparound=True,
    alpha=True,
    sourceAlpha=255,
    screendoor=False,
):
    if porterDuffOp < 0 or porterDuffOp > 12:
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
    if porterDuffOp == 0 and ((not srcimage) or sourceAlpha == 0):
        return
    if (not alpha) and (porterDuffOp == 5 or porterDuffOp == 6):
        # destination in and destination held out operators
        # have no visible effect when alpha=False
        return
    if porterDuffOp == 9:
        # Destination left unchanged
        return
    if srcimage is dstimage:
        # Avoid overlapping source/pattern with destination
        return imagecomposite(
            dstimage,
            dstwidth,
            dstheight,
            x0,
            y0,
            x1,
            y1,
            (
                srcimage
                if srcimage is not dstimage
                else ([x for x in srcimage] if srcimage else None)
            ),
            srcwidth,
            srcheight,
            x0src,
            y0src,
            porterDuffOp=porterDuffOp,
            wraparound=wraparound,
            alpha=alpha,
            sourceAlpha=sourceAlpha,
            screendoor=screendoor,
        )
    pixelsize = 4 if alpha else 3
    fakesrc = [0, 0, 0, 0]
    for y in range(y1 - y0):
        dy = y0 + y
        if wraparound:
            dy %= dstheight
        if (not wraparound) and dy < 0 or dy >= dstheight:
            continue
        sy = (y0src + y) * srcwidth * pixelsize
        dy = dy * dstwidth * pixelsize
        for x in range(x1 - x0):
            dx = x0 + x
            if wraparound:
                dx %= dstwidth
            if (not wraparound) and dx < 0 or dx >= dstwidth:
                continue
            dstpos = dy + dx * pixelsize
            srcpos = sy + (x0src + x) * pixelsize
            if not srcimage:
                _porterduff(dstimage, dstpos, fakesrc, 0, porterDuffOp, alpha=alpha)
            else:
                srca = srcimage[srcpos + 3] if alpha else 255
                srca *= sourceAlpha
                if screendoor:
                    bdither = _DitherMatrix[(dypos & 7) * 8 + (dx & 7)]
                    if not (bdither < srca * 64 // 65025):
                        continue
                    srca = 65025
                _porterduff16bitalpha(
                    dstimage,
                    dstpos,
                    srcimage,
                    srcpos,
                    porterDuffOp,
                    sa65025=srca,
                    alpha=alpha,
                )

# Bilinear interpolation
def _bilerp(y0x0, y0x1, y1x0, y1x1, tx, ty):
    y0 = y0x0 + (y0x1 - y0x0) * tx
    y1 = y1x0 + (y1x1 - y1x0) * tx
    return y0 + (y1 - y0) * ty

# Gets the color of the in-between pixel at the specified point
# of the image, using bilinear interpolation.
# 'image' has the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is True.
# 'width' and 'height' is the image's width and height.
# 'x' is the point's x-coordinate, which need not be an integer.
# 'y' is the point's y-coordinate, which need not be an integer.
# If 'wraparound' is True (the default), an out-of-bounds point ('x','y') will
# undergo a wraparound adjustment, as though the specified image were part
# of an "infinite" tiling.  If False, an out-of-bounds point is adjusted to
# lie in the image (0<=x<='width'-1; 0<=y<='height'-1).
#
# Blending Note: Operations that involve the blending of two RGB (red-green-
# blue) colors work best if the RGB color space is linear.  This is not the case
# for the sRGB color space, which is the color space assumed for images created
# using the blankimage() method.  Moreover, converting an image from a nonlinear
# to a linear color space and back can lead to data loss especially if the image's color
# components are 8 bits or fewer in length (as with images returned by blankimage()).
# This function does not do any such conversion.
def imagept(image, width, height, x, y, alpha=False, wraparound=True):
    if width <= 0 or height <= 0:
        raise ValueError
    if not image:
        raise ValueError
    pixelBytes = 4 if alpha else 3
    if width * height * pixelBytes > len(image):
        raise ValueError
    if wraparound:
        x = x % width
        y = y % height
        xi = int(x)
        xi1 = (xi + 1) % width
        yi = int(y)
        yi1 = (yi + 1) % height
    else:
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))
        xi = int(x)
        xi1 = min(width - 1, (xi + 1))
        yi = int(y)
        yi1 = min(height - 1, (yi + 1))
    index = (yi * width + xi) * pixelBytes
    y0x0 = image[index : index + pixelBytes]
    index = (yi * width + xi1) * pixelBytes
    y0x1 = image[index : index + pixelBytes]
    index = (yi1 * width + xi) * pixelBytes
    y1x0 = image[index : index + pixelBytes]
    index = (yi1 * width + xi1) * pixelBytes
    y1x1 = image[index : index + pixelBytes]
    ret = [
        ((int(_bilerp(y0x0[i], y0x1[i], y1x0[i], y1x1[i], x - xi, y - yi))))
        for i in range(pixelBytes)
    ]
    return ret

# Wallpaper group Pmm.  Source rectangle
# takes the upper-left quarter of the image
# and is reflected and repeated to cover the
# remaining image. No requirements on the source to generate seamless images with this group function.
def pmm(x, y):
    if x > 0.5:
        if y < 0.5:
            return ((0.5 - (x - 0.5)) * 2, y * 2)
        else:
            return ((0.5 - (x - 0.5)) * 2, (0.5 - (y - 0.5)) * 2)
    else:
        if y < 0.5:
            return (x * 2, y * 2)
        else:
            return (x * 2, (0.5 - (y - 0.5)) * 2)

# Wallpaper group P4m. Source triangle is formed
# by the upper-left, upper-right, and lower-left corners of
# a rectangle that takes the upper-left quarter of the destination image
# (triangle's right angle is at the rectangle's upper-left corner).
def p4mul(x, y):
    rx, ry = pmm(x, y)
    if rx + ry < 1.0:
        return (rx, ry)
    return (1.0 - ry, 1.0 - rx)

# Wallpaper group P4m. Source triangle is formed
# by the upper-left, upper-right, and lower-right corners of
# a rectangle that takes the upper-left quarter of the destination image
# (triangle's right angle is at the rectangle's upper-right corner).
# No requirements on the source to generate seamless images with this group function.
def p4mur(x, y):
    rx, ry = pmm(x, y)
    if (1 - rx) + ry < 1.0:
        return (rx, ry)
    return (ry, rx)

# Wallpaper group P4m. Source triangle is formed
# by the upper-left, lower-left, and lower-right corners of
# a rectangle that takes the upper-left quarter of the destination image
# (triangle's right angle is at the rectangle's lower-left corner).
# No requirements on the source to generate seamless images with this group function.
def p4mll(x, y):
    rx, ry = pmm(x, y)
    if rx + (1 - ry) < 1.0:
        return (rx, ry)
    return (ry, rx)

# Wallpaper group P4m. Source triangle is formed
# by the upper-right, lower-left, and lower-right corners of
# a rectangle that takes the upper-left quarter of the destination image
# (triangle's right angle is at the rectangle's lower-right corner).
# No requirements on the source to generate seamless images with this group function.
def p4mlr(x, y):
    rx, ry = pmm(x, y)
    if (1 - rx) + (1 - ry) < 1.0:
        return (rx, ry)
    return (1.0 - ry, 1.0 - rx)

# Wallpaper group P4m. Same as p4mll().
def p4m(x, y):
    return p4mll(x, y)

# Wallpaper group P4m. Same as p4mur().
def p4malt(x, y):
    return p4mur(x, y)

# Wallpaper group P3m1.  Source shape is as described in p6().
# No requirements on the source to generate seamless images with this group function.
def p3m1(x, y):
    rx, ry = _p3m1(x, y)
    rx = max(0, min(1, rx))
    ry = max(0, min(1, ry))
    return (rx, ry)

def _p3m1(x, y):
    xx = x * 6
    xarea = min(5, max(0, int(xx)))
    xpos = xx - xarea
    yarea = 0 if y < 0.5 else 1
    ypos = y * 2 if y < 0.5 else (y - 0.5) * 2
    isdiag1 = (xarea + yarea) % 2 == 0
    leftHalf = (xpos + ypos) < 1.0 if isdiag1 else (xpos + (1 - ypos)) < 1.0
    match (xarea, yarea, leftHalf):
        case (1, 1, False) | (4, 0, False):
            # Left half of source triangle (lower middle of hexagon)
            return (xpos / 2, ypos)
        case (2, 1, True) | (5, 0, True):
            # Right half of source triangle (lower middle)
            return (xpos / 2 + 0.5, ypos)
        case (0, 0, False) | (3, 1, False):
            # upper left, left half
            xp = xpos / 2
            yp = 1 - ypos
            newx = -xp / 2 - 3 * yp / 4 + 1
            newy = -xp + yp / 2 + 1
            return (newx, newy)
        case (1, 0, True) | (4, 1, True):
            # upper left, right half
            xp = (xpos / 2) + 0.5
            yp = 1 - ypos
            newx = -xp / 2 - 3 * yp / 4 + 1
            newy = -xp + yp / 2 + 1
            return (newx, newy)
        case (2, 0, False) | (5, 1, False):
            # upper right, left half
            xp = xpos / 2
            yp = 1 - ypos
            newx = -xp / 2 + 3 * yp / 4 + 0.5
            newy = xp + yp / 2
            return (newx, newy)
        case (3, 0, True) | (0, 1, True):
            # upper right, right half
            xp = (xpos / 2) + 0.5
            yp = 1 - ypos
            newx = -xp / 2 + 3 * yp / 4 + 0.5
            newy = xp + yp / 2
            return (newx, newy)
        case (1, 0, False) | (4, 1, False):
            # upper middle, left half
            newx = xpos / 2
            return (newx, 1 - ypos)
        case (2, 0, True) | (5, 1, True):
            # upper middle, right half
            newx = xpos / 2 + 0.5
            return (newx, 1 - ypos)
        case (0, 1, False) | (3, 0, False):
            # lower left, left half
            xp = xpos / 2
            yp = ypos
            newx = -xp / 2 - 3 * yp / 4 + 1
            newy = -xp + yp / 2 + 1
            return (newx, newy)
        case (1, 1, True) | (4, 0, True):
            # lower left, right half
            xp = (xpos / 2) + 0.5
            yp = ypos
            newx = -xp / 2 - 3 * yp / 4 + 1
            newy = -xp + yp / 2 + 1
            return (newx, newy)
        case (2, 1, False) | (5, 0, False):
            # lower right, left half
            xp = xpos / 2
            yp = ypos
            newx = -xp / 2 + 3 * yp / 4 + 0.5
            newy = xp + yp / 2
            return (newx, newy)
        case (3, 1, True) | (0, 0, True):
            # lower right, right half
            xp = (xpos / 2) + 0.5
            yp = ypos
            newx = -xp / 2 + 3 * yp / 4 + 0.5
            newy = xp + yp / 2
            return (newx, newy)
        case _:
            # unknown
            return (0, 0)

# Wallpaper group P6.
# Source triangle is formed from the upper midpoint (point A), lower-left corner (point B),
# and lower-right corner (point C) of a rectangle.  Edge AB is the edge between
# A and B; edge AC, between A and C.
# Source triangle is part of a scaled regular hexagon that is oriented
# such that the hexagon's lower edge is horizontal; the triangle's upper
# point is at the hexagon's center, and the triangle's lower edge is the
# same as the hexagon's lower edge.  To generate seamless images with this group function,
# the source shape should satisfy the following: Edge AB is a mirrored edge AC; lower edge is mirrored.
def p6(x, y):
    rx, ry = p3m1(x, y)
    if _isForward(x, y):
        return (rx, ry)
    return (1 - rx, ry)

# Wallpaper group P3.  Source shape is a parallelogram with the following
# vertices: A is (0, 0); B is (W*2/3, 0); C is (W, H); D is (W/3, H),
# where W and H are the width and height, respectively, of a rectangle that
# tightly covers the source shape.  Edge AD is the edge between A and D; edge BC,
# between B and C. To generate seamless images with this group function,
# the source shape should satisfy the following: Upper edge is a reversed
# edge BC; lower edge is a reversed edge AD.
def p3(x, y):
    rx, ry = p3m1(x, y)
    if _isForward(x, y):
        return (max(0, min(1, rx * 2 / 3 + (1 / 3))), ry)
    else:
        nx = -rx / 3 - ry / 2 + 5 / 6
        ny = -rx + ry / 2 + 1 / 2
        nx = max(0, min(1, nx))
        ny = max(0, min(1, ny))
        return (nx, ny)

# Wallpaper group P31m.  Source shape is a quadrilateral with the following
# vertices: A is (0, H/2); B is (W/3, H); C is (W, H); D is (W, 0), where
# W and H are the width and height, respectively, of a rectangle that tightly
# covers the source shape. Edge AB is the edge between A and B; edge BC,
# between B and C. To generate seamless images with this group function, the
# source shape should satisfy the following: Edge AB is a mirrored edge BC.
def p31m(x, y):
    rx, ry = p6m(x, y)
    if _isForward(x, y):
        return (max(0, min(1, rx * 4 / 3 + (1 / 3))), ry)
    else:
        nx = -2 * rx / 3 - ry + 4 / 3
        ny = -rx + ry / 2 + 1 / 2
        nx = max(0, min(1, nx))
        ny = max(0, min(1, ny))
        return (nx, ny)

def _isForward(x, y):
    xx = x * 6
    xarea = min(5, max(0, int(xx)))
    xpos = xx - xarea
    yarea = 0 if y < 0.5 else 1
    ypos = y * 2 if y < 0.5 else (y - 0.5) * 2
    isdiag1 = (xarea + yarea) % 2 == 0
    leftHalf = (xpos + ypos) < 1.0 if isdiag1 else (xpos + (1 - ypos)) < 1.0
    match (xarea, yarea, leftHalf):
        case (
            (1, 1, False)
            | (4, 0, False)
            | (2, 1, True)
            | (5, 0, True)
            | (0, 0, False)
            | (3, 1, False)
            | (1, 0, True)
            | (4, 1, True)
            | (2, 0, False)
            | (5, 1, False)
            | (3, 0, True)
            | (0, 1, True)
        ):
            return True
        case _:
            return False

# Wallpaper group P6m (same source rectangle
# as p3m1(), but exposing only the left half of
# the triangle mentioned there).
# No requirements on the source to generate seamless images with this group function.
def p6m(x, y):
    rx, ry = p3m1(x, y)
    if rx > 0.5:
        rx = 1 - rx
    return (rx, ry)

# Wallpaper group P6m, alternative definition
# (same source rectangle as p3m1(), but exposing
# only the right half of the triangle described there).
# No requirements on the source to generate seamless images with this group function.
def p6malt(x, y):
    rx, ry = p3m1(x, y)
    if rx < 0.5:
        rx = 1 - rx
    return (rx, ry)

# Wallpaper group P3m1, alternative definition.
# Source triangle is isosceles and is formed from a rectangle
# by using the left edge as the triangle's
# and setting the triangle's right-hand point as the rectangle's
# right-hand midpoint.
# Source triangle is part of a scaled regular hexagon that is oriented
# such that the hexagon's left edge is vertical; the triangle's right-hand
# point is at the hexagon's center, and the triangle's left edge is the
# same as the hexagon's left edge.
# No requirements on the source to generate seamless images with this group function.
def p3m1alt1(x, y):
    rx, ry = p3m1(y, 1 - x)
    return (1 - ry, rx)

# Wallpaper group P3m1, alternative definition.
# Source triangle is isosceles and is formed from a rectangle
# by using the right edge as the triangle's
# and setting the triangle's left-hand point as the rectangle's
# left-hand midpoint.
# Source triangle is part of a scaled regular hexagon that is oriented
# such that the hexagon's right-hand edge is vertical; the triangle's left
# point is at the hexagon's center, and the triangle's right-hand edge is the
# same as the hexagon's right-hand edge.
# No requirements on the source to generate seamless images with this group function.
def p3m1alt2(x, y):
    rx, ry = p3m1(y, x)
    return (ry, rx)

# Wallpaper group P6m, alternative definition
# (same source rectangle as p3m1alt1(), but exposing
# only the upper half of the triangle described there).
# 'x' and 'y' are each 0 or greater
# and 1 or less.
# No requirements on the source to generate seamless images with this group function.
def p6malt1a(x, y):
    rx, ry = p3m1alt1(x, y)
    if ry > 0.5:
        ry = 1 - ry
    return (rx, ry)

# Wallpaper group P6m, alternative definition
# (same source rectangle as p3m1alt1(), but exposing
# only the lower half of the triangle described there).
# No requirements on the source to generate seamless images with this group function.
def p6malt1b(x, y):
    rx, ry = p3m1alt1(x, y)
    if ry < 0.5:
        ry = 1 - ry
    return (rx, ry)

# Wallpaper group P6m, alternative definition
# (same source rectangle as p3m1alt2(), but exposing
# only the upper half of the triangle described there).
# No requirements on the source to generate seamless images with this group function.
def p6malt2a(x, y):
    rx, ry = p3m1alt2(x, y)
    if ry > 0.5:
        ry = 1 - ry
    return (rx, ry)

# Wallpaper group P6m, alternative definition
# (same source rectangle as p3m1alt2(), but exposing
# only the lower half of the triangle described there).
# No requirements on the source to generate seamless images with this group function.
def p6malt2b(x, y):
    rx, ry = p3m1alt2(x, y)
    if ry < 0.5:
        ry = 1 - ry
    return (rx, ry)

# Wallpaper group function that wraps another
# group function ('groupFunc'), in which the image
# after applying 'groupFunc'
# is rotated and scaled to fit into
# a diamond that touches the canvas's edges.
# This diamond will repeat to cover the rest of
# the canvas.
# If 'groupFunc' is None, 'groupFunc' is treated
# as the function p4m().
# This function is a variation of the
# wallpaper group implemented by 'groupFunc'; for example, if
# 'groupFunc' is a variation of wallpaper group P3m1,
# so is this group function.
# The source is recommended to meet the same requirements
# as those for 'groupFunc' to generate
# seamless images with this group function.
def diamondgroup(x, y, groupFunc=None):
    if not groupFunc:
        groupFunc = p4m
    # Translate the coordinates to achieve the desired
    # result to the final image.
    x, y = ((x + y - 0.5) % 1.0, (y + 0.5 - x) % 1.0)
    # Pass the translated coordinates to the wallpaper
    # group function.
    return groupFunc(x, y)

# Wallpaper group P1. Source rectangle takes the whole destination image.  To
# generate seamless images with this group function, the source shape should satisfy
# the following: Upper edge is same as lower edge, left edge is same as right edge.
def p1(x, y):
    return (x, y)

# Wallpaper group P2. Source triangle is formed from the upper-left, lower-left,
# and lower-right corners of a rectangle that covers the whole destination image.
# To generate seamless images with this group function, the source shape should
# satisfy the following: Lower edge is mirrored, left edge is mirrored.
def p2(x, y):
    if x + (1.0 - y) < 1.0:
        return (x, y)
    return (1.0 - x, 1.0 - y)

# Wallpaper group Cm. Source triangle is formed from the upper-left, lower-left,
# and lower-right corners of a rectangle that covers the whole destination image.
# To generate seamless images with this group function, the source shape should
# satisfy the following: Left edge is same as lower edge.
def cm(x, y):
    if x + (1.0 - y) < 1.0:
        return (x, y)
    return (y, x)

# Wallpaper group Cmm. Source triangle is formed from the upper midpoint,
# lower-left corner, and lower-right corner of a rectangle that takes the lower
# half of the destination image. To generate seamless images with this group
# function, the source shape should satisfy the following: Lower edge is mirrored.
def cmm(x, y):
    if x + y < 1.0:
        x, y = cm(1 - x, 1 - y)
        # Adjust result to tightly fit
        # source rectangle
        return (x, (y - 0.5) * 2.0)
    else:
        x, y = cm(x, y)
        # Ditto
        return (x, (y - 0.5) * 2.0)

# Wallpaper group Pm. Source rectangle takes the lower half of the destination image.
# To generate seamless images with this group function, the source shape should
# satisfy the following: Left edge is same as right edge.
def pm(x, y):
    if y > 0.5:
        return (x, (y - 0.5) * 2.0)
    return (x, 1 - y * 2.0)

# Wallpaper group Pg. Source rectangle takes the lower half of the destination image.
#  To generate seamless images with this group function, the source shape should satisfy
# the following: Upper edge is a reversed lower edge, left edge is same as right edge.
def pg(x, y):
    if y > 0.5:
        return (x, (y - 0.5) * 2.0)
    return (1 - x, y * 2.0)

# Wallpaper group Pmm. Same as pmm(), except the source rectangle
# takes the lower-left quarter of the destination image.
def pmmalt(x, y):
    return dw.pmm(x, (y + 0.5) % 1.0)

# Wallpaper group Pmg. Source rectangle takes the lower-left quarter of the
# destination image. To generate seamless images with this group function, the
# source shape should satisfy the following: Left edge is mirrored, right edge
# is mirrored.
def pmg(x, y):
    if x > 0.5:
        return pmmalt(x, (y + 0.5) % 1.0)
    return pmmalt(x, y)

# Wallpaper group P4. Source rectangle takes the lower-left quarter of the destination
#  image. To generate seamless images with this group function, the source shape
# should satisfy the following: Upper edge is a reversed lower edge, left edge is
# a reversed right edge.
def p4(x, y):
    if (x < 0.5 and y < 0.5) or (x > 0.5 and y > 0.5):
        return pmmalt(y, x)
    return pmmalt(x, y)

# Wallpaper group P4m.  Same as p4mul(), except the source rectangle
# takes the lower-left quarter of the destination image.
def p4mul2(x, y):
    rx, ry = pmmalt(x, y)
    if rx + ry < 1.0:
        return (rx, ry)
    return (1.0 - ry, 1.0 - rx)

# Wallpaper group P4m.  Same as p4mur(), except the source rectangle
# takes the lower-left quarter of the destination image.
def p4mur2(x, y):
    rx, ry = pmmalt(x, y)
    if (1 - rx) + ry < 1.0:
        return (rx, ry)
    return (ry, rx)

# Wallpaper group P4m.  Same as p4mll(), except the source rectangle
# takes the lower-left quarter of the destination image.
def p4mll2(x, y):
    rx, ry = pmmalt(x, y)
    if rx + (1 - ry) < 1.0:
        return (rx, ry)
    return (ry, rx)

# Wallpaper group P4m.  Same as p4mlr(), except the source rectangle
# takes the lower-left quarter of the destination image.
def p4mlr2(x, y):
    rx, ry = pmmalt(x, y)
    if (1 - rx) + (1 - ry) < 1.0:
        return (rx, ry)
    return (1.0 - ry, 1.0 - rx)

# Wallpaper group P4g. Source triangle is formed from the upper-left, lower-left,
# and lower-right corners of a rectangle that takes the lower-left quarter of the
# destination image. To generate seamless images with this group function, the
# source shape should satisfy the following: Lower edge is a reversed left edge
# (assuming the positive x-axis points to the right and the positive y-axis downward).
def p4g(x, y):
    return cm(*p4(x, y))

# Wallpaper group Pgg. Source rectangle takes the lower-left quarter of the
# destination image. To generate seamless images with this group function, the
# source shape should satisfy the following: Upper edge is a reversed lower edge,
# left edge is a reversed right edge.
def pgg(x, y):
    rx, ry = p4(x, y)
    if (x < 0.5 and y < 0.5) or (x > 0.5 and y > 0.5):
        return (ry, rx)
    return (rx, ry)

# Creates an image based on a portion of a source
# image, with the help of a wallpaper group function.
# 'srcImage' and the return value have the same format returned by the
# blankimage() method with the specified value of 'alpha'.
# 'sx0', 'sy0', 'sx1', and 'sy1' mark the source rectangle, which is
# allowed to go outside the bounds of the source image.
# 'sw' and 'sh' are the source image's width and height in pixels.
# 'width' and 'height' are the width and height of the image to create.
# If 'wraparound' is True (the default), an out-of-bounds source point will
# undergo a wraparound adjustment, as though the source image were part
# of an "infinite" tiling.  If False, an out-of-bounds point is adjusted to
# lie in the image (0<=x<='sw'-1; 0<=y<='sh'-1).
# 'groupFunc' is a wallpaper group function that translates output image
# coordinates to input image (source image) coordinates; default is pmm().
# 'groupFunc' takes two parameters: 'x' and 'y' are each 0 or greater
# and 1 or less, and are in relation to the destination image; 0 is leftmost
# or uppermost, and 1 is rightmost or bottommost, assuming that the positive x-axis points
# to the right and the positive y-axis points downward.  'groupFunc' returns a tuple indicating
# a point in relation to the source rectangle. The tuple has two elements,
# each 0 or greater and 1 or less: the first is the x-coordinate and the
# second, the y-coordinate; 0 is leftmost or uppermost, and 1 is
# rightmost or bottommost, with the assumption given earlier.
# The following wallpaper group functions in this module are intended to
# result in seamless tileable images from areas with arbitrary contents:
# pmm(), p4m(), p4malt(), p3m1(), p6m(), p6malt(), p3m1alt1(), p3m1alt2(),
# p6malt1a(), p6malt1b(), p6malt2a(), p6malt2b().  The functions implement
# variations of wallpaper groups Pmm, P4m, P3m1, and P6m, which are the only
# four that produce seamless images from areas with arbitrary contents.
# (There are seventeen wallpaper groups in all.)  The documentation for
# those and other wallpaper group functions in this module assumes that
# the positive x-axis points to
# the right and the positive y-axis points downward.
def wallpaperImage(
    width,
    height,
    srcImage,
    sw,
    sh,
    sx0,
    sy0,
    sx1,
    sy1,
    groupFunc=None,
    alpha=False,
    wraparound=True,
):
    if not groupFunc:
        groupFunc = pmm
    img = blankimage(width, height, alpha=alpha)
    for y in range(height):
        for x in range(width):
            px, py = groupFunc(x / width, y / height)
            sx = sx0 + (sx1 - sx0) * px
            sy = sy0 + (sy1 - sy0) * py
            pixel = imagept(
                srcImage, sw, sh, sx, sy, alpha=alpha, wraparound=wraparound
            )
            if alpha:
                setpixelalpha(img, width, height, x, y, pixel)
            else:
                setpixel(img, width, height, x, y, pixel)
    return img

# 'dstimage' and 'srcimage' have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
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
    alpha=False,
):
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
        ropForeground=0xCC,
        alpha=alpha,
    )

# Generate a Pm wallpaper group tiling pattern from a tileable image.
# For best results, the command should be applied to images whose
# last row's first half is a mirror of its second half.
# Returns a three-element list with the new image, its width, and its height.
# The input image and the returned image have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def groupPmImage(img, width, height, alpha=False):
    rw = width * 2 - 2
    rh = height
    ret = blankimage(rw, rh, alpha=alpha)
    imageblit(ret, rw, rh, 0, 0, img, width, height, alpha=alpha)
    img2 = imagereversecolumnorder([x for x in img], width, height, alpha=alpha)
    imageblitex(
        ret,
        rw,
        rh,
        width - 1,
        0,
        width * 2 - 2,
        height,
        img2,
        width,
        height,
        0,
        0,
        alpha=alpha,
    )
    return [ret, rw, rh]

# Generate a Pg wallpaper group tiling pattern from a tileable image.
# For best results, the command should be applied to images whose
# last column's first half is a mirror of its second half.
# Returns a three-element list with the new image, its width, and its height.
# The input image and the returned image have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def groupPgImage(img, width, height, alpha=False):
    rw = width
    rh = height * 2 - 2
    ret = blankimage(rw, rh, alpha=alpha)
    imageblit(ret, rw, rh, 0, 0, img, width, height, alpha=alpha)
    img2 = imagereverseroworder([x for x in img], width, height, alpha=alpha)
    imageblitex(
        ret,
        rw,
        rh,
        0,
        height - 1,
        width,
        height * 2 - 2,
        img2,
        width,
        height,
        0,
        0,
        alpha=alpha,
    )
    return [ret, rw, rh]

# Generate a tileable wallpaper pattern from an image that need not be tileable.
# Returns a three-element list with the new image, its width, and its height.
# The input image and the returned image have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def tileableImage(img, width, height, alpha=False):
    i2, w2, h2 = groupPmImage(img, width, height, alpha=alpha)
    return groupPgImage(i2, w2, h2, alpha=alpha)

# Returns an image with the specified destination width and height ('dstwidth', ´destheight'),
# in the form of a repeated tiling of the source image.
# 'srcimage' has the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def tiledImage(srcimage, srcwidth, srcheight, dstwidth, dstheight, alpha=False):
    if srcwidth < 0 or srcheight < 0 or dstwidth < 0 or dstheight < 0:
        raise ValueError
    image = blankimage(dstwidth, dstheight, alpha=alpha)
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
                alpha=alpha,
            )
    return image

# Images in 'sourceImages' have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def randomtiles(columns, rows, sourceImages, srcwidth, srcheight, alpha=False):
    if srcwidth <= 0 or srcheight <= 0:
        raise ValueError
    if (not sourceImages) or len(sourceImages) == 0:
        raise ValueError
    width = columns * srcwidth
    height = rows * srcheight
    image = blankimage(width, height, alpha=alpha)
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
                alpha=alpha,
            )
    return image

# Draws a box filled with a transparent vertical hatch pattern.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False
def verthatchedbox(image, width, height, color, x0, y0, x1, y1, alpha=False):
    pattern = [0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA]
    hatchedbox(image, width, height, color, pattern, x0, y0, x1, y1, alpha=alpha)

# Draws a box filled with a transparent horizontal hatch pattern.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False
def horizhatchedbox(image, width, height, color, x0, y0, x1, y1, alpha=False):
    pattern = [0xFF, 0, 0xFF, 0, 0xFF, 0, 0xFF, 0]
    hatchedbox(image, width, height, color, pattern, x0, y0, x1, y1, alpha=alpha)

# Image has the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False
def shadowedborderedbox(
    image, width, height, border, shadow, color1, color2, x0, y0, x1, y1, alpha=False
):
    # Draw box's shadow
    pattern = [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55]
    hatchedbox(
        image,
        width,
        height,
        shadow,
        pattern,
        x0 + 4,
        y0 + 4,
        x1 + 4,
        y1 + 4,
        alpha=alpha,
    )
    borderedbox(
        image, width, height, border, color1, color2, x0, y0, x1, y1, alpha=alpha
    )

# Creates a brush pattern (also known as a stipple) with width 2 and height equal to 'spacing'*2.
# The image returned by this method has the same format returned by the blankimage() method with alpha=False.
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
# The image returned by this method has the same format returned by the blankimage() method with alpha=False.
# Designed for drawing filled, unstroked, opaque vector paths,
# generally vector paths of an abstract design or symbol.
def styledbrush2(color1, color2, color3):
    return styledbrush1(color1, color2, color3, spacing=4, hatchsize=2)

# 'inputimages' is an array of images, each of which has the same format
# returned by the blankimage() method with alpha=False.
# 'outputimage' likewise has that format.
# 'gradient' and 'contour' are as in borderedgradientbox()
def imagegradientbox(
    outputimage,
    inputimages,
    width,
    height,
    gradient,
    contour,
    x0,
    y0,
    x1,
    y1,
    wraparound=True,
    jitter=False,
):
    if not inputimages:
        raise ValueError
    if len(inputimages) < 2:
        raise ValueError("not supported")
    if x1 < x0 or y1 < y0:
        raise ValueError
    if width <= 0 or height <= 0:
        raise ValueError
    if (not gradient) or (not outputimage) or (not contour):
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
            xv = (x - x0) / (x1 - x0)
            z = contour(xv, yv)
            if jitter:
                z = (z + 1) / 2.0
                rnge = (0.5 - min(0.5, abs(0.5 - z))) / 3
                z = z + random.random() * rnge - rnge / 2.0
                z = z * 2 - 1.0
            c = abs(z)
            cn = c * (len(inputimages) - 1)
            ci = int(cn)
            pos = yp + xp * 3
            if ci >= len(inputimages) - 1:
                color = [inputimages[ci][pos + i] for i in range(3)]
            else:
                color = [
                    inputimages[ci][pos + i]
                    + int(
                        (cn - ci)
                        * (inputimages[ci + 1][pos + i] - inputimages[ci][pos + i])
                    )
                    for i in range(3)
                ]
            outputimage[pos] = color[0]
            outputimage[pos + 1] = color[1]
            outputimage[pos + 2] = color[2]

# Image has the same format returned by the blankimage() method with alpha=False.
# Draw a wraparound box in a gradient fill on an image.
# 'border' is the color of the 1-pixel-thick border. Can be None (so
# that no border is drawn)
# 'gradient' is a list of 256 colors for mapping the 256 possible shades
# of the gradient fill.
# 'contour' is a function that takes two parameters and returns a number in [-1, 1].
# Each parameter is in [0, 1] and gives x- and y-coordinate of a point in
# the box: (0,0) is the upper-left corner; (1,1) is the lower-right, assuming the positive
# x-axis points to the right and the positive y-axis downward.  The return value
# of 'contour', as its absolute value, is a point along the gradient in which to color
# the specified point: 0 means first color in the gradient; 1 and -1 mean the last
# color in the gradient; points in between are intermediate colors along the gradient.
def borderedgradientbox(
    image,
    width,
    height,
    border,
    gradient,
    contour,
    x0,
    y0,
    x1,
    y1,
    wraparound=True,
    jitter=False,
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
                z = contour(xv, yv)
                if jitter:
                    z = (z + 1) / 2.0
                    rnge = (0.5 - min(0.5, abs(0.5 - z))) / 3
                    z = z + random.random() * rnge - rnge / 2.0
                    z = z * 2 - 1.0
                c = _togray255(z)
                color = gradient[c]
                image[yp + xp * 3] = color[0]
                image[yp + xp * 3 + 1] = color[1]
                image[yp + xp * 3 + 2] = color[2]

# Image has the same format returned by the blankimage() method with alpha=False.
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

# Modifies the specified 4-byte-per-pixel image by
# converting its 256-level alpha channel to two levels (opaque
# and transparent).
# Image has the same format returned by the blankimage() method with alpha=True.
# If 'dither' is True, the conversion is done by dithering, that
# is, by scattering opaque and transparent pixels to simulate
# pixels between the two extremes. (Reducing the alpha channel
# by dithering is also known as stippled or screen-door
# transparency.)  If False, the conversion is
# done by thresholding: alpha values 127 or below become 0 (transparent), and
# alpha values 128 or higher become 255 (opaque).  Default is False
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
# The parameter 'image' has the same format returned by the blankimage() method with alpha=True.
# Returns a list of two elements, the color mask and the alpha mask, both
# with the same format returned by the blankimage() method with alpha=False.
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
# Image has the same format returned by the blankimage() method with alpha=True.
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
            # "Then" draw lower right outline black
            if (
                image[xp + 3] == 255
                and (x == width - 1 or image[(xp + 4) + 3] != 255)
                or (y == height - 1 or image[(xp + width * 4) + 3] != 255)
            ):
                image[xp] = sh[0] if sh else 0x00
                image[xp + 1] = sh[1] if sh else 0x00
                image[xp + 2] = sh[2] if sh else 0x00

# Draw a wraparound dither-colored box on an image.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False
# 'border' is the color of the 1-pixel-thick border. Can be None (so
# that no border is drawn)
# 'color1' and 'color2' are the dithered
# versions of the inner color. 'color1' and 'color2' can't be None.
# This method currently does no "alpha blending".
def borderedbox(
    image,
    width,
    height,
    border,
    color1,
    color2,
    x0,
    y0,
    x1,
    y1,
    wraparound=True,
    alpha=False,
):
    if x1 < x0 or y1 < y0:
        raise ValueError
    if width < 0 or height < 0:
        raise ValueError
    # Nothing to do for zero-width images
    if width == 0 or height == 0:
        return
    if (not color1) or (not image) or (not color2):
        raise ValueError
    c1a = color1[3] if (alpha and len(color1) > 3) else 255
    c2a = color2[3] if (alpha and len(color2) > 3) else 255
    ba = border[3] if (alpha and border and len(border) > 3) else 255
    if x0 == x1 or y0 == y1:
        return
    if not wraparound:
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, width)
        y1 = min(y1, height)
        if x0 >= x1 or y0 >= y1:
            return
    pixelCount = 4 if alpha else 3
    for y in range(y0, y1):
        ypp = y % height
        yp = ypp * width * pixelCount
        for x in range(x0, x1):
            xp = x % width
            pos = yp + xp * pixelCount
            if border and (y == y0 or y == y1 - 1 or x == x0 or x == x1 - 1):
                # Draw border color
                image[pos] = border[0]
                image[pos + 1] = border[1]
                image[pos + 2] = border[2]
                if alpha:
                    image[pos + 3] = ba
            elif ypp % 2 == xp % 2:
                # Draw first color
                image[pos] = color1[0]
                image[pos + 1] = color1[1]
                image[pos + 2] = color1[2]
                if alpha:
                    image[pos + 3] = c1a
            else:
                # Draw second color
                image[pos] = color2[0]
                image[pos + 1] = color2[1]
                image[pos + 2] = color2[2]
                if alpha:
                    image[pos + 3] = c2a

# Split an image into two interlaced versions (known as "fields") with half the height.
# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
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

# Creates a blank image with 3 or 4 bytes per pixel and the specified width, height,
# and fill color.
#
# The image is in the form of a list with a number of
# elements equal to width*height*3 (or width*height*4 if 'alpha' is True).  The
# array is divided into 'height' many rows running from top to bottom. Each row
# is divided into 'width' many pixels (one pixel for each column from left to
# right), with three elements per pixel (or four elements if 'alpha' is True).
# In each pixel, which represents a color at the specified row and column, the
# first element is the color's red component; the second, its blue component;
# the third, its red component; the fourth, if present, is the color's alpha
# component or _opacity_ (0 if the color is transparent; 255 if opaque; otherwise,
# the color is translucent or semitransparent). Each component is an integer
# from 0 through 255.  In this format, lower-intensity red, green, or blue components are
# generally "darker", higher-intensity components "lighter", so that [0,0,0,255] (4 bytes per pixel)
# or [0,0,0] (3 bytes per pixel) is "black", and [255,255,255,255] or [255,255,255] is "white".
# Each color in the returned image is assumed to be in the nonlinear sRGB color space.
#
# 'color' is the fill color; if 'color' is None, the fill color is [255,255,255,255], or white.
# If 'alpha' is True, generates a 4-byte-per-pixel image; if False, generates a
# 3-byte-per-pixel image.  The default is False.
#
# Blending Note: Operations that involve the blending of two RGB (red-green-
# blue) colors work best if the RGB color space is linear.  This is not the case
# for the sRGB color space, which is the color space assumed for images created
# using the blankimage() method.  Moreover, converting an image from a nonlinear
# to a linear color space and back can lead to data loss especially if the image's color
# components are 8 bits or fewer in length (as with images returned by blankimage()).
# This function does not do any such conversion.
def blankimage(width, height, color=None, alpha=False):
    if color and len(color) < (4 if alpha else 3):
        raise ValueError
    # default background is white; default alpha is 255
    image = [255 for i in range(width * height * (4 if alpha else 3))]
    if color:
        pos = 0
        pixelBytes = 4 if alpha else 3
        for i in range(height * width):
            image[pos] = color[0]
            image[pos + 1] = color[1]
            image[pos + 2] = color[2]
            if alpha:
                image[pos + 3] = color[3]
            pos += pixelBytes
    return image

# Generates a tileable argyle pattern from two images of the
# same size.  The images have the same format returned by the blankimage()
# method with the specified value of 'alpha' (default value for 'alpha' is False).  'backgroundImage' must be tileable if shiftImageBg=False;
# 'foregroundImage' need not be tileable.
# 'expo' is a parameter that determines the shape in the middle of the image,
# and can be any number greater than 0. If 1, the shape resembles a
# diamond; if 2, an ellipse.  Default is 1.
def argyle(
    foregroundImage,
    backgroundImage,
    width,
    height,
    expo=1,
    shiftImageBg=False,
    alpha=False,
):
    if expo <= 0:
        raise ValueError
    pixelBytes = 4 if alpha else 3
    if width * height * pixelBytes > len(foregroundImage):
        raise ValueError
    if width * height * pixelBytes > len(backgroundImage):
        raise ValueError
    if shiftImageBg:
        i2 = blankimage(width, height, alpha=alpha)
        imageblit(
            i2,
            width,
            height,
            width // 2,
            height // 2,
            backgroundImage,
            width,
            height,
            alpha=alpha,
        )
        return argyle(
            foregroundImage, i2, width, height, expo, shiftImageBg=False, alpha=alpha
        )
    ret = blankimage(width, height, alpha=alpha)
    pos = 0
    for y in range(height):
        yp = (y / height) * 2 - 1
        for x in range(width):
            xp = (x / width) * 2 - 1
            if abs(xp) ** expo + abs(yp) ** expo <= 1:
                # image 1 is inside the diamond
                for i in range(pixelBytes):
                    ret[pos + i] = foregroundImage[pos + i]
            else:
                # image 2 is outside the diamond
                for i in range(pixelBytes):
                    ret[pos + i] = backgroundImage[pos + i]
            pos += pixelBytes
    if width * height * pixelBytes > len(ret):
        raise ValueError
    return ret

# Generates a tileable checkerboard pattern using two images of the same size;
# each tile is the whole of one of the source images, and the return value's
# width in pixels is width*columns; its height is height*rows.
# The two images should be tileable.
# The images have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
# The number of columns and of rows must be even and positive.
def checkerboardtile(
    upperLeftImage, otherImage, width, height, columns=2, rows=2, alpha=False
):
    if rows <= 0 or columns <= 0 or rows % 2 == 1 or columns % 2 == 1:
        raise ValueError
    pixelBytes = 4 if alpha else 3
    if width * height * pixelBytes > len(upperLeftImage):
        raise ValueError
    if width * height * pixelBytes > len(otherImage):
        raise ValueError
    ret = blankimage(width * columns, height * rows, alpha=alpha)
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
                alpha=alpha,
            )
    return ret

# Generates a tileable checkerboard pattern made of parts of two images of the same size;
# the return value has the same width and height as the source images.
# The two images should be tileable.
# The images have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
# The number of columns and of rows must be even and positive.
def checkerboard(
    upperLeftImage, otherImage, width, height, columns=2, rows=2, alpha=False
):
    if rows <= 0 or columns <= 0 or rows % 2 == 1 or columns % 2 == 1:
        raise ValueError
    ret = blankimage(width, height, alpha=alpha)
    pos = 0
    pixelBytes = 4 if alpha else 3
    for y in range(height):
        yp = y * rows // height
        for x in range(width):
            xp = x * columns // width
            if (yp + xp) % 2 == 0:
                ret[pos] = upperLeftImage[pos]
                ret[pos + 1] = upperLeftImage[pos + 1]
                ret[pos + 2] = upperLeftImage[pos + 2]
                if alpha:
                    ret[pos + 3] = upperLeftImage[pos + 3]
            else:
                ret[pos] = otherImage[pos]
                ret[pos + 1] = otherImage[pos + 1]
                ret[pos + 2] = otherImage[pos + 2]
                if alpha:
                    ret[pos + 3] = otherImage[pos + 3]
            pos += pixelBytes
    return ret

# Returns an image with the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def simpleargyle(fgcolor, bgcolor, linecolor, w, h, alpha=False, expo=1):
    fg = blankimage(w, h, fgcolor, alpha=alpha)
    bg = blankimage(w, h, bgcolor, alpha=alpha)
    bg = argyle(fg, bg, w, h, alpha=alpha, expo=expo)
    linedraw(bg, w, h, linecolor, 0, 0, w, h)
    linedraw(bg, w, h, linecolor, 0, h, w, 0)
    return bg

# The returned image has the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
# Returned image's width is twice 'w' and its height is twice 'h'.
def doubleargyle(
    fgcolor1, fgcolor2, bgcolor, linecolor1, linecolor2, w, h, alpha=False
):
    f1 = simpleargyle(fgcolor1, bgcolor, linecolor1, w, h, alpha=alpha)
    f2 = simpleargyle(fgcolor2, bgcolor, linecolor2, w, h, alpha=alpha)
    return checkerboardtile(f1, f2, w, h, alpha=alpha)

# 'fg1Image', 'fg2Image', and 'bgImage' have width 'w' and height 'h'.
# These images and the return value have the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
# Returned image's width is twice 'w' and its height is twice 'h'.
def doubleargyleimage(fg1Image, fg2Image, bgImage, w, h, alpha=False):
    img1 = argyle(fg1Image, bgImage, w, h, shiftImageBg=True, alpha=alpha)
    img2 = argyle(fg2Image, bgImage, w, h, shiftImageBg=True, alpha=alpha)
    return checkerboardtile(img1, img2, w, h, alpha=alpha)

# Returns an image with the same format returned by the blankimage() method with alpha=False.
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
            if dist == 0:
                break
    return ret

def _nearest_rgb(pal, rgb):
    return _nearest_rgb3(pal, rgb[0], rgb[1], rgb[2])

# Image has the same format returned by the blankimage() method with alpha=False.
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

# Image has the same format returned by the blankimage() method with alpha=False.
# hatchdist - distance from beginning of one horizontal hash line to the
# beginning of the next, in pixels.
# hatchthick - thickness in pixels of each horizontal hash line.
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

# Image has the same format returned by the blankimage() method with alpha=False.
# 'stripesize' is in pixels
# reverse=false: stripe runs from upper left to bottom
# right assuming the image's first row is the top row
# reverse=true: stripe runs from upper right to bottom
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

# Finds the gray tones in the specified color palette and returns
# a sorted list of them (as a list of integers, not three-element
# lists).
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
    return ret  # return a sorted list of gray tones in the specified palette

# Recolors the image using the specified color as a substitute for (255,0,0)
# or "red".  The only colors allowed in the input image are gray tones
# (x,x,x); shades of red (x,0,0); and tints of red (255,x,x),
# disregarding the alpha channel if any.
# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
# This method disregards the input image's alpha channel.
def recolor(image, width, height, color, alpha=False):
    if color == None or len(color) < 3:
        raise ValueError
    pixelSize = 4 if alpha else 3
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            r = image[xp]
            g = image[xp + 1]
            b = image[xp + 2]
            if r == g and g == b:
                # gray tone
                pass
            elif r == 255 and g == b:
                # Mixture of color and white
                image[xp] = color[0] + (255 - color[0]) * g // 255
                image[xp + 1] = color[1] + (255 - color[1]) * g // 255
                image[xp + 2] = color[2] + (255 - color[2]) * g // 255
            elif g == 0 and b == 0:
                # Mixture of color and black
                image[xp] = r * color[0] // 255
                image[xp + 1] = r * color[1] // 255
                image[xp + 2] = r * color[2] // 255
            else:
                raise ValueError("Invalid color")
    return image

# Converts the image as in recolor() and dithers the image to the
# gray tones given and the specified color.  The only colors allowed
# in the input image are gray tones (x,x,x); shades of red (x,0,0); and tints of red (255,x,x),
# disregarding the alpha channel if any.
# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
# 'grays' is as in dithertograyimage().  If None, uses [0, 128, 192, 255].
# 'darkcolor' is a darker version of the color, at position 128/255 between black and
# the specified color.
# This method disregards the input image's alpha channel.
def recolordither(image, width, height, color, grays=None, darkcolor=None, alpha=False):
    if grays == None:
        grays = [0, 128, 192, 255]
    if color == None or len(color) < 3:
        raise ValueError
    if darkcolor != None and len(darkcolor) < 3:
        raise ValueError
    dithertograyimage(image, width, height, grays, alpha=alpha, disregardNonGrays=True)
    pixelSize = 4 if alpha else 3
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            r = image[xp]
            g = image[xp + 1]
            b = image[xp + 2]
            if r == g and g == b:
                # gray tone; already dithered
                pass
            elif r == 255 and g == b:
                # Mixture of color and white
                bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                if bdither < g * 64 // 255:
                    image[xp] = 255
                    image[xp + 1] = 255
                    image[xp + 2] = 255
                else:
                    image[xp] = color[0]
                    image[xp + 1] = color[1]
                    image[xp + 2] = color[2]
            elif g == 0 and b == 0:
                # Mixture of color and black
                bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                if darkcolor != None:
                    if r >= 128 and bdither < (r - 128) * 64 // 127:
                        image[xp] = color[0]
                        image[xp + 1] = color[1]
                        image[xp + 2] = color[2]
                    elif r >= 128 or bdither < r * 64 // 128:
                        image[xp] = darkcolor[0]
                        image[xp + 1] = darkcolor[1]
                        image[xp + 2] = darkcolor[2]
                    else:
                        image[xp] = 0
                        image[xp + 1] = 0
                        image[xp + 2] = 0
                elif bdither < r * 64 // 255:
                    image[xp] = color[0]
                    image[xp + 1] = color[1]
                    image[xp + 2] = color[2]
                else:
                    image[xp] = 0
                    image[xp + 1] = 0
                    image[xp + 2] = 0
            else:
                raise ValueError("Invalid color: %d %d %d" % (r, g, b))
    return image

# Converts the image to grayscale and dithers the resulting image
# to the gray tones given.  The conversion is in-place.
# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
# 'grays' is a sorted list of gray tones.  Each gray tone must be an integer
# from 0 through 255.  The list must have a length of 2 or greater.
# 'grays' can be None, in which case this method behaves like 'graymap'.
# If 'disregardNonGrays' is True, just dither the gray tones and leave the other
# colors in the image unchanged.  Default is False.
# This method disregards the input image's alpha channel.
def dithertograyimage(
    image, width, height, grays, alpha=False, disregardNonGrays=False
):
    if not grays:
        if disregardNonGrays:
            return image
        return graymap(image, width, height, alpha=alpha)
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
            if disregardNonGrays:
                if c != image[xp + 1] or image[xp + 1] != image[xp + 2]:
                    continue
            else:
                c = (c * 2126 + image[xp + 1] * 7152 + image[xp + 2] * 722) // 10000
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
# to colors in the specified colors array.  If 'colors' is None (the default),
# the mapping step is skipped.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
# If 'disregardNonGrays' is True, leave colors other than gray tones
# in the image unchanged.  Default is False.
# Returns the value of 'image'; the image is modified in place.
#
#  Example: Generate a random background image, dither to black, gray,
# and white, and map these gray tones to lighter tones.
#
# img2 = dw.randombackgroundimage(320, 240)
# dw.dithertograyimage(img2, 320, 240, [0, 128, 255])
# colors = [[i, i, i] for i in range(256)]
# colors[192] = [255, 255, 255]
# colors[128] = [192, 192, 192]
# colors[0] = [128, 128, 128]
# dw.graymap(img2, 320, 240, colors)
def graymap(image, width, height, colors=None, alpha=False, disregardNonGrays=False):
    pixelSize = 4 if alpha else 3
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            c = image[xp]
            if c != image[xp + 1] or image[xp + 1] != image[xp + 2]:
                if disregardNonGrays:
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

# Converts an image without an alpha channel to an image with an alpha channel by
# setting the alpha value of every pixel in the output to 255.
# The input image has the same format returned by the blankimage() method with alpha=False.
# The output image has the same format returned by the blankimage() method with alpha=True.
def toalpha(image, width, height):
    if width * height * 3 != len(image):
        raise ValueError
    ret = [0 for x in range(width * height * 4)]
    pos = 0
    apos = 0
    for i in range(width * height):
        ret[apos] = image[pos]
        ret[apos + 1] = image[pos + 1]
        ret[apos + 2] = image[pos + 2]
        ret[apos + 3] = 0xFF
        apos += 4
        pos += 3
    return ret

# Converts an image with an alpha channel to an image without an alpha channel by
# removing that alpha channel.
# The input image has the same format returned by the blankimage() method with alpha=True.
# The output image has the same format returned by the blankimage() method with alpha=False.
def noalpha(image, width, height):
    if width * height * 4 != len(image):
        raise ValueError(
            "w=%d h=%d size=%d len=%d" % (width, height, width * height * 4, len(image))
        )
    ret = [0 for x in range(width * height * 3)]
    pos = 0
    apos = 0
    for i in range(width * height):
        ret[pos] = image[apos]
        ret[pos + 1] = image[apos + 1]
        ret[pos + 2] = image[apos + 2]
        apos += 4
        pos += 3
    return ret

# Image has the same format returned by the blankimage() method with alpha=False.
# Returns a list describing a color; its elements are the red, green, and blue
# components, in that order.
def getpixel(image, width, height, x, y):
    pos = (y * width + x) * 3
    return image[pos : pos + 3]

# Image has the same format returned by the blankimage() method with alpha=False.
# Returns a list describing a color; its elements are the blue, green, and red
# components, in that order.
def getpixelbgr(image, width, height, x, y):
    r = getpixel(image, width, height, x, y)
    return [r[2], r[1], r[0]]

# Image has the same format returned by the blankimage() method with alpha=False.
# Returns a list describing a color; its elements are the blue, green, red, and alpha
# components, in that order.
def getpixelbgralpha(image, width, height, x, y):
    r = getpixelalpha(image, width, height, x, y)
    return [r[2], r[1], r[0], r[3]]

# Image has the same format returned by the blankimage() method with alpha=False.
# 'c' is a list describing a color; its elements are the red, green, and blue
# components, in that order.
def setpixel(image, width, height, x, y, c):
    pos = (y * width + x) * 3
    image[pos] = c[0]
    image[pos + 1] = c[1]
    image[pos + 2] = c[2]

# Image has the same format returned by the blankimage() method with alpha=False.
# 'c' is a list describing a color; its elements are the blue, green, and
# red components, in that order.
def setpixelbgr(image, width, height, x, y, c):
    pos = (y * width + x) * 3
    image[pos] = c[2]
    image[pos + 1] = c[1]
    image[pos + 2] = c[0]

# Image has the same format returned by the blankimage() method with alpha=True.
# Returns a list describing a color; its elements are the red, green, blue, and
# alpha components, in that order.
def getpixelalpha(image, width, height, x, y):
    pos = (y * width + x) * 4
    return image[pos : pos + 4]

# Image has the same format returned by the blankimage() method with alpha=True.
# 'c' is a list describing a color; its elements are the red, green, blue, and
# alpha components, in that order.
def setpixelalpha(image, width, height, x, y, c):
    pos = (y * width + x) * 4
    image[pos] = c[0]
    image[pos + 1] = c[1]
    image[pos + 2] = c[2]
    image[pos + 3] = c[3]

# Image has the same format returned by the blankimage() method with alpha=True.
# 'c' is a list describing a color; its elements are the blue, green, red, and
# alpha components, in that order.
def setpixelbgralpha(image, width, height, x, y, c):
    pos = (y * width + x) * 4
    image[pos] = c[2]
    image[pos + 1] = c[1]
    image[pos + 2] = c[0]
    image[pos + 3] = c[3]

# Image has the same format returned by the blankimage() method with alpha=False.
def convolveRow(image, width, height):
    pos = 0
    for y in range(height):
        rowstart = pos
        for x in range(width):
            r = 0
            g = 0
            b = 0
            for i in range(50):
                xx = (x + i - 25) % width
                r += image[rowstart + xx * 3]
                g += image[rowstart + xx * 3 + 1]
                b += image[rowstart + xx * 3 + 2]
            image[pos] = r // 50
            image[pos + 1] = g // 50
            image[pos + 2] = b // 50
            pos += 3

# Image has the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
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

# Image has the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
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

# Dithers in place the specified image to the colors in color palette returned by websafecolors().
# Image has the same format returned by the blankimage() method with the specified value
# of 'alpha' (default value for 'alpha' is False).
# If 'includeVga' is True, leave unchanged any colors in the color palette returned
# by classiccolors(). Default is False.
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
            bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
            for i in range(3):
                c = image[xp + i]
                cm = c % 51
                image[xp + i] = (c - cm) + 51 if bdither < cm * 64 // 51 else c - cm
    return image

# Dithers in place the specified image to the colors in color palette returned by classiccolors().
# Image has the same format returned by the blankimage() method with the specified value
# of 'alpha' (default value for 'alpha' is False).
def vgaPaletteDither(image, width, height, alpha=False):
    pixelSize = 4 if alpha else 3
    if len(image) < width * height * pixelSize:
        raise ValueError("len=%d width=%d height=%d" % (len(image), width, height))
    missing = False
    for y in range(height):
        yp = y * width * pixelSize
        for x in range(width):
            xp = yp + x * pixelSize
            r = image[xp]
            g = image[xp + 1]
            b = image[xp + 2]
            if r <= 128 and g <= 128 and b <= 128:
                # Red, green, and blue are in lowest-valued corner of color cube.
                bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                image[xp] = 128 if bdither < ((r >> 1) & 0xFF) else 0
                image[xp + 1] = 128 if bdither < ((g >> 1) & 0xFF) else 0
                image[xp + 2] = 128 if bdither < ((b >> 1) & 0xFF) else 0
            elif (
                (g == 0 and b == 0)
                or (r == 0 and b == 0)
                or (r == 0 and g == 0)
                or (g == 0 and b == r)
                or (r == 0 and b == g)
                or (b == 0 and g == r)
            ):
                bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
                for i in range(3):
                    v = image[xp + i]
                    if v < 128:
                        image[xp + i] = 128 if bdither < v * 64 // 128 else 0
                    else:
                        image[xp + i] = 255 if bdither < (v - 128) * 64 // 127 else 128
            else:
                missing = True
    if missing:
        return patternDither(image, width, height, classiccolors(), alpha=alpha)
    return image

# Dithers in place the specified image to the colors in an 8-bit color palette returned by ega8colors().
# Image has the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
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
            bdither = _DitherMatrix[(y & 7) * 8 + (x & 7)]
            for i in range(3):
                c = image[xp + i]
                cm = c
                image[xp + i] = (c - cm) + 255 if bdither < cm * 64 // 255 else c - cm
    return image

# Converts each color in the specified image to the nearest color (in ordinary red&ndash;green&ndash;blue
# space) in the specified color palette.
# Image has the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
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

# Same as patternDither(), but uses the Floyd-Steinberg algorithm.
# There is no 'fast' parameter.
def floydSteinbergDither(image, width, height, palette, alpha=False):
    if width < 0 or height < 0 or not palette:
        raise ValueError
    if width == 0 or height == 0:
        return image
    err = [0 for i in range(width * 6)]
    rerr1 = 0
    rerr2 = rerr1 + width
    gerr1 = rerr2 + width
    gerr2 = gerr1 + width
    berr1 = gerr2 + width
    berr2 = berr1 + width
    pixelBytes = 4 if alpha else 3
    pos = 0
    for j in range(height):
        for i in range(width):
            cr = (
                getpixelalpha(image, width, height, i, j)
                if alpha
                else getpixel(image, width, height, i, j)
            )
            err[rerr1 + i] = err[rerr2 + i] + cr[0]
            err[gerr1 + i] = err[gerr2 + i] + cr[1]
            err[berr1 + i] = err[berr2 + i] + cr[2]
            err[rerr2 + i] = err[gerr2 + i] = err[berr2 + i] = 0
        err[rerr1] = max(0, min(255, err[rerr1]))
        err[gerr1] = max(0, min(255, err[gerr1]))
        err[berr1] = max(0, min(255, err[berr1]))
        idx = _nearest_rgb3(palette, err[rerr1], err[gerr1], err[berr1])
        pos = (j * width) * pixelBytes
        image[pos] = palette[idx][0]
        image[pos + 1] = palette[idx][1]
        image[pos + 2] = palette[idx][2]
        for i in range(width - 1):
            err[rerr1 + i] = max(0, min(255, err[rerr1 + i]))
            err[gerr1 + i] = max(0, min(255, err[gerr1 + i]))
            err[berr1 + i] = max(0, min(255, err[berr1 + i]))
            idx = _nearest_rgb3(palette, err[rerr1 + i], err[gerr1 + i], err[berr1 + i])
            pos = (j * width + i) * pixelBytes
            image[pos] = palette[idx][0]
            image[pos + 1] = palette[idx][1]
            image[pos + 2] = palette[idx][2]
            rerr = err[rerr1 + i] - palette[idx][0]
            gerr = err[gerr1 + i] - palette[idx][1]
            berr = err[berr1 + i] - palette[idx][2]
            # diffuse red error
            err[rerr1 + i + 1] += (rerr * 7) >> 4
            err[rerr2 + i - 1] += (rerr * 3) >> 4
            err[rerr2 + i] += (rerr * 5) >> 4
            err[rerr2 + i + 1] += (rerr) >> 4
            # diffuse green error
            err[gerr1 + i + 1] += (gerr * 7) >> 4
            err[gerr2 + i - 1] += (gerr * 3) >> 4
            err[gerr2 + i] += (gerr * 5) >> 4
            err[gerr2 + i + 1] += (gerr) >> 4
            # diffuse red error
            err[berr1 + i + 1] += (berr * 7) >> 4
            err[berr2 + i - 1] += (berr * 3) >> 4
            err[berr2 + i] += (berr * 5) >> 4
            err[berr2 + i + 1] += (berr) >> 4
        err[rerr1] = max(0, min(255, err[rerr1]))
        err[gerr1] = max(0, min(255, err[gerr1]))
        err[berr1] = max(0, min(255, err[berr1]))
        idx = _nearest_rgb3(palette, err[rerr1], err[gerr1], err[berr1])
        pos = (j * width) * pixelBytes
        image[pos] = palette[idx][0]
        image[pos + 1] = palette[idx][1]
        image[pos + 2] = palette[idx][2]
    return image

# Dithers in place the specified image to the colors in an arbitrary color palette.
# Derived from Adobe's pattern dithering algorithm, described by J. Yliluoma at:
# https://bisqwit.iki.fi/story/howto/dither/jy/
# Image has the same format returned by the blankimage() method with the specified
# value of 'alpha' (default value for 'alpha' is False).
# If 'fast' is True, use a smaller dither matrix. The default value for
# 'fast' is False.
# Example: The following function generates an 8 &times; 8 image of a solid color simulated
# by the colors in the specified color palette.  By default, the palette is the same
# as that returned by the _classiccolors_ function.  The solid color is a three-element
# list of a color as described for the blankimage() function.
#
# def ditherBrush(color, palette=None):
#     image=blankimage(8,8,color)
#     patternDither(image,8,8,palette if palette else classiccolors())
#     return image
#
def patternDither(image, width, height, palette, alpha=False, fast=False):
    pixelSize = 4 if alpha else 3
    ditherMatrixLen = len(_DitherMatrix4x4) if fast else len(_DitherMatrix)
    candidates = [[] for i in range(ditherMatrixLen)]
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
            for i in range(ditherMatrixLen):
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
                if i == 0 and cv1[0] == ir and cv1[1] == ig and cv1[2] == ib:
                    exact = True
                    break
                e[0] += ir - cv1[0]
                e[1] += ig - cv1[1]
                e[2] += ib - cv1[2]
            if exact:
                continue
            candidates.sort()
            bdither = (
                _DitherMatrix4x4[(y & 3) * 4 + (x & 3)]
                if fast
                else _DitherMatrix[(y & 7) * 8 + (x & 7)]
            )
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

# Returns a 256-element color gradient for coloring user-interface elements (for example,
# using the 'graymap' function).
# The parameters are all three-element lists identifying colors.  Each parameter can
# be None.  The examples for this function are similar to those given in the
# 'uicolorgradient2' function.
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

# Returns a 256-element color gradient for coloring user-interface elements (for example,
# using the 'graymap' function), given a desired button face color.  The parameters are all
# three-element lists identifying colors.  Each parameter can be None.
#
# Example 1: Suppose 'img' is the image of a custom drawn button in grayscale,
# with the button face colored light gray (192, 192, 192) and highlights
# and shadows colored in other gray tones.  Then the following code colors
# the gray tones of the button image and saves the resulting image to a file.
#
#  import imageformat as ifmt
#
#  grad = dw.uicolorgradient2([220, 200, 150])
#  img256 = dw.graymap([x for x in img], w, h, grad, disregardNonGrays=True)
#  ifmt.writepng("button.png",img256, w, h)
#
# Example 2: Same as the previous example, but the image is first dithered
# to have at most four gray tones, including possibly light gray.  This
# dithering procedure is useful in order to prepare the image for display
# on devices that can show only a limited number of colors at a time.
#
#  import imageformat as ifmt
#
#  img = dw.dithertograyimage(
#    [x for x in img], w, h, [0, 128, 192, 255], disregardNonGrays=True
#  )
#  grad = dw.uicolorgradient2([220, 200, 150])
#  img256 = dw.graymap([x for x in img], w, h, grad, disregardNonGrays=True)
#  ifmt.writepng("button.png", img256, w, h)
def uicolorgradient2(btnface=None):
    if not btnface:
        btnface = [192, 192, 192]
    return uicolorgradient(
        hilightColor=[255, 255, 255],
        lightColor=btnface,
        shadowColor=[x * 2 // 3 for x in btnface],
        darkShadowColor=[0, 0, 0],
    )

# Returns an image with the same format returned by the blankimage() method with alpha=False.
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

# Generate an image of white noise.  The noise image will have only gray tones.
# Returns an image with the same format returned by the blankimage() method with alpha=False.
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
# Returns an image with the same format returned by the blankimage() method with alpha=False.
# If 'bgcolor' is None or not given, it becomes (255,255,255).
# If 'noisecolor' is None or not given, it becomes (0,0,0).
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
# Image has the same format returned by the blankimage() method with alpha=False.
def circledraw(image, width, height, c, cx, cy, r, wraparound=True, alpha=False):
    helper = ImageDrawHelper(image, width, height, wraparound=wraparound, alpha=alpha)
    helpercircledraw(helper, c, cx, cy, r)

# Draws the outline of a superellipse using a drawing helper.
# Default for 'expo' is 2, indicating an ordinary ellipse.
def helperellipsedraw(helper, color, x0, y0, x1, y1, expo=2, fill=False):
    if x1 < x0 or y1 < y0:
        raise ValueError
    if expo <= 0:
        raise ValueError
    # Shrink the ellipse by 1 pixel for drawing purposes
    x1 -= 1
    y1 -= 1
    if x0 >= x1 or y0 >= y1:
        # Empty or too-small ellipse
        return
    invexpo = 1 / expo
    xmin = min(x0, x1)
    xmax = max(x0, x1)
    xmid = (xmin + xmax) / 2
    xhalf = (xmax - xmin) / 2
    ymin = min(y0, y1)
    ymax = max(y0, y1)
    last2xa = 0
    last2xb = 0
    lastxa = 0
    lastxb = 0
    for i in range(ymin, ymax + 1):
        # Calculate this scan line at 'i'
        yp = ((i - ymin) / (ymax - ymin)) * 2 - 1
        if abs(yp) < 0 or abs(yp) > 1:
            raise ValueError
        s = (1 - abs(yp) ** expo) ** invexpo
        if s < 0 or s > 1:
            raise ValueError
        xa = int(xmid - xhalf * s + 0.5)
        xb = int(xmid + xhalf * s + 0.5)
        if fill or i == ymin:
            drawpositiverect(helper, xa, i, xb + 1, i + 1, color)
        elif i == ymax:
            xxa = max(last2xa, xa)
            if xxa == lastxa:
                xxa = lastxa + 1
            xxb = min(last2xb + 1, xb + 1)
            if xxb == lastxb + 1:
                xxb = lastxb
            drawpositiverect(helper, lastxa, i - 1, xxa, i, color)
            drawpositiverect(helper, xxb, i - 1, lastxb + 1, i, color)
            drawpositiverect(helper, xa, i, xb + 1, i + 1, color)
        else:
            xxa = max(last2xa, xa)
            if xxa == lastxa:
                xxa = lastxa + 1
            xxb = min(last2xb + 1, xb + 1)
            if xxb == lastxb + 1:
                xxb = lastxb
            drawpositiverect(helper, lastxa, i - 1, xxa, i, color)
            drawpositiverect(helper, xxb, i - 1, lastxb + 1, i, color)
        last2xa = xa if i == ymin else lastxa
        last2xb = xb if i == ymin else lastxb
        lastxa = xa
        lastxb = xb

# Fills a superellipse using a drawing helper.
# Default for 'expo' is 2, indicating an ordinary ellipse.
def helperellipsefill(helper, color, x0, y0, x1, y1, expo=2):
    helperellipsedraw(helper, color, x0, y0, x1, y1, expo=expo, fill=True)

# Draws a circle using a drawing helper.
def helpercircledraw(helper, color, cx, cy, r):
    # midpoint circle algorithm
    z = -r
    x = r
    y = 0
    while y < x:
        octs = [[x, y], [-x, -y], [x, -y], [-x, y], [y, x], [-y, -x], [y, -x], [-y, x]]
        for xx, yy in octs:
            px = cx + xx
            py = cy + yy
            drawpositiverect(helper, px, py, px + 1, py + 1, color)
        z += 1 + y + y
        y += 1
        if z >= 0:
            z -= x + x - 1
            x -= 1

# Draws a line that optionally wraps around.
# Image has the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def linedraw(
    image,
    width,
    height,
    c,
    x0,
    y0,
    x1,
    y1,
    drawEndPoint=False,
    wraparound=True,
    alpha=False,
):
    if (not len) or len(c) < 3:
        raise ValueError
    if len(c) >= 4:
        raise NotImplementedError("color values with alpha are currently not supported")
    helper = ImageDrawHelper(image, width, height, wraparound=wraparound, alpha=alpha)
    helperlinedraw(helper, c, x0, y0, x1, y1, drawEndPoint=drawEndPoint)

# Draws a line using a drawing helper.
def helperlinedraw(
    helper,
    c,
    x0,
    y0,
    x1,
    y1,
    drawEndPoint=False,
):
    if x0 == x1 and drawEndPoint and y0 < y1:
        drawpositiverect(helper, x0, y0, x0 + 1, y1 + 1, c)
        return
    elif y0 == y1 and drawEndPoint and x0 < x1:
        drawpositiverect(helper, x0, y0, x1 + 1, y0 + 1, c)
        return
    elif x0 == x1 and y0 == y1 and drawEndPoint:
        drawpositiverect(helper, x0, y0, x1 + 1, y0 + 1, c)
        return
    # Bresenham's algorithm
    dx = x1 - x0
    dy = y1 - y0
    drawpositiverect(helper, x0, y0, x0 + 1, y0 + 1, c)
    # Ending point
    if drawEndPoint:
        drawpositiverect(helper, x1, y1, x1 + 1, y1 + 1, c)
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
        coordchange = -1 if dx < 0 else 1
        for i in range(1, y1 - y0):
            y += 1
            if z < 0:
                z += a
            else:
                z += b
                x += coordchange
            drawpositiverect(helper, x, y, x + 1, y + 1, c)
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
        coordchange = -1 if dy < 0 else 1
        for i in range(1, x1 - x0):
            x += 1
            if z < 0:
                z += a
            else:
                z += b
                y += coordchange
            drawpositiverect(helper, x, y, x + 1, y + 1, c)

def _edgetoscans(
    scans,
    scanY,
    x0,
    y0,
    x1,
    y1,
):
    if y0 > y1:
        t = y0
        y0 = y1
        y1 = t
        t = x0
        x0 = x1
        x1 = t
    if y0 < scanY:
        raise ValueError
    if x0 == x1:
        # vertical
        for i in range(y0, y1):
            p = i - scanY
            scans[p * 2] = min(scans[p * 2], x0) if scans[p * 2] != None else x0
            scans[p * 2 + 1] = (
                max(scans[p * 2 + 1], x0) if scans[p * 2 + 1] != None else x0
            )
        return
    if y0 == y1:
        # horizontal; so no scan lines
        return
    # Bresenham's algorithm
    dx = x1 - x0
    dy = y1 - y0
    p = y0 - scanY
    scans[p * 2] = min(scans[p * 2], x0) if scans[p * 2] != None else x0
    scans[p * 2 + 1] = max(scans[p * 2 + 1], x0) if scans[p * 2 + 1] != None else x0
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
        coordchange = -1 if dx < 0 else 1
        for i in range(1, y1 - y0):
            y += 1
            if z < 0:
                z += a
            else:
                z += b
                x += coordchange
            p = y - scanY
            scans[p * 2] = min(scans[p * 2], x) if scans[p * 2] != None else x
            scans[p * 2 + 1] = (
                max(scans[p * 2 + 1], x) if scans[p * 2 + 1] != None else x
            )
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
        coordchange = -1 if dy < 0 else 1
        for i in range(1, x1 - x0):
            x += 1
            if z < 0:
                z += a
            else:
                z += b
                y += coordchange
            p = y - scanY
            # print([y,scanY,p,len(scans)])
            scans[p * 2] = min(scans[p * 2], x) if scans[p * 2] != None else x
            scans[p * 2 + 1] = (
                max(scans[p * 2 + 1], x) if scans[p * 2 + 1] != None else x
            )

def simplepolygonfill(helper, color, points):
    # Fill a so-called "monotone-vertical" polygon, one that changes direction along
    # the y-axis exactly twice, whether or not the polygon is self-intersecting.
    # Every convex polygon is monotone-vertical.
    # Each point is a two-item list containing the x and y integer coordinates.
    # See Michael Abrash's Graphics Programming Black Book Special Edition,
    # chapter 41.
    if len(points) < 3:
        return
    direc = 0
    direcChanged = False
    splitPoint = True
    lasty = 0
    minY = points[0][1]
    maxY = points[0][1]
    for i in range(1, len(points)):
        y = points[i][1]
        if y < minY:
            minY = y
        elif y > maxY:
            maxY = y
    if maxY == minY:
        return
    length = maxY - minY + 1
    edges = [None for i in range(length * 2)]
    for i in range(1, len(points)):
        _edgetoscans(
            edges, minY, points[i - 1][0], points[i - 1][1], points[i][0], points[i][1]
        )
    z = len(points) - 1
    _edgetoscans(edges, minY, points[z][0], points[z][1], points[0][0], points[0][1])
    i = 0
    # Draw the scan lines making up the polygon
    y = minY
    while i < length * 2:
        if edges[i] != None:
            drawpositiverect(helper, edges[i], y, edges[i + 1], y + 1, color)
        i += 2
        y += 1

def roundedborder(helper, x0, y0, x1, y1, upper, lower, topdom=True):
    if x0 >= x1 or y0 >= y1:
        raise ValueError
    if topdom:
        upperlines = [
            x1 - 2,
            y0 + 1,
            x1 - 3,
            y0,
            x0 + 2,
            y0,
            x0,
            y0 + 2,
            x0,
            y1 - 3,
            x0 + 1,
            y1 - 2,
        ]
        lowerlines = [x0 + 2, y1 - 1, x1 - 3, y1 - 1, x1 - 1, y1 - 3, x1 - 1, y0 + 2]
    else:
        upperlines = [x1 - 3, y0, x0 + 2, y0, x0, y0 + 2, x0, y1 - 3]
        lowerlines = [
            x0 + 1,
            y1 - 2,
            x0 + 2,
            y1 - 1,
            x1 - 3,
            y1 - 1,
            x1 - 1,
            y1 - 3,
            x1 - 1,
            y0 + 2,
            x1 - 2,
            y0 + 1,
        ]
    for i in range(len(upperlines) // 2):
        upperlines[i * 2] = min(x1, max(x0, upperlines[i * 2]))
        upperlines[i * 2 + 1] = min(y1, max(y0, upperlines[i * 2 + 1]))
    for i in range(len(lowerlines) // 2):
        lowerlines[i * 2] = min(x1, max(x0, lowerlines[i * 2]))
        lowerlines[i * 2 + 1] = min(y1, max(y0, lowerlines[i * 2 + 1]))
    i = 2
    while i < len(upperlines):
        dw.helperlinedraw(
            helper,
            upper,
            upperlines[i - 2],
            upperlines[i - 1],
            upperlines[i],
            upperlines[i + 1],
            drawEndPoint=True,
        )
        i += 2
    i = 2
    while i < len(lowerlines):
        dw.helperlinedraw(
            helper,
            lower,
            lowerlines[i - 2],
            lowerlines[i - 1],
            lowerlines[i],
            lowerlines[i + 1],
            drawEndPoint=True,
        )
        i += 2

# 'dst' and 'mask' have the same format returned by the blankimage() method with alpha=False.
# 'wraparound' has the same meaning as in imageblitex(); default is False.
def drawgradientmask(
    dst, dstw, dsth, dstx, dsty, mask, maskw, maskh, color1, color2, wraparound=False
):
    iters = maskh
    rowsize = 1
    if color1 == color2:
        iters = 1
        rowsize = maskh
    for i in range(0, iters):
        c = [a + (b - a) * i // iters for a, b in zip(color1, color2)]
        imageblitex(
            dst,
            dstw,
            dsth,
            dstx,
            dsty + i,
            dstx + maskw,
            dsty + i + rowsize,
            mask,
            maskw,
            maskh,
            0,
            i,
            patternimage=c,
            patternwidth=1,
            patternheight=1,
            # where the source (here, mask) is 1, leave unchanged;
            # where the pattern is 0 and source is 0, set black;
            # where the pattern is 1 and source is 0, set white
            ropForeground=0xB8,
            wraparound=wraparound,
        )

# 'dst' and 'mask' have the same format returned by the blankimage() method with alpha=False.
# 'wraparound' has the same meaning as in imageblitex(); default is False.
#
# Example: White-over-black-over gray text effect, seen in some early-90s Windows applications.
# ----
# dw.drawmask(img, w, h, x-1, y-1, mask,maskWidth,maskHeight, [255,255,255])
# dw.drawmask(img, w, h, x+1, y+1, mask,maskWidth,maskHeight, [128,128,128])
# dw.drawmask(img, w, h, x,y, mask,maskWidth,maskHeight, [0, 0, 0]) # Main text
#
# Example: Shadowed in the upper right and more strongly in the lower left
# ----
# dw.drawmask(img, w, h, x+1, y-1, mask,maskWidth,maskHeight, [0, 255, 0]) # Upper shadow
# dw.drawmask(img, w, h, x-1, y+1, mask,maskWidth,maskHeight, [0, 255, 0]) # Lower shadow
# dw.drawmask(img, w, h, x-2, y+2, mask,maskWidth,maskHeight, [0, 255, 0])
# dw.drawmask(img, w, h, x-3, y+3, mask,maskWidth,maskHeight, [0, 255, 0])
# dw.drawmask(img, w, h, x, y, img, w, h, [255, 255, 0]) # Main text
#
# Example: Create a dark-over-light pattern over a midtone background, given a tileable
# mask pattern.
#
# darktone=[0,0,0]
# midtone=[128,0,0]
# lighttone=[255,0,0]
# img=dw.blankimage(maskWidth,maskHeight,midtone) # Midtone background
# dw.drawmask(img,maskWidth,maskHeight,0,0,mask,maskWidth,maskHeight,
#    darktone,wraparound=True) # Dark pattern
# dw.drawmask(img,maskWidth,maskHeight,1,1,mask,maskWidth,maskHeight,
#    lighttone,wraparound=True)
#
# Example: Same as previous, but "1,1" becomes "0,1".  In this case, the light-toned pattern
# is shifted 1 pixel downward rather than 1 pixel downward and rightward.
def drawmask(dst, dstw, dsth, dstx, dsty, mask, maskw, maskh, color, wraparound=False):
    drawgradientmask(
        dst,
        dstw,
        dsth,
        dstx,
        dsty,
        mask,
        maskw,
        maskh,
        color,
        color,
        wraparound=wraparound,
    )

# 'image1' and 'image2' have the same format returned by the blankimage() method with alpha=False.
def transition(image1, image2, w, h, transition, tw, th, t, fuzziness=0.25):
    return _transition(
        image1,
        image2,
        w,
        h,
        transition,
        tw,
        th,
        (-fuzziness) + (1 + fuzziness * 2) * t,
        fuzziness=fuzziness,
    )

def _transition(image1, image2, w, h, transition, tw, th, t, fuzziness=0.25):
    if fuzziness < 0:
        raise ValueError
    if tw == None or tw <= 0 or th <= 0:
        raise ValueError
    fuzziness = min(fuzziness, 1.0)
    if t <= 0 - fuzziness:
        return [x for x in image1]
    if t >= 1 + fuzziness:
        return [x for x in image2]
    img = blankimage(w, h)
    for y in range(h):
        ty = th * y / max(1, h - 1)
        for x in range(w):
            c = imagept(transition, tw, th, tw * x / max(1, w - 1), ty)
            tt = c[0] / 255.0
            if t < tt - fuzziness:
                setpixel(img, w, h, x, y, getpixel(image1, w, h, x, y))
            elif t >= tt + fuzziness:
                setpixel(img, w, h, x, y, getpixel(image2, w, h, x, y))
            else:
                p1 = getpixel(image1, w, h, x, y)
                p2 = getpixel(image2, w, h, x, y)
                alpha = (t - (tt - fuzziness)) / (fuzziness * 2)
                pb = [int(a + (b - a) * alpha) for a, b in zip(p1, p2)]
                setpixel(img, w, h, x, y, pb)
    return img

def _off_mask(mask, w, h, x, y, pos, stride, ox, oy):
    return (
        y + oy < 0
        or y + oy >= h
        or x + ox < 0
        or x + ox >= w
        or mask[pos + stride * oy + 3 * ox] != 0
    )

def _on_mask(mask, w, h, x, y, pos, stride, ox, oy):
    return (
        y + oy >= 0
        and y + oy < h
        and x + ox >= 0
        and x + ox < w
        and mask[pos + stride * oy + 3 * ox] == 0
    )

# Draws one or more 3-D borders on the inner edge of a shape defined by a mask image,
# each of whose pixels is all zeros or all ones.
# The area of the shape is defined by the all-zero pixels.
# 'mask' has the same format returned by the blankimage() method with alpha=False.
# 'fillColor' is the fill color, if any; can be None, and default is None, indicating
# no fill color.
# 'traceInnerCorners' means whether the inner corners of a mask's outline are filled in
# by a pixel.
# 'lowerDominates' means the lower and right edges "dominate" over the upper and left
# edges.
# 'layercolors' is an list of two-element lists for the borders to draw from outermost
# to innermost.  Each two-element list contains the upper color and the lower color
# for a specific border.
#
# Example: Draws a raised outline, along with a lower right black edge,
# around a shape defined by a two-level mask image.
#
# helper = dw.ImageDrawHelper(image, w, h)
# dw.threedee(
#     helper,
#     0,
#     0,
#     mask,
#     w,
#     h,
#     # Raised outline has two layers
#     [
#         # Upper color, lower coloe
#         [[255, 255, 255], [128, 128, 128]],
#         [[255, 255, 255], [128, 128, 128]],
#     ], traceInnerCorners=True
# )
# dw.outeredge(helper, 0, 0, mask, w, h, [0, 0, 0],upperEdge=False,lowerEdge=True, traceInnerCorners=True)
#
# Example: Draw a yellow outline and a blue fill.
#
# helper = dw.ImageDrawHelper(image, w, h)
# dw.threedee(
#    helper, 0, 0, mask, w, h, [[[255, 255, 0], [255, 255, 0]]], fillColor=[0, 0, 255], traceInnerCorners=True
# )
#
def threedee(
    helper,
    x0,
    y0,
    mask,
    w,
    h,
    layercolors,
    fillColor=None,
    traceInnerCorners=False,
    lowerDominates=True,
):
    if len(layercolors) <= 0:
        raise ValueError
    layers = len(layercolors)
    maskbuffer1 = None
    maskbuffer2 = None
    frontmask = mask
    backmask = None
    stride = w * 3
    if layers > 1:
        maskbuffer1 = [x for x in mask]
        maskbuffer2 = [x for x in mask]
        frontmask = mask
        backmask = maskbuffer2
    for i in range(layers):
        pos = 0
        lc1 = layercolors[i][0]
        lc2 = layercolors[i][1]
        for y in range(h):
            xfill = -1
            for x in range(w):
                if frontmask[pos] != 0:
                    # Pixel not in mask
                    if backmask:
                        backmask[pos] = 0xFF
                    pos += 3
                    continue
                # Nonmask pixel flags.
                # Areas outside the image are considered outside the mask.
                left = x == 0 or frontmask[pos - 3] != 0
                upper = y == 0 or frontmask[pos - stride] != 0
                right = x == w - 1 or frontmask[pos + 3] != 0
                lower = y == h - 1 or frontmask[pos + stride] != 0
                upperleft = x == 0 or y == 0 or frontmask[pos - stride - 3] != 0
                upperright = x == w - 1 or y == 0 or frontmask[pos - stride + 3] != 0
                lowerright = (
                    x == w - 1 or y == h - 1 or frontmask[pos + stride + 3] != 0
                )
                lowerleft = y == h - 1 or x == 0 or frontmask[pos + stride - 3] != 0
                # nonmask pixel at left, or nonmask pixel above
                topshade = (
                    left
                    or upper
                    or (
                        traceInnerCorners
                        and (
                            (
                                # nonmask pixel at upper left, and mask pixels above
                                upperleft
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, -1)
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, -2)
                            )
                            or (
                                # nonmask pixel at lower left, and mask pixels below:
                                lowerleft
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, 1)
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, 2)
                            )
                        )
                    )
                )
                # nonmask pixel at right, or nonmask pixel below
                botshade = (
                    right
                    or lower
                    or (
                        traceInnerCorners
                        and (
                            (
                                # nonmask pixel at lower right, and mask pixels below
                                lowerright
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, 1)
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, 2)
                            )
                            or (
                                # nonmask pixel at upper right, and mask pixels above:
                                upperright
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, -1)
                                and _on_mask(frontmask, w, h, x, y, pos, stride, 0, -2)
                            )
                        )
                    )
                )
                isFill = False
                if not lowerDominates:
                    if topshade and botshade:
                        # avoid unsightly changes in relief color
                        if _off_mask(
                            frontmask, w, h, x, y, pos, stride, 0, -1
                        ) and not _off_mask(frontmask, w, h, x, y, pos, stride, -1, -1):
                            botshade = False
                        elif _off_mask(
                            frontmask, w, h, x, y, pos, stride, -1, 0
                        ) and not _off_mask(frontmask, w, h, x, y, pos, stride, -1, -1):
                            botshade = False
                    if topshade:
                        helper.rect(x + x0, y + y0, x + x0 + 1, y + y0 + 1, lc1)
                        if backmask:
                            backmask[pos] = 0xFF
                    elif botshade:
                        helper.rect(x + x0, y + y0, x + x0 + 1, y + y0 + 1, lc2)
                        if backmask:
                            backmask[pos] = 0xFF
                else:
                    if topshade and botshade:
                        # avoid unsightly changes in relief color
                        if _off_mask(
                            frontmask, w, h, x, y, pos, stride, 0, 1
                        ) and not _off_mask(frontmask, w, h, x, y, pos, stride, 1, 1):
                            botshade = False
                        elif _off_mask(
                            frontmask, w, h, x, y, pos, stride, 1, 0
                        ) and not _off_mask(frontmask, w, h, x, y, pos, stride, 1, 1):
                            botshade = False
                    if botshade:
                        helper.rect(x + x0, y + y0, x + x0 + 1, y + y0 + 1, lc2)
                        if backmask:
                            backmask[pos] = 0xFF
                    elif topshade:
                        helper.rect(x + x0, y + y0, x + x0 + 1, y + y0 + 1, lc1)
                        if backmask:
                            backmask[pos] = 0xFF

                if fillColor and (not botshade and not topshade) and i == layers - 1:
                    # Inner fill not taken up by edge borders
                    if xfill < 0:
                        xfill = x
                    isFill = True
                if (not isFill) and xfill >= 0:
                    helper.rect(xfill + x0, y + y0, x + x0, y + y0 + 1, fillColor)
                    xfill = -1
                pos += 3
            if xfill >= 0:
                helper.rect(x + xfill, y + y0, w + x0, y + y0 + 1, fillColor)
                xfill = -1
        frontmask = backmask
        backmask = maskbuffer1 if i % 2 == 0 else maskbuffer2

def outeredge(helper, x0, y0, mask, w, h, color, upperEdge=True, lowerEdge=True):
    if (not upperEdge) and (not lowerEdge):
        return
    maskbuffer1 = None
    maskbuffer2 = None
    frontmask = mask
    backmask = None
    stride = w * 3
    for i in range(1):
        pos = 0
        lc1 = color  # layercolors[i][0]
        lc2 = color  # layercolors[i][1]
        for y in range(h):
            xfill = -1
            for x in range(w):
                if frontmask[pos] == 0:
                    # Pixel in mask
                    pos += 3
                    continue
                # Mask pixel flags.
                # Areas outside the image are considered outside the mask.
                left = x > 0 and frontmask[pos - 3] == 0
                upper = y > 0 and frontmask[pos - stride] == 0
                right = x < w - 1 and frontmask[pos + 3] == 0
                lower = y < h - 1 and frontmask[pos + stride] == 0
                upperleft = x > 0 and y > 0 and frontmask[pos - stride - 3] == 0
                upperright = x < w - 1 and y > 0 and frontmask[pos - stride + 3] == 0
                lowerright = (
                    x < w - 1 and y < h - 1 and frontmask[pos + stride + 3] == 0
                )
                lowerleft = y < h - 1 and x < 0 and frontmask[pos + stride - 3] == 0
                botshade = (
                    lowerEdge
                    and (
                        (left and (upperleft or lowerleft))
                        or (upper and (upperleft or upperright))
                    )
                ) or (
                    upperEdge
                    and (
                        (right and (upperright or lowerright))
                        or (lower and (lowerleft or lowerright))
                    )
                )
                isFill = False
                if botshade:
                    helper.rect(x + x0, y + y0, x + x0 + 1, y + y0 + 1, lc2)
                    if backmask:
                        backmask[pos] = 0xFF
                pos += 3
        frontmask = backmask
        backmask = maskbuffer1 if i % 2 == 0 else maskbuffer2

# 'image1' and 'image2' have the same format returned by the blankimage() method with alpha=False.
def grayblackshadow(dst, dstw, dsth, dstx, dsty, src, srcw, srch, color):
    drawmask(dst, dstw, dsth, dstx - 2, dsty - 2, src, srcw, srch, [192, 192, 192])
    drawmask(dst, dstw, dsth, dstx + 2, dsty + 2, src, srcw, srch, [128, 128, 128])
    drawmask(dst, dstw, dsth, dstx, dsty, src, srcw, srch, color)

# Draws a colored cartoon or "pixel-art" sphere using only colors accepted by recolor()
# and recolordither().
# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def toonSphere(
    img,
    imgwidth,
    imgheight,
    xOff,
    yOff,
    sizewidth=128,
    sizeheight=128,
    drawOutline=True,
    alpha=False,
):
    w = sizewidth
    h = sizeheight
    cc2 = blankimage(w, h, [0, 0, 0, 0], alpha=alpha)
    # black mask
    cmask = blankimage(w, h, [0, 0, 0, 0], alpha=alpha)
    cmaskhelper = ImageDrawHelper(cmask, w, h, alpha=alpha)
    # draw white on the mask where the filled circle is
    helperellipsefill(cmaskhelper, [255, 255, 255, 255], 0, 0, w, h)
    helper = ImageDrawHelper(cc2, w, h, alpha=alpha)
    levels = 20
    # To achieve the "pixel-art" shading, fill concentric
    # circles.  This was a suggestion from a tutorial
    # video by "Mislav".
    for i in range(levels):
        cx = int(w * (0.5 - 0.25 * (i) / levels))
        cy = int(h * (0.5 - 0.25 * (i) / levels))
        radius = 0.5 - 0.49 * (i) / levels
        # Calculate circle position and size based
        # on a light source shining from the upper left
        # The outermost circle fills the entire final sphere; the
        # innermost circle pinpoints the specular highlight
        # on the sphere.
        if i == 0:
            # Outermost circle
            x0, y0, x1, y1 = (0, 0, w, h)
        else:
            x0 = int(cx - radius * w)
            y0 = int(cy - radius * h)
            x1 = int(cx + radius * w)
            y1 = int(cy + radius * h)
        col = None
        half = levels / 2
        if i <= half:
            # "Black" to color for the outer circles
            col = [min(255, int(255 * (i) / half) + 64), 0, 0, 255]
        else:
            # Color to "white" for the inner circles;
            # this simulates a specular highlight
            v = min(255, int(255 * (i - half) / half) + 32)
            col = [255, v, v, 255]
        helperellipsefill(helper, col, x0, y0, x1, y1)
    imageblitex(
        img,
        imgwidth,
        imgheight,
        0,
        0,
        w,
        h,
        cc2,
        w,
        h,
        maskimage=cmask,
        maskwidth=w,
        maskheight=h,
        alpha=alpha,
    )
    if drawOutline:
        helper = ImageDrawHelper(img, imgwidth, imgheight, alpha=alpha)
        helperellipsedraw(helper, [128, 0, 0, 255], 0, 0, imgwidth, imgheight)

# 3-dimensional vector dot product
def _dot3(a, b):
    return (a[0] * b[0]) + (a[1] * b[1]) + (a[2] * b[2])

# 3-dimensional vector addition
def _vecadd3(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]

# 3-dimensional vector subtraction
def _vecsub3(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

# Normalize 3-dimensional vector to a unit vector
def _normalize3(a):
    d = math.sqrt(abs(a[0] ** 2) + abs(a[1] ** 2) + abs(a[2] ** 2))
    if d == 0:
        # Degenerate (near-zero) vector
        return a
    return [v / d for v in a]

# Drawing modes:
# 0 = Colored mask
# 1 = Ambient/diffuse only
# 2 = Ambient/diffuse and specular
# 3 = Ambient/diffuse and two-level specular
# 4 = Two-level specular
def _threedeeCapsule(
    helper, xOff, yOff, color=None, sizewidth=128, sizeheight=128, drawingMode=0
):
    if color == None:
        color = [192, 0, 0]
    dcolor = [c / 255.0 for c in color]
    minsize = min(sizewidth, sizeheight)
    halfsize = minsize / 2
    xdiff = sizewidth - minsize
    ydiff = sizeheight - minsize
    drewSpecular = False
    lightpos = [-3, -3, 10]  # Light position
    if sizewidth > sizeheight:
        fac = max(sizewidth, sizeheight) / minsize
        lightpos = [-3 * fac, -3, 10]
    else:
        fac = max(sizewidth, sizeheight) / minsize
        lightpos = [-3, -3 * fac, 10]
    for y in range(sizeheight):
        # Vertex position
        yypos = (y + 0.5 - sizeheight / 2) / (sizeheight / 2)
        # Vertex normal
        yy = (
            (y + 0.5 - halfsize) / halfsize
            if y < halfsize
            else (
                (y + 0.5 - halfsize - ydiff) / halfsize
                if y > sizeheight - halfsize
                else 0
            )
        )
        haveSpecular = False
        for x in range(sizewidth):
            # Vertex normal
            xx = (
                (x + 0.5 - halfsize) / halfsize
                if x < halfsize
                else (
                    (x + 0.5 - halfsize - xdiff) / halfsize
                    if x > sizewidth - halfsize
                    else 0
                )
            )
            if xx * xx + yy * yy <= 1:  # On or inside capsule
                # Vertex position
                xxpos = (x + 0.5 - sizewidth / 2) / (sizewidth / 2)
                if drawingMode == 0:
                    # Drawing colored mask
                    helper.rect(x, y, x + 1, y + 1, color)
                    continue
                # z-coordinate of capsule
                z = (1 - xx * xx - yy * yy) ** (1 / 2)
                if z < 0:
                    raise ValueError
                vec = [xxpos, yypos, z]  # Vertex position for capsule
                n = [xx, yy, z]  # Vertex normal for capsule
                lightdir = _normalize3(_vecsub3(lightpos, vec))
                # Diffusion
                dd = _dot3(n, lightdir)
                newColor = [0, 0, 0]
                if dd >= 0:
                    if drawingMode >= 1 and drawingMode <= 3:
                        # Add diffuse color
                        newColor[0] += dcolor[0] * dd
                        newColor[1] += dcolor[1] * dd
                        newColor[2] += dcolor[2] * dd
                    if drawingMode >= 2:
                        # Calculate specular color with shininess of 40
                        half = _normalize3(
                            _vecadd3(_normalize3(_vecsub3([0, 0, 3], vec)), lightpos)
                        )
                        ds = max(0, _dot3(n, half)) ** 40
                        if ds > 0.5:  # Specular reflection bright enough
                            if drawingMode == 4:
                                haveSpecular = True
                                drewSpecular = True
                                helper.rect(
                                    x + xOff,
                                    y + yOff,
                                    x + xOff + 1,
                                    y + yOff + 1,
                                    color,
                                )
                            if drawingMode == 3:
                                ds = 1 if ds > 0.5 else 0
                            if drawingMode == 2 or drawingMode == 3:
                                newColor[0] += ds
                                newColor[1] += ds
                                newColor[2] += ds
                if drawingMode >= 1 and drawingMode <= 3:
                    # Add 1/4 of diffuse color as ambient color
                    newColor[0] += dcolor[0] / 4
                    newColor[1] += dcolor[1] / 4
                    newColor[2] += dcolor[2] / 4
                    newColor = [max(0, min(255, int(v * 255))) for v in newColor]
                    helper.rect(
                        x + xOff, y + yOff, x + xOff + 1, y + yOff + 1, newColor
                    )
        if (not haveSpecular) and drewSpecular:
            # finished drawing specular, which must be in one piece, so exit
            return

def threedeeCapsuleMask(sizewidth=128, sizeheight=128):
    img2 = dw.blankimage(sizewidth, sizeheight)
    helper = dw.ImageDrawHelper(img2, sizewidth, sizeheight)
    _threedeeCapsule(helper, 0, 0, [0, 0, 0], sizewidth, sizeheight, drawingMode=0)
    return img2

def threedeeCapsule(
    helper,
    x,
    y,
    sizewidth=128,
    sizeheight=128,
    color=None,
    specular=False,
    twoLevelSpecular=False,
):
    mode = 1
    if specular and twoLevelSpecular:
        mode = 3
    elif specular:
        mode = 2
    _threedeeCapsule(helper, x, y, color, sizewidth, sizeheight, drawingMode=mode)

# Returns an image with the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False.
def brushednoise(width, height, tileable=True, alpha=False):
    image = blankimage(width, height, [192, 192, 192], alpha=alpha)
    for i in range(max(width, height) * 5):
        c = random.choice([128, 128, 128, 128, 0, 255])
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        x1 = x + random.randint(0, width // 2)
        simplebox(
            image,
            width,
            height,
            [c, c, c],
            x,
            y,
            x1,
            y + 1,
            wraparound=tileable,
            alpha=alpha,
        )
    return image

# Returns an image with the same format returned by the blankimage() method with the specified value of 'alpha'.  The returned image is of dots at random positions and random gray tones.
# The default value for 'alpha' is False.
def marknoise(width, height, tileable=True, alpha=False):
    image = blankimage(width, height, [192, 192, 192], alpha=alpha)
    for i in range(max(width, height) * 5):
        c = random.choice([128, 128, 128, 128, 0, 255])
        pattern = [0x18, 0x3C, 0x7E, 0xFF, 0xFF, 0x7E, 0x3C, 0x18]
        x = random.randint(0, width)
        y = random.randint(0, height)
        hatchedbox_alignorigins(
            image,
            width,
            height,
            [c, c, c],
            pattern,
            x,
            y,
            x + 8,
            y + 8,
            wraparound=tileable,
            alpha=alpha,
        )
    return image

# Returns an image with the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False.
def brushednoise2(width, height, tileable=True, alpha=False):
    image = blankimage(width, height, [192, 192, 192], alpha=alpha)
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
        linedraw(
            image,
            width,
            height,
            [c, c, c],
            x,
            y,
            x1,
            y1,
            wraparound=tileable,
            alpha=alpha,
        )
    return image

# Returns an image with the same format returned by the blankimage() method with the specified value of 'alpha'.
# The default value for 'alpha' is False.
def brushednoise3(width, height, tileable=True, alpha=False):
    image = blankimage(width, height, [192, 192, 192], alpha=alpha)
    for i in range(max(width, height) * 3):
        c = random.choice([128, 128, 128, 128, 0, 255])
        if random.randint(0, 2) == 0:
            # circle
            x = random.randint(0, width)
            y = random.randint(0, height)
            x1 = random.randint(0, width // 2)
            circledraw(
                image,
                width,
                height,
                [c, c, c],
                x,
                y,
                x1,
                wraparound=tileable,
                alpha=alpha,
            )
        else:
            x = random.randint(0, width)
            y = random.randint(0, height)
            x1 = x + (-1 if random.randint(0, 1) == 0 else 1) * random.randint(
                0, width // 2
            )
            y1 = y + (-1 if random.randint(0, 1) == 0 else 1) * random.randint(
                0, height // 2
            )
            linedraw(
                image,
                width,
                height,
                [c, c, c],
                x,
                y,
                x1,
                y1,
                wraparound=tileable,
                alpha=alpha,
            )
    return image

# Rotates in place a column of the image by the specified downward offset in pixels,
# which may be negative or not.
# Image has the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def imagerotatecolumn(image, width, height, x, offset=0, alpha=False):
    if x < 0 or x >= width or width < 0 or height < 0:
        raise ValueError
    if height == 0 or width == 0:
        return image
    offset %= height
    if offset == 0:
        return image
    pixelBytes = 4 if alpha else 3
    pixels = [
        image[(y * width + x) * pixelBytes : (y * width + x + 1) * pixelBytes]
        for y in range(height)
    ]
    y = 0
    for i in range(height - offset, height):
        image[(y * width + x) * pixelBytes : (y * width + x + 1) * pixelBytes] = pixels[
            i
        ]
        y += 1
    for i in range(0, height - offset):
        image[(y * width + x) * pixelBytes : (y * width + x + 1) * pixelBytes] = pixels[
            i
        ]
        y += 1
    return image

# Rotates in place a row of the image by the specified rightward offset in pixels,
# which may be negative or not.
# Image has the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def imagerotaterow(image, width, height, y, offset=0, alpha=False):
    if y < 0 or y >= height or width < 0 or height < 0:
        raise ValueError
    if height == 0 or width == 0:
        return image
    pixelBytes = 4 if alpha else 3
    offset %= width
    if offset == 0:
        return image
    image[y * width * pixelBytes : (y + 1) * width * pixelBytes] = (
        image[
            (y * width + (width - offset)) * pixelBytes : (y + 1) * width * pixelBytes
        ]
        + image[y * width * pixelBytes : (y * width + (width - offset)) * pixelBytes]
    )
    return image

# Reverses in place the order of columns in the specified image.  Returns 'image'.
# Image has the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def imagereversecolumnorder(image, width, height, alpha=False):
    pixelBytes = 4 if alpha else 3
    for y in range(height):
        pixels = [
            image[(y * width + x) * pixelBytes : (y * width + x + 1) * pixelBytes]
            for x in range(width)
        ]
        pixels.reverse()
        image[y * width * pixelBytes : (y + 1) * width * pixelBytes] = [
            c for pixel in pixels for c in pixel
        ]
    return image

# Reverses in place the order of rows in the specified image.  Returns 'image'.
# Image has the same format returned by the blankimage() method with
# the specified value of 'alpha' (the default value for 'alpha' is False).
def imagereverseroworder(image, width, height, alpha=False):
    pixelBytes = 4 if alpha else 3
    halfHeight = height // 2  # floor of half height; don't care about middle row
    scan = width * pixelBytes
    for y in range(halfHeight):
        row = image[y * scan : (y + 1) * scan]
        otherRow = image[(height - 1 - y) * scan : (height - y) * scan]
        image[y * scan : (y + 1) * scan] = otherRow
        image[(height - 1 - y) * scan : (height - y) * scan] = row
    return image

# Returns True if width or height is 0 or if:
# - The image's first column's first half is a mirror
# of its second half, and...
# - The image's last column's first half is a mirror
# of its second half.
# Image has the same format returned by the blankimage() method with alpha=False.
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
# Image has the same format returned by the blankimage() method with alpha=False.
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

# Image has the same format returned by the blankimage() method with alpha=False.
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

# Images have the same format returned by the blankimage() method with the specified value of 'alpha' (default value for 'alpha' is False).
def affine(
    dstimage,
    dstwidth,
    dstheight,
    srcimage,
    srcwidth,
    srcheight,
    m11,  # upper left of matrix
    m12,  # upper right of matrix
    m21,  # lower left of matrix
    m22,  # lower right of matrix
    alpha=False,
    smoothing=True,
):
    bypp = 4 if alpha else 3
    for y in range(dstheight):
        yp = y / srcheight
        for x in range(dstwidth):
            xp = x / srcwidth
            tx = (xp * m11 + yp * m21) * srcwidth
            ty = (xp * m12 + yp * m22) * srcheight
            if smoothing:
                pixel = imagept(srcimage, srcwidth, srcheight, tx, ty, alpha=alpha)
                if alpha:
                    setpixelalpha(dstimage, dstwidth, dstheight, x, y, pixel)
                else:
                    setpixel(dstimage, dstwidth, dstheight, x, y, pixel)
            else:
                tx = int(tx) % srcwidth
                ty = int(ty) % srcheight
                dstindex = (y * dstwidth + x) * bypp
                srcindex = (ty * srcwidth + tx) * bypp
                if dstindex < 0 or dstindex > len(dstimage):
                    raise ValueError([x, y, tx, ty])
                if srcindex < 0 or srcindex > len(srcimage):
                    raise ValueError([x, y, tx, ty])
                dstimage[dstindex : dstindex + bypp] = srcimage[
                    srcindex : srcindex + bypp
                ]
    return dstimage

# Generates an image with a horizontal doubling of pixels.
# The returned image has width 2*'w' and height 2*'h'.
# Images have the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def twobyonestretch(image, w, h, alpha=False):
    return affine(
        blankimage(w * 2, h),
        w * 2,
        h,
        image,
        w,
        h,
        1 / 2,
        0,
        0,
        1,
        alpha=alpha,
        smoothing=False,
    )

# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def horizskew(image, width, height, skew, alpha=False):
    if skew < -1 or skew > 1:
        raise ValueError
    for i in range(height):
        p = i / height
        imagerotaterow(image, width, height, i, int(skew * p * width), alpha=alpha)
    return image

# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def vertskew(image, width, height, skew, alpha=False):
    if skew < -1 or skew > 1:
        raise ValueError
    for i in range(width):
        p = i / width
        imagerotatecolumn(image, width, height, i, int(skew * p * height), alpha=alpha)
    return image

# Generates a sheared image, with optional resizing.
# 'newwidth' is the new width of the image in pixels.  If not given, same as 'width'.
# 'newheight' is the new height of the image in pixels.  If not given, same as 'height'.
# If upward=True (the default), the shear is upward and only the left and right edges
# of the input image must be tileable; the upper and lower edges need not be.
# If upward=False, the shear is rightward and only the upper and lowe edges
# of the input image must be tileable.
# Input and output images have the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def imageshear(
    img,
    width,
    height,
    newwidth=None,
    newheight=None,
    alpha=False,
    upward=True,
    smoothing=True,
):
    if not newwidth:
        newwidth = width
    if not newheight:
        newheight = height
    if width <= 0 or height <= 0 or not img:
        raise ValueError
    if newwidth <= 0 or newheight <= 0 or not img:
        raise ValueError
    img2 = blankimage(newwidth, newheight, alpha=alpha)
    if len(img2) != newwidth * newheight * 3:
        raise ValueError
    affine(
        img2,
        newwidth,
        newheight,
        img,
        width,
        height,
        width / newwidth,
        width / newwidth if upward else 0,
        0 if upward else height / newheight,
        height / newheight,
        alpha=alpha,
        smoothing=smoothing,
    )
    return img2

# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def randomRotated(image, width, height, alpha=False):
    # Do the rotation rarely
    if random.randint(0, 6) > 0:
        return [image, width, height]
    # A rotated but still tileable version of the specified image
    stretch = 2  # must be an integer
    slant = int(math.hypot(width * stretch, height))
    size = width
    image2width = int(slant * (width / size))
    image2height = int(slant * (height / size))
    image2 = blankimage(image2width, image2height, alpha=alpha)
    r1 = random.choice([1, -1])  # normally -1
    r2 = random.choice([-1, 1])  # normally 1
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
            alpha=alpha,
            smoothing=True,
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

# Makes a tileable image from a not necessarily tileable image, by blending
# the image's edge with its middle.
# Image has the same format returned by the blankimage() method
# with the specified value of 'alpha' (default value for 'alpha' is False).
#
# Blending Note: Operations that involve the blending of two RGB (red-green-
# blue) colors work best if the RGB color space is linear.  This is not the case
# for the sRGB color space, which is the color space assumed for images created
# using the blankimage() method.  Moreover, converting an image from a nonlinear
# to a linear color space and back can lead to data loss especially if the image's color
# components are 8 bits or fewer in length (as with images returned by blankimage()).
# This function does not do any such conversion.
def maketileable(image, width, height, alpha=False):
    # Use tiling method described by Paul Bourke,
    # Tiling Textures on the Plane (Part 1)
    # https://paulbourke.net/geometry/tiling/
    if width * height * (4 if alpha else 3) > len(image):
        raise ValueError
    ret = blankimage(width, height, alpha=alpha)
    for y in range(height):
        yp = (y + height // 2) % height
        for x in range(width):
            xp = (x + width // 2) % width
            m1 = 1 - _linearmask(width, height, x, y)
            m2 = 1 - _linearmask(width, height, xp, yp)
            m1 = max(0.001, m1)
            m2 = max(0.001, m2)
            o1 = (
                getpixelalpha(image, width, height, x, y)
                if alpha
                else getpixel(image, width, height, x, y)
            )
            o2 = (
                getpixelalpha(image, width, height, xp, yp)
                if alpha
                else getpixel(image, width, height, xp, yp)
            )
            if alpha:
                if len(o1) != 4 or len(o2) != 4:
                    raise ValueError
                t = [
                    m1 * ov1 / (m1 + m2) + m2 * ov2 / (m1 + m2)
                    for ov1, ov2 in zip(o1, o2)
                ]
                if len(t) != 4:
                    raise ValueError
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
# and raster graphics of classic-operating-system-style borders and button controls.
# Although the SVGs are scalable
# by definition, they are pixelated just as they would appear in classic OSs.
#
# NOTE: A more flexible approach for this kind of drawing
# is to prepare an SVG defining the frame of a user-interface element
# with five different parts (in the form of 2D shapes): an "upper outer part", a
# "lower outer part", an "upper inner part", a "lower inner part", and a "middle part".
# Each of these five parts can be colored separately or filled with a pattern.

# Image has the same format returned by the blankimage() method with alpha=False.
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

class ImageDrawHelper:
    # Image has the same format returned by the blankimage() method with
    # the specified value of 'alpha'.  The default value of 'alpha' is False.
    def __init__(self, image, width, height, wraparound=True, alpha=False):
        self.image = image
        self.width = width
        self.height = height
        self.alpha = alpha
        self.wraparound = wraparound

    def rect(self, x0, y0, x1, y1, c):
        if len(c) == 2:
            borderedbox(
                image,
                width,
                height,
                None,
                c[0],
                c[1],
                x0,
                y0,
                x1,
                y1,
                wraparound=self.wraparound,
                alpha=self.alpha,
            )
        else:
            simplebox(
                self.image,
                self.width,
                self.height,
                c,
                x0,
                y0,
                x1,
                y1,
                wraparound=self.wraparound,
                alpha=self.alpha,
            )

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

    def _ditherbg(self, idstr, face, hilt, hiltIsScrollbarColor=False, stripe=False):
        # 'face' is the button face color
        # 'hilt' is the button highlight color
        if hiltIsScrollbarColor:
            return hilt
        if "'" in idstr:
            raise ValueError
        if '"' in idstr:
            raise ValueError
        image = blankimage(2, 2)
        helper = ImageDrawHelper(image, 2, 2)
        if hiltIsScrollbarColor:
            helper.rect(0, 0, 2, 2, hilt)
        # elif 256 or more colors and hilt is not white:
        #    helper.rect(0, 0, 2, 2, [(a+b)//2 for a,b in zip(face, hilt)])
        elif stripe:
            # stripe pattern (highlight and face colors are in alternating
            # rows)
            helper.rect(0, 0, 1, 1, hilt)
            helper.rect(1, 1, 2, 2, face)
            helper.rect(0, 1, 1, 2, face)
            helper.rect(1, 0, 2, 1, hilt)
        else:
            # checkerboard pattern
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
        ret = "<svg width='%dpx' height='%dpx' viewBox='0 0 %d %d'" % (
            width,
            height,
            width,
            height,
        )
        ret += " xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>"
        ret += str(self) + "</svg>"
        return ret

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
    if len(points) < 1:
        raise ValueError
    size = 4 + len(points) * 2
    lastpt = points[len(points) - 1]
    firstpt = points[0]
    closed = firstpt[0] == lastpt[0] and firstpt[0][1] == lastpt[1]
    if not closed:
        size += 4
    ret = struct.pack("<LHH", size, 0x324, len(points))
    for pt in points:
        if pt[0] < -32768 or pt[0] > 32767:
            raise ValueError
        if pt[1] < -32768 or pt[1] > 32767:
            raise ValueError
        ret += struct.pack("<hh", pt[0], pt[1])
    if not closed:
        ret += struct.pack("<hh", firstpt[0], firstpt[1])
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
        # left edge (includes lower left and upper left "pixels")
        helper.rect(x0, y0, x0 + edgesize, y1, color)
        # upper edge (includes upper right "pixel")
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
        # left edge (includes upper right and lower right "pixels")
        helper.rect(x1 - edgesize, y0, x1, y1, color)  # right edge
        # lower edge (includes lower left "pixel")
        helper.rect(x0, y1 - edgesize, x1 - edgesize, y1, color)

# hilt = upper part of edge, dksh = lower part of edge
def _drawroundededgecore(helper, x0, y0, x1, y1, upper, lower, edgesize=1):
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        return
    elif x1 - x0 < edgesize * 2:  # too narrow
        helper.rect(x0, y0 + edgesize, x1, y0 - edgesize, upper)
    elif y1 - y0 < edgesize * 2:  # too short
        helper.rect(x0 + edgesize, y0, x1 - edgesize, y1, upper)
    else:
        helper.rect(x0, y0 + edgesize, x0 + edgesize, y1 - edgesize, upper)  # left edge
        helper.rect(
            x0 + edgesize, y0, x1 - edgesize, y0 + edgesize, upper
        )  # upper edge
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
        )  # lower edge

def drawpositiverect(helper, x0, y0, x1, y1, face):
    if x1 <= x0 or y1 <= y0:  # empty or negative
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

def drawsunkengroup(helper, x0, y0, x1, y1, hilt, lt, shadow, dkshadow):
    z = 0
    drawedgebotdom(helper, x0 + z, y0 + z, x1 - z, y1 - z, dkshadow, dkshadow)
    z += 1
    drawedgebotdom(helper, x0 + z, y0 + z, x1 - z, y1 - z, shadow, hilt)
    return [x0 + z, y0 + z, max(x0 + z, x1 - z), max(y0 + z, y1 - z)]

def drawreliefborder(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt,
    lt,
    shadow,
    dkshadow,
    outerbevel=1,
    midframe=1,
    innerbevel=1,
):
    z = 0
    drawedgetopdom(helper, x0 + z, y0 + z, x1 - z, y1 - z, dkshadow, dkshadow)
    z += 1
    drawedgetopdom(
        helper, x0 + z, y0 + z, x1 - z, y1 - z, hilt, shadow, bordersize=outerbevel
    )
    z += outerbevel
    for i in range(midframe):
        drawedgebotdom(helper, x0 + z, y0 + z, x1 - z, y1 - z, lt, lt)
        z += 1
    drawedgetopdom(
        helper, x0 + z, y0 + z, x1 - z, y1 - z, shadow, hilt, bordersize=innerbevel
    )
    z += innerbevel
    drawedgebotdom(helper, x0 + z, y0 + z, x1 - z, y1 - z, dkshadow, dkshadow)
    return [x0 + z, y0 + z, max(x0 + z, x1 - z), max(y0 + z, y1 - z)]

# helper for edge drawing (lower right edge "dominates")
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
def drawedgenodomex(
    helper,
    x0,
    y0,
    x1,
    y1,
    upper,
    lower,
    upperRight,
    lowerLeft,
    edgesize=1,
    bordersize=1,
):
    for i in range(bordersize):
        drawupperedge(
            helper, x0, y0, x1 - edgesize, y1 - edgesize, upper, edgesize=edgesize
        )
        drawloweredge(
            helper, x0 + edgesize, y0 + edgesize, x1, y1, lower, edgesize=edgesize
        )
        # uupper-right corner
        drawpositiverect(helper, x1 - edgesize, y0, x1, y0 + edgesize, upperRight)
        # lower-left corner
        drawpositiverect(helper, x0, y1 - edgesize, x0 + edgesize, y1, lowerLeft)
        x0 += edgesize
        y0 += edgesize
        x1 -= edgesize
        y1 -= edgesize

# helper for edge drawing (neither edge "dominates")
def drawedgenodom(
    helper, x0, y0, x1, y1, upper, lower, corner, edgesize=1, bordersize=1
):
    drawedgenodomex(
        helper,
        x0,
        y0,
        x1,
        y1,
        upper,
        lower,
        corner,
        corner,
        edgesize=edgesize,
        bordersize=bordersize,
    )

# If basrelief=True: draw a sunken-middle-raised "groove" border (from outer to inner).
# If basrelief=False: draw a raised-middle-sunken "bump" border (from outer to inner).
def drawreliefborder(
    helper,
    x0,
    y0,
    x1,
    y1,
    hilt=None,
    sh=None,
    lt=None,
    frame=None,
    outerbordersize=1,
    innerbordersize=1,
    midbordersize=1,
    basrelief=True,
):
    if hilt == None:
        hilt = [255, 255, 255]
    if sh == None:
        sh = [128, 128, 128]
    if lt == None:
        lt = [128, 128, 128]
    if frame == None:
        frame = [0, 0, 0]
    if innerbordersize < 0:
        raise ValueError
    if outerbordersize < 0:
        raise ValueError
    if midbordersize < 0:
        raise ValueError
    # Outer border
    if basrelief:
        drawsunkenborderbotdom(
            helper, x0, y1, x1, y1, hilt, None, sh, None, bordersize=outerbordersize
        )
    else:
        drawraisedborderbotdom(
            helper, x0, y1, x1, y1, hilt, None, sh, None, bordersize=outerbordersize
        )
    # Middle border
    drawedgebotdom(
        helper,
        x0 + outerbordersize,
        y1 + outerbordersize,
        x1 - outerbordersize,
        y1 - outerbordersize,
        frame if basrelief else lt,
        frame if basrelief else lt,
        bordersize=midbordersize,
    )
    # Inner border
    if basrelief:
        drawraisedborderbotdom(
            helper,
            x0 + outerbordersize + midbordersize,
            y1 + outerbordersize + midbordersize,
            x1 - outerbordersize - midbordersize,
            y1 - outerbordersize - midbordersize,
            hilt,
            None,
            sh,
            None,
            bordersize=innerbordersize,
        )
    else:
        drawsunkenborderbotdom(
            helper,
            x0 + outerbordersize + midbordersize,
            y1 + outerbordersize + midbordersize,
            x1 - outerbordersize - midbordersize,
            y1 - outerbordersize - midbordersize,
            hilt,
            None,
            sh,
            None,
            bordersize=innerbordersize,
        )
    c = midbordersize + outerbordersize + innerbordersize
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

# Draw an inner window edge in raised style,
# according to Windows 95 design guide (The Windows
# Interface Guidelines for Software Design).
def drawraisedinnerwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, hilt, sh)

# Draw an outer window edge in sunken style,
# according to Windows 95 design guide
def drawsunkenouterwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, sh, hilt)

# Draw an outer window edge in sunken style,
# according to Windows 95 design guide
def drawsunkeninnerwindow(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, dksh, lt)

# The following four functions draw button edges (also known as "soft" edges)
# in raised or sunken style

# Draw an outer button edge (or "soft" edge) in raised style,
# according to Windows 95 design guide
def drawraisedouterwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, hilt, dksh)

# Draw an inner button edge (or "soft" edge) in raised style,
# according to Windows 95 design guide
def drawraisedinnerwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, lt, sh)

# Draw an outer button edge (or "soft" edge) in sunken style,
# according to Windows 95 design guide
def drawsunkenouterwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0, y0, x1, y1, dksh, hilt)

# Draw an inner button edge (or "soft" edge) in sunken style,
# according to Windows 95 design guide
def drawsunkeninnerwindowbutton(helper, x0, y0, x1, y1, hilt, lt, sh, dksh):
    drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, sh, lt)

####

# Raised border where the "upper left dominates"
def drawraisedbordertopdom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgetopdom(helper, x0, y0, x1, y1, hilt, sh, bordersize=bordersize)

# Sunken border where the "upper left dominates"
def drawsunkenbordertopdom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgetopdom(helper, x0, y0, x1, y1, sh, hilt, bordersize=bordersize)

# Raised border where neither edge "dominates"
def drawraisedbordernodom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgenodom(helper, x0, y0, x1, y1, hilt, sh, lt, bordersize=bordersize)

# Sunken border where neither edge "dominates"
def drawsunkenbordernodom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgenodom(helper, x0, y0, x1, y1, sh, hilt, lt, bordersize=bordersize)

# Raised border where the "lower right dominates"
def drawraisedborderbotdom(helper, x0, y0, x1, y1, hilt, lt, sh, dksh, bordersize=1):
    drawedgebotdom(helper, x0, y0, x1, y1, hilt, sh, bordersize=bordersize)

# Sunken border where the "lower right dominates"
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

# Draws a grouping box, intended to resemble a grooved box, in Windows 95 style.
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

# Draws a status field box, intended to resemble a slightly recessed box, in Windows 95 style.
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
        drawroundededge(helper, x0, y0, x1, y1, lt, sh)

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
    lowLight=False,
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    drawedgebotdom(helper, x0 + edge, y0 + edge, x1 - edge, y1 - edge, hilt, sh)
    drawedgebotdom(
        helper,
        x0 + edge + 1,
        y0 + edge + 1,
        x1 - edge - 1,
        y1 - edge - 1,
        None if lowLight else hilt,
        sh,
    )
    if frame:
        drawRoundOrSquareEdge(helper, x0, y0, x1, y1, frame, frame, squareFrame)
        if isDefault:
            drawedgebotdom(helper, x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)
    if lowLight:
        return [x0 + edge + 1, y0 + edge + 1, x1 - edge - 2, y1 - edge - 2, btn]
    else:
        return [x0 + edge + 2, y0 + edge + 2, x1 - edge - 2, y1 - edge - 2, btn]

# Draws a mask pattern with a "shaded" and shifted mask pattern above it.
# 'image' and 'mask' have the same format returned by the blankimage() method with alpha=False.
# 'mask' should be limited to "black" pixels (0,0,0) and "white" pixels (255,255,255).
def shadeabove(
    image,
    w,
    h,
    x,
    y,
    mask,
    maskwidth,
    maskheight,
    shiftx,  # X shift of shaded shape
    shifty,  # Y shift of shaded shape
    color,
    shadowcolor,  # Optional; can be None
    midcolor,
    wraparound=False,
):
    newmask = [x for x in mask]
    sx = shiftx
    sy = shifty
    # Do an OR on the mask with a shifted version of itself
    imageblitex(
        newmask,
        maskwidth,
        maskheight,
        sx,
        sy,
        maskwidth + sx,
        maskheight + sy,
        mask,
        maskwidth,
        maskheight,
        0,
        0,
        ropForeground=0xEE,
        wraparound=False,
    )
    # Fill upper rows with "white"
    imageblitex(
        newmask,
        maskwidth,
        maskheight,
        0,
        0,
        maskwidth,
        sy,
        mask,
        maskwidth,
        maskheight,
        0,
        0,
        ropForeground=0xFF,
    )
    # Fill left-hand columns with "white"
    imageblitex(
        newmask,
        maskwidth,
        maskheight,
        0,
        sy,
        sx,
        maskheight,
        mask,
        maskwidth,
        maskheight,
        0,
        0,
        ropForeground=0xFF,
    )
    drawmask(
        image, w, h, x, y, mask, maskwidth, maskheight, color, wraparound=wraparound
    )
    if shadowcolor != None:
        drawmask(
            image,
            w,
            h,
            x + sx,
            y + sy,
            mask,
            maskwidth,
            maskheight,
            shadowcolor,
            wraparound=wraparound,
        )
    drawmask(
        image,
        w,
        h,
        x,
        y,
        newmask,
        maskwidth,
        maskheight,
        midcolor,
        wraparound=wraparound,
    )

# Draw a 3-D slider thumb.
# 'dst' has the same format returned by the blankimage() method with alpha=False.
def slider3d(dst, dstwidth, dstheight, x0, y0, sw=12, sh=24):
    # Draw slider thumb mask
    mask = blankimage(sw, sh)
    helper = ImageDrawHelper(mask, sw, sh)
    simplepolygonfill(
        helper,
        [0, 0, 0],
        [[0, 0], [sw, 0], [sw, sh - sw // 2], [sw // 2, sh], [0, sh - sw // 2]],
    )
    # Draw 3-D effect using mask
    helper = ImageDrawHelper(dst, dstwidth, dstheight)
    threedee(
        helper,
        x0,
        y0,
        mask,
        sw,
        sh,
        [
            [[255, 255, 255], [0, 0, 0]],
            [[192, 192, 192], [128, 128, 128]],
        ],
        fillColor=[150, 150, 150],
        traceInnerCorners=True,
    )

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
    if x * 6.0 < 1 or y * 6.0 < 1 or x * 6 > 5 or y * 6 > 5:
        return contour(x, y)
    x = min(1, max(0, 3 * x / 2 - 1 / 4))
    y = min(1, max(0, 3 * y / 2 - 1 / 4))
    return contour(x, y)

def _randomgradientfillex(width, height, palette, contour):
    image = blankimage(width, height)
    grad = randomColorization()
    borderedgradientbox(
        image,
        width,
        height,
        None,
        grad,
        contour,
        0,
        0,
        width,
        height,
        jitter=random.randint(0, 1) == 0,
    )
    if palette:
        patternDither(image, width, height, palette)
    return image

def _randomcontour(tileable=True, includeWhole=False):
    contours = []
    r = random.choice([0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 3.5, 4])
    if tileable:
        # Tileable gradient contours
        # NOTE: These contours return a value in [-1, 1],
        # except for _square and _argyle, which returns
        # a value in [0, 1].
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
        # NOTE: These contours return a value in [-1, 1],
        # except for _square and _argyle, which returns
        # a value in [0, 1].
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
        # _whole returns 1
        contours.append(_whole)
    ret = random.choice(contours)
    if random.randint(0, 9) == 0:
        rr = ret
        ret = lambda x, y: _insetbox(x, y, rr)
    return ret

def _randomgradientfill(width, height, palette, tileable=True):
    return _randomgradientfillex(width, height, palette, _randomcontour(tileable))

def _colorizeInPlaceFromFourGrays(image, width, height):
    black = [0, 0, 0]
    white = [255, 255, 255]
    # dark gray and light gray from the VGA palette
    color0 = [128, 128, 128]
    color1 = [192, 192, 192]
    r2 = random.randint(0, 6)
    if r2 > 0:
        # use a "colored" dark gray and light gray from the VGA palette instead
        color0 = [(r2 & 1) * 0x80, ((r2 >> 1) & 1) * 0x80, ((r2 >> 2) & 1) * 0x80]
        color1 = [(r2 & 1) * 0xFF, ((r2 >> 1) & 1) * 0xFF, ((r2 >> 2) & 1) * 0xFF]
    # replace the grays with the colors
    gcolors = _gradient([[0, black], [128, color0], [192, color1], [255, white]])
    return graymap(image, width, height, gcolors)

# Image has the same format returned by the blankimage() method with alpha=False.
def randommaybemonochrome(image, width, height, vga=False):
    r = random.randint(0, 99)
    black = [0, 0, 0]
    white = [255, 255, 255]
    if r < 16:
        r2 = random.randint(0, 6)
        # dark gray and light gray from the VGA palette
        color0 = [128, 128, 128]
        color1 = [192, 192, 192]
        if r2 > 0:
            # use a "colored" dark gray and light gray from the VGA palette instead
            color0 = [(r2 & 1) * 0x80, ((r2 >> 1) & 1) * 0x80, ((r2 >> 2) & 1) * 0x80]
            color1 = [(r2 & 1) * 0xFF, ((r2 >> 1) & 1) * 0xFF, ((r2 >> 2) & 1) * 0xFF]
        if r < 8:
            image = dithertograyimage(
                [x for x in image], width, height, [0, 128, 255] if vga else None
            )
            minipal = random.choice(
                [
                    [black, color0, color1],  # dark
                    [black, color0, white],  # gray
                    [black, color1, white],  # light gray
                    [color0, color1, white],  # light
                ]
            )
            # replace the grays with the colors
            gcolors = _gradient([[0, minipal[0]], [128, minipal[1]], [255, minipal[2]]])
            return graymap([x for x in image], width, height, gcolors)
        else:
            image = dithertograyimage(
                [x for x in image], width, height, [0, 128, 192, 255] if vga else None
            )
            return _colorizeInPlaceFromFourGrays(image, width, height)
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
    r = random.randint(0, 99)
    if r < 25:
        return _randomnoiseimage(w, h, palette, tileable=tileable)
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

# Image returned by this method has the same format returned by the blankimage() method with alpha=False.
def randomhatchimage(w, h, palette=None, tileable=True):
    # Generates a random hatch image (using the specified palette, if any)
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
    # Generates a random boxes image (using the specified palette, if any)
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

def _randomhatch():
    match random.randint(0, 4):
        case 0:
            return [0, 0xFF, 0, 0xFF, 0, 0xFF, 0, 0xFF]
        case 1:
            return [0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55]
        case 2:
            return [0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA]
        case 3:
            return [0x88, 0x44, 0x22, 0x11, 0x88, 0x44, 0x22, 0x11]
        case 4:
            return [0x11, 0x22, 0x44, 0x88, 0x11, 0x22, 0x44, 0x88]
        case _:
            raise ValueError

def _tileborder(image, width, height, orgx=0, orgy=0):
    match random.randint(0, 1):
        case 0:
            _tileborder1(image, width, height, orgx, orgy)
        case 1:
            _tileborder2(image, width, height, orgx, orgy)
        case _:
            raise ValueError

def _tileborder2(image, width, height, orgx=0, orgy=0):
    thick = random.randint(1, 10)
    padding = random.randint(1, 10)
    mindim = (thick + padding + 2 + 1) * 2
    if width < mindim or height < mindim:
        _tileborder1(image, width, height, orgx, orgy)
        return
    helper = ImageDrawHelper(image, width, height)
    z = 0
    x0 = orgx
    y0 = orgy
    x1 = orgx + width
    y1 = orgy + height
    if random.randint(0, 1) == 0:
        # Draw "black" border
        drawedgetopdom(helper, x0 + z, y0 + z, x1 - z, y1 - z, [0, 0, 0], [0, 0, 0])
        z += 1
    # Draw raised bevel
    drawedgetopdom(
        helper,
        x0 + z,
        y0 + z,
        x1 - z,
        y1 - z,
        [255, 255, 255],
        [128, 128, 128],
        bordersize=thick,
    )
    # Draw engraved and padded inner border
    z += thick + padding
    drawedgetopdom(
        helper, x0 + z, y0 + z, x1 - z, y1 - z, [128, 128, 128], [255, 255, 255]
    )
    z += 1
    drawedgetopdom(
        helper, x0 + z, y0 + z, x1 - z, y1 - z, [255, 255, 255], [128, 128, 128]
    )

def _tileborder1(image, width, height, orgx=0, orgy=0):
    thick = random.randint(2, 10)
    x0 = orgx - thick // 2
    y0 = orgy - thick // 2
    pattern = _randomhatch()
    simplebox(image, width, height, [128, 128, 128], x0, 0, x0 + thick, height)
    hatchedbox(image, width, height, [0, 0, 0], pattern, x0, 0, x0 + thick, height)
    simplebox(image, width, height, [128, 128, 128], 0, y0, width, y0 + thick)
    hatchedbox(image, width, height, [0, 0, 0], pattern, 0, y0, width, y0 + thick)
    helper = ImageDrawHelper(image, width, height)
    xt = x0 + thick
    yt = y0 + thick
    drawedgetopdom(
        helper, xt, yt, xt + width - thick, yt + height - thick, [0, 0, 0], [0, 0, 0]
    )
    drawedgetopdom(
        helper,
        xt + 1,
        yt,
        xt + width - thick,
        yt + height - thick - 1,
        [255, 255, 255],
        [0, 0, 0],
    )

def _randomnoiseimage(w, h, palette=None, tileable=True):
    transpose = random.randint(0, 1) == 0
    ww = h if transpose else w
    hh = w if transpose else h
    r = random.randint(0, 5)
    if r == 0:
        image = brushednoise(ww, hh, tileable=tileable)
    elif r == 1:
        image = brushednoise2(ww, hh, tileable=tileable)
    elif r == 2:
        image = noiseimage(ww, hh)
        convolveRow(image, ww, hh)
    elif r == 2:
        image = marknoise(ww, hh, tileable=tileable)
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

# Generates a random checkerboard pattern image (using the specified palette, if any)
# Image returned by this method has the same format returned by the blankimage() method with alpha=False.
def randomcheckimage(w, h, palette=None, tileable=True):
    if w % 2 == 0 and h % 2 == 0 and random.randint(0, 99) < 10:
        otherImage = _randombackground(w // 2, h // 2, palette, tileable=tileable)
        return _colorizeInPlaceFromFourGrays(
            graychecker(
                otherImage, w // 2, h // 2, lightFirst=(random.randint(0, 1) == 0)
            ),
            w,
            h,
        )
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
    image3 = simpleargyle(fg, bg, linecolor, w, h, expo=random.uniform(0.5, 2.5))
    if palette:
        halfhalfditherimage(image3, w, h, palette)
    return image3

def randommixedimage(width, height, palette, tileable=True):
    numimages = random.randint(1, 6)
    images = [
        randombackgroundimage(width, height, None, tileable) for i in range(numimages)
    ]
    if numimages == 1:
        return images[0]
    contour = _randomcontour(tileable)
    image = blankimage(width, height)
    grad = randomColorization()
    imagegradientbox(
        image,
        images,
        width,
        height,
        grad,
        contour,
        0,
        0,
        width,
        height,
        jitter=random.randint(0, 1) == 0,
    )
    if palette:
        patternDither(image, width, height, palette)
    return image

# Image returned by this method has the same format returned by the blankimage() method with alpha=False.
def randombackgroundimage(w, h, palette=None, tileable=True):
    r = random.randint(0, 6)
    bordertile = random.randint(0, 5) == 0
    ret = None
    dotile = tileable and not bordertile
    if r == 0:
        ret = randomhatchimage(w, h, palette, tileable=dotile)
    elif r == 1:
        ret = randomcheckimage(w, h, palette, tileable=dotile)
    elif r == 2:
        ret = _randomboxesimage(
            w, h, palette, tileable=dotile, fancy=(random.randint(0, 3) != 0)
        )
    elif r == 3:
        ret = _randomgradientfill(w, h, palette, tileable=dotile)
    elif r == 4:
        ret = _randomsimpleargyle(w, h, palette, tileable=dotile)
    elif r == 5:
        ret = _randomshadedboxesimage(w, h, palette, tileable=dotile)
    else:
        ret = _randomnoiseimage(w, h, palette, tileable=dotile)
    if bordertile:
        _tileborder(ret, w, h)
        graymap(
            ret,
            w,
            h,
            colorgradient([0, 0, 0], [random.randint(0, 255) for i in range(3)]),
        )
    if random.randint(0, 7) == 0 and (not tileable or (w % 4 == 0 and h % 4 == 0)):
        # Draw a random hatch pattern, only if width and height are
        # divisible by 4 or image is not tileable
        r = random.randint(0, 1)
        color = (
            random.choice(palette)
            if palette
            else [random.randint(0, 255) for i in range(3)]
        )
        wstart = random.randint(0, w // 3)
        hstart = random.randint(0, h // 3)
        x0 = wstart if r == 0 else 0
        y0 = 0 if r == 0 else hstart
        x1 = w - wstart if r == 0 else w
        y1 = h if r == 0 else h - hstart
        hatchedbox(ret, w, h, color, _randomhatch(), x0, y0, x1, y1)
    return ret

# Creates a checkerboard pattern of a "light" version and a "dark" version of the specified image,
# after converting that image to grayscale.
# Input image has the same format returned by the blankimage() method with alpha=False.
def graychecker(image, width, height, lightFirst=False):
    # darker image
    colors = [[i * 192 // 255, i * 192 // 255, i * 192 // 255] for i in range(256)]
    image1 = graymap([x for x in image], width, height, colors)
    # lighter image
    colors = [
        [128 + i * 127 // 255, 128 + i * 127 // 255, 128 + i * 127 // 255]
        for i in range(256)
    ]
    image2 = graymap([x for x in image], width, height, colors)
    if lightFirst:
        return checkerboardtile(image2, image1, width, height)
    else:
        return checkerboardtile(image1, image2, width, height)

# Input image uses only three colors: (0,0,0) or black,(128,128,128),(255,255,255) or white
# Creates a checkerboard pattern of a "light" version and a "dark" version of the specified image.
# Input image has the same format returned by the blankimage() method with alpha=False.
def checkerFromThreeGrays(image, width, height, lightFirst=False):
    colors = [[] for i in range(256)]
    # darker image
    colors[0] = [0, 0, 0]
    colors[128] = [128, 128, 128]
    colors[255] = [192, 192, 192]
    image1 = graymap([x for x in image], width, height, colors)
    # lighter image
    colors[0] = [128, 128, 128]
    colors[128] = [192, 192, 192]
    colors[255] = [255, 255, 255]
    image2 = graymap([x for x in image], width, height, colors)
    if lightFirst:
        return checkerboardtile(image2, image1, width, height)
    else:
        return checkerboardtile(image1, image2, width, height)

# Input image uses only three colors: (0,0,0) or black,(128,128,128),(255,255,255) or white
# Turns the image into a black-and-white image, with middle gray dithered.
# Image has the same format returned by the blankimage() method with alpha=False.
def monochromeFromThreeGrays(image, width, height):
    image = [x for x in image]
    dithertograyimage(image, width, height, [0, 255])
    return image

# Input image uses only three colors: (0,0,0) or black,(128,128,128),(255,255,255) or white
# Default for palette is VGA palette (classiccolors())
# Image has the same format returned by the blankimage() method with alpha=False.
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
# to those in the specified palette.
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

def _writeu16(ff, x):  # big-endian write of 16-bit value
    ff.write(bytes([(x >> 8) & 0xFF, (x) & 0xFF]))

def _writeu32(ff, x):  # big-endian write of 32-bit value
    ff.write(bytes([(x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, (x) & 0xFF]))

def _writeu16le(ff, x):  # little-endian write of 16-bit value
    ff.write(bytes([(x) & 0xFF, (x >> 8) & 0xFF]))

def _writeu32le(ff, x):  # big-endian write of 32-bit value
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

def _colorname(colorhash, c):
    cname = "#%02x%02x%02x" % (c[0], c[1], c[2])
    if cname in colorhash:
        return colorhash[cname] + " " + cname
    return cname

def writepalette(f, palette, name=None, raiseIfExists=False, comment=None):
    if name and "\n" in name:
        raise ValueError
    if (not palette) or len(palette) > 512:
        raise ValueError
    colorhash = _setup_rgba_to_colorname_hash()
    # GIMP palette
    ff = open(f + ".gpl", "xb" if raiseIfExists else "wb")
    ff.write(bytes("GIMP Palette\n", "utf-8"))
    ff.write(
        bytes("Name: " + (name.replace("\n", " ").replace("#", "_")) + "\n", "utf-8")
    )
    ff.write(bytes("Columns: 8\n", "utf-8"))
    if comment:
        for c in comment:
            ff.write(
                bytes("# " + (c.replace("\n", " ").replace("#", "_")) + "\n", "utf-8")
            )
    for c in palette:
        col = [c[0] & 0xFF, c[1] & 0xFF, c[2] & 0xFF]
        ff.write(
            bytes(
                "%d %d %d %s\n" % (col[0], col[1], col[2], _colorname(colorhash, col)),
                "utf-8",
            )
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
        _writeutf16(ff, _colorname(colorhash, c))
    ff.close()
    # Adobe swatch exchange format
    ff = open(f + ".ase", "xb" if raiseIfExists else "wb")
    ff.write(bytes("ASEF", "utf-8"))
    _writeu16(ff, 1)
    _writeu16(ff, 0)
    _writeu32(ff, len(palette) + 1)
    inv255 = 1.0 / 255.0
    for i in range(len(palette)):
        c = palette[i]
        _writeu16(ff, 1)
        colorname = _colorname(colorhash, c)
        _writeu32(ff, _utf16len(colorname) + 18)
        _writeutf16(ff, colorname)
        ff.write(bytes("RGB ", "utf-8"))
        _writef32(ff, c[0] * inv255)
        _writef32(ff, c[1] * inv255)
        _writef32(ff, c[2] * inv255)
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
    reco = (
        [[x * 255 // 85, x * 255 // 85, x * 255 // 85] for x in range(86)]
        + [[x * 255 // 85, 0, 0] for x in range(1, 85)]
        + [[255, x * 255 // 85, x * 255 // 85] for x in range(85)]
    )
    for c in reco:
        if c[0] == 129:
            c[0] = 128
        if c[1] == 129:
            c[1] = 128
        if c[2] == 129:
            c[2] = 128
    writepalette(
        "palettes/recolor",
        reco,
        "Recolorable Palette",
        comment=[
            "NOTE: Designed for recoloring using the recolor() and recolordither()",
            "methods in the `desktopwallpaper` Python module.",
        ],
    )
    writepalette("palettes/256gray", [[x, x, x] for x in range(256)], "256 Grays")
    writepalette(
        "palettes/cga-canonical", cgacolors(), "Canonical 16-Color CGA Palette"
    )
    writepalette(
        "palettes/cga-with-halfmixtures",
        paletteandhalfhalf(cgacolors()),
        "Canonical CGA Palette with Half-and-Half Mixtures",
        comment=[
            "NOTE: Images drawn with this palette should",
            'be in solid colors only; "manual" dithering patterns',
            "to simulate off-palette colors should be avoided.",
            "The `desktopwallpaper` Python module contains the method",
            "`dw.halfhalfditherimage(image,width,height,dw.cgacolors())`",
            "to dither images using this palette.",
        ],
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
        comment=[
            "NOTE: Images drawn with this palette should",
            'be in solid colors only; "manual" dithering patterns',
            "to simulate off-palette colors should be avoided.",
            "The `desktopwallpaper` Python module contains the method",
            "`dw.halfhalfditherimage(image,width,height,dw.classiccolors())`",
            "to dither images using this palette.",
        ],
    )

    ##### Tests

    # Test threedee
    img2 = blankimage(3, 3, [192, 192, 192])
    mask = blankimage(3, 3, [0, 0, 0])  # black mask
    helper = ImageDrawHelper(img2, 3, 3)
    threedee(
        helper,
        0,
        0,
        mask,
        3,
        3,
        [[[255, 255, 255], [128, 128, 128]]],
        traceInnerCorners=True,
    )
    expected = [
        255,
        255,
        255,
        255,
        255,
        255,
        128,
        128,
        128,
        255,
        255,
        255,
        192,
        192,
        192,
        128,
        128,
        128,
        128,
        128,
        128,
        128,
        128,
        128,
        128,
        128,
        128,
    ]
    if img2 != expected:
        print("unexpected output of threedee")
        print(img2)
    img2 = blankimage(3, 3, [192, 192, 192])
    helper = ImageDrawHelper(img2, 3, 3)
    threedee(
        helper,
        0,
        0,
        mask,
        3,
        3,
        [[[255, 255, 255], [128, 128, 128]]],
        traceInnerCorners=True,
    )
    if img2 != expected:
        print("unexpected output of threedee")
        print(img2)
