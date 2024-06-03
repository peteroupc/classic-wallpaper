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

import shlex
import os
import math
import random

def _listdir(p):
  return [os.path.abspath(p+"/"+x) for x in os.listdir(p)]

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

def _ceil(x, y):
    return -(-x // y)

def cgacolors2():
    # colors in cgacolors() and their "half-and-half" versions
    colors = []
    cc = cgacolors()
    for c in cc:
        cij = [x for x in c]
        if cij not in colors:
            colors.append(cij)
    for i in range(len(cc)):
        for j in range(i + 1, len(cc)):
            ci = cc[i]
            cj = cc[j]
            cij = [a + _ceil(b - a, 2) for a, b in zip(ci, cj)]
            if cij not in colors:
                colors.append(cij)
    return colors

def classicdithercolors():
    colors = {}
    cc = classiccolors()
    for c in cc:
        cij = c[0] | (c[1] << 8) | (c[2] << 16)
        if cij not in colors:
            colors[cij] = [cij, cij]
    for i in range(len(cc)):
        for j in range(i + 1, len(cc)):
            ci = cc[i]
            cj = cc[j]
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

def classicditherimage(image, width, height):
    if width <= 0 or height <= 0:
        raise ValueError
    cdcolors = classicdithercolors()
    for y in range(height):
        yd = y * width
        for x in range(width):
            xp = yd + x
            col = image[xp * 3] | (image[xp * 3] << 8) | (image[xp * 3] << 16)
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
# 3. If basecolors is not nil, performs a dithering operation on the input image; that is, it
# reduces the number of colors of the image to those given in 'basecolors', which is a list
# of colors (each color is of the same format as rgb1 and rgb2),
# and scatters the remaining colors in the image so that they appear close to the original colors.
# Raises an error if 'basecolors' has a length greater than 256.
# 'abstractImage' indicates that the image to apply the filter to
# is abstract or geometric (as opposed to photographic).  Default is False.
def magickgradientditherfilter(
    rgb1=None, rgb2=None, basecolors=None, hue=0, abstractImage=False
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
    huemod = (hue + 180) * 100.0 / 180.0
    hueshift = "" if hue == 0 else ("-modulate 100,100,%.02f" % (huemod))
    mgradient = None
    if rgb1 != None and rgb2 != None:
        r1 = "#%02x%02x%02x" % (int(rgb1[0]), int(rgb1[1]), int(rgb1[2]))
        r2 = "#%02x%02x%02x" % (int(rgb2[0]), int(rgb2[1]), int(rgb2[2]))
        mgradient = (
            "\\( +clone -grayscale Rec709Luma \\) \\( -size 1x256 gradient:%s-%s \\) -delete 0 -clut"
            % (r1, r2)
        )
    else:
        mgradient = ""
    if basecolors and len(basecolors) > 0:
        bases = ["xc:#%02X%02X%02X" % (k[0], k[1], k[2]) for k in basecolors]
        # ImageMagick command to generate the palette image
        image = "-size 1x1 " + (" ".join(bases)) + " +append -write mpr:z +delete"
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
        ditherkind = (
            "-ordered-dither 8x8,%d" % (min(2, _isqrtceil(len(basecolors)) - 1))
            if abstractImage
            else "-dither FloydSteinberg"
        )
        return "%s %s \\( %s \\) %s -remap mpr:z" % (
            mgradient,
            hueshift,
            image,
            ditherkind,
        )
    else:
        return "%s %s" % (mgradient, hueshift)

def solid(bg=[192, 192, 192], w=64, h=64):
    if bg == None or len(bg) < 3:
        raise ValueError
    bc = "#%02x%02x%02x" % (int(bg[0]), int(bg[1]), int(bg[2]))
    return "-size %dx%d xc:%s" % (w, h, bg)

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
        "-grayscale Rec709Luma -channel RGB -threshold 50%% -write mpr:z "
        + '\\( -clone 0 -morphology Convolve "3:0,0,0 0,0,0 0,0,1" -write mpr:z1 \\) '
        + '\\( -clone 0 -morphology Convolve "3:1,0,0 0,0,0 0,0,0" -write mpr:z2 \\) -delete 0 '
        + "-compose Multiply -composite "
        + "\\( mpr:z1 mpr:z2 -compose Screen -composite -negate \\) -compose Plus -composite "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a1 -delete 0 "
        + 'mpr:z1 \\( mpr:z -negate -morphology Convolve "3:1,0,0 0,0,0 0,0,0" \\) -compose Multiply -composite '
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a2 -delete 0 "
        + '\\( mpr:z -negate -morphology Convolve "3:0,0,0 0,0,0 0,0,1" \\) mpr:z2 -compose Multiply -composite '
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut mpr:a2 -compose Plus -composite mpr:a1 -compose Plus -composite"
    ) % (bc, hc, sc)

def emboss():
    # Emboss a two-color black and white image into a 3-color (black/gray/white) image
    return (
        "\\( +clone \\( +clone \\) -append \\( +clone \\) +append -crop 50%x50%+1+1 \\( "
        + "-size 1x2 gradient:#FFFFFF-#808080 \\) -clut \\) -compose Multiply -composite"
    )

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
        "-grayscale Rec709Luma -channel RGB -threshold 50%% -write mpr:z "
        + '\\( -clone 0 -morphology Convolve "3:0,0,0 0,0,0 0,0,1" -write mpr:z1 \\) '
        + '\\( -clone 0 -morphology Convolve "3:1,0,0 0,0,0 0,0,0" -write mpr:z2 \\) -delete 0--1 '
        + "mpr:z2 \\( mpr:z -negate \\) -compose Multiply -composite -write mpr:a10 "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a2 -delete 0 "
        + "\\( mpr:z -negate \\) mpr:z1 -compose Multiply -composite -write mpr:a20 "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut -write mpr:a1 -delete 0 "
        + "mpr:a10 mpr:a20 -compose Plus -composite -negate "
        + "\\( -size 1x1 xc:black xc:%s +append \\) -clut mpr:a2 -compose Plus -composite "
        + "mpr:a1 -compose Plus -composite"
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

def tileable():
    # ImageMagick command to generate a Pmm wallpaper group tiling pattern.
    # This command can be applied to arbitrary images to render them
    # tileable.
    # NOTE: "-append" is a vertical append; "+append" is a horizontal append;
    # "-flip" reverses the row order; "-flop" reverses the column order.
    return "\\( +clone -flip \\) -append \\( +clone -flop \\) +append"

def groupP2():
    # ImageMagick command to generate a P2 wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last row's first half is a mirror of its second half.
    return "\\( +clone -flip -flop \\) -append"

def groupPm():
    # ImageMagick command to generate a Pm wallpaper group tiling pattern.
    return "\\( +clone -flop \\) +append"

def groupPg():
    # ImageMagick command to generate a Pg wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last column's first half is a mirror of its second half.
    return "\\( +clone -flip \\) -append"

def groupPgg():
    # ImageMagick command to generate a Pgg wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last row's and last column's first half is a mirror of its
    # second half.
    return (
        "-write mpr:wpgroup -delete 0 "
        + "\\( mpr:wpgroup \\( mpr:wpgroup -flip -flop \\) +append \\) "
        + "\\( \\( mpr:wpgroup -flip -flop \\) mpr:wpgroup +append \\) "
        + "-append"
    )

def groupCmm():
    # ImageMagick command to generate a Cmm wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last row's and last column's first half is a mirror of its
    # second half.
    return (
        "\\( +clone -flip \\) -append -write mpr:wpgroup -delete 0 "
        + "\\( mpr:wpgroup \\( mpr:wpgroup -flop \\) +append \\) "
        + "\\( \\( mpr:wpgroup -flop \\) mpr:wpgroup +append \\) "
        + "-append"
    )

def diamondTiling(bgcolor):
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
        bc += " xc:#%02x%02x%02x \\) -compose DstOver -composite" % (
            int(bg[0]),
            int(bg[1]),
            int(bg[2]),
        )
    return (
        "\\( +clone \\( +clone \\) -append \\( +clone \\) +append -chop "
        + "25%x25% \\) -compose Over -composite"
        + bc
    )

def groupPmg():
    # ImageMagick command to generate a Pmg wallpaper group tiling pattern.
    # For best results, the command should be applied to images whose
    # last column's first half is a mirror of its
    # second half.
    return (
        "-write mpr:wpgroup -delete 0 "
        + "\\( mpr:wpgroup \\( mpr:wpgroup -flip -flop \\) +append \\) "
        + "\\( \\( mpr:wpgroup -flip \\) \\( mpr:wpgroup -flop \\) +append \\) "
        + "-append"
    )

def writeppm(f, image, width, height):
    fd = open(f, "x+b")
    fd.write(bytes("P6\n%d %d\n255\n" % (width, height), "utf-8"))
    fd.write(bytes(image))
    fd.close()

def horizhatch(hatchspace=8):
    # Generate a portable pixelmap (PPM) of a horizontal hatch pattern.
    if hatchspace <= 0:
        raise ValueError
    size = hatchspace * 4
    image=[]
    for y in range(size):
        b = 0 if y % hatchspace == 0 else 255
        image.append([b for i in range(size * 3)])
    return [px for row in image for px in row]

def borderedbox(image, width, height, border, color1, color2, x0, y0, x1, y1):
    # Draw a wraparound dither-colored box on an image.
    # 'border' is the border color, and 'color1' and 'color2' are the dithered
    # versions of the inner color.  'border' can be None; 'color1' and 'color2'
    # can't be.
    if x0 < 0 or y0 < 0 or x1 < x0 or y1 < y0:
        raise ValueError
    if width <= 0 or height <= 0:
        raise ValueError
    if (not color1) or (not image) or (not color2):
        raise ValueError
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

def randomboxes(width, height, palette):
    # Generate a portable pixelmap (PPM) of a tileable pattern with random boxes,
    # using only the colors in the given palette
    if width <= 0 or int(width) != width:
        raise ValueError
    if height <= 0 or int(height) != height:
        raise ValueError
    image = [255 for i in range(width * height * 3)]
    borderedbox(
        image, width, height, palette[0], palette[0], palette[0], 0, 0, width, height
    )
    for i in range(45):
        x0 = random.randint(0, width - 1)
        x1 = x0 + random.randint(3, max(3, width * 3 // 4))
        y0 = random.randint(0, height - 1)
        y1 = y0 + random.randint(3, max(3, height * 3 // 4))
        border = (
            palette[random.randint(0, len(palette) - 1)]
            if random.randint(0, 5) == 0
            else palette[0]
        )
        color1 = palette[random.randint(0, len(palette) - 1)]
        color2 = palette[random.randint(0, len(palette) - 1)]
        borderedbox(image, width, height, border, color1, color2, x0, y0, x1, y1)
    return image

def crosshatch(hhatchspace=8, vhatchspace=8):
    # Generate a portable pixelmap (PPM) of a horizontal and vertical hatch pattern.
    if hhatchspace <= 0:
        raise ValueError
    if vhatchspace <= 0:
        raise ValueError
    width = vhatchspace * 4
    height = hhatchspace * 4
    image=[]
    for y in range(height * 4):
        if y % hhatchspace == 0:
            image.append([0 for i in range(width * 3)])
        else:
            image.append(
                    [
                        0 if (i // 3) % vhatchspace == 0 else 255
                        for i in range(width * 3)
                    ]
            )
    return [px for row in image for px in row]

def verthatch(hatchspace=8):
    # Generate a portable pixelmap (PPM) of a vertical hatch pattern.
    if hatchspace <= 0 or int(hatchspace) != hatchspace:
        raise ValueError
    rowbyte=[0 if (i // 3) % hatchspace == 0 else 255 for i in range(size * 3)]
    im=[rowbyte for i in range(size)]
    return [px for row in image for px in row]

def diagstripe(wpsize=64, stripesize=32, reverse=False):
    # Generate a portable pixelmap (PPM) of a diagonal stripe pattern
    if stripesize > wpsize:
        raise ValueError
    if wpsize <= 0 or int(wpsize) != wpsize:
        raise ValueError
    image = [255 for i in range(wpsize * wpsize * 3)]
    # Draw the stripe
    xpstart = -(stripesize // 2)
    for y in range(wpsize):
        yp = y * wpsize * 3
        for x in range(stripesize):
            xp = x + xpstart
            while xp < 0:
                xp += wpsize
            while xp >= wpsize:
                xp -= wpsize
            if reverse:
                xp = wpsize - 1 - xp
            image[yp + xp * 3] = 0
            image[yp + xp * 3 + 1] = 0
            image[yp + xp * 3 + 2] = 0
        xpstart += 1
    return image

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
            elif grays == 3:
                # Dither to three grays
                bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
                if r <= 128:
                    r = 128 if bdither < r * 64 // 128 else 0
                else:
                    r = 255 if bdither < (r - 128) * 64 // 127 else 128
            elif grays == 6:
                # Dither to the six grays in the "Web safe" palette
                bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
                rmod = r%51
                r = (r-rmod)+51 if bdither < r * 64 // 51 else (r-rmod)
            return r

def diaggradient(size=32, grays=255):
    # Generate a portable pixelmap (PPM) of a diagonal linear gradient
    if size <= 0 or int(size) != size:
        raise ValueError
    image=[]
    for y in range(size):
        row = [0 for i in range(size * 3)]
        for x in range(size):
            r = abs(x - (size - 1 - y)) * 255 // (size - 1)
            r = _dithergray(r,x,y,grays)
            row[x * 3] = r
            row[x * 3 + 1] = r
            row[x * 3 + 2] = r
        image.append(row)
    return [px for row in image for px in row]

def noiseppm(size=32):
    # Generate a portable pixelmap (PPM) of noise
    if width <= 0 or int(width) != width:
        raise ValueError
    if height <= 0 or int(height) != height:
        raise ValueError
    rarr = [0, 255, 192, 192, 192, 192, 192, 192, 128]
    image=[]
    for y in range(height):
        row = [0 for i in range(size * 3)]
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
    image=[]
    for y in range(height):
        row = [0 for i in range(size * 3)]
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
    return (
        '+clone +append -morphology Convolve "50x1+49+0:'
        + _join([1 / 50 for i in range(50)])
        + '" -crop 50%x0+0+0'
    )

# What follows are methods for generating scalable vector graphics (SVGs) of
# classic OS style borders and button controls.  Although the SVGs are scalable
# by definition, they are pixelated just as they would appear in classic OSs.
#
# NOTE: A more flexible approach for this kind of drawing
# is to prepare an SVG defining the frame of a user interface element
# with five different parts (in the form of 2D shapes): an "upper outer part", a
# "lower outer part", an "upper inner part", a "lower inner part", and a "middle part".
# Each of these five parts can be colored separately or filled with a pattern.

# helper for rectangle drawing
def _rect(x0, y0, x1, y1, c):
    if x0 >= x1 or y0 >= y1:
        return ""
    return "<path style='stroke:none;fill:%s' d='M%d %dL%d %dL%d %dL%d %dZ'/>" % (
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

# helper for edge drawing (top left edge "dominates")
# hilt = upper part of edge, dksh = lower part of edge
def _drawedgetopdom(x0, y0, x1, y1, hilt, dksh=None, edgesize=1):
    if x1 - x0 < edgesize * 2 or y1 - y0 < edgesize * 2:  # too narrow and short
        return _drawedgebotdom(x0, y0, x1, y1, hilt, dksh, edgesize)
    return (
        _rect(x0, y0, x0 + edgesize, y1, hilt)  # left edge
        + _rect(x0 + edgesize, y0, x1, y0 + edgesize, hilt)  # top edge
        + _rect(x1 - edgesize, y0 + edgesize, x1, y1, dksh)  # right edge
        + _rect(x0 + edgesize, y1 - edgesize, x1 - edgesize, y1, dksh)  # bottom edge
    )

def _drawface(x0, y0, x1, y1, face, edgesize=1):
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        return ""
    if x1 - x0 < edgesize * 2:  # too narrow
        return _rect(x0, y0 + edgesize, x1, y0 - edgesize, face)
    if y1 - y0 < edgesize * 2:  # too short
        return _rect(x0 + edgesize, y0, x1 - edgesize, y1, face)
    return _rect(x0 + edgesize, y0 + edgesize, x1 - edgesize, y1 - edgesize, face)

# helper for edge drawing (bottom right edge "dominates")
# hilt = upper part of edge, dksh = lower part of edge
def _drawedgebotdom(x0, y0, x1, y1, hilt, dksh=None, edgesize=1):
    if hilt and (dksh is None):
        dksh = hilt
    if dksh and (hilt is None):
        hilt = dksh
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        return _rect(x0, y0, x1, y1, dksh)
    if x1 - x0 < edgesize * 2:  # too narrow
        return (
            _rect(x0, y0, x1, y0 + edgesize, hilt)
            + _rect(x0, y0 + edgesize, x1, y0 - edgesize, hilt)
            + _rect(x0, y1 - edgesize, x1, y1, dksh)
        )
    if y1 - y0 < edgesize * 2:  # too short
        return (
            _rect(x0, y0, x0 + edgesize, y1, dksh)
            + _rect(x0 + edgesize, y0, x1 - edgesize, y1, hilt)
            + _rect(x1 - edgesize, y0, x1, y1, dksh)
        )
    return (
        _rect(x0, y0, x0 + edgesize, y1 - edgesize, hilt)  # left edge
        + _rect(x0 + edgesize, y0, x1 - edgesize, y0 + edgesize, hilt)  # top edge
        + _rect(x1 - edgesize, y0, x1, y1, dksh)  # right edge
        + _rect(x0, y1 - edgesize, x1 - edgesize, y1, dksh)  # bottom edge
    )

# hilt = upper part of edge, dksh = lower part of edge
def _drawroundedge(x0, y0, x1, y1, hilt, dksh=None, edgesize=1):
    if hilt and (dksh is None):
        dksh = hilt
    if dksh and (hilt is None):
        hilt = dksh
    if x1 - x0 < edgesize * 2 and y1 - y0 < edgesize * 2:  # too narrow and short
        return ""
    if x1 - x0 < edgesize * 2:  # too narrow
        return _rect(x0, y0 + edgesize, x1, y0 - edgesize, hilt)
    if y1 - y0 < edgesize * 2:  # too short
        return _rect(x0 + edgesize, y0, x1 - edgesize, y1, hilt)
    return (
        _rect(x0, y0 + edgesize, x0 + edgesize, y1 - edgesize, hilt)  # left edge
        + _rect(x0 + edgesize, y0, x1 - edgesize, y0 + edgesize, hilt)  # top edge
        + _rect(
            x1 - edgesize,
            y0 + edgesize,
            x1,
            y1 - edgesize,
            hilt if dksh is None else dksh,
        )  # right edge
        + _rect(
            x0 + edgesize,
            y1 - edgesize,
            x1 - edgesize,
            y1,
            hilt if dksh is None else dksh,
        )  # bottom edge
    )

def _drawinnerface(x0, y0, x1, y1, face):
    edgesize = 1
    return _drawface(
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        face,
        edgesize=edgesize,
    )

def drawindentborder(
    x0, y0, x1, y1, hilt, sh, frame, outerBorderSize=1, innerBorderSize=1
):
    if innerBorderSize < 0:
        raise ValueError
    ret = ""
    for i in range(outerBorderSize):
        ret += _drawedgebotdom(x0, y0, x1, y1, sh, hilt)
        x0 += 1
        y0 += 1
        x1 -= 1
        y1 -= 1
    ret += _drawedgebotdom(x0 + 1, y1 + 1, x1 - 1, y1 - 1, frame, frame)
    x0 += 1
    y0 += 1
    x1 -= 1
    y1 -= 1
    for i in range(innerBorderSize):
        ret += _drawedgebotdom(x0, y0, x1, y1, hilt, sh)
        x0 += 1
        y0 += 1
        x1 -= 1
        y1 -= 1
    return ret

# highlight color, light color, shadow color, dark shadow color
def drawraisedouter(x0, y0, x1, y1, hilt, lt, sh, dksh):
    return _drawedgebotdom(x0, y0, x1, y1, lt, dksh)

def drawraisedinner(x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    return _drawedgebotdom(
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        hilt,  # draw the "upper part" with this color
        sh,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

def drawsunkenouter(x0, y0, x1, y1, hilt, lt, sh, dksh):
    return _drawedgebotdom(x0, y0, x1, y1, sh, hilt)

def drawsunkeninner(x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    return _drawedgebotdom(
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        dksh,  # draw the "upper part" with this color
        lt,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

# button edges (also known as "soft" edges)
def drawraisedouterbutton(x0, y0, x1, y1, hilt, lt, sh, dksh):
    return _drawedgebotdom(x0, y0, x1, y1, hilt, dksh)

def drawraisedinnerbutton(x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    return _drawedgebotdom(
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        lt,  # draw the "upper part" with this color
        sh,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

def drawsunkenouterbutton(x0, y0, x1, y1, hilt, lt, sh, dksh):
    return _drawedgebotdom(x0, y0, x1, y1, dksh, hilt)

def drawsunkeninnerbutton(x0, y0, x1, y1, hilt, lt, sh, dksh):
    edgesize = 1
    return _drawedgebotdom(
        x0 + edgesize,
        y0 + edgesize,
        x1 - edgesize,
        y1 - edgesize,
        sh,  # draw the "upper part" with this color
        lt,  # draw the "lower part" with this color
        edgesize=edgesize,
    )

def monoborder(  # "Monochrome" flat border
    x0,
    y0,
    x1,
    y1,
    clientAreaColor,  # draw the inner and middle parts with this color
    windowFrameColor,  # draw the outer parts with this color
):
    return (
        drawraisedouter(  # upper and lower outer parts
            x0,
            y0,
            x1,
            y1,
            windowFrameColor,
            windowFrameColor,
            windowFrameColor,
            windowFrameColor,
        )
        + drawraisedinner(  # upper and lower inner parts
            x0,
            y0,
            x1,
            y1,
            clientAreaColor,
            clientAreaColor,
            clientAreaColor,
            clientAreaColor,
        )
        + _drawinnerface(  # middle
            x0,
            y0,
            x1,
            y1,
            clientAreaColor,
            clientAreaColor,
            clientAreaColor,
            clientAreaColor,
        )
    )

def flatborder(  # Flat border
    x0,
    y0,
    x1,
    y1,
    sh,  # draw the outer parts with this color
    buttonFace,  # draw the inner and middle parts with this color
):
    return (
        drawraisedouter(x0, y0, x1, y1, sh, sh, sh, sh)
        + drawraisedinner(
            x0, y0, x1, y1, buttonFace, buttonFace, buttonFace, buttonFace
        )
        + _drawinnerface(x0, y0, x1, y1, buttonFace, buttonFace, buttonFace, buttonFace)
    )

def windowborder(
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
    return (
        drawraisedouter(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + drawraisedinner(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + _drawinnerface(x0, y0, x1, y1, face)
    )

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
):
    face = face if face else lt
    return (
        drawraisedouterbutton(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + drawraisedinnerbutton(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + _drawinnerface(x0, y0, x1, y1, face)
    )

def buttondown(
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
    return (
        drawsunkenouterbutton(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + drawsunkeninnerbutton(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + _drawinnerface(x0, y0, x1, y1, face)
    )

def fieldbox(
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
    return (
        drawsunkenouter(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + drawsunkeninner(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + _drawinnerface(x0, y0, x1, y1, face)
    )

def wellborder(x0, y0, x1, y1, hilt, windowText):
    face = face if face else (lt if pressed else hilt)
    return (
        drawsunkenouter(x0, y0, x1, y1, hilt, hilt, hilt, hilt)
        + drawsunkeninner(
            x0, y0, x1, y1, windowText, windowText, windowText, windowText
        )
        + drawsunkenouter(
            x0 - 1,
            y0 - 1,
            x1 + 1,
            y1 + 1,
            windowText,
            windowText,
            windowText,
            windowText,
        )
    )

def groupingbox(
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
    return (
        drawsunkenouter(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + drawraisedinner(x0, y0, x1, y1, hilt, lt, sh, dksh)
        + _drawinnerface(x0, y0, x1, y1, face)
    )

def statusfieldbox(
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
    return drawsunkenouter(x0, y0, x1, y1, hilt, lt, sh, dksh) + _drawinnerface(
        x0, y0, x1, y1, face
    )

def _drawrsedge(x0, y0, x1, y1, lt, sh, squareedge=False):
    if squareedge:
        return _drawedgebotdom(x0, y0, x1, y1, lt, sh)
    else:
        return _drawroundedge(x0, y0, x1, y1, lt, sh)

def _dither(face, hilt, hiltIsScrollbarColor=False):
    if hiltIsScrollbarColor:
        return _rect(0, 0, 2, 2, hilt)
    # if 256 or more colors and hilt is not white:
    #    return _rect(0, 0, 2, 2, mix(face, hilt))
    return (
        _rect(0, 0, 1, 1, hilt)
        + _rect(1, 1, 2, 2, hilt)
        + _rect(0, 1, 1, 2, face)
        + _rect(1, 0, 2, 1, face)
    )

# Generate SVG code for an 8x8 monochrome pattern.
# 'idstr' is a string identifying the pattern in SVG.
# 'pattern' is an 8-item array with integers in the interval [0,255].
# The first integer represents the first row, the second, the second row, etc.
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
# the top left corner of the image.
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
    for y in range(8):
        for x in range(8):
            c = (
                bw[(pattern[y] >> (7 - x)) & 1]
                if msbfirst
                else bw[(pattern[y] >> x) & 1]
            )
            if c is None:
                continue
            ret += _rect(x, y, x + 1, y + 1, c)
    return ret + "</pattern>"

def _ditherbg(idstr, face, hilt, hiltIsScrollbarColor=False):
    if hiltIsScrollbarColor:
        return hilt
    if "'" in idstr:
        raise ValueError
    if '"' in idstr:
        raise ValueError
    return (
        "<pattern patternUnits='userSpaceOnUse' id='"
        + idstr
        + "' width='2' height='2' patternTransform='translate(1 1)'>"
        + _dither(face, hilt, hiltIsScrollbarColor)
        + "</pattern>"
    )

def drawbutton(
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
    squareedge=True,
    isDefault=False,  # whether the button is a default button
):
    if lt == None:
        lt = btn
    if dksh == None:
        dksh = sh
    if isDefault:
        return (
            _drawedgebotdom(x0, y0, x1, y1, frame, frame)
            + _drawedgebotdom(x0 + 1, y0 + 1, x1 - 1, y1 - 1, sh, sh)
            + _drawinnerface(x0 + 2, y0 + 2, x1 - 2, y1 - 2, btn)
        )
    else:
        edge = 1 if isDefault else 0
        return buttondown(
            x0 + edge, y0 + edge, x1 - edge, y1 - edge, hilt, lt, sh, dksh, btn
        )

def drawbuttonpush(
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
    squareedge=True,
    isDefault=False,  # whether the button is a default button
):
    if lt == None:
        lt = btn
    if dksh == None:
        dksh = sh
    # If isDefault is True, no frame is drawn and no room is left for the frame
    edge = 1 if isDefault else 0
    return buttonup(
        x0 + edge, y0 + edge, x1 - edge, y1 - edge, hilt, lt, sh, dksh, btn
    ) + ("" if not isDefault else _drawrsedge(x0, y0, x1, y1, frame, frame, squareedge))

# Draws a pressed button in 16-bit style
def draw16buttonpush(
    x0,
    y0,
    x1,
    y1,
    lt,
    sh,
    btn,  # button face color
    frame=None,  # optional frame color
    squareframe=False,
    isDefault=False,  # whether the button is a default button
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    return (
        _drawedgetopdom(x0 + edge, y0 + edge, x1 - edge, y1 - edge, sh, btn)
        + _rect(x0 + edge + 1, y0 + edge + 1, x1 - edge - 1, y1 - edge - 1, btn)
        + (
            ""
            if frame is None
            else _drawrsedge(x0, y0, x1, y1, frame, frame, squareframe)
            + (
                _drawedgebotdom(x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)
                if isDefault
                else ""
            )
        )
    )

# Draws a button in 16-bit style
def draw16button(
    x0,
    y0,
    x1,
    y1,
    lt,
    sh,
    btn,  # button face color
    frame=None,  # optional frame color
    squareframe=False,
    isDefault=False,
):
    # Leave 1-pixel room for the frame even if 'frame' is None
    edge = 2 if isDefault else 1
    return (
        _drawedgebotdom(x0 + edge, y0 + edge, x1 - edge, y1 - edge, lt, sh)
        + _drawedgebotdom(
            x0 + edge + 1, y0 + edge + 1, x1 - edge - 1, y1 - edge - 1, lt, sh
        )
        + _rect(x0 + edge + 2, y0 + edge + 2, x1 - edge - 2, y1 - edge - 2, btn)
        + (
            ""
            if frame is None
            else _drawrsedge(x0, y0, x1, y1, frame, frame, squareframe)
            + (
                _drawedgebotdom(x0 + 1, y0 + 1, x1 - 1, y1 - 1, frame, frame)
                if isDefault
                else ""
            )
        )
    )

def makesvg():
    width = 100
    height = 100
    hilt = "white"
    lt = "rgb(192,192,192)"
    sh = "rgb(128,128,128)"
    dksh = "black"
    face = "rgb(192,192,192)"
    frame = "black"
    return (
        (
            "<svg width='%dpx' height='%dpx' viewBox='0 0 %d %d'"
            % (width, height, width, height)
        )
        + " xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>"
        + "</svg>"
    )

def _bayerdither(a, b, t, x, y):
    # 't' is such that 0<=t<=1; closer to 1 means closer to 'b';
    # closer to 0 means closer to 'a'.
    # 'x' and 'y' are a pixel position.
    bdither = DitherMatrix[(y & 7) * 8 + (x & 7)]
    if bdither < t * 64:
        return b
    else:
        return a
