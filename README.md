# Classic Tiled Wallpaper Challenge

This repository is intended to hold open-source wallpaper graphics and source code for the following challenge.

Given that desktop backgrounds today tend to cover the full computer screen, to employ thousands of colors, and to have a high-definition resolution (1920 &times; 1080 or larger), rendering tileable backgrounds with limited colors and pixel size ever harder to find, I make the following challenge.

<a id=The_Challenge></a>

## The Challenge

Create a tileable desktop wallpaper graphic [^1] meeting the following requirements.

- The graphic is an image (also known as a _raster image_, a rectangular array of pixels) with one of the color palettes given in "[**Color Palettes for Classic-Style Graphics Projects**](https://peteroupc.github.io/classic-wallpaper/docs/palettes.html)" and one of the pixel dimensions given later.
- The graphic is preferably abstract, should not employ trademarks, and is suitable for all ages.
- The graphic does not contain text.  Graphics that contain depictions of people or human faces are not preferred.
- The graphic should be uncompressed or compressed without loss (so in PNG or BMP format, for example, rather than JPG format).
- The graphic is in the public domain or licensed under the [**Unlicense**](https://unlicense.org/) or, less preferably, another open-source license approved by the Open Source Initiative.
- The graphic was not produced by artificial-intelligence tools or with their help.

Instead of being an image, the graphic is allowed to be a vector graphic with two-dimensional filled outlines with no stroke, where&mdash;

- each outline is filled black and either opaque or translucent (semitransparent),[^2] or
- each outline is opaque and filled with one of up to ten colors from a color palette given in "[**Color Palettes for Classic-Style Graphics Projects**](https://peteroupc.github.io/classic-wallpaper/docs/palettes.html)".[^3]

Also welcome would be computer code (released to the public domain or licensed under the Unlicense) to generate tileable or seamless&mdash;

- noise,
- procedural textures or patterns, or
- arrangements of symbols or small graphics or images with partial transparency,

meeting the requirements given earlier.

In general, the following are not within the scope of this challenge.

- Photographic images (see "Wallpaper Generation Notes", later in this document).
- Graphics with a single solid color on all four sides; such graphics are trivially tileable.
- Graphics that can be tiled in one dimension only, such as those depicting horizontal or vertical borders with an "infinitely" extending background.

<a id=Pixel_Dimensions></a>

## Pixel Dimensions

The pixel dimensions allowed are as follows.

- Preferred: 8 &times; 8, 16 &times; 16, 32 &times; 32, 64 &times; 64, 64 &times; 32, 32 &times; 64, 96 &times; 96, 128 &times; 128, 256 &times; 256.
- 32 &times; 32 or 64 &times; 64, where the second, fourth, etc. column is the same as the previous column (each logical pixel is 2 &times; 1).
- Not preferred: 320 &times; 240, 320 &times; 200.
- Not preferred: Custom size up to 96 &times; 96.
- Not preferred: Custom size up to 256 &times; 256.

<a id=Examples></a>

## Examples

|  Name  | Made by  |  Colors  |  Size  | License/Notes |
  --- | --- | --- | -- | --- |
| dstripe.png | peteroupc | Black and white | 32 &times; 32 | Unlicense |
| dzigzag.png | peteroupc | Black and white | 64 &times; 32 | Unlicense [^4] |
| dzigzagcyan.png | peteroupc | Two colors (cyan and teal) | 64 &times; 32 | Unlicense |
| truchet2color.png | peteroupc | Black and white | 32 &times; 32 | Unlicense |
| truchet2colorthick.png | peteroupc | Black and white | 32 &times; 32 | Unlicense |
| truchet3color.png | peteroupc | Black/gray/white | 32 &times; 32 | Unlicense [^5] |
| smallslant.png | peteroupc | Four tones | 8 &times; 8 | Unlicense |
| truchetff5500vga.png | peteroupc | VGA palette [^9] | 32 &times; 32 | Unlicense [^6] |
| boxes.png | peteroupc | VGA palette | 128 &times; 128 | Unlicense |
| circlec.png | peteroupc | VGA palette | 128 &times; 128 | Unlicense |
| circlews.png | peteroupc | "Safety palette" | 128 &times; 128 | Unlicense |
| check.png | peteroupc | VGA palette | 96 &times; 96 | Unlicense |
| brushed.png | peteroupc | VGA palette | 96 &times; 96 | Unlicense |
| [**JohnGWebDev/Background-Textures**](https://github.com/JohnGWebDev/Background-Textures) | John Galiszewski | Black and white | All 100 &times; 100 | MIT License |

The texture generator at [**`schalkt/tgen`**](https://github.com/schalkt/tgen), under an MIT License, is another example.

<a id=Wallpaper_Generation_Notes></a>

## Wallpaper Generation Notes

1. Suppose an image used as wallpaper has only colors of the same hue and "saturation".  Then a _grayscale_ version of the image is preferred (that is, a version of the image where the colors are limited to gray tones, black, and white), since then the image could be color-shifted and then adapted to have the colors of any limited-color palette (as given in "[**Color Palettes for Classic-Style Graphics Projects**](https://peteroupc.github.io/classic-wallpaper/docs/palettes.html)") by known [**dithering techniques**](https://bisqwit.iki.fi/story/howto/dither/jy/) or print-simulating _halftoning techniques_. Dithering scatters an image's pixels in a limited-color palette to simulate colors outside that palette.  For an example, see the `patternDither` method in _desktopwallpaper.py_.
     - If only part of the image has only colors of the same hue and "saturation", and the rest is grayscale, then the color shifting can be limited to the nongrayscale part.
     - If an image looks unsatisfactory after being automatically adapted to a particular color palette (such as one mentioned in "[**Color Palettes for Classic-Style Graphics Projects**](https://peteroupc.github.io/classic-wallpaper/docs/palettes.html)"), it can be manually adapted instead.

2. Other tileable wallpapers employing more than 256 colors and otherwise satisfying the challenge's requirements are acceptable, though not preferable.  If an image used as wallpaper has more than 256 colors and otherwise meets those requirements, it can be adapted to have the colors of a limited-color palette (see "[**Color Palettes for Classic-Style Graphics Projects**](https://peteroupc.github.io/classic-wallpaper/docs/palettes.html)") by dithering techniques, where the image can be converted to a grayscale image, color shifted, or both before adapting it this way.  And, if the image is not tileable, the _desktopwallpaper.py_ has an `argyle` method that generates a tileable wallpaper image from two images of the same size, neither of which need be tileable.

3. An unusual form of wallpaper results from layering a tileable foreground over a nontileable (abstract) background, where the foreground has transparent pixels and wraps around the edges.  Examples of this technique are shown in the wallpaper files `RIBBONS.BMP` and `PARTY.BMP`, both of which were distributed with Windows 3.0 and the latter was inspired by the Memphis group style.

4. One example of tileable noise can be generated using the "[**diamond-square algorithm**](https://en.wikipedia.org/wiki/Diamond-square_algorithm)".

5. One way to generate a wallpaper image is by blending a solid color (or another tileable wallpaper) with a tileable image consisting of only transparent pixels and semitransparent and opaque black pixels (such as a masonry pattern).

6. **Stochastic tiling:** Wang tiles are a finite set of tiles (here, wallpaper graphics) that can cover an arbitrary grid without seams.  One example is the [**set of 16 tiles**](https://web.archive.org/web/20150612010851/http://www.cr31.co.uk/stagecast/wang/intro.html) whose edges have two variations each: two upper-edge, two lower-edge, two left-edge, and two right-edge variations.

    - A randomized tiling, or _stochastic tiling_, can be generated from this tile set by repeatedly selecting a grid position and choosing a random tile that can go in that position without introducing seams, until the whole grid is covered.
    - Another kind of stochastic tiling occurs with placing a randomly chosen version of a wallpaper graphic at each grid position, where each version has the same dimensions and the same edges as each other version but can otherwise vary.[^7]

    Both kinds of stochastic tiling can be combined.  [**See example**](https://web.archive.org/web/20160220062702/http://www.cr31.co.uk/stagecast/wang/2edge.html).[^8]

<a id=Sample_Wallpaper_Generation_Code></a>

## Sample Wallpaper Generation Code

This repository has the following code files in Python for generating tiled wallpapers and reading and writing Windows icon files and images in the PNG and Windows bitmap formats: `desktopwallpaper.py`, `imageformat.py`, `randomwp.py`.

This repository also has a directory (`rust/`) with Rust source code for generating a tiled wallpaper.

In addition, the following code in Python is presented as an example of computer code to generate tileable wallpaper patterns. It uses the `desktopwallpaper` and `imageformat` modules and helped generate `circlec.png` and `circlews.png`.

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

Replacing the `contouring` method just given with the one given next leads to a diagonal gradient fill that's tileable:

    def contouring(x,y,z):
       c=abs(x+y)%2.0; return 2-c if c > 1.0 else c

<a id=Other_User_Interface_Graphics></a>

## Other User-Interface Graphics

For discussions on the traditional design of user-interface elements such as buttons, border styles, icons, cursors, and animations, see [**uielements.md**](https://peteroupc.github.io/classic-wallpaper/docs/uielements.html) in this repository.

The page also describes an additional challenge to write computer code (released to the public domain or licensed under the Unlicense) to draw traditional button and border styles.

For discussions on converting traditional icons to vector graphics, see [**pixeltovector.md**](https://peteroupc.github.io/classic-wallpaper/docs/pixeltovector.html) in this repository.

<a id=License></a>

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [**Unlicense**](https://unlicense.org).

<a id=Notes></a>

## Notes

[^1]: Every tileable desktop wallpaper has a pattern that belongs in one of 17 [**_wallpaper groups_**](https://en.wikipedia.org/wiki/Wallpaper_group).  The shape of the pattern is a rectangle in ten of them, a diamond with one corner pointing upward in two of them, and another parallelogram in the remaining five.  Many tileable wallpapers are _seamless_, but not all (consider a pattern of bricks or square floor tiles).<br>For the Macintosh operating system, System 7.5.x and Mac OS 7.6.x, 8.x, and 9.x supported _desktop patterns_ of size up to 128 &times; 128 pixels, Mac OS 8.x and 9.x distinguished between desktop patterns and _desktop pictures_ (of usually larger size and lying above the desktop pattern), and versions earlier than System 7.5 supported only 8-&times;-8-pixel desktop patterns.<br>In Windows version 3.1, Windows 95, and Windows 98, _desktop patterns_ are of size 8x8 pixels and have only two colors (black and the desktop background color), and _desktop wallpaper_ is of arbitrary size and lies above the desktop pattern.

[^2]: See [**_Hero Patterns_**](https://heropatterns.com/) for an example.

[^3]: See [**_colourlovers.com_**](https://www.colourlovers.com/patterns) for examples.

[^4]: Can be generated from `dstripe` using the following ImageMagick command: `magick dstripe.png \( +clone -flop \) +append dzigzag.png`.

[^5]: Can be generated from `truchet2color` using the following ImageMagick command: `magick truchet2color.png \( +clone \( +clone \) -append \( +clone \) +append -crop 50%x50%+1+1 \( -size 1x2 gradient:#FFFFFF-#808080 \) -clut \) -compose Multiply -composite truchet3color.png`.  Here, `#FFFFFF` and `#808080` indicate the two colors white and gray, respectively.

[^6]: Can be generated from `truchet3color` using the following [**ImageMagick**](https://imagemagick.org/) command: `magick truchet3color.png \( +clone -grayscale Rec709Luma \) \( -size 1x256 gradient:#000000-#ff5500 \) -delete 0 -clut  \( -size 1x1 xc:#000000 xc:#808080 xc:#FFFFFF xc:#C0C0C0 xc:#FF0000 xc:#800000 xc:#00FF00 xc:#008000 xc:#0000FF xc:#000080 xc:#FF00FF xc:#800080 xc:#00FFFF xc:#008080 xc:#FFFF00 xc:#808000 +append -write mpr:z +delete \) -dither FloydSteinberg -remap mpr:z truchetff5500vga.png`. This example, which employs a color shift and dither, demonstrates that derivative colored wallpapers with limited colored palettes can easily be generated from black/gray/white wallpapers using non-AI computer programs.

[^7]: This covers the special case of _Truchet tiles_, involving two versions of a graphic where each edge is symmetric and the second version is horizontally or vertically mirrored from the first.

[^8]: For more on stochastic tiling using Wang tiles, see Cohen, M.F., Shade, J., et al., "Wang Tiles for Image and Texture Generation", SIGGRAPH 2003.<br>Tiling techniques that also blend adjacent tiles to hide seams are too complex to describe here. For examples, see Efros and Freeman, "Image Quilting for Texture Synthesis and Transfer", SIGGRAPH 2001; Deliot and Heitz, "Procedural Stochastic Textures by Tiling and Blending", 2019.

[^9]: The 16-color VGA (Video Graphics Array) palette has colors as follows: light gray, that is, (192, 192, 192); or each color component is 0 or 255; or each color component is 0 or 128).
