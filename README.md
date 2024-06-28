# Classic Tiled Wallpaper Challenge

This repository is intended to hold public-domain wallpaper images and source code for the following challenge.

Given that desktop backgrounds today tend to cover the full computer screen, to employ thousands of colors, and to have a high-definition resolution (1920&times;1080 or larger), rendering tileable backgrounds with limited colors and pixel size ever harder to find, I make the following challenge.

Create a tileable desktop wallpaper image [^1] meeting the following requirements.

- The image employs one of the following color options:
    - Two colors only.
        - Such as black and white, which allows for hue shifting to, say, a black-to-red or gray-to-blue palette.
    - Three gray tones: black (0, 0, 0), gray (128, 128, 128), white (255, 255, 255).
        - Allows for hue shifting to, say, a black-to-red palette.
    - Four gray tones: black, gray (128, 128, 128), light gray (192, 192, 192), white.
        - Allows for hue shifting to, say, a black-to-red palette.
    - 16-color [**canonical CGA palette**](https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/) (each color component is 85 or 255; or each color component is 0 or 170, except (170, 85, 0) instead of (170, 170, 0)).[^3]
    - 16-color VGA palette (light gray; or each color component is 0 or 255; or each color component is 0 or 128).[^3]
    - The VGA palette plus the following four colors set by legacy versions of Windows: (192,220,192), (160,160,164), (255,251,240), (166,202,240).
    - Up to four colors from the VGA palette.
    - Up to four colors from the canonical CGA palette.
    - Up to eight colors from the VGA palette.
    - 216-color "web safe" palette (each color component is a multiple of 51).[^3]
    - 216-color "web safe" palette plus VGA palette.[^3]
    - The VGA palette plus each "half-and-half mixture" [^6] of any two colors in the palette, for a total of 98 unique colors (each color component is 0, 64, 128, or 192; or each color component is 0, 128, or 255; or each color component is 96 or 160; or each color component is 96 or 224).
    - The canonical CGA palette plus each "half-and-half mixture" [^6] of any two colors in the palette, for a total of 85 unique colors.
    - The 64 colors displayable by EGA monitors (each color component is 0, 85, 170, or 255).[^3]
    - Up to 16 colors from the "web safe" palette.
    - Up to 16 colors from the "web safe" and VGA palettes.
    - Up to 16 colors from those displayable by EGA monitors (each color component is 0, 85, 170, or 255).
    - 5- to 64-color grayscale palette (all color components the same).
    - Not preferred: Up to 16 colors from those displayable by pure VGA monitors (each color component is a multiple of 4).
    - Not preferred: 65- to 236-color grayscale palette (all color components the same).
    - Not preferred: 237- to 256-color grayscale palette (all color components the same).

    > **Notes:**
    >
    > 1. _Grayscale_ means having no colors other than gray tones, black, and white.
    >
    > 2. If a wallpaper image is _monochrome_ (it is grayscale, or its colors are of the same hue and the same chroma or "saturation"), then a grayscale version of the image is preferred, since then it could be color shifted and then adapted to have the colors of any limited-color palette by known [dithering techniques](https://bisqwit.iki.fi/story/howto/dither/jy/).  For an example, see the `magickgradientditherfilter` method in _desktopwallpaper.py_.  If the automatic adaptation to a particular color palette (such as black and white, or the three VGA gray tones, or the six "Web safe" gray tones, or the full VGA palette) leads to an unsatisfactory appearance, then a version optimized for that palette can be supplied.
    >
    > 3. The wallpaper image is allowed to be a vector graphic in the SVG format made only of two-dimensional vector paths, each of which has no stroke, a black fill, and any fill opacity from 0 through 100%.  With this vector format, the image can be scaled to any pixel dimension desired and turned into a grayscale bitmap image using known techniques (see [_Hero Patterns_](https://heropatterns.com/) for an example).
    >
    > 4. The [_palettes_ directory](https://github.com/peteroupc/classic-wallpaper/tree/main/palettes) of this repository hosts palette files for many of the color combinations described above.  The palette files are designed for use in drawing programs, especially those devoted to pixel art.

- The image employs one of the following pixel dimension options:
    - Preferred: 8&times;8, 16&times;16, 32&times;32, 64&times;64, 64&times;32, 32&times;64, 96&times;96, 128&times;128, 256&times;256.
    - Not preferred: 320&times;240, 320&times;200.
    - Not preferred: Custom size up to 96&times;96.
    - Not preferred: Custom size up to 256&times;256.

- The image is preferably abstract, should not employ trademarks, and is suitable for all ages.
- The image does not contain text.  Images that contain depictions of people or human faces are not preferred.
- The image should be uncompressed or compressed without loss (so in PNG or BMP format, for example, rather than JPG format).
- The image is in the public domain or licensed under Creative Commons Zero (CC0) or Attribution (CC-BY) or, less preferably, another open-source license.
- The image was not produced by artificial intelligence tools or with their help.

Also welcome would be computer code (released to the public domain or under Creative Commons Zero) to generate tileable&mdash;

- noise,
- procedural textures or patterns, or
- arrangements of symbols or small images with partial transparency,

meeting the requirements given above.

## Examples

|  Name  | Made by  |  Colors  |  Size  | License/Notes |
  --- | --- | --- | -- | --- |
| dstripe.png | peteroupc | Black and white | 32x32 | CC0 |
| dzigzag.png | peteroupc | Black and white | 64x32 | CC0 [^2] |
| dzigzagcyan.png | peteroupc | Two colors (cyan and teal) | 64x32 | CC0 |
| truchet2color.png | peteroupc | Black and white | 32x32 | CC0 |
| truchet3color.png | peteroupc | Black/gray/white | 32x32 | CC0 [^5] |
| smallslant.png | peteroupc | Four tones | 8x8 | CC0 |
| truchetff5500vga.png | peteroupc | VGA palette | 32x32 | CC0 [^4] |
| boxes.png | peteroupc | VGA palette | 128x128 | CC0 |
| circlec.png | peteroupc | VGA palette | 128x128 | CC0 |
| circlews.png | peteroupc | "Web safe" palette | 128x128 | CC0 |
| check.png | peteroupc | VGA palette | 96x96 | CC0 |
| brushed.png | peteroupc | VGA palette | 96x96 | CC0 |
| [JohnGWebDev/Background-Textures](https://github.com/JohnGWebDev/Background-Textures) | John Galiszewski | Black and white | All 100x100 | MIT License |

## Sample Wallpaper Generation Code

The following code in Python is presented as an example of computer code to generate tileable wallpaper patterns. It helped generate `circlec.png` and `circlews.png`.

```python
import desktopwallpaper as dw
import random

def contouring(x,y,z):
   return abs(x**z+y**z)**(1/z)

def _togray(x):
   return int(abs(max(-1,min(1,x)))*255.0)

width=128
height=128
# Draw a grayscale gradient image
image = [_togray(contouring(x*2.0/width-1.0,y*2.0/height-1.0,2.5)) for x in range(width) for y in range(height)]
image = [cc for pix in [(x,x,x) for x in image] for cc in pix]
# Colorize the image
dw.graymap(image, width, height, dw.randomColorization())
# Draw a checkerboard overlay over the image
dw.checkerboardoverlay(image,width,height,[random.randint(0,255) for i in range(3)])
# Dither the image
image2=[x for x in image] # copy image for dithering
dw.patternDither(image, width, height, dw.classiccolors())
dw.websafeDither(image2, width, height)
# Dither in VGA colors
dw.writepng("circlec.png", image, width,height)
# Dither in "web safe" colors
dw.writepng("circlews.png", image2, width,height)
```

## Button and Border Styles

Another challenge, related to classic user-interface style, this time relating to user interface elements.  Write computer code (released to the public domain or under Creative Commons Zero) to draw the following border and button styles:

- Window border, field border, status field border, and grouping border.
- Buttons and default buttons:
    - Unpressed, pressed, mixed value, unavailable.
- Toolbar buttons:
    - Unpressed, hover, pressed, unavailable.
- Buttons, default buttons, and toolbar buttons in the option-set style:
    - Unpressed, unavailable.
- Checkboxes when set, checkboxes when unset:
    - Unpressed, pressed, mixed value (same for both), unavailable.
- Option buttons ("radio buttons") when set, option buttons when unset, sliders:
    - Unpressed, pressed, unavailable.
- Optionally, other user interface elements (such as scroll bars).

Using only the following colors and with some pixels allowed to be transparent:

- Button highlight color (white by default).
- Button "light" highlight color (by default, (192, 192, 192)).
- Button shadow color (by default, (128, 128, 128)).
- Button dark shadow color (black by default).
- Button face color (by default, (192, 192, 192)).
- Window frame color (black by default).

It is allowed to use dithering to simulate the appearance of more colors using these six colors.

The _desktopwallpaper.py_ file contains some example code for border and button drawing. I expect many other variations here, some more subtle than others, but the design should not employ trademarks, should be suitable for all ages, and must not involve the help of artificial intelligence tools.

<a id=License></a>

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under [**Creative Commons Zero**](https://creativecommons.org/publicdomain/zero/1.0/).

[^1]: Every tileable desktop wallpaper has a pattern that belongs in one of 17 [_wallpaper groups_](https://en.wikipedia.org/wiki/Wallpaper_group).  The shape of the pattern is a rectangle in ten of them, a diamond with one corner pointing upward in two of them, and another parallelogram in the remaining five.  Many tileable wallpapers are _seamless_, but not all (consider a pattern of bricks or square floor tiles).  Images that can be tiled in one dimension only, such as those depicting horizontal or vertical borders with an "infinitely" extending background, are not tileable for purposes of this challenge.

[^2]: Can be generated from `dstripe` using the following ImageMagick command: `magick dstripe.png \( +clone -flop \) +append dzigzag.png`.

[^3]: Tileable wallpapers employing more than 256 colors are acceptable, though not preferable, if they otherwise meet all requirements here, since they can be adapted to have the colors of this color palette using known techniques for color dithering.

[^4]: Can be gnerated from `truchet3color` using the following [ImageMagick](https://imagemagick.org/) command: `magick truchet3color.png \( +clone -grayscale Rec709Luma \) \( -size 1x256 gradient:#000000-#ff5500 \) -delete 0 -clut  \( -size 1x1 xc:#000000 xc:#808080 xc:#FFFFFF xc:#C0C0C0 xc:#FF0000 xc:#800000 xc:#00FF00 xc:#008000 xc:#0000FF xc:#000080 xc:#FF00FF xc:#800080 xc:#00FFFF xc:#008080 xc:#FFFF00 xc:#808000 +append -write mpr:z +delete \) -dither FloydSteinberg -remap mpr:z truchetff5500vga.png`. This example, which employs a color shift and dither, demonstrates that derivative colored wallpapers with limited colored palettes can easily be generated from black/gray/white wallpapers using non-AI computer programs.

[^5]: Can be generated from `truchet2color` using the following ImageMagick command: `magick truchet2color.png \( +clone \( +clone \) -append \( +clone \) +append -crop 50%x50%+1+1 \( -size 1x2 gradient:#FFFFFF-#808080 \) -clut \) -compose Multiply -composite truchet3color.png`.  Here, `#FFFFFF-808080` indicates the two colors white and gray, respectively.

[^6]: A "half-and-half mixture" of two colors is found by averaging their three components then rounding each average up to the nearest integer.
