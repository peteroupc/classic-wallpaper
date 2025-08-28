# Traditional User-Interface Graphics

This page discusses aspects of the traditional design of user-interface graphics, such as button and border styles, icons, and mouse pointers.

## Logical Resolutions

A _display mode_ is a way to set up a computer display to show graphics.  Some display modes follow:

- VGA's (IBM Video Graphics Array) 640 &times; 480 display mode: A _logical resolution_ of 96 horizontal and vertical pixels per inch (pixels are "squares").
- IBM Extended Graphics Adapter's (EGA) 640 &times; 350 color display mode: 96 horizontal and 72 vertical pixels per inch (pixels are not squares).
- IBM Color/Graphics Adapter's (CGA) 640 &times; 200 two-tone display mode: 96 horizontal and 48 vertical pixels per inch (pixels are not squares).

An image can be adapted for display modes with logical resolutions that differ from the VGA mode just given (which is the usual one in the mid-1990s) by scaling the image's width, height, or both.  For example, a 300 &times; 300 image, when adapted for the EGA mode, becomes a shrunken 300 &times; 225 image (the height becomes 72/96 = 3/4 of the original height).

Logical resolutions also cover the special case of _pixel density_ (such as 2 to 1).  Pixel density is determined by a scale factor, or a number to multiply by the logical resolution of 96 horizontal and vertical pixels per inch, such as 1.25 (for the pixel density 1.25 to 1; IBM 8514/a), 2, and 3.

More generally, units similar to pixels may be employed as units of measure for user-interface elements, for design purposes to promote right-sized user interfaces.  Examples include [_dialog box units_](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdialogbaseunits) (which depend on the font in which text is rendered) and [_effective pixels_](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/guidance-for-rounded-display-bezels) (which depend on the kind of display, its size, and its resolution).

## Button and Border Styles

Here is a challenge.  Write computer code (released to the public domain or licensed under the Unlicense) to draw the following ways to style borders and buttons:

- Window border, text box border, status field border, and grouping border.[^7]
- The following elements in the unpressed, pressed, and unavailable ("disabled" or "inactive") appearances:
    - Buttons in normal, "option-set", and mixed-value ("indeterminate" or "third state") states.
    - Buttons selected by default in normal, "option-set", and mixed-value states.
    - Toolbar buttons in normal, "option-set", and mixed-value states.
    - Checkboxes when unset, when set, and in mixed-value state.
    - Option buttons ("radio buttons") when unset, option buttons when set, sliders.
- Toolbar buttons in normal, mixed-value, and "option-set" states:  Hover style.
- Optionally, other user-interface elements (such as scroll bars and toggle switches).

Using only the following colors and with some pixels allowed to be transparent:

- Button highlight color (by default, (255,255,255) or white).
- Button "light" highlight color (by default, (192, 192, 192)).
- Button shadow color (by default, (128, 128, 128)).
- Button dark shadow color (by default, (0,0,0) or black).
- Button face color (by default, (192, 192, 192)).
- Window frame color (black by default).

It is allowed to simulate the appearance of more colors using these six colors by means of dithering.[^6]

The _desktopwallpaper.py_ file has some example code for border and button drawing. I expect many other variations here, some more subtle than others, but the design should not employ trademarks, should be suitable for all ages, and must not involve the help of artificial-intelligence tools.

### Traditional Button Styles

The following appearances are traditionally seen in ordinary buttons:

- _Monochrome appearance_: The button's text and icons are drawn using the button shadow color instead of its normal colors, but with transparency and opacity in the label preserved.
- _Embossed appearance_: The button's text and icons are drawn&mdash;

    - using the button highlight color instead of its normal colors, then
    - using the button shadow color instead of its normal colors and offset 1 pixel upward and 1 pixel to the left,

    in each case with transparency and opacity in the label preserved.
