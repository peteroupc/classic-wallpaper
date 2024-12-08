# Methods that generate random tileable wallpaper images.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under the Unlicense: https://unlicense.org/

import random
import desktopwallpaper as dw

def scatteredIconAnimation(icons, bgwidth, bgheight, framecount=40, palette=None):
    if (not icons) or bgwidth <= 0 or bgheight <= 0 or framecount <= 0:
        raise ValueError
    exposures = []
    for i in range(len(icons)):
        expo = 1 + random.randint(framecount * 1 // 4, framecount * 3 // 4)
        firstframe = random.randint(0, framecount - 1)
        x0 = random.randint(0, bgwidth - 1)
        y0 = random.randint(0, bgheight - 1)
        exposures.append([firstframe, expo, x0, y0])
    if not palette:
        palette = dw.classiccolors()
    bg = dw.randombackgroundimage(bgwidth, bgheight, palette, tileable=False)
    animation = []
    for i in range(framecount):
        bgi = [x for x in bg]
        for j in range(len(icons)):
            firstframe = exposures[j][0]
            endexpo = exposures[j][1] + firstframe
            iconalpha = 255
            visible = False
            fadeframes = 3
            # Fade the icon in at the beginning and out at the end,
            # if there are multiple frames to draw
            if i >= firstframe and i < endexpo:
                visible = True
                if framecount > 1 and i - firstframe < fadeframes:
                    iconalpha = ((i - firstframe) + 1) * 255 // fadeframes
                elif framecount > 1 and endexpo - i < fadeframes:
                    iconalpha = ((endexpo - i) + 1) * 255 // fadeframes
            elif endexpo > framecount and i < endexpo % framecount:
                visible = True
                ee = endexpo % framecount
                if framecount > 1 and ee - i < fadeframes:
                    iconalpha = (ee - i) * 255 // fadeframes
            if visible:
                # icon is visible
                x0 = exposures[j][2]
                y0 = exposures[j][3]
                x1 = x0 + icons[j][1]
                y1 = y0 + icons[j][2]
                dw.imagesrcover(
                    bgi,
                    bgwidth,
                    bgheight,
                    x0,
                    y0,
                    x1,
                    y1,
                    icons[j][0],
                    icons[j][1],
                    icons[j][2],
                    0,
                    0,
                    wraparound=True,
                    sourceAlpha=iconalpha,
                    screendoor=False,
                )
        dw.patternDither(bgi, bgwidth, bgheight, palette)
        animation.append(bgi)
    return animation

def randomdiamondtile(icon, iconwidth, iconheight, palette=None):
    padding = random.randint(0, iconwidth)
    imgwidth = 0
    imgheight = 0
    iconpos1 = []
    iconpos2 = []
    match random.randint(0, 2):
        case 0:
            imgwidth = (iconwidth + padding) * 2
            imgheight = (iconwidth + padding) * 2
            iconpos1 = [(imgwidth - iconwidth) // 2, (imgheight - iconheight) // 2]
            iconpos2 = [imgwidth - (iconwidth) // 2, imgheight - (iconheight) // 2]
        case 1:
            imgwidth = (iconwidth + padding) * 2
            imgheight = iconwidth + padding
            iconpos1 = [padding // 2, padding // 2]
            iconpos2 = [imgwidth // 2 + padding // 2, imgheight // 2 + padding // 2]
        case 2:
            imgwidth = iconwidth + padding
            imgheight = (iconwidth + padding) * 2
            iconpos1 = [padding // 2, padding // 2]
            iconpos2 = [imgwidth // 2 + padding // 2, imgheight // 2 + padding // 2]
    # Generate a random background for the icon tiling
    bg = dw.randombackgroundimage(imgwidth, imgheight, palette)
    dw.imagesrcover(
        bg,
        imgwidth,
        imgheight,
        iconpos1[0],
        iconpos1[1],
        iconpos1[0] + iconwidth,
        iconpos1[1] + iconheight,
        icon,
        iconwidth,
        iconheight,
        0,
        0,
        wraparound=True,
    )
    dw.imagesrcover(
        bg,
        imgwidth,
        imgheight,
        iconpos2[0],
        iconpos2[1],
        iconpos2[0] + iconwidth,
        iconpos2[1] + iconheight,
        icon,
        iconwidth,
        iconheight,
        0,
        0,
        wraparound=True,
    )
    return [bg, imgwidth, imgheight]

def randomwallpaper3(palette=None):
    w = random.randint(32, 192)
    w -= w % 8
    h = random.randint(32, 192)
    h -= h % 8
    image = dw.randombackgroundimage(w, h, palette)
    image, w, h = dw.randomRotated(image, w, h)
    image = dw.randommaybemonochrome(image, w, h)
    match random.randint(0, 4):
        case 0:
            image, w, h = dw.groupPmImage(image, w, h)
        case 1:
            image, w, h = dw.groupPgImage(image, w, h)
        case 2:
            image, w, h = dw.tileableImage(image, w, h)
        case _:
            pass
    return [image, w, h]

def randomwallpaper2(palette=None):
    w = random.randint(32, 128)
    h = random.randint(32, 128)
    w -= w % 8
    h -= h % 8
    # shape background, which need not be tileable
    imagebg = dw.randombackgroundimage(w, h, palette, tileable=False)
    # combinations
    columns = 2
    rows = 2
    ia = dw.argyle(
        dw.randombackgroundimage(w, h, palette, tileable=False),
        imagebg,
        w,
        h,
        expo=random.choice([1, 2]),
        shiftImageBg=True,
    )
    ib = dw.argyle(
        dw.randombackgroundimage(w, h, palette, tileable=False),
        imagebg,
        w,
        h,
        expo=random.choice([1, 2]),
        shiftImageBg=True,
    )
    image3 = dw.checkerboardtile(ia, ib, w, h, columns, rows)
    image3, width, height = dw.randomRotated(image3, w * columns, h * rows)
    image3 = dw.randommaybemonochrome(image3, width, height)
    return [image3, width, height]

def randomwallpaper(palette=None):
    w = random.randint(96, 256)
    h = random.randint(96, 256)
    columns = random.choice([1, 1, 1, 2, 3, 4, 5])
    rows = random.choice([1, 1, 1, 2, 3, 4, 5])
    w = w // columns
    h = h // rows
    w = max(32, w - w % 8)
    h = max(32, h - h % 8)
    # shape background, which need not be tileable
    imagebg = dw.randombackgroundimage(w, h, palette, tileable=False)
    # shape foregrounds, which need not be tileable
    image1 = dw.randombackgroundimage(w, h, palette, tileable=False)
    image1a = dw.randombackgroundimage(w, h, palette, tileable=False)
    image1b = dw.randombackgroundimage(w, h, palette, tileable=False)
    # combinations
    image3 = dw.argyle(
        image1, imagebg, w, h, expo=random.choice([1, 2]), shiftImageBg=True
    )
    image3a = dw.argyle(
        image1a,
        imagebg,
        w,
        h,
        expo=random.choice([1, 2]),
        shiftImageBg=True,
    )
    image3b = dw.argyle(
        image1b,
        imagebg,
        w,
        h,
        expo=random.choice([1, 2]),
        shiftImageBg=True,
    )
    # tiling
    image3 = dw.randomtiles(columns, rows, [image3, image3a, image3b], w, h)
    image3, width, height = dw.randomRotated(image3, w * columns, h * rows)
    image3 = dw.randommaybemonochrome(image3, width, height)
    return [image3, width, height]
