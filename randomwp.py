import random
import desktopwallpaper as dw

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
                return [image3,width,height]
