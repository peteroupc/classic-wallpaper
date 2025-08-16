# Converting Pixel Images to Vector Graphics

This page concerns ways to go about remaking traditional user interface icons, which have the form of pixel images, into vector graphics.  The icons concerned here tend to have the following properties:

- The icon's dimensions in pixels are 32 &times; 32, but can range from 15 &times; 15 to 64 &times; 64.
- The icon is drawn in a limited color palette (no more than 256 colors), ordinarily 16 colors.
- The icon may have transparent pixels, but no semitransparent (translucent) pixels.

The output should be a vector graphic with the following properties:

- When rendered without antialiasing or scaling, the vector graphic should closely match the pixel image.
- Single-pixel, single-color line segments or curves should be rendered as line or curve commands.
- Simple polygons of a single color in the input image should be rendered as such in the vector graphic.
- Size blowup compared to the pixel image should be reasonable (for example, no more than a double blowup on average).  Notably, if the input image depicts a single-color polygon, the vector graphic should be a single-color polygon which is often much smaller than the pixel image.
- Optional: Contours recognized as arcs, ellipses, or circles should be rendered as such.
- Optional: The algorithm should recognize half-tone dithered areas as solid-colored areas.

There is an algorithm by Kopf and Lischinski ("Depixelizing Pixel Art", _ACM Transactions on Graphics_ 30(4), 2011) that tackles the task of generating vector graphics from pixel-art images, including those of the kind at issue here.  However:

- The algorithm generates smooth contours even if they originate from single-pixel line segments or curves.
- The algorithm doesn't generate polygons even in cases where that shape is best.
- The algorithm runs slowly: tens of seconds to generate a vector graphic from a 64-bit icon.
- The resulting vector graphic does not have a reasonable size compared to the input pixel image.
- I don't know whether the algorithm is covered by any pending or active patents.

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [Unlicense](https://unlicense.org).
