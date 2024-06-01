# Classic Tiled Wallpaper Challenge

This repository is intended to hold public-domain wallpaper images and source code for the following challenge.

Given that desktop backgrounds today tend to cover the full computer screen, to employ thousands of colors, and to have a high-definition resolution (1920&times;1080 or larger), rendering tileable backgrounds with limited colors and pixel size ever harder to find, I make the following challenge.

Create a tileable desktop wallpaper image [^1] meeting the following requirements.

- The image employs one of the following color options:
    - Two colors only.
        - Such as black and white, which allows for hue shifting to, say, a black-to-red or gray-to-blue palette.
    - Three tints: black, gray (128, 128, 128), white.
        - Allows for hue shifting to, say, a black-to-red palette.
    - Four tints: black, gray (128, 128, 128), light gray (192, 192, 192), white.
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
    - Not preferred: Up to 16 colors from those displayable by pure VGA monitors (each color component modulo 4 is 0).
    - Not preferred: 65- to 236-color grayscale palette (all color components the same).
    - Not preferred: 237- to 256-color grayscale palette (all color components the same).
- The image employs one of the following pixel dimension options:
    - Preferred: 8&times;8, 16&times;16, 32&times;32, 64&times;64, 64&times;32, 32&times;64, 96&times;96, 128&times;128, 256&times;256.
    - Not preferred: 320&times;240, 320&times;200.
    - Not preferred: Custom size up to 96&times;96.
    - Not preferred: Custom size up to 256&times;256.
- The image is preferably abstract, should not employ trademarks, and is suitable for all ages.
- The image is in the public domain or licensed under Creative Commons Zero or Attribution or, less preferably, another open-source license.
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
| truchetff5500vga.png | peteroupc | VGA palette | 32x32 | CC0 [^4] |
| boxes.png | peteroupc | VGA palette | 128x128 | CC0 |

<a id=License></a>

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under [**Creative Commons Zero**](https://creativecommons.org/publicdomain/zero/1.0/).

[^1]: Every tileable desktop wallpaper has a pattern that belongs in one of 17 [_wallpaper groups_](https://en.wikipedia.org/wiki/Wallpaper_group).  The shape of the pattern is a rectangle in ten of them, a diamond with one corner pointing upward in two of them, and another parallelogram in the remaining five.

[^2]: Generated from `dstripe` using the following ImageMagick command: `convert dstripe.png \( +clone -flop \) +append dzigzag.png`.

[^3]: Tileable wallpapers employing more than 256 colors are acceptable, though not preferable, if they otherwise meet all requirements here, since they can be reduced to this color palette using known techniques for color dithering.

[^4]: Generated from `truchet3color` using the following [ImageMagick](https://imagemagick.org/) command: `convert truchet3color.png \( +clone -grayscale Rec709Luma \) \( -size 1x256 gradient:#000000-#ff5500 \) -delete 0 -clut  \( -size 1x1 xc:#000000 xc:#808080 xc:#FFFFFF xc:#C0C0C0 xc:#FF0000 xc:#800000 xc:#00FF00 xc:#008000 xc:#0000FF xc:#000080 xc:#FF00FF xc:#800080 xc:#00FFFF xc:#008080 xc:#FFFF00 xc:#808000 +append -write mpr:z +delete \) -dither FloydSteinberg -remap mpr:z truchetff5500vga.png`. This example, which employs a color shift and dither, demonstrates that derivative colored wallpapers with limited colored palettes can easily be generated from black/gray/white wallpapers using non-AI computer programs.

[^5]: Can be generated from `truchet2color` using the following ImageMagick command: `convert truchet2color.png \( +clone \( +clone \) -append \( +clone \) +append -crop 50%x50%+1+1 \( -size 1x2 gradient:#FFFFFF-#808080 \) -clut \) -compose Multiply -composite truchet3color.png`.  Here, `#FFFFFF-808080` indicates the two colors white and gray, respectively.

[^6]: A "half-and-half mixture" of two colors is found by averaging their three components then rounding each up to the nearest integer.
