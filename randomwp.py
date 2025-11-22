# Methods that generate random tileable wallpaper images.
#
# This script is released to the public domain; in case that is not possible, the
# file is also licensed under the Unlicense: https://unlicense.org/

import random
import math
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

def _drawmask1(img, mask, w, h, palette=None):
    # Draw dark version of image where mask is black, and light version elsewhere,
    # or vice versa.
    offx = random.randint(0, w - 1)
    offy = random.randint(0, h - 1)
    dk = [v * 65 // 100 for v in img]
    lt = [v + (255 - v) * 35 // 100 for v in img]
    if random.randint(0, 1) == 0:
        t = dk
        dk = lt
        lt = t  # swap dk and lt
    # Draw dk on lt where mask is "black"
    dw.imageblitex(
        # destination
        lt,
        w,
        h,
        offx,
        offy,
        w + offx,
        h + offy,
        # source
        mask,
        w,
        h,
        0,
        0,
        # pattern
        dk,
        w,
        h,
        0,
        0,
        ropForeground=0xB8,
        wraparound=True,
    )
    # copy to image
    dw.imageblitex(img, w, h, 0, 0, w, h, lt, w, h)
    if palette:
        dw.patternDither(img, w, h, palette)

def _drawmask2(img, mask, w, h, palette=None):
    # draw color on the image, where mask is black, along
    # with a drop shadow.
    colors = [[0, 0, 0], [128, 128, 128], [192, 192, 192], [255, 255, 255]]
    usedefaults = (not palette) or (
        colors[0] in palette
        and colors[1] in palette
        and colors[2] in palette
        and colors[3] in palette
    )
    if usedefaults and random.randint(0, 1) == 0:
        colors.reverse()
    colors2 = colors
    if random.randint(0, 99) < 50 or (not usedefaults):
        colors = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            (
                random.choose(palette)
                if palette
                else [random.randint(0, 255) for i in range(3)]
            ),
        ]
        colors2 = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            (
                random.choose(palette)
                if palette
                else [random.randint(0, 255) for i in range(3)]
            ),
        ]
    offx = random.randint(0, w - 1)
    offy = random.randint(0, h - 1)
    for i in range(len(colors)):
        dw.drawgradientmask(
            img,
            w,
            h,
            offx + len(colors) - 1 - i,
            offy + len(colors2) - 1 - i,
            mask,
            w,
            h,
            colors[i],
            colors2[i],
            paintAtZero=True,
            wraparound=True,
        )
    if palette:
        dw.patternDither(img, w, h, palette)

def randomdrawmask(img, mask, w, h, palette=None):
    match random.randint(0, 1):
        case 0:
            _drawmask1(img, mask, w, h, palette=palette)
        case 1:
            _drawmask2(img, mask, w, h, palette=palette)
        case _:
            raise ValueError

def randomwallpaper(palette=None):
    match random.randint(0, 2):
        case 0:
            return randomwallpaper1(palette=palette)
        case 1:
            return randomwallpaper2(palette=palette)
        case _:
            return randomwallpaper3(palette=palette)

# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def _waverotaterows(image, width, height, wavesize, wavecount=1, alpha=False):
    if wavecount == 0:
        raise ValueError
    for i in range(height):
        p = math.sin((i / height) * wavecount * math.pi * 2)
        dw.imagerotaterow(
            image, width, height, i, int((0.5 * wavesize) * p + 0.5), alpha=alpha
        )
    return image

# Image has the same format returned by the blankimage() method with the
# specified value of 'alpha' (default value for 'alpha' is False).
def _waverotatecolumns(image, width, height, wavesize, wavecount=1, alpha=False):
    if wavecount == 0:
        raise ValueError
    for i in range(width):
        p = math.sin((i / width) * wavecount * math.pi * 2)
        dw.imagerotatecolumn(
            image, width, height, i, int((0.5 * wavesize) * p + 0.5), alpha=alpha
        )
    return image

