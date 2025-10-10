# Classic Tiled Wallpaper Challenge

This repository is intended to hold open-source wallpaper images and source code for the following challenge.

Given that desktop backgrounds today tend to cover the full computer screen, to employ thousands of colors, and to have a high-definition resolution (1920 &times; 1080 or larger), rendering tileable backgrounds with limited colors and pixel size ever harder to find, I make the following challenge.

## The Challenge

Create a tileable desktop wallpaper image [^1] meeting the following requirements.

- The image is one of the following:
    - It is a pixel image (also known as _raster image_ or _bitmap_) with one of the color palettes and one of the pixel dimensions given later.
    - It is a vector graphic in the Scalable Vector Graphics (SVG) format made only of two-dimensional filled outlines with no stroke.  Excessive detail should be avoided.  Moreover:
        - Each outline is filled black and either opaque or translucent (semitransparent).  The image can then be scaled to any pixel dimension desired and turned into a grayscale (see later) pixel image using known techniques (see [_Hero Patterns_](https://heropatterns.com/) for an example).  Or...
        - Each outline is opaque and filled with one of up to ten colors from a color palette given later.  See [_colourlovers.com_](https://www.colourlovers.com/patterns) for examples.
- The image is preferably abstract, should not employ trademarks, and is suitable for all ages.
- The image does not contain text.  Images that contain depictions of people or human faces are not preferred.
- The image should be uncompressed or compressed without loss (so in PNG or BMP format, for example, rather than JPG format).
- The image is in the public domain or licensed under the [Unlicense](https://unlicense.org/) or, less preferably, another open-source license approved by the Open Source Initiative.
- The image was not produced by artificial-intelligence tools or with their help.

Also welcome would be computer code (released to the public domain or licensed under the Unlicense) to generate tileable or seamless&mdash;

- noise,
- procedural textures or patterns, or
- arrangements of symbols or small images with partial transparency,

meeting the requirements given earlier.

In general, the following are not within the scope of this challenge.

- Photographic images (see "Wallpaper Generation Notes", later in this document).
- Images with a single solid color on all four sides; such images are trivially tileable.
- Images that can be tiled in one dimension only, such as those depicting horizontal or vertical borders with an "infinitely" extending background.

## Color Palettes

The color palettes allowed are as follows.

- Two colors only.
    - Such as black and white, which allows for hue shifting to, say, a black-to-red or gray-to-blue palette.
- 16-color VGA (video graphics array) palette (light gray, that is, (192, 192, 192); or each color component is 0 or 255; or each color component is 0 or 128).
- 216-color "safety palette" (each color component is a multiple of 51). [^7]
- 216-color "safety palette" plus VGA palette.
- A subset of a color palette given earlier.

Any 16-color or 256-color repertoire that was used in a significant volume of application and video-game graphics before the year 2000 is also allowed.

Additional color palettes allowed are as follows.

- Three gray tones: black (0, 0, 0), gray (128, 128, 128), white (255, 255, 255).
    - Allows for hue shifting to, say, a black-to-red palette.
- Four gray tones: black, gray (128, 128, 128), light gray (192, 192, 192), white.
    - Allows for hue shifting to, say, a black-to-red palette.
- The VGA palette plus the following four colors set by legacy versions of Windows: (192,220,192), (160,160,164), (255,251,240), (166,202,240).
- The VGA palette plus each "half-and-half mixture" [^6] of any two colors in the palette, for a total of 98 unique colors (each color component is 0, 64, 128, or 192; or each color component is 0, 128, or 255; or each color component is 96 or 160; or each color component is 96 or 224).
- 16-color [**canonical Color/Graphics Adapter (CGA) palette**](https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/) (each color component is 85 or 255; or each color component is 0 or 170, except (170, 85, 0) instead of (170, 170, 0)).
- An 8-color palette where each color component is 0 or 255 (a subset of the 16-color VGA palette).
- The canonical CGA palette plus each "half-and-half mixture" [^6] of any two colors in the palette, for a total of 85 unique colors.
- The 64 colors displayable by Extended Graphics Adapter (EGA) monitors (each color component is 0, 85, 170, or 255).
- Up to 16 colors from those displayable by Amiga computers and other 12-bit color displays (each color component is a multiple of 17).
- Up to 16 colors from those displayable by original Atari ST computers and other 9-bit color displays (each color component is either 255 or a multiple of 32).
- Up to 16 colors from those displayable by 15-bit color displays (each color component is a multiple of 8).
- Up to 32 colors from those displayable by 12-bit color displays.
- A palette of the 256 colors used by default in [VGA 256-color mode](https://github.com/canidlogic/vgapal).
- 5- to 64-color grayscale palette (all color components the same).
- A 27-color palette where each color component is 0, 128, or 255.
- A 125-color palette where each color component is 0, 64, 128, 192, or 255.
- Up to four colors from a palette mentioned earlier in this section.
- Up to eight colors from a palette mentioned earlier in this section.
- Up to 16 colors from a palette mentioned earlier in this section.
- A 255-color palette in which each color component is a multiple of 3 and each color is as follows: All components are the same; or both the green and blue components are 0; or the red component is 255 and the green and blue components are the same.
    - Essentially, the palette is made of two color gradients: one going from black to white, and another going from black to "red" (255,0,0) to white.
    - This palette is proposed to allow for easy "recoloring" of an image based on a so-called _accent color_: the cases just given deal with a mixture of "black" and "white"; a mixture of "black" (0,0,0) and the accent color; and a mixture of "white" (255,255,255) and the accent color.  An example occurs with "red" and "blue" variants of a playing card back.  For examples, see the `recolor()` and `recolordither()` methods in `desktopwallpaper.py`.
- A palette just described, except (129, 129, 129) is replaced with (128, 128, 128); (129, 0, 0), with (128, 0, 0); and (255, 129, 129), with (255, 128, 128).
- A 255-color palette consisting of a gradient from "black" to "white": (0, 0, 0), (2, 2, 2), (4, 4, 4), ..., (250, 250, 250), (252, 252, 252), (255, 255, 255); and a gradient from "black" to "red": (2, 0, 0), (4, 0, 0), ..., (250, 0, 0), (252, 0, 0), (254, 0, 0), (255, 0, 0).

The following color palettes are allowed, but not preferred:

- Up to 16 colors from those displayable by 16-bit color displays (each red and blue component is a multiple of 8; each green, a multiple of 4).
- Up to 16 colors from those displayable by pure VGA monitors (each color component is a multiple of 4).
- 65- to 236-color grayscale palette (all color components the same).
- 237- to 256-color grayscale palette (all color components the same).
- A color palette of up to 256 colors listed in the [_Lospec_ palette list](https://lospec.com/palette-list).
- A 765-color palette in which each color is as follows: All components are the same; or both the green and blue components are 0; or the red component is 255 and the green and blue components are the same.
    - Essentially, the palette is made of two color gradients: one going from black to white, and another going from black to "red" (255,0,0) to white.

> **Notes:**
>
> 1. The [_palettes_ directory](https://github.com/peteroupc/classic-wallpaper/tree/main/palettes) of this repository hosts palette files for many of the color combinations described earlier.  The palette files are designed for use in software programs for drawing, especially those devoted to pixel art.
> 2. The palette can have one or more sequences of colors that smoothly range from one color to another, to aid in achieving gradient fills or other specialized shading techniques in a _ramp color model_.  For example, a palette can have ten colors (indexed from 0 through 9) that range from black to green, and ten additional colors (indexed from 10 through 19) that range from black to red.

## Pixel Dimensions

The pixel dimensions allowed are as follows.

- Preferred: 8 &times; 8, 16 &times; 16, 32 &times; 32, 64 &times; 64, 64 &times; 32, 32 &times; 64, 96 &times; 96, 128 &times; 128, 256 &times; 256.
- 32 &times; 32 or 64 &times; 64, where the second, fourth, etc. column is the same as the previous column (each logical pixel is 2 &times; 1).
- Not preferred: 320 &times; 240, 320 &times; 200.
- Not preferred: Custom size up to 96 &times; 96.
- Not preferred: Custom size up to 256 &times; 256.

## Examples

|  Name  | Made by  |  Colors  |  Size  | License/Notes |
  --- | --- | --- | -- | --- |
| dstripe.png | peteroupc | Black and white | 32 &times; 32 | Unlicense |
| dzigzag.png | peteroupc | Black and white | 64 &times; 32 | Unlicense [^2] |
| dzigzagcyan.png | peteroupc | Two colors (cyan and teal) | 64 &times; 32 | Unlicense |
| truchet2color.png | peteroupc | Black and white | 32 &times; 32 | Unlicense |
| truchet2colorthick.png | peteroupc | Black and white | 32 &times; 32 | Unlicense |
| truchet3color.png | peteroupc | Black/gray/white | 32 &times; 32 | Unlicense [^5] |
| smallslant.png | peteroupc | Four tones | 8 &times; 8 | Unlicense |
| truchetff5500vga.png | peteroupc | VGA palette | 32 &times; 32 | Unlicense [^4] |
| boxes.png | peteroupc | VGA palette | 128 &times; 128 | Unlicense |
| circlec.png | peteroupc | VGA palette | 128 &times; 128 | Unlicense |
| circlews.png | peteroupc | "Safety palette" | 128 &times; 128 | Unlicense |
| check.png | peteroupc | VGA palette | 96 &times; 96 | Unlicense |
| brushed.png | peteroupc | VGA palette | 96 &times; 96 | Unlicense |
| [JohnGWebDev/Background-Textures](https://github.com/JohnGWebDev/Background-Textures) | John Galiszewski | Black and white | All 100 &times; 100 | MIT License |

The texture generator at [`schalkt/tgen`](https://github.com/schalkt/tgen), under an MIT License, is another example.

## Wallpaper Generation Notes

1. Suppose a wallpaper image has only colors of the same hue and "saturation".  Then a _grayscale_ version of the image is preferred (that is, a version of the image where the colors are limited to gray tones, black, and white), since then the image could be color-shifted and then adapted to have the colors of any limited-color palette by known [dithering techniques](https://bisqwit.iki.fi/story/howto/dither/jy/) or print-simulating _halftoning techniques_. Dithering scatters an image's pixels in a limited-color palette to simulate colors outside that palette.  For an example, see the `patternDither` method in _desktopwallpaper.py_.
     - This point can also apply to an image if only part of the image has only colors of the same hue and "saturation", and the rest is grayscale.  In that case, the color shifting can then be made to apply only to the nongrayscale part of the image.
     - If the automatic adaptation to a particular color palette (such as black and white, or the three VGA gray tones, or the full VGA palette; see "Color Palettes", earlier) leads to an unsatisfactory appearance, then a version optimized for that palette can be supplied.

2. Other tileable wallpapers employing more than 256 colors and otherwise satisfying the challenge's requirements are acceptable, though not preferable.  If a wallpaper image has more than 256 colors and otherwise meets those requirements, it can be adapted to have the colors of a limited-color palette (see the "Color Palettes" section below) by dithering techniques, where the image can be converted to a grayscale image, color shifted, or both before adapting it this way.  And, if the image is not tileable, the _desktopwallpaper.py_ has an `argyle` method that generates a tileable wallpaper image from two images of the same size, neither of which need be tileable.

3. An unusual form of wallpaper results from layering a tileable foreground over a nontileable (abstract) background, where the foreground has transparent pixels and wraps around the edges.  Examples of this technique are shown in the wallpaper files `RIBBONS.BMP` and `PARTY.BMP`, both of which were distributed with Windows 3.0 and the latter was inspired by the Memphis group style.

4. One example of tileable noise can be generated using the "[diamond-square algorithm](https://en.wikipedia.org/wiki/Diamond-square_algorithm)".

5. One way to generate a wallpaper image is by blending a solid color (or another tileable wallpaper) with a tileable image consisting of only transparent pixels and semitransparent and opaque black pixels (such as a masonry pattern).

6. **Stochastic tiling:** Wang tiles are a finite set of tiles (here, wallpaper images) that can cover an arbitrary grid without seams.  One example is the [set of 16 tiles](https://web.archive.org/web/20150612010851/http://www.cr31.co.uk/stagecast/wang/intro.html) whose edges have two variations each: two upper-edge, two lower-edge, two left-edge, and two right-edge variations.

    - A randomized tiling, or _stochastic tiling_, can be generated from this tile set by repeatedly selecting a grid position and choosing a random tile that can go in that position without introducing seams, until the whole grid is covered.
    - Another kind of stochastic tiling occurs with placing a randomly chosen version of a wallpaper image at each grid position, where each version has the same dimensions and the same edges as each other version but can otherwise vary.[^8]

    Both kinds of stochastic tiling can be combined.  [See example](https://web.archive.org/web/20160220062702/http://www.cr31.co.uk/stagecast/wang/2edge.html).[^9]

## Sample Wallpaper Generation Code

This repository has the following code files in Python for generating tiled wallpapers and reading and writing Windows icon files and pixel images in the PNG and Windows bitmap formats: `desktopwallpaper.py`, `imageformat.py`, `randomwp.py`.

This repository also has a directory (`rust/`) with Rust source code for generating a tiled wallpaper.

In addition, the following code in Python is presented as an example of computer code to generate tileable wallpaper patterns. It uses the `desktopwallpaper` and `imageformat` modules and helped generate `circlec.png` and `circlews.png`.

```python
import desktopwallpaper as dw
import imageformat as ifmt
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
# Dither in VGA colors
dw.patternDither(image, width, height, dw.classiccolors())
# Dither in "safety palette"
dw.websafeDither(image2, width, height)
# Write dithered images
ifmt.writepng("/tmp/circlec.png", image, width, height)
ifmt.writepng("/tmp/circlews.png", image2, width, height)
```

Replacing the `contouring` method above with the one below leads to a diagonal gradient fill that's tileable:

```
def contouring(x,y,z):
   c=abs(x+y)%2.0; return 2-c if c > 1.0 else c
```

## Other User Interface Graphics

For discussions on the traditional design of user-interface elements such as buttons, border styles, icons, cursors, and animations, see [uielements.md](https://github.com/peteroupc/classic-wallpaper/blob/main/uielements.md) in this repository.

The page also describes an additional challenge to write computer code (released to the public domain or licensed under the Unlicense) to draw traditional button and border styles.

For discussions on converting traditional icons to vector graphics, see [pixeltovector.md](https://github.com/peteroupc/classic-wallpaper/blob/main/pixeltovector.md) in this repository.

<a id=License></a>

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [Unlicense](https://unlicense.org).

[^1]: Every tileable desktop wallpaper has a pattern that belongs in one of 17 [_wallpaper groups_](https://en.wikipedia.org/wiki/Wallpaper_group).  The shape of the pattern is a rectangle in ten of them, a diamond with one corner pointing upward in two of them, and another parallelogram in the remaining five.  Many tileable wallpapers are _seamless_, but not all (consider a pattern of bricks or square floor tiles).<br>For the Macintosh operating system, System 7.5.x and Mac OS 7.6.x, 8.x, and 9.x supported _desktop patterns_ of size up to 128 &times; 128 pixels, Mac OS 8.x and 9.x distinguished between desktop patterns and _desktop pictures_ (of usually larger size and lying above the desktop pattern), and versions earlier than System 7.5 supported only 8-&times;-8-pixel desktop patterns.<br>In Windows version 3.1, Windows 95, and Windows 98, _desktop patterns_ are of size 8x8 pixels and have only two colors (black and the desktop background color), and _desktop wallpaper_ is of arbitrary size and lies above the desktop pattern.

[^2]: Can be generated from `dstripe` using the following ImageMagick command: `magick dstripe.png \( +clone -flop \) +append dzigzag.png`.

[^4]: Can be generated from `truchet3color` using the following [ImageMagick](https://imagemagick.org/) command: `magick truchet3color.png \( +clone -grayscale Rec709Luma \) \( -size 1x256 gradient:#000000-#ff5500 \) -delete 0 -clut  \( -size 1x1 xc:#000000 xc:#808080 xc:#FFFFFF xc:#C0C0C0 xc:#FF0000 xc:#800000 xc:#00FF00 xc:#008000 xc:#0000FF xc:#000080 xc:#FF00FF xc:#800080 xc:#00FFFF xc:#008080 xc:#FFFF00 xc:#808000 +append -write mpr:z +delete \) -dither FloydSteinberg -remap mpr:z truchetff5500vga.png`. This example, which employs a color shift and dither, demonstrates that derivative colored wallpapers with limited colored palettes can easily be generated from black/gray/white wallpapers using non-AI computer programs.

[^5]: Can be generated from `truchet2color` using the following ImageMagick command: `magick truchet2color.png \( +clone \( +clone \) -append \( +clone \) +append -crop 50%x50%+1+1 \( -size 1x2 gradient:#FFFFFF-#808080 \) -clut \) -compose Multiply -composite truchet3color.png`.  Here, `#FFFFFF` and `#808080` indicate the two colors white and gray, respectively.

[^6]: A "half-and-half mixture" of two colors is found by averaging their three components then rounding each average up to the nearest integer.

[^7]: The "safety palette", also known as the "Web safe" colors, consists of 216 colors that are uniformly spaced in the red&ndash;green&ndash;blue color cube.  Robert Hess's article "[The Safety Palette](https://learn.microsoft.com/en-us/previous-versions/ms976419(v=msdn.10))", 1996, described the advantage that images that use only colors in this palette won't dither when displayed by Web browsers on displays that can show up to 256 colors at once. (See also [**Wikipedia**](http://en.wikipedia.org/wiki/Web_colors). Dithering is the scattering of colors in a limited set to simulate colors outside that set.)  When the "safety palette" forms part of a 256-color repertoire, as it usually does, 40 slots are left that can be filled with additional colors, and as Hess mentions, graphics designers have no control over what these additional colors are. Usually these additional colors include the four legacy Windows colors plus the eight VGA palette colors not already in the "safety palette".  For Java's `BufferedImage.TYPE_BYTE_INDEXED`, these 40 colors are gray tones not already in the "safety palette".

[^8]: This covers the special case of _Truchet tiles_, involving two versions of an image where each edge is symmetric and the second version is horizontally or vertically mirrored from the first.

[^9]: For more on stochastic tiling using Wang tiles, see Cohen, M.F., Shade, J., et al., "Wang Tiles for Image and Texture Generation", SIGGRAPH 2003.<br>Tiling techniques that also blend adjacent tiles to hide seams are too complex to describe here. For examples, see Efros and Freeman, "Image Quilting for Texture Synthesis and Transfer", SIGGRAPH 2001; Deliot and Heitz, "Procedural Stochastic Textures by Tiling and Blending", 2019.
