# Classic Tiled Wallpaper Challenge

This repository is intended to hold open-source wallpaper images and source code for the following challenge.

Given that desktop backgrounds today tend to cover the full computer screen, to employ thousands of colors, and to have a high-definition resolution (1920&times;1080 or larger), rendering tileable backgrounds with limited colors and pixel size ever harder to find, I make the following challenge.

Create a tileable desktop wallpaper image [^1] meeting the following requirements.

- The image is one of the following:
    - It is a raster (bitmap) image with one of the color palettes and one of the pixel dimensions given later.
    - It is a vector graphic in the Scalable Vector Graphics (SVG) format made only of two-dimensional vector paths with no stroke.  Excessive detail should be avoided.  Moreover, one of the following is true.
        - Each path has a black fill and any fill opacity from 0 through 100%.  The image can then be scaled to any pixel dimension desired and turned into a grayscale (see later) bitmap image using known techniques (see [_Hero Patterns_](https://heropatterns.com/) for an example).
        - Each path has a 100% fill opacity and is filled with one of up to ten colors from a color palette given later.  See [_colourlovers.com_](https://www.colourlovers.com/patterns) for examples.
- The image is preferably abstract, should not employ trademarks, and is suitable for all ages.
- The image does not contain text.  Images that contain depictions of people or human faces are not preferred.
- The image should be uncompressed or compressed without loss (so in PNG or BMP format, for example, rather than JPG format).
- The image is in the public domain or licensed under the [Unlicense](https://unlicense.org/) or, less preferably, another open-source license approved by the Open Source Initiative.
- The image was not produced by artificial intelligence tools or with their help.

Also welcome would be computer code (released to the public domain or licensed under the Unlicense) to generate tileable or seamless&mdash;

- noise,
- procedural textures or patterns, or
- arrangements of symbols or small images with partial transparency,

meeting the requirements given above.

> **Notes:**
>
> 1. If a wallpaper image is _monochrome_, then a _grayscale_ version of the image is preferred, since then the image could be color shifted and then adapted to have the colors of any limited-color palette by known [dithering techniques](https://bisqwit.iki.fi/story/howto/dither/jy/) or print-simulating _halftoning techniques_. Dithering scatters an image's pixels in a limited-color palette to simulate colors outside that palette.  For an example, see the `patternDither` method in _desktopwallpaper.py_.  (_Grayscale_ means having no colors other than gray tones, black, or white.  _Monochrome_ means the image is grayscale or its colors are of the same hue and the same chroma or "saturation".) If the automatic adaptation to a particular color palette (such as black and white, or the three VGA gray tones, or the full VGA palette; see below) leads to an unsatisfactory appearance, then a version optimized for that palette can be supplied.
> 2. Photographic images are not within the scope of this challenge.  Indeed, if the image has more than 256 colors and otherwise meets the requirements above, it can be adapted to have the colors of a limited-color palette (such as the VGA palette, the "safety palette", or a 236- or 256-color palette) by dithering techniques, where the image can be converted to a grayscale image, color shifted, or both before adapting it this way.  And, if the image is not tileable, the _desktopwallpaper.py_ has an `argyle` method that generates a tileable wallpaper image from two images of the same size, neither of which need be tileable.
> 3. An unusual form of wallpaper results from layering a tileable foreground over a nontileable (abstract) background, where the foreground has transparent pixels and wraps around the edges.  An example of this technique is shown in the wallpaper file `RIBBONS.BMP`, which was distributed with Microsoft Windows 3.0.
> 4. One example of tileable noise can be generated using the "[diamond-square algorithm](https://en.wikipedia.org/wiki/Diamond-square_algorithm)", which is not yet implemented on this repository.

## Color Palettes

The color palettes allowed are as follows.

- Two colors only.
    - Such as black and white, which allows for hue shifting to, say, a black-to-red or gray-to-blue palette.
- 16-color VGA (video graphics array) palette (light gray, that is, (192, 192, 192); or each color component is 0 or 255; or each color component is 0 or 128).[^3]
- 216-color "safety palette", also known as "Web safe" palette (each color component is a multiple of 51).[^3] [^7]
- 216-color "safety palette" plus VGA palette.[^3]
- A subset of a color palette given earlier.

Any 16-color or 256-color palette that was used in a significant volume of application and video game graphics before the year 2000 is also allowed.

Additional color palettes allowed are as follows.

- Three gray tones: black (0, 0, 0), gray (128, 128, 128), white (255, 255, 255).
    - Allows for hue shifting to, say, a black-to-red palette.
- Four gray tones: black, gray (128, 128, 128), light gray (192, 192, 192), white.
    - Allows for hue shifting to, say, a black-to-red palette.
- The VGA palette plus the following four colors set by legacy versions of Windows: (192,220,192), (160,160,164), (255,251,240), (166,202,240).
- The VGA palette plus each "half-and-half mixture" [^6] of any two colors in the palette, for a total of 98 unique colors (each color component is 0, 64, 128, or 192; or each color component is 0, 128, or 255; or each color component is 96 or 160; or each color component is 96 or 224).
- 16-color [**canonical Color/Graphics Adapter (CGA) palette**](https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/) (each color component is 85 or 255; or each color component is 0 or 170, except (170, 85, 0) instead of (170, 170, 0)).[^3]
- An 8-color palette where each color component is 0 or 255 (a subset of the 16-color VGA palette).
- A 16-color palette where each color is one of the following: each color component is 0 or 255; or each color component is 0 or 128 except for (128, 128, 128); or the color is (64, 64, 64).
- The canonical CGA palette plus each "half-and-half mixture" [^6] of any two colors in the palette, for a total of 85 unique colors.
- The 64 colors displayable by Extended Graphics Adapter (EGA) monitors (each color component is 0, 85, 170, or 255).[^3]
- Up to 16 colors from those displayable by 12-bit color displays (each color component is a multiple of 17).
- Up to 16 colors from those displayable by 15-bit color displays (each color component is a multiple of 8).
- A palette of the 256 colors used by default in [VGA 256-color mode](https://github.com/canidlogic/vgapal).
- 5- to 64-color grayscale palette (all color components the same).
- A 27-color palette where each color component is 0, 128, or 255.
- A 125-color palette where each color component is 0, 64, 128, 192, or 255.
- Up to four colors from a palette mentioned earlier in this section.
- Up to eight colors from a palette mentioned earlier in this section.
- Up to 16 colors from a palette mentioned earlier in this section.

The following color palettes are allowed, but not preferred:

- Up to 16 colors from those displayable by 16-bit color displays (each red and blue component is a multiple of 8; each green, a multiple of 4).
- Up to 16 colors from those displayable by pure VGA monitors (each color component is a multiple of 4).
- 65- to 236-color grayscale palette (all color components the same).
- 237- to 256-color grayscale palette (all color components the same).

> **Notes:**
>
> 1. The [_palettes_ directory](https://github.com/peteroupc/classic-wallpaper/tree/main/palettes) of this repository hosts palette files for many of the color combinations described above.  The palette files are designed for use in software programs for drawing, especially those devoted to pixel art.
> 2. The palette can have one or more sequences of colors that smoothly range from one color to another, to aid in achieving gradient fills or other specialized shading techniques in a _ramp color model_.  For example, a palette can have ten colors (indexed from 0 through 9) that range from black to green, and ten additional colors (indexed from 10 through 19) that range from black to red.

## Pixel Dimensions

The pixel dimensions allowed are as follows.

- Preferred: 8&times;8, 16&times;16, 32&times;32, 64&times;64, 64&times;32, 32&times;64, 96&times;96, 128&times;128, 256&times;256.
- 32&times;32 or 64&times;64, where the second, fourth, etc. column is the same as the previous column (each logical pixel is 2&times;1).
- Not preferred: 320&times;240, 320&times;200.
- Not preferred: Custom size up to 96&times;96.
- Not preferred: Custom size up to 256&times;256.

## Examples

|  Name  | Made by  |  Colors  |  Size  | License/Notes |
  --- | --- | --- | -- | --- |
| dstripe.png | peteroupc | Black and white | 32x32 | Unlicense |
| dzigzag.png | peteroupc | Black and white | 64x32 | Unlicense [^2] |
| dzigzagcyan.png | peteroupc | Two colors (cyan and teal) | 64x32 | Unlicense |
| truchet2color.png | peteroupc | Black and white | 32x32 | Unlicense |
| truchet2colorthick.png | peteroupc | Black and white | 32x32 | Unlicense |
| truchet3color.png | peteroupc | Black/gray/white | 32x32 | Unlicense [^5] |
| smallslant.png | peteroupc | Four tones | 8x8 | Unlicense |
| truchetff5500vga.png | peteroupc | VGA palette | 32x32 | Unlicense [^4] |
| boxes.png | peteroupc | VGA palette | 128x128 | Unlicense |
| circlec.png | peteroupc | VGA palette | 128x128 | Unlicense |
| circlews.png | peteroupc | "Safety palette" | 128x128 | Unlicense |
| check.png | peteroupc | VGA palette | 96x96 | Unlicense |
| brushed.png | peteroupc | VGA palette | 96x96 | Unlicense |
| [JohnGWebDev/Background-Textures](https://github.com/JohnGWebDev/Background-Textures) | John Galiszewski | Black and white | All 100x100 | MIT License |

The texture generator at [`schalkt/tgen`](https://github.com/schalkt/tgen), under an MIT License, is another example.

## Sample Wallpaper Generation Code

The following code in Python is presented as an example of computer code to generate tileable wallpaper patterns. It helped generate `circlec.png` and `circlews.png`.

```python
import desktopwallpaper as dw
import random

def contouring(x,y,z):
    return abs(x**z+y**z)**(1/z)

def _togray(x):
    return int(abs(max(-1, min(1, x))) * 255.0)

width = 128
height = 128
# Draw an image with a grayscale gradient fill
image = [
    _togray(contouring((p%width) * 2.0 / width - 1.0, (p//width) * 2.0 / height - 1.0, 2.5))
    for p in range(width*height)
]
# Generate a random color gradient
colors = dw.randomColorization()
# Create a colorized version of the image
image = [cc for pix in [colors[x] for x in image] for cc in pix]
# Draw a checkerboard overlay over the image
image = dw.checkerboard(
  dw.blankimage(width,height,[random.randint(0, 255) for i in range(3)]),
  image,
  width, height)
# Dither the image
image2 = [x for x in image]  # copy image for dithering
dw.patternDither(image, width, height, dw.classiccolors())
dw.websafeDither(image2, width, height)
# Dither in VGA colors
dw.writepng("/tmp/circlec.png", image, width, height)
# Dither in "safety palette"
dw.writepng("/tmp/circlews.png", image2, width, height)
```

Replacing the `contouring` method above with the one below leads to a diagonal gradient fill that's tileable:

```
def contouring(x,y,z):
   c=abs(x+y)%2.0; return 2-c if c > 1.0 else c
```

## Other User Interface Graphics

For discussions on the traditional design of user interface elements such as buttons, border styles, icons, cursors, and animations, see [uielements.md](https://github.com/peteroupc/classic-wallpaper/blob/main/uielements.md) in this repository.

The page also describes an additional challenge to write computer code (released to the public domain or licensed under the Unlicense) to draw traditional button and border styles.

<a id=License></a>

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [Unlicense](https://unlicense.org).

[^1]: Every tileable desktop wallpaper has a pattern that belongs in one of 17 [_wallpaper groups_](https://en.wikipedia.org/wiki/Wallpaper_group).  The shape of the pattern is a rectangle in ten of them, a diamond with one corner pointing upward in two of them, and another parallelogram in the remaining five.  Many tileable wallpapers are _seamless_, but not all (consider a pattern of bricks or square floor tiles).  Images that can be tiled in one dimension only, such as those depicting horizontal or vertical borders with an "infinitely" extending background, are not tileable for purposes of this challenge.

[^2]: Can be generated from `dstripe` using the following ImageMagick command: `magick dstripe.png \( +clone -flop \) +append dzigzag.png`.

[^3]: Tileable wallpapers employing more than 256 colors are acceptable, though not preferable, if they otherwise meet all requirements here, since they can be adapted to have the colors of this color palette using known techniques for color dithering.

[^4]: Can be generated from `truchet3color` using the following [ImageMagick](https://imagemagick.org/) command: `magick truchet3color.png \( +clone -grayscale Rec709Luma \) \( -size 1x256 gradient:#000000-#ff5500 \) -delete 0 -clut  \( -size 1x1 xc:#000000 xc:#808080 xc:#FFFFFF xc:#C0C0C0 xc:#FF0000 xc:#800000 xc:#00FF00 xc:#008000 xc:#0000FF xc:#000080 xc:#FF00FF xc:#800080 xc:#00FFFF xc:#008080 xc:#FFFF00 xc:#808000 +append -write mpr:z +delete \) -dither FloydSteinberg -remap mpr:z truchetff5500vga.png`. This example, which employs a color shift and dither, demonstrates that derivative colored wallpapers with limited colored palettes can easily be generated from black/gray/white wallpapers using non-AI computer programs.

[^5]: Can be generated from `truchet2color` using the following ImageMagick command: `magick truchet2color.png \( +clone \( +clone \) -append \( +clone \) +append -crop 50%x50%+1+1 \( -size 1x2 gradient:#FFFFFF-#808080 \) -clut \) -compose Multiply -composite truchet3color.png`.  Here, `#FFFFFF-808080` indicates the two colors white and gray, respectively.

[^6]: A "half-and-half mixture" of two colors is found by averaging their three components then rounding each average up to the nearest integer.

[^7]: The "safety palette" consists of 216 colors that are uniformly spaced in the red-green-blue color cube.  Robert Hess's article "[The Safety Palette](https://learn.microsoft.com/en-us/previous-versions/ms976419(v=msdn.10))", 1996, described the advantage that images that use only colors in this palette won't dither when displayed by Web browsers on a 256-color display. (See also [**Wikipedia**](http://en.wikipedia.org/wiki/Web_colors). Dithering is the scattering of colors in a limited set to simulate colors outside that set.)  When the "safety palette" forms part of a 256-color repertoire, as it usually does, 40 slots are left that can be filled with additional colors, and as Hess mentions, Web designers have no control over what these additional colors are. Usually these additional colors include the four legacy Windows colors plus the eight VGA palette colors not already in the "safety palette".  For Java's `BufferedImage.TYPE_BYTE_INDEXED`, these 40 colors are gray tones not already in the "safety palette".