def _randomTransformed(image, w, h):
    if random.randint(0, 99) < 5 and w > 4 and h > 4:
        image = _waverotatecolumns(
            image,
            w,
            h,
            wavesize=random.randint(h // 8, h // 3),
            wavecount=random.randint(1, 3),
        )
    if random.randint(0, 99) < 5 and w > 4 and h > 4:
        image = _waverotaterows(
            image,
            w,
            h,
            wavesize=random.randint(h // 8, h // 3),
            wavecount=random.randint(1, 3),
        )
    image2, w2, h2 = dw.randomRotated(image, w, h)
    if (w2 != w or h2 != h) and w2 * h2 >= (1920 * 1080 // 10):
        return (image, w, h)
    return (image2, w2, h2)

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
    image, w, h = _randomTransformed(image, w, h)
    image = dw.randommaybemonochrome(image, w, h)
    if random.randint(0, 9) == 0:
        dw.randombordertile(image, w, h)
    return [image, w, h]

def randomwallpaper2(palette=None):
    return _randomwallpaper1ex(palette=palette, variant=2)

def _argylemask(width, height, expo):
    img = dw.blankimage(width, height, [0, 0, 0], alpha=False)
    helper = dw.ImageDrawHelper(img, width, height, alpha=False)
    dw.helperellipsefill(helper, [255, 255, 255], 0, 0, width, height, expo=expo)
    return img

def _shiftImage(image, width, height):
    dw.imageblitex(
        image,
        width,
        height,
        width // 2,
        height // 2,
        width + width // 2,
        height + height // 2,
        image,
        width,
        height,
        0,
        0,
        wraparound=True,
        alpha=False,
    )

def randomwallpaper1(palette=None):
    return _randomwallpaper1ex(palette=palette, variant=1)

def _randomwallpaper1ex(palette=None, variant=1):
    w = random.randint(96, 256)
    h = random.randint(96, 256)
    columns = 2 if variant == 2 else random.choice([1, 1, 1, 2, 3, 4, 5])
    rows = 2 if variant == 2 else random.choice([1, 1, 1, 2, 3, 4, 5])
    w = w // columns
    h = h // rows
    w = max(32, w - w % 8)
    h = max(32, h - h % 8)
    # shape foregrounds, which need not be tileable
    image1 = dw.randombackgroundimage(w, h, palette, tileable=False)
    image1a = dw.randombackgroundimage(w, h, palette, tileable=False)
    image1b = (
        None
        if variant == 2
        else dw.randombackgroundimage(w, h, palette, tileable=False)
    )
    expo1 = random.uniform(0.5, 2.5)
    expo1a = random.uniform(0.5, 2.5)
    expo1b = random.uniform(0.5, 2.5)
    ###############
    if random.randint(0, 99) < 90:
        # shape background
        imagebg = dw.randombackgroundimage(
            w * columns, h * rows, palette, tileable=True
        )
    else:
        # shape background, tiled style
        imagebg = dw.randombackgroundimage(w, h, palette, tileable=False)
        _shiftImage(imagebg, w, h)
        imagebg = dw.tiledImage(imagebg, w, h, w * columns, h * rows)
    mask1 = _argylemask(w, h, expo1)
    mask2 = _argylemask(w, h, expo1a)
    mask3 = None if variant == 2 else _argylemask(w, h, expo1b)
    for y in range(rows):
        for x in range(columns):
            i = random.choice([0, 1, 2])
            if variant == 2:
                mask = [mask1, mask2][(x + y) % 2]
                img = [image1, image1a][(x + y) % 2]
            else:
                mask = [mask1, mask2, mask3][i]
                img = [image1, image1a, image1b][i]
            dw.imageblitex(
                imagebg,
                w * columns,
                h * rows,
                w * x,
                h * y,
                w * (x + 1),
                h * (y + 1),
                img,
                w,
                h,
                maskimage=mask,
                maskwidth=w,
                maskheight=h,
                alpha=False,
            )
    image3, width, height = _randomTransformed(imagebg, w * columns, h * rows)
    image3 = dw.randommaybemonochrome(image3, width, height)
    if random.randint(0, 9) == 0:
        dw.randombordertile(image3, width, height)
    return [image3, width, height]