- _Unavailable appearance_: The button's text and icons have an _embossed appearance_ [^3], are drawn with 50% opacity, or are drawn such that only every other pixel is rendered in a checkerboard pattern.
- _Mixed appearance_: The button's inner background is drawn&mdash;

    - such that the button face color and the button highlight color alternate every other pixel in a checkerboard pattern, or
    - as a solid color that's a mixture of the button face color and the button highlight color.

The following is typical in buttons found in Windows versions 3.0 and 3.1 [^3a], Windows 95 [^3], and applications for these systems:

- For the pressed button style, the button's text and icons are shifted one pixel to the right and one pixel down, compared to the unpressed style.

The following ways to draw buttons, default buttons, and toolbar buttons are typical in Windows 95 [^3] and applications for it:

- The mixed value style tends to be drawn as the unpressed variant, except the button's text and icons have a _monochrome appearance_ and its inner background has a _mixed appearance_.
- The unavailable style tends to be drawn as the unpressed variant, except the button's text and icons have an _unavailable appearance_.
- For the option-set style, the button tends to be drawn as the normal pressed variant, except:
    - For the unpressed style, its inner background has a _mixed appearance_. [^2]
    - For the unavailable style, its text and icons have an _unavailable appearance_.

In Presentation Manager, to render a button in the unavailable style, the entire button (including text, icons, and borders) is drawn such that only every other pixel is rendered in a checkerboard pattern.

Traditionally, the three dimensional effects of buttons, icons, and other user-interface elements are based on a light source shining from the upper left. [^3]

## Icons and Cursors

An icon (a small graphic representing a computer program) should come in a set of variations in color and dimensions:

