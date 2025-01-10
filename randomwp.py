# Methods that generate random tileable wallpaper images.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under the Unlicense: https://unlicense.org/

import random
import desktopwallpaper as dw

def scatteredIconAnimationOverlay(icons, bgwidth, bgheight, framecount=40):
    if (not icons) or bgwidth <= 0 or bgheight <= 0 or framecount <= 0:
        raise ValueError
    exposures = []
    for i in range(len(icons)):
        expo = 1 + random.randint(framecount // 4, framecount * 3 // 4)
        firstframe = random.randint(0, framecount - 1)
        x0 = random.randint(0, bgwidth - 1)
        y0 = random.randint(0, bgheight - 1)
        exposures.append([firstframe, expo, x0, y0])
    bg = dw.blankimage(bgwidth, bgheight, [0, 0, 0, 0], alpha=True)
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
                dw.imagecomposite(
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
                    alpha=True,
                    wraparound=True,
                    sourceAlpha=iconalpha,
                    screendoor=False,
                )
        animation.append(bgi)
    return animation

def scatteredIconAnimation(
    icons, bgImage, bgwidth, bgheight, framecount=40, palette=None
):
    anim = scatteredIconAnimationOverlay(
        icons, bgwidth, bgheight, framecount=framecount
    )
    bg = dw.toalpha(bgImage, bgwidth, bgheight)
    for i in range(len(anim)):
        dw.imagecomposite(
            anim[i],
            bgwidth,
            bgheight,
            0,
            0,
            bgwidth,
            bgheight,
            bg,
            bgwidth,
            bgheight,
            0,
            0,
            porterDuffOp=4,  # destination copy
            alpha=True,
        )
        anim[i] = dw.noalpha(anim[i], bgwidth, bgheight)
        if palette:
            dw.patternDither(anim[i], bgwidth, bgheight, palette, alpha=False)
    return anim

def randomdiamondtileoverlay(imgwidth, imgheight, icon, iconwidth, iconheight):
    iconpos1 = [0, 0]
    iconpos2 = [0, 0]
    match random.randint(0, 5):
        case 0 | 1:
            iconpos1 = [imgwidth // 2, imgheight // 2]
            iconpos2 = [imgwidth, 0]
        case 2:
            iconpos1 = [imgwidth // 3, imgheight // 2]
            iconpos2 = [imgwidth * 2 // 3, 0]
        case 3:
            iconpos1 = [imgwidth * 2 // 3, imgheight // 2]
            iconpos2 = [imgwidth // 3, 0]
        case 4:
            iconpos1 = [imgwidth // 2, imgheight // 3]
            iconpos2 = [0, imgheight * 2 // 3]
        case 5:
            iconpos1 = [imgwidth // 2, imgheight * 2 // 3]
            iconpos2 = [0, imgheight // 3]
    iconpos1[0] -= iconwidth // 2
    iconpos2[0] -= iconwidth // 2
    iconpos1[1] -= iconheight // 2
    iconpos2[1] -= iconheight // 2
    return _diamondtileoverlay(
        imgwidth,
        imgheight,
        icon,
        iconwidth,
        iconheight,
        iconpos1=iconpos1,
        iconpos2=iconpos2,
    )

def _diamondtileoverlay(
    imgwidth, imgheight, icon, iconwidth, iconheight, iconpos1, iconpos2
):
    bg = dw.blankimage(imgwidth, imgheight, [0, 0, 0, 0], alpha=True)
    dw.imagecomposite(
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
        alpha=True,
    )
    dw.imagecomposite(
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
        alpha=True,
    )
    return [bg, imgwidth, imgheight]

def randomwallpaper(palette=None):
    match random.randint(0, 2):
        case 0:
            return randomwallpaper1(palette=palette)
        case 1:
            return randomwallpaper2(palette=palette)
        case _:
            return randomwallpaper3(palette=palette)

def _randomRotated(image, w, h):
    image2, w2, h2 = dw.randomRotated(image, w, h)
    if (w2 != w or h2 != h) and w2 * h2 >= (1920 * 1080 // 10):
        return (image, w, h)
    return (image2, w, h)

def randomwallpaper3(palette=None):
    w = random.randint(32, 192)
    w -= w % 8
    h = random.randint(32, 192)
    h -= h % 8
    image = dw.randombackgroundimage(w, h, palette)
    match random.randint(0, 4):
        case 0:
            image, w, h = dw.groupPmImage(image, w, h)
        case 1:
            image, w, h = dw.groupPgImage(image, w, h)
        case 2:
            image, w, h = dw.tileableImage(image, w, h)
        case _:
            pass
    image, w, h = _randomRotated(image, w, h)
    image = dw.randommaybemonochrome(image, w, h)
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
    image3, width, height = _randomRotated(image3, w * columns, h * rows)
    image3 = dw.randommaybemonochrome(image3, width, height)
    return [image3, width, height]

def randomwallpaper1(palette=None):
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
    image3, width, height = _randomRotated(image3, w * columns, h * rows)
    image3 = dw.randommaybemonochrome(image3, width, height)
    return [image3, width, height]
