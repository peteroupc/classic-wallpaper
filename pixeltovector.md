# Converting Pixel Images to Vector Graphics

This page concerns ways to go about remaking traditional user interface icons, which have the form of pixel images, as vector graphics.  The icons concerned here tend to have the following properties:

- The icon's dimensions in pixels are usually 32 &times; 32, but can range from 15 &times; 15 to 64 &times; 64.
- The icon is drawn in a limited color palette (no more than 256 colors), ordinarily 16 colors or fewer.
- The icon may have transparent pixels, but no semitransparent (translucent) pixels.

The output should be a vector graphic with the following properties:

- When rendered without antialiasing or scaling, the vector graphic should closely match the pixel image.
- The graphic is reasonably scalable, with horizontal and vertical scaling factors each from 50% through 300%.   The low end is given to accommodate displays with nonsquare pixels; the high end, displays with high pixel density (pixels per inch).
- Single-pixel, single-color line segments or curves should be rendered as line or curve commands.
- Simple polygons of a single color in the input image should be rendered as such in the vector graphic.
- Size blowup compared to the pixel image should be reasonable (for example, no more than a 2-times blowup on average).  Notably, if the input image depicts a single-color polygon, the vector graphic should be a single-color polygon which often consumes less memory than the pixel image.
- Optional: Contours recognized as arcs, ellipses, or circles should be rendered as such.
- Optional: The algorithm should recognize half-tone dithered areas as solid-colored areas.

In addition, the algorithm:

- Should not involve neural networks.
- Should not be covered by patents or patent applications.

Algorithms that convert pixel images to vector graphics in the form of unions of rectangles that cover the input's pixels (for example, [_png2svg_](https://github.com/xyproto/png2svg)) are not within the scope of this document.

There is an algorithm by Kopf and Lischinski ("Depixelizing Pixel Art", _ACM Transactions on Graphics_ 30(4), 2011) that tackles the task of generating vector graphics from pixel-art images, including those of the kind at issue here.  However:

1. The algorithm generates curved contours even if they originate from single-pixel line segments or curves.
2. The algorithm doesn't generate polygons even in cases where that shape is best.
3. The algorithm runs slowly: tens of seconds to generate a vector graphic from a 64-bit icon.
4. The resulting vector graphic does not have a reasonable size compared to the input pixel image.
5. I don't know whether the algorithm is covered by any pending or active patents.

Potrace version 1.16 (2019) likewise suffers from points 1 and 2, and also supports only black-and-white opaque pixel images and not color ones.

## Example

Take the following pixel image:

![Diamond pixel image](diamond.png)

The desired vector graphic should have the following commands in this order:

1. Polygon, filled with white, connecting the points (1, 15), (15, 1), (29, 15), (15, 29).
2. 1-pixel-thick polyline (sequence of line segments), colored black, connecting the points in the foregoing polygon.  Alternatively, that polygon is stroked with a 1-pixel-thick black outline in addition to being filled.

![Diamond vector graphic](diamond.svg)

## License

Any copyright to this page is released to the Public Domain.  In case this is not possible, this page is also licensed under the [Unlicense](https://unlicense.org).
