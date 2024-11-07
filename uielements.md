# Traditional User Interface Graphics

This section discusses aspects of the traditional design of user interface graphics, such as button and border styles, icons, and cursors.

## Logical Display Resolutions

An image can be adapted for displays with logical resolutions that differ from VGA (video graphics array; 96 horizontal and vertical pixels per inch) by scaling the image's width and height.

For example, displays compatible with the IBM Extended Graphics Adapter (EGA) or IBM Color/Graphics Adapter (CGA) have nonsquare pixels (nominally 96 horizontal pixels per inch and 72 or 48 vertical pixels per inch, respectively), so that graphics designed for such displays are often adapted by shrinking the height of images to 3/4 or 1/2 of the original, respectively.  For example, a 300&times;300 image, when adapted for EGA displays, becomes a shrunken 300&times;225 image.

A table of logical resolutions (per inch) for different devices is found in the [OpenType 1.8 specification](https://learn.microsoft.com/en-us/typography/opentype/otspec180/recom#device-resolutions) (the most recent version doesn't have this table).

Logical resolutions also include the special case of _pixel depth_, or a factor to multiply by the logical resolution of 96 horizontal and vertical pixels per inch.  Pixel depths include the factors 1.25 (IBM 8514/a), 2, and 3.  More generally, units similar to pixels may be employed as units of measure for user interface elements, for design purposes to promote right-sized user interfaces.  Examples include [_dialog box units_](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdialogbaseunits) (which depend on the font in which text is rendered) and [_effective pixels_](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/guidance-for-rounded-display-bezels) (which depend on the kind of display, its size, and its resolution).

## Button and Border Styles

Here is a challenge.  Write computer code (released to the public domain or licensed under the Unlicense) to draw the following border and button styles:

- Window border, field border, status field border, and grouping border.
- Buttons and default buttons:
    - Unpressed, pressed, mixed value ("indeterminate" or "third state"), unavailable ("disabled").
- Toolbar buttons:
    - Unpressed, hover, pressed, mixed value, unavailable.
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

### Traditional Button Styles

The following terms are used to describe the traditional appearance of ordinary buttons:

- The _button label_ consists of the text and icons within the button.
- The _button face_ is the inner background of the button.
- _Monochrome appearance_: The button label is drawn using the button shadow color instead of its normal colors, but with transparency and opacity in the label preserved.
- _Embossed appearance_: The button label is drawn&mdash;

    - using the button highlight color instead of its normal colors, then
    - using the button shadow color instead of its normal colors and offset
      1 pixel upward and 1 pixel to the left,

    in each case with transparency and opacity in the label preserved.
- _Unavailable appearance_: The button label has an _embossed appearance_, is drawn
  with 50% opacity, or is masked with a pattern of alternating black
  and white pixels.
- _Mixed value appearance_: The button face is drawn as a dither pattern of the button face color and the button highlight color, or as a color that's a mixture of those two colors.

Traditionally, to draw buttons, default buttons, and toolbar buttons:

- For the pressed button style, the button label is shifted one pixel to the right and one pixel down, compared to the unpressed style.
- The mixed value style tends to be drawn as the unpressed variant, except the button label has a _monochrome appearance_ and the button face has a _mixed value appearance_.
- The unavailable style tends to be drawn as the unpressed variant, except the button label has an _unavailable appearance_.
- For the option-set style, the button tends to be drawn as the normal pressed variant, except:
    - For the unpressed style, the button face has a _mixed value appearance_. [^2]
    - For the unavailable style, the button label has an _unavailable appearance_.

Traditionally, the three dimensional effects of buttons, icons, and other user interface elements are based on a light source shining from the upper left. [^3]

## Icons and Cursors

An icon (a small graphic representing a computer program) should be present in a set of variations in color and dimensions:

- The same icon should be drawn in up to 2, up to 8, up to 16, and up to 256 unique colors, and optionally with 8 bits per color component (also known as 8 bits per color channel or _8 bpc_).  A traditional color choice for 16-color icons is the VGA palette; for 8-color icons, an 8-color palette where each color component is 0 or 255 [^1].
- The same icon should be drawn in the pixel dimensions 16&times;16, 24&times;24, 32&times;32, 48&times;48, and 64&times;64, and may be drawn in other dimensions to account for [logical display resolution](#logical-display-resolutions). (Modern guidelines recommend a 256&times;256 icon as well.  Toolbar icons are traditionally offered in 16&times;16 and 20&times;20.)
- All icons can include transparent pixels, but should have no translucent (semitransparent) pixels except for 8-bpc icons.
- If 16- and 256-color icons are derived from 8-bpc icons, then the 256-color icon should be made from the 8-bpc icon without translucent pixels, and the 16-color icon should be made from the 256-color icon with a "black outline" on the bottom and right edges and with a "dark gray or other dark outline" on the other edges. [^4]

Of these variations, 32&times;32 icons with the VGA palette are traditionally the main icon variation.

Cursors (mouse pointer graphics) can follow the guidelines given above as well, but most cursors are traditionally drawn:

- In a single pixel dimension, generally 32&times;32, except to account for [logical display resolution](#logical-display-resolutions).
- In two colors (black and white) or in grayscale, in either case with optional transparency.  In the two-color case, each shape of the cursor is generally either white with a 1-pixel black outline or vice versa, to make the cursor easy to see over any background.

> **Note:** Icons and cursors with no translucent pixels are often stored in the form of an _XOR mask_ (color mask) and a black-and-white _AND mask_ ("inverted alpha" mask).
>
>  1. First, the output pixels are combined using a bit-by-bit AND operation with the pixels in the AND mask, so that the output pixels become black where the mask is black (in the _opaque_ areas of the icon or cursor) and left unchanged elsewhere.
>  2. Then, the output pixels are combined using a bit-by-bit XOR operation with the pixels in the XOR mask, so that, among other things, the mask is copied to the output where the output is black, and the rest of the output is inverted where the mask is white.
>
>  For icons and cursors with only colored and transparent pixels (and no inverted pixels), the XOR mask should be black wherever the AND mask is white.

## Animations

Although Windows 95 and later versions have an _animation control_ for displaying simple 8-bit-per pixel video files without sound in the AVI format, this control appears to be rarely used.  More usually, in traditional desktop applications, animations are implemented manually, with the frames of the animation either stored as separate image files or arranged in a row or column of a single image file (in either case with transparent pixels marked with a color not used by the animation's frames).  AVI file writing at 20 frames per second is implemented in _desktopwallpaper.py_ under the method `writeavi`.

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [Unlicense](https://unlicense.org).

[^1]: The VGA palette has 16 colors, each of which is one of the following: light gray, that is, (192, 192, 192); or each color component is 0 or 255; or each color component is 0 or 128.  Windows CE also supports icons with the four gray tones of the VGA palette (namely, black, white, light gray, and dark gray or (128, 128, 128)).

[^2]:  In this case, if the button is a toolbar button with a thin border, the button face involved in the mixed-value appearance is surrounded by an additional 1-pixel thick edge drawn in the button face color.

[^3]:  See, for example, _The Windows Interface Guidelines for Software Design_, which applies to Microsoft Windows 95.

[^4]: ["Creating Windows XP Icons"](https://learn.microsoft.com/en-us/previous-versions/ms997636(v=msdn.10)).  Similar advice was also given in _The Microsoft Windows User Experience_, which applies to Windows 98 and Windows 2000.
