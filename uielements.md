# Traditional User Interface Graphics

This page discusses aspects of the traditional design of user interface graphics, such as button and border styles, icons, and mouse pointers.

## Logical Resolutions

A _display mode_ is a way to set up a computer display to show graphics.  One thing associated with a display mode is a _logical resolution_, or the number of pixels per inch the display can logically fit horizontally and vertically.  Some display modes follow, and others are found in a table in the [OpenType 1.8 specification](https://learn.microsoft.com/en-us/typography/opentype/otspec180/recom#device-resolutions) (which the recent version doesn't have):

- VGA's (video graphics array) 640 &times; 480 display mode: 96 horizontal and vertical pixels per inch (pixels are "squares").
- IBM Extended Graphics Adapter's (EGA) 640 &times; 350 color display mode: 96 horizontal and 72 vertical pixels per inch (pixels are not squares).
- IBM Color/Graphics Adapter's (CGA) 640 &times; 200 two-tone display mode: 96 horizontal and 48 vertical pixels per inch (pixels are not squares).

An image can be adapted for display modes with logical resolutions that differ from the VGA mode just given (which is the usual one in the mid-1990s) by scaling the image's width, height, or both.  For example, a 300 &times; 300 image, when adapted for the EGA mode, becomes a shrunken 300 &times; 225 image (the height becomes 72/96 = 3/4 of the original height).

Logical resolutions also include the special case of _pixel density_, or a factor to multiply by the logical resolution of 96 horizontal and vertical pixels per inch.  Pixel densities include the factors 1.25 (IBM 8514/a), 2, and 3.

More generally, units similar to pixels may be employed as units of measure for user interface elements, for design purposes to promote right-sized user interfaces.  Examples include [_dialog box units_](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdialogbaseunits) (which depend on the font in which text is rendered) and [_effective pixels_](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/guidance-for-rounded-display-bezels) (which depend on the kind of display, its size, and its resolution).

## Button and Border Styles

Here is a challenge.  Write computer code (released to the public domain or licensed under the Unlicense) to draw the following ways to style borders and buttons:

- Window border, field border, status field border, and grouping border.[^7]
- Buttons and default buttons:
    - Unpressed, pressed, mixed value ("indeterminate" or "third state"), unavailable ("disabled").
- Toolbar buttons:
    - Unpressed, hover ("hot-tracked"), pressed, mixed value, unavailable.
- Buttons, default buttons, and toolbar buttons in the option-set style:
    - Unpressed, unavailable.
- Checkboxes when set, checkboxes when unset:
    - Unpressed, pressed, mixed value (same for both), unavailable.
- Option buttons ("radio buttons") when set, option buttons when unset, sliders:
    - Unpressed, pressed, unavailable.
- Optionally, other user interface elements (such as scroll bars).

Using only the following colors and with some pixels allowed to be transparent:

- Button highlight color (by default, (255,255,255) or white).
- Button "light" highlight color (by default, (192, 192, 192)).
- Button shadow color (by default, (128, 128, 128)).
- Button dark shadow color (by default, (0,0,0) or black).
- Button face color (by default, (192, 192, 192)).
- Window frame color (black by default).

It is allowed to simulate the appearance of more colors using these six colors by means of dithering.[^6]

The _desktopwallpaper.py_ file contains some example code for border and button drawing. I expect many other variations here, some more subtle than others, but the design should not employ trademarks, should be suitable for all ages, and must not involve the help of artificial intelligence tools.

### Traditional Button Styles

The following terms serve to describe the traditional appearance of ordinary buttons:

- The _button label_ consists of the text and icons within the button.
- The _button face_ is the inner background of the button.
- _Monochrome appearance_: The button label is drawn using the button shadow color instead of its normal colors, but with transparency and opacity in the label preserved.
- _Embossed appearance_: The button label is drawn&mdash;

    - using the button highlight color instead of its normal colors, then
    - using the button shadow color instead of its normal colors and offset 1 pixel upward and 1 pixel to the left,

    in each case with transparency and opacity in the label preserved.
- _Unavailable appearance_: The button label has an _embossed appearance_ [^3], is drawn with 50% opacity, or is drawn such that only every other pixel is rendered in a checkerboard pattern.
- _Mixed value appearance_: The button face is drawn&mdash;

    - such that the button face color and the button highlight color alternate every other pixel in a checkerboard pattern, or
    - as a solid color that's a mixture of the button face color and the button highlight color.

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
- The same icon should be drawn in the pixel dimensions 16 &times; 16, 24 &times; 24, 32 &times; 32, 48 &times; 48, and 64 &times; 64, and may be drawn in other dimensions to account for [logical display resolution](#logical-display-resolutions). [^5]
- All icons can include transparent pixels, but should have no translucent (semitransparent) pixels except for 8-bpc icons.
- Although the 256- and 16-color icons should be specially drawn if feasible, it is allowed to derive such icons from 8-bpc and 256-color icons, respectively, through an automated method.

Of these variations, 32 &times; 32 icons with the VGA palette are traditionally the main icon variation.

Cursors (mouse pointer graphics) can follow the guidelines given above as well, but most cursors are traditionally drawn:

- In a single pixel dimension, generally 32 &times; 32, except to account for [logical display resolution](#logical-display-resolutions).
- In black and white or in grayscale (with colors limited to white, black, and other gray tones), in either case with optional transparency.  In the black-and-white case, each shape of the cursor is generally either white with a 1-pixel black outline or vice versa, to make the cursor easy to see over any background.

> **Note:** Icon formats for OS/2 and Windows allow for icons with _inverted pixels_ (where some existing pixels have their colors inverted), in addition to transparent and translucent (semitransparent) pixels.  Describing these icon formats here is beyond the scope of this page, but see the [`imageformat` module documentation](./imageformat.html).

## Animations

Although Windows 95 and later versions have an _animation control_ for displaying simple 8-bit-per pixel video files without sound in the AVI format, this control appears to be rarely in use.  More usually, in traditional desktop applications, animations are implemented manually, with the frames of the animation either stored as separate image files or arranged in a row or column of a single image file (in either case with transparent pixels marked with a color not present in the animation's frames).  AVI file writing at 20 frames per second is implemented in _desktopwallpaper.py_ under the method `writeavi`.

## Drawing Style

The following points are observed in general in user interface graphics, including icons, cursors, and illustrations, from about 1995 to about 2003, when they are drawn using a limited color palette:

- Curves and straight line segments are drawn unsmoothed and one pixel thick.
- Straight line segments are horizontal, are vertical, or have a slope equal to an integer or 1 divided by an integer.  This can be achieved by drawing the line segment in equally sized steps.
- The three-dimensional (3-D) appearance of graphics (including buttons, window borders, and real-world objects) is based on a light source shining from the upper left.[^3]  Thus, for example, graphics are drawn with a "black outline" on the bottom and right edges and with a "dark gray or other dark outline" on the other edges. [^4]
    - If it is desired to give a real-world object a 3-D look with a limited color palette, that object is generally drawn in an _isometric_ view (rather than straight on).
- Real-world objects depicted in icons and other graphics tend to have an illustrative look with clean lines and curves rather than an abstract, pencil- or brush-drawn, highly realistic, or even _photorealistic_ look.
- In general, in icons, cursors, and digital illustrations limited to the 16-color VGA palette[^1]&mdash;
    - areas are filled with either a solid color in the palette or an alternating checkerboard pattern of two colors (to simulate a color outside the palette), and
    - color gradient fills (smooth transitions from one color to another) and simulations of color gradients are avoided.
- For graphics in a 256-color palette, gradient fills are present but subtle.
- Larger versions of originally 32 &times; 32 icons (for example, the 48 &times; 48 version) tend to appear the same as the original icon but with finer but non-essential detail.

After about 2003, icons, cursors, and illustrations for user interfaces tend to be 8-bpc images and are less interesting to discuss here, as 16- and 256-color versions tend to be derived from those images through _dithering_[^6] or similar techniques.

## Flexible User Interface Graphics

For a high degree of flexibility, new graphical user interface systems should allow for the following:

- Designing icons, cursors, and other user interface elements in the form of vector graphics.
- Having certain outlines of shapes in vector graphics be filled with user-specified system colors, or _system colors_ for short (such as a button face color or button highlight color).
- Designing user interface elements as grayscale images, where the system replaces each gray tone in the image with the corresponding color in a color gradient involving one or more system colors.
- Drawing the same icon, cursor, or graphic&mdash;
    - in multiple sizes, each with a different level of detail (where the system is expected to use a shrinking of the smallest available graphic that's larger than the requested size, if the requested size is not available), even in the case of [vector graphics](https://www.haiku-os.org/docs/userguide/en/applications/icon-o-matic.html), for example, in order to render parts of the graphic more crisply, especially if their [smallest feature would measure less than two pixels](http://rastertragedy.com/RTRCh1.htm), and
    - with a different maximum number of unique colors (such as 2, 8, 16, 256, or 2^24 colors).
- Animation of icons and cursors.

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [Unlicense](https://unlicense.org).

[^1]: The VGA palette has 16 colors, each of which is one of the following: light gray, that is, (192, 192, 192); or each color component is 0 or 255; or each color component is 0 or 128.  Windows CE also supports icons with colors limited to the four gray tones of the VGA palette (namely, black or (0,0,0), white or (255,255,255), light gray, and dark gray or (128, 128, 128)).

[^2]:  In this case, if the button is a toolbar button with a thin border, the button face involved in the mixed-value appearance is surrounded by an additional 1-pixel thick edge drawn in the button face color.

[^3]:  See, for example, _The Windows Interface Guidelines for Software Design_, which applies to Microsoft Windows 95.

[^4]: ["Creating Windows XP Icons"](https://learn.microsoft.com/en-us/previous-versions/ms997636(v=msdn.10)).  Similar advice was also given in _The Microsoft Windows User Experience_, which applies to Windows 98 and Windows 2000.

[^5]: Modern guidelines recommend a 256 &times; 256 icon as well.  Toolbar icons are traditionally offered in 16 &times; 16 and 20 &times; 20.  The standard icon sizes in the OS/2 operating system are 16 &times; 16, 20 &times; 20, 32 &times; 32, and 40 &times; 40 ("Bitmap File Format", in _Presentation Manager Programming Guide and Reference_); sometimes larger icons such as 64 &times; 64 occur.

[^6]: Dithering is the scattering of colors in a limited set to simulate colors outside that set.

[^7]: _Window borders_ are the outer edges of desktop windows.  _Field borders_ are the edges of text boxes.  _Status field borders_ are the edges of inner boxes found in a _status bar_, which can appear on the bottom of some desktop windows.  _Grouping borders_ are the outer edges of areas that bring together several user interface elements, such as checkboxes or option buttons ("radio buttons") with a common purpose; grouping borders also serve as horizontal bars that separate parts of a menu.
