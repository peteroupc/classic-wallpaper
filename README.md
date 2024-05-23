# Classic Tiled Wallpaper Challenge

This repository is intended to hold public-domain wallpaper images and source code for the following challenge.

Given that desktop backgrounds today tend to cover the full computer screen, to employ thousands of colors, and to have a high-definition resolution (1920&times;1080 or larger), rendering tileable backgrounds with limited colors and pixel size ever harder to find, I make the following challenge.

Create a tileable desktop wallpaper image meeting the following requirements.

- The image employs one of the following color options:
    - Two colors only.
        - Such as black and white, which allows for hue shifting to, say, a black-to-red or gray-to-blue palette.
    - Three tints: black, gray (128, 128, 128), white.
        - Allows for hue shifting to, say, a black-to-red palette.
    - Four tints: black, gray (128, 128, 128), light gray (192, 192, 192), white.
        - Allows for hue shifting to, say, a black-to-red palette.
    - 16-color [**canonical CGA palette**](https://int10h.org/blog/2022/06/ibm-5153-color-true-cga-palette/) (each color component is 85 or 255; or each color component is 0 or 170, except (170, 85, 0) instead of (170, 170, 0)).[^3]
    - 16-color VGA palette (light gray; or each color component is 0 or 255; or each color component is 0 or 128).[^3]
    - Up to four colors from the VGA palette.
    - Up to four colors from the canonical CGA palette.
    - Up to eight colors from the VGA palette.
    - 216-color "web safe" palette (each color component is a multiple of 51).[^3]
    - 216-color "web safe" palette plus VGA palette.[^3]
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

<a id=License></a>

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under [**Creative Commons Zero**](https://creativecommons.org/publicdomain/zero/1.0/).

[^3]: Tileable wallpapers employing more than 256 colors are acceptable, though not preferable, if they otherwise meet all requirements here, since they can be reduced to this color palette using known techniques for color dithering.
