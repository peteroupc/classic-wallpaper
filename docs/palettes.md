# Color Palettes for Classic-Style Graphics Projects

This page gathers suggested limited-color palettes that graphics artists (for example, "pixel artists") and game developers can decide to adopt for their projects, when they wish for their creations to have a "classic" or "retro" look (for example, one that is characteristic of the year 1995 or earlier).  Almost all of these palettes have 256 colors or fewer.

The color palettes suggested are as follows.

- Two colors only.
    - Such as black and white, which allows for hue shifting to, say, a black-to-red or gray-to-blue palette.
- 16-color VGA (Video Graphics Array) palette (light gray, that is, (192, 192, 192); or each color component is 0 or 255; or each color component is 0 or 128).
- 216-color "safety palette" (each color component is a multiple of 51).[^1]
- 216-color "safety palette" plus VGA palette.
- A subset of a color palette given earlier, such as:
    - The following gray tones: black (0, 0, 0), gray (128, 128, 128), white (255, 255, 255). (Allows for hue shifting to, say, a black-to-red palette.)
    - The VGA palette's four gray tones: black, gray (128, 128, 128), light gray (192, 192, 192), white. (Allows for hue shifting to, say, a black-to-red palette.)
    - An 8-color palette where each color component is 0 or 255 (a subset of the 16-color VGA palette).
    - The VGA palette without the color (192, 192, 192).[^2]

Any 16-color or 256-color repertoire that was used in a significant volume of application and video-game graphics before the year 2000 is also suggested.[^3]

Additional color palettes suggested are as follows.

- The VGA palette plus the following four colors set by early versions of Windows: (192,220,192), (160,160,164), (255,251,240), (166,202,240).
- The VGA palette plus each "half-and-half mixture"[^4] of any two colors in the palette, for a total of 98 unique colors (each color component is 0, 64, 128, or 192; or each color component is 0, 128, or 255; or each color component is 96 or 160; or each color component is 96 or 224).
- 16-color [**canonical Color/Graphics Adapter (CGA) palette**](https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/) (each color component is 85 or 255; or each color component is 0 or 170, except (170, 85, 0) instead of (170, 170, 0)).
- The canonical CGA palette plus each "half-and-half mixture"[^4] of any two colors in the palette, for a total of 85 unique colors.
- One of the following "color-cube" palettes:
    - A 27-color palette where each color component is 0, 128, or 255.
    - The 64 colors displayable by Enhanced Graphics Adapter (EGA) and "Tandy graphics adapter" monitors (each color component is 0, 85, 170, or 255).
    - A 125-color palette where each color component is 0, 64, 128, 192, or 255.
- An excerpt from larger divisions of the "color cube":
    - Up to 16 colors from those displayable by original Atari ST computers and other 9-bit color displays (each color component is either 255 or a multiple of 32).
    - Up to 32 or 64 colors from those displayable by Amiga computers and other 12-bit color displays (each color component is a multiple of 17).
    - Up to 16 colors from those displayable by 15-bit color displays (each color component is a multiple of 8).