- The same icon should be drawn in up to 2, up to 16, and up to 256 unique colors, and optionally with 8 bits per color component (also known as 8 bits per color channel or _8 bpc_).  A traditional color choice for 16-color icons is the VGA palette; for 8-color icons, an 8-color palette where each color component is 0 or 255 [^1].
- The same icon should be drawn in the pixel dimensions 16 &times; 16, 24 &times; 24, 32 &times; 32, 48 &times; 48, and 64 &times; 64, and may be drawn in other dimensions to account for [logical display resolution](#logical-resolutions). [^5]
- All icons can include transparent pixels, but should have no translucent (semitransparent) pixels except for 8-bpc icons.
- Although the 256- and 16-color icons should be specially drawn if feasible, it is allowed to derive those icons from 8-bpc and 256-color icons, respectively, through an automated method.

Traditionally, 32 &times; 32 icons with the VGA palette are the most common variation.

Cursors (mouse pointer graphics) can follow the guidelines given earlier as well, but most cursors are traditionally drawn:

- In a single width and height, generally 32 &times; 32 pixels, except to account for [logical display resolution](#logical-resolutions).
- In black and white or in grayscale (with colors limited to white, black, and other gray tones), in either case with optional transparency.  In the black-and-white case, each shape of the cursor is generally either white with a 1-pixel black outline or vice versa, to make the cursor easy to see over any background.

> **Note:** Icon formats for OS/2 Presentation Manager and Windows allow for icons and cursors with _inverted pixels_ (where some existing pixels have their colors inverted), in addition to transparent and translucent (semitransparent) pixels.  Describing these icon formats here is beyond the scope of this page, but see the [`imageformat` module documentation](./imageformat.html).

## Animations

Although Windows 95 and later versions have an _animation control_ for displaying simple video files without sound that are limited to 256 colors, this control appears to be rarely used.  More usually, traditional desktop applications don't store an  animation as a video file; rather, its frames are either stored as separate image files or arranged in a row or column of a single image file (in either case with transparent pixels marked with a color not present in the animation's frames). [^8]  The source code file _desktopwallpaper.py_ has a method, named `writeavi`, to write video files.

## Drawing Style

In general, when user-interface graphics, including icons, cursors, and illustrations, from about 1995 to about 2003 are drawn using a limited color palette, the following is observed:

- Curves and straight line segments are drawn unsmoothed and one pixel thick.
- Straight line segments are horizontal, are vertical, or have a slope equal to an integer or 1 divided by an integer.  This can be achieved by drawing the line segment in equally sized steps.
- The three-dimensional (3-D) appearance of buttons and other objects in graphics is based on a light source shining from the upper left.[^3]  Thus, for example, graphics are drawn with a "black outline" on the bottom and right edges and with a "dark gray or other dark outline" on the other edges. [^4]
    - If a real-world object should have a 3-D look with a limited number of colors, that object is drawn in an _isometric_ view (rather than straight on).[^9]
- Real-world objects depicted in user-interface graphics have an illustrative look with clean lines and curves rather than an abstract, pencil- or brush-drawn, highly realistic, or even _photorealistic_ look. [^10]
- For graphics limited to the 16-color VGA palette[^1]:
    - Areas are filled with either a solid color in the palette or an alternating checkerboard pattern of two colors (to simulate a color outside the palette).
    - Color gradient fills (smooth transitions from one color to another) and simulations of color gradients are rare (and then especially in backgrounds of illustrations), if not avoided.
- For graphics in a 256-color palette, gradient fills are present but subtle.
- Larger versions of originally 32 &times; 32 icons (for example, the 48 &times; 48 version) appear the same as the original icon but with finer but nonessential detail.

After about 2003, user-interface graphics tend to be 8-bpc images and are less interesting to discuss here, as 16- and 256-color versions are often made from those images through _dithering_[^6] or similar techniques.

From about 1990 to about 1997, most user-interface text was rendered in a solid color.  In fancier displays of text, a "shadowed" text look was often achieved using multiple shifted renderings of the text in a single color (for example, from one pixel upward and leftward to three pixels downward and rightward) followed by an unshifted rendering in the base color or pattern.[^11]  But new applications should avoid having text in icons, cursors, and pixel images.

## Flexible User Interface Graphics

For a high degree of flexibility, new graphical user interface systems should allow for the following:

- Designing icons, cursors, and other user-interface elements in the form of [vector graphics](https://github.com/peteroupc/classic-wallpaper/blob/main/pixeltovector.md).
- Having certain outlines of shapes in vector graphics be filled with system colors, the values of which are user-defined (such as a button face color or button highlight color).
- Designing user-interface elements as grayscale images, where the system replaces each gray tone in the image with the corresponding color in a color gradient involving one or more system colors.
- Drawing the same icon, cursor, or graphic&mdash;
    - in multiple sizes, each with a different level of detail (where the system is expected to use a shrinking of the smallest available graphic that's larger than the requested size, if the requested size is not available), even in the case of [vector graphics](https://www.haiku-os.org/docs/userguide/en/applications/icon-o-matic.html) [^12], and
    - with a different maximum number of unique colors (such as 2, 8, 16, 256, or 2^24 colors).
- Animation of icons and cursors.

## Relevant Works

The following books and other works discuss design matters on traditional user interfaces:

- _The Microsoft Windows User Experience_, which applies to Windows 98 and Windows 2000
- _The Windows Interface Guidelines for Software Design_, which applies to Windows 95.
- "Wizard 97 Specifications and Development FAQ" (1999), part of the Windows Platform SDK, April 2000.
- _Common User Access: Basic Interface Design Guide_ and _Common User Access: Advanced Interface Design Guide_, which apply to Windows version 3.0 and Presentation Manager.
- _The Windows Interface: An Application Design Guide_, which applies to Windows version 3.1.
- Matt Saettler, "Graphics Design and Optimization", Multimedia Technical Note (Microsoft), 1992.
- W. Cherry and K. Marsh, "Adding 3-D Effects to Controls", Technical Note (Microsoft), 1992-1993.
- Kyle Marsh, "Creating a Toolbar", Technical Note (Microsoft), December 31, 1992.
- J. Osborne, D. Thomas, "Working in the Third Dimension", _develop_ (Apple), September 1993, describes the authors' suggestions for the three-dimensional appearance of buttons and certain other interface elements compatible with MacOS System 7.
- ["Creating Windows XP Icons"](https://learn.microsoft.com/en-us/previous-versions/ms997636(v=msdn.10)) (Microsoft Learn), July 2001.

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [Unlicense](https://unlicense.org).

## Notes

[^1]: The VGA palette has 16 colors, each of which is one of the following: light gray, that is, (192, 192, 192); or each color component is 0 or 255; or each color component is 0 or 128.  Windows CE also supports icons with colors limited to the four gray tones of the VGA palette (namely, black or (0,0,0), white or (255,255,255), light gray, and dark gray or (128, 128, 128)).

[^2]:  In this case, if the button is a toolbar button with a thin border, the button's inner background involved in the mixed-value appearance is surrounded by an additional 1-pixel thick edge drawn in the button face color.

[^3]:  See, for example, _The Windows Interface Guidelines for Software Design_.

[^3a]:  Buttons possessed a 3-D effect in Windows versions 3.0 and 3.1 by default, but not other interface elements.  The article "Adding 3-D Effects to Controls" describes a library for these versions that give 3-D effects to more places in an application.

[^4]: See "Creating Windows XP Icons".  Similar advice was also given in _The Microsoft Windows User Experience_. <br>Before 1995 the icon outline tended to be black on all edges. And, before 1992, Windows version 3.0 icons tended to be drawn over a _drop shadow_, more specifically a dark gray silhouette of the icon, which silhouette is offset down and to the right by two pixels.

[^5]: Modern guidelines recommend a 256 &times; 256 icon as well.  Toolbar icons are traditionally offered in 16 &times; 16 and 20 &times; 20.  The standard icon sizes in OS/2 Presentation Manager are 16 &times; 16, 20 &times; 20, 32 &times; 32, and 40 &times; 40 ("Bitmap File Format", in _Presentation Manager Programming Guide and Reference_); sometimes larger icons such as 64 &times; 64 occur.

[^6]: _Dithering_ is the scattering of colors in a limited set to simulate colors outside that set.

[^7]: _Window borders_ are the outer edges of desktop windows.  Text box borders are also known as "field borders".  _Status field borders_ are the edges of inner boxes found in a _status bar_, which can appear on the bottom of some desktop windows.  _Grouping borders_ are the outer edges of areas that bring together several user-interface elements, such as checkboxes or option buttons ("radio buttons") with a common purpose; grouping borders also serve as horizontal bars that separate parts of a menu.

[^8]: _The Microsoft Windows User Experience_ considers an animation to be fluid only if it runs at 16 or more frames per second.

[^9]: This is evident in the graphics (also known as _watermarks_) of Windows 95's wizards, which are drawn in a teal background (color (0,128,128)) and show one or more computing devices in a three-dimensional, often rectangular appearance, and where, although there is internal shadowing, no shadow is cast on the teal background.  But computer monitors may still be drawn straight on in order to accentuate what the monitor is showing.

[^10]: Adventure games developed by Sierra On-Line in the early 1990s are well known to employ essentially one-pixel-thick lines and flood fills in their illustrations.  (A _flood fill_ is a way to fill an area of pixels that is surrounded by pixels of other colors.) Windows 95 wizard watermarks are also of this style, essentially, except that the use of black outlines, as opposed to outlines of other colors, is rarer and less systematic.

[^11]: For example, see the discussion on buttons in the _RIPscrip_ specification developed by TeleGrafix in 1992 and 1993. This specification was designed for building graphical user interfaces for online bulletin board systems under the EGA display mode.

[^12]: Multiple sizes and vector versions of a graphic are useful for several reasons, including: (1) to accommodate different display modes and pixel densities; (2) to render parts of the graphic more crisply, especially if their [smallest feature would measure less than two pixels](http://rastertragedy.com/RTRCh1.htm).  They are useful for toolbar icons, for example, especially nowadays where the icon style is a single-color filled outline akin to a typographic symbol.  Indeed, even 16-&times;-15-pixel bitmaps often used as toolbar icons are, in many cases, ultimately vector graphics consisting of polygons and one-pixel-thick line segments.