- A palette of the 256 colors used by default in [**VGA 256-color mode**](https://github.com/canidlogic/vgapal).
- A palette of five to 64 gray tones (all color components the same).
- A 255-color palette in which each color component is a multiple of 3 and each color is as follows: All components are the same; or both the green and blue components are 0; or the red component is 255 and the green and blue components are the same.
    - Essentially, the palette is made of two color gradients: one going from black to white, and another going from black to "red" (255,0,0) to white.
    - This palette is proposed to allow for easy "recoloring" of an image based on a so-called _accent color_: the cases just given deal with a mixture of "black" and "white"; a mixture of "black" (0,0,0) and the accent color; and a mixture of "white" (255,255,255) and the accent color.[^5]  An example occurs with "red" and "blue" variants of a playing card back.  For examples, see the `recolor()` and `recolordither()` methods in `desktopwallpaper.py`.
- A palette just described, except (129, 129, 129) is replaced with (128, 128, 128); (129, 0, 0), with (128, 0, 0); and (255, 129, 129), with (255, 128, 128).
- A 255-color palette consisting of a gradient from "black" to "white": (0, 0, 0), (2, 2, 2), (4, 4, 4), ..., (250, 250, 250), (252, 252, 252), (255, 255, 255); and a gradient from "black" to "red": (2, 0, 0), (4, 0, 0), ..., (250, 0, 0), (252, 0, 0), (254, 0, 0), (255, 0, 0).
- A subset of a color palette mentioned earlier in this section.

The following color palettes are within the spirit of this page, but not preferred:

- Up to 16 colors from those displayable by 16-bit color displays (each red and blue component is a multiple of 8; each green, a multiple of 4).
- Up to 16 colors from those displayable by pure VGA monitors (each color component is a multiple of 4).
- A palette of 236 gray tones (all color components the same).
- A palette of 256 gray tones (all color components the same).
- A color palette of up to 256 colors listed in the [**_Lospec_ palette list**](https://lospec.com/palette-list).
- A 765-color palette in which each color is as follows: All components are the same; or both the green and blue components are 0; or the red component is 255 and the green and blue components are the same.
    - Essentially, the palette is made of two color gradients: one going from black to white, and another going from black to "red" (255,0,0) to white.

> **Notes:**
>
> 1. The [**_palettes_ directory**](https://github.com/peteroupc/classic-wallpaper/tree/main/palettes) of this repository hosts palette files for many of the color combinations described earlier.  The palette files are designed for use in software programs for drawing, especially those devoted to pixel art.
> 2. The palette can have one or more sequences of colors that smoothly range from one color to another, to aid in achieving gradient fills or other specialized shading techniques in a _ramp color model_.  For example, a palette can have ten colors (indexed from 0 through 9) that range from black to green, and ten additional colors (indexed from 10 through 19) that range from black to red.[^5]

<a id=License></a>

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [**Unlicense**](https://unlicense.org).

<a id=Notes></a>

## Notes

[^1]: The "safety palette", also known as the "Web safe" colors, consists of 216 colors that are uniformly spaced in the red&ndash;green&ndash;blue color cube.  Robert Hess's article "[**The Safety Palette**](https://learn.microsoft.com/en-us/previous-versions/ms976419(v=msdn.10))", 1996, described the advantage that images that use only colors in this palette won't dither when displayed by Web browsers on displays that can show up to 256 colors at once. (See also [**Wikipedia**](http://en.wikipedia.org/wiki/Web_colors). Dithering is the scattering of colors in a limited set to simulate colors outside that set.)  When the "safety palette" forms part of a 256-color repertoire, as it usually does, 40 slots are left that can be filled with additional colors, and as Hess mentions, graphics designers have no control over what these additional colors are. Usually these additional colors include the four Windows-specific colors plus the eight VGA palette colors not already in the "safety palette".  For Java's `BufferedImage.TYPE_BYTE_INDEXED`, these 40 colors are gray tones not already in the "safety palette".

[^2]: The Enhanced Graphics Adapter (EGA) video driver for Windows version 3.1 supports 16 logical colors, but only 15 "physical" colors: the VGA palette is used, except the logical color (192, 192, 192) is missing and often replaced with a dithered mixture of dark gray and "white" (which is one possible way to adapt images colored using the VGA palette to the EGA driver).

[^3]: In the Windows version 3.1 system palette, "the low-intensity system color values for the VGA [driver] are different from those for the [IBM] 8514 [video driver]" (Windows 3.1 SDK, _Programmer's Reference_ Volume 1, section 23.2.2), but how exactly they differ is not set forth in any article, as far as I am aware.

[^4]: A "half-and-half mixture" of two colors is found by averaging their three components then rounding each average up to the nearest integer.

[^5]: See also:<br>Chapter 4 of Woo, Mason, et al., _OpenGL Programming Guide: The Official Guide to Learning OpenGL, Version 1.1_, second edition, Addison Wesley Longman, 1997. ISBN 0-201-46138-2.<br>D. Rogerson, "OpenGL IV: Color Index Mode" (Jan. 19, 1995).
