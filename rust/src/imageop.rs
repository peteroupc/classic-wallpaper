use crate::basicrgbimage::*;
use std::cmp::max;
use std::cmp::min;

// Minimum of a 32-bit signed integer
// and a 32-bit unsigned integer,
// expressed as a 32-bit signed integer
fn _min32(a: i32, b: u32) -> i32 {
    if a < 0 {
        // If negative, return 'a', since no
        // u32 value can be negative
        a
    } else {
        min(a.wrapping_abs() as u32, b) as i32
    }
}

// Modulus of a 32-bit signed integer
// and a 32-bit unsigned integer
fn _mod32(a: i32, b: u32) -> u32 {
    if a < 0 {
        let au32: u32 = a.wrapping_abs() as u32;
        let ret: u32 = au32 % b;
        if ret != 0 {
            b - ret
        } else {
            ret
        }
    } else {
        let au32: u32 = a.try_into().unwrap();
        au32 % b
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_min32() {
        assert_eq!(_min32(-1, 0), -1);
        assert_eq!(_min32(0, 1), 0);
        assert_eq!(_min32(-2, u32::MAX), -2);
        assert_eq!(_min32(i32::MAX, 0), 0);
        assert_eq!(_min32(i32::MAX, u32::MAX), i32::MAX);
        assert_eq!(_min32(i32::MIN, 0), i32::MIN);
        assert_eq!(_min32(i32::MIN, u32::MAX), i32::MIN);
    }
    #[test]
    fn test_mod32() {
        assert_eq!(_mod32(-5, 4), 3);
        assert_eq!(_mod32(-4, 4), 0);
        assert_eq!(_mod32(-3, 4), 1);
        assert_eq!(_mod32(-2, 4), 2);
        assert_eq!(_mod32(-1, 4), 3);
        assert_eq!(_mod32(0, 4), 0);
        assert_eq!(_mod32(1, 4), 1);
        assert_eq!(_mod32(2, 4), 2);
        assert_eq!(_mod32(3, 4), 3);
        assert_eq!(_mod32(4, 4), 0);
        assert_eq!(_mod32(5, 4), 1);
    }
}

pub fn classiccolors() -> Vec<[u8; 3]> {
    vec![
        [0, 0, 0],
        [128, 128, 128],
        [192, 192, 192],
        [255, 0, 0],
        [128, 0, 0],
        [0, 255, 0],
        [0, 128, 0],
        [0, 0, 255],
        [0, 0, 128],
        [255, 0, 255],
        [128, 0, 128],
        [0, 255, 255],
        [0, 128, 128],
        [255, 255, 0],
        [128, 128, 0],
        [255, 255, 255],
    ]
}

static DITHER_MATRIX: [u8; 64] = [
    // Bayer 8 &times; 8 ordered dither matrix
    0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26, 12, 44, 4, 36, 14, 46, 6, 38, 60,
    28, 52, 20, 62, 30, 54, 22, 3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25, 15,
    47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21,
];


/**
 * Does an ordered dither of the given image to use only colors in the "safety palette", also known as the
 * "Web safe" palette.  The "safety palette" consists of 216 colors that are
 * uniformly spaced in the red&ndash;green&ndash;blue color cube.  Robert Hess's
 * article "[The Safety Palette](https://learn.microsoft.com/en-us/previous-versions/ms976419(v=msdn.10))",
 * 1996, described the advantage that images that use only colors in this palette
 * won't dither when displayed by Web browsers on displays that can show up to 256
 * colors at once. (See also [**Wikipedia**](http://en.wikipedia.org/wiki/Web_colors).
 * Dithering is the scattering of colors in a limited set to simulate colors
 * outside that set.)
 * 'include_vga' preserves colors in the VGA palette that are not already in the safety palette,
 * that is, the colors (0xc0, 0xc0, 0xc0), (0x80, 0, 0), (0, 0x80, 0), (0x80, 0x80, 0), 
 * (0, 0, 0x80), (0x80, 0, 0x80), (0, 0x80, 0x80), (0x80, 0x80, 0x80).
 */
pub fn websafedither<T: BasicRgbImage>(image: &mut T, include_vga: bool) -> &mut T {
    for y in 0..image.height() {
        for x in 0..image.width() {
            let rc = image.get_pixel(x, y);
            let mut rr: u32 = rc[0].into();
            let mut rg: u32 = rc[1].into();
            let mut rb: u32 = rc[2].into();
            if include_vga {
                // Leave unchanged any colors in the VGA palette
                // but not in the "safety palette".
                let c0 = rr;
                if c0 == 0xC0 {
                    if rg == 0xC0 && rb == 0xC0 {
                        continue;
                    }
                } else if (c0 == 0x80 || c0 == 0)
                    && (rg == 0 || rg == 0x80)
                    && (rb == 0 || rb == 0x80)
                {
                    continue;
                }
            }
            let mut cm: u32 = rr % 51;
            let bdither: u32 = DITHER_MATRIX[((y & 7) * 8 + (x & 7)) as usize].into();
            if bdither < (cm * 64) / 51 {
                rr = (rr - cm) + 51;
            } else {
                rr -= cm;
            }
            cm = rg % 51;
            if bdither < (cm * 64) / 51 {
                rg = (rg - cm) + 51;
            } else {
                rg -= cm;
            }
            cm = rb % 51;
            if bdither < (cm * 64) / 51 {
                rb = (rb - cm) + 51;
            } else {
                rb -= cm;
            }
            image.put_pixel(x, y, [rr as u8, rg as u8, rb as u8]);
        }
    }
    image
}

fn nearestrgb3(palette: &[[u8; 3]], r: u8, g: u8, b: u8) -> usize {
    let mut best: usize = 0;
    let mut ret: usize = 0;
    for (i, color) in palette.iter().enumerate() {
        let dr: i32 = (r as i32) - (color[0] as i32);
        let dg: i32 = (g as i32) - (color[1] as i32);
        let db: i32 = (b as i32) - (color[2] as i32);
        let dist: usize = (dr * dr + dg * dg + db * db).try_into().unwrap();
        if i == 0 || dist < best {
            best = dist;
            ret = i;
            if dist == 0 {
                break;
            }
        }
    }
    ret
}

pub fn floyd_steinberg_dither<T: BasicRgbImage>(image: &mut T, palette: &[[u8; 3]]) {
    if image.width() == 0 || image.height() == 0 {
        return;
    }
    let mut err = vec![0; (image.width() * 6).try_into().unwrap()];
    let rerr1: usize = 0;
    let uswidth: usize = image.width() as usize;
    let rerr2 = rerr1 + uswidth;
    let gerr1 = rerr2 + uswidth;
    let gerr2 = gerr1 + uswidth;
    let berr1 = gerr2 + uswidth;
    let berr2 = berr1 + uswidth;
    for j in 0..image.height() {
        for i in 0..image.width() {
            let cr = image.get_pixel(i, j);
            let ui = i as usize;
            err[rerr1 + ui] = err[rerr2 + ui] + (cr[0] as i32);
            err[gerr1 + ui] = err[gerr2 + ui] + (cr[1] as i32);
            err[berr1 + ui] = err[berr2 + ui] + (cr[2] as i32);
            err[rerr2 + ui] = 0;
            err[gerr2 + ui] = 0;
            err[berr2 + ui] = 0;
        }
        err[rerr1] = err[rerr1].clamp(0, 255);
        err[gerr1] = err[gerr1].clamp(0, 255);
        err[berr1] = err[berr1].clamp(0, 255);
        let mut idx = nearestrgb3(
            palette,
            err[rerr1] as u8,
            err[gerr1] as u8,
            err[berr1] as u8,
        );
        image.put_pixel(0, j, palette[idx]);
        for i in 0..(image.width() - 1) {
            let ui = i as usize;
            err[rerr1 + ui] = err[rerr1 + ui].clamp(0, 255);
            err[gerr1 + ui] = err[gerr1 + ui].clamp(0, 255);
            err[berr1 + ui] = err[berr1 + ui].clamp(0, 255);
            idx = nearestrgb3(
                palette,
                err[rerr1 + ui] as u8,
                err[gerr1 + ui] as u8,
                err[berr1 + ui] as u8,
            );
            image.put_pixel(i, j, palette[idx]);
            let rerr = err[rerr1 + ui] - (palette[idx][0] as i32);
            let gerr = err[gerr1 + ui] - (palette[idx][1] as i32);
            let berr = err[berr1 + ui] - (palette[idx][2] as i32);
            // diffuse red error
            err[rerr1 + ui + 1] += (rerr * 7) >> 4;
            err[rerr2 + ui - 1] += (rerr * 3) >> 4;
            err[rerr2 + ui] += (rerr * 5) >> 4;
            err[rerr2 + ui + 1] += (rerr) >> 4;
            // diffuse green error
            err[gerr1 + ui + 1] += (gerr * 7) >> 4;
            err[gerr2 + ui - 1] += (gerr * 3) >> 4;
            err[gerr2 + ui] += (gerr * 5) >> 4;
            err[gerr2 + ui + 1] += (gerr) >> 4;
            // diffuse red error
            err[berr1 + ui + 1] += (berr * 7) >> 4;
            err[berr2 + ui - 1] += (berr * 3) >> 4;
            err[berr2 + ui] += (berr * 5) >> 4;
            err[berr2 + ui + 1] += (berr) >> 4;
        }
        err[rerr1] = err[rerr1].clamp(0, 255);
        err[gerr1] = err[gerr1].clamp(0, 255);
        err[berr1] = err[berr1].clamp(0, 255);
        idx = nearestrgb3(
            palette,
            err[rerr1] as u8,
            err[gerr1] as u8,
            err[berr1] as u8,
        );
        image.put_pixel(0, j, palette[idx]);
    }
}

fn _bilerp(y0x0: f64, y0x1: f64, y1x0: f64, y1x1: f64, tx: f64, ty: f64) -> f64 {
    let y0 = y0x0 + (y0x1 - y0x0) * tx;
    let y1 = y1x0 + (y1x1 - y1x0) * tx;
    y0 + (y1 - y0) * ty
}

/**
 * Gets the color of the in-between pixel at the given point
 * of the image, using bilinear interpolation.
 * 'x' is the point's x-coordinate, which need not be an integer.
 * 'y' is the point's y-coordinate, which need not be an integer.
 * An out-of-bounds point ('x','y') will undergo a wraparound adjustment, as though
 * the given image were part of an "infinite" tiling.
 *
 * Blending Note: Operations that involve the blending of two RGB (red-green-
 * blue) colors work best if the RGB color space is linear.  This is not the case
 * for the sRGB color space, which is the color space assumed for BasicRgbImage images.
 * Moreover, converting an image from a nonlinear
 * to a linear color space and back can lead to data loss especially if the image's color
 * components are 8 bits or fewer in length (as with RgbImage).
 * This function does not do any such conversion.
 */
pub fn imagept<T: BasicRgbImage>(image: &T, x: f64, y: f64) -> [u8; 3] {
    if image.width() == 0 || image.height() == 0 {
        return [0, 0, 0];
    }
    let mut x = x;
    let mut y = y;
    x %= image.width() as f64;
    y %= image.height() as f64;
    let xifloat = x.floor();
    let yifloat = y.floor();
    let xi: u32 = xifloat as u32;
    let xi1 = (xi + 1) % image.width();
    let yi: u32 = yifloat as u32;
    let yi1 = (yi + 1) % image.height();
    let y0x0 = image.get_pixel(xi, yi);
    let y0x1 = image.get_pixel(xi, yi1);
    let y1x0 = image.get_pixel(xi1, yi);
    let y1x1 = image.get_pixel(xi1, yi1);
    let mut rgb: [u8; 3] = [0, 0, 0];
    rgb[0] = _bilerp(
        y0x0[0].into(),
        y0x1[0].into(),
        y1x0[0].into(),
        y1x1[0].into(),
        x - xifloat,
        y - yifloat,
    )
    .floor()
    .clamp(0.0, 255.0) as u8;
    rgb[1] = _bilerp(
        y0x0[1].into(),
        y0x1[1].into(),
        y1x0[1].into(),
        y1x1[1].into(),
        x - xifloat,
        y - yifloat,
    )
    .floor()
    .clamp(0.0, 255.0) as u8;
    rgb[2] = _bilerp(
        y0x0[2].into(),
        y0x1[2].into(),
        y1x0[2].into(),
        y1x1[2].into(),
        x - xifloat,
        y - yifloat,
    )
    .floor()
    .clamp(0.0, 255.0) as u8;
    rgb
}

/**
* Wallpaper group Pmm.  Source rectangle
* takes the upper left quarter of the image
* and is reflected and repeated to cover the
* remaining image, assuming x-axis points
* to the right and the y-axis down.
* 'x' and 'y' are each 0 or greater
* and 1 or less. */
pub fn pmm(x: f64, y: f64) -> (f64, f64) {
    if x > 0.5 {
        if y < 0.5 {
            ((0.5 - (x - 0.5)) * 2.0, y * 2.0)
        } else {
            ((0.5 - (x - 0.5)) * 2.0, (0.5 - (y - 0.5)) * 2.0)
        }
    } else if y < 0.5 {
        (x * 2.0, y * 2.0)
    } else {
        (x * 2.0, (0.5 - (y - 0.5)) * 2.0)
    }
}

/**
* Wallpaper group P4m. Source triangle is formed
* by the upper-left, lower-left, and lower-right corners of
* a rectangle that takes the upper-left quarter of the destination image
* (triangle's right angle is at the rectangle's lower-left corner).
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p4m(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = pmm(x, y);
    if rx + (1.0 - ry) > 1.0 {
        (ry, rx)
    } else {
        (rx, ry)
    }
}

/**
* Wallpaper group P4m. Source triangle is formed
* by the upper-left, upper-right, lower-right corners of
* a rectangle that takes the upper-left quarter of the destination image
* (triangle's right angle is at the rectangle's upper-right corner).
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p4malt(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = pmm(x, y);
    if ry + (1.0 - rx) < 1.0 {
        (ry, rx)
    } else {
        (rx, ry)
    }
}

/**
 * Wallpaper group P3m1.  Source triangle
* is isosceles and is formed from a rectangle
* by using the bottom edge as the triangle's
* and the top point as the rectangle's
* upper midpoint, assuming x-axis points
* to the right and the y-axis down. Source triangle is part 
* of a scaled regular hexagon that is oriented
* such that the hexagon's lower edge is horizontal; the triangle's upper
* point is at the hexagon's center, and the triangle's lower edge is the
* same as the hexagon's lower edge.
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p3m1(x: f64, y: f64) -> (f64, f64) {
    let xx = x * 6.0;
    let xarea: i32 = min(5, xx.floor() as i32);
    let xpos = xx - (xarea as f64);
    let yarea: i32 = if y < 0.5 { 0 } else { 1 };
    let ypos = if y < 0.5 { y * 2.0 } else { (y - 0.5) * 2.0 };
    let isdiag1 = (xarea + yarea) % 2 == 0;
    let left_half = if isdiag1 {
        (xpos + ypos) < 1.0
    } else {
        (xpos + (1.0 - ypos)) < 1.0
    };
    match (xarea, yarea, left_half) {
        (1, 1, false) | (4, 0, false) => (xpos / 2.0, ypos),
        (2, 1, true) | (5, 0, true) => (xpos / 2.0 + 0.5, ypos),
        (1, 0, false) | (4, 1, false) => ((xpos / 2.0), 1.0 - ypos),
        (2, 0, true) | (5, 1, true) => ((xpos / 2.0 + 0.5), 1.0 - ypos),
        (0, 1, false) | (3, 0, false) => {
            let xp = xpos / 2.0;
            let yp = ypos;
            let mut newx = -xp / 2.0 - 3.0 * yp / 4.0 + 1.0;
            let mut newy = -xp + yp / 2.0 + 1.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        (1, 1, true) | (4, 0, true) => {
            let xp = (xpos / 2.0) + 0.5;
            let yp = ypos;
            let mut newx = -xp / 2.0 - 3.0 * yp / 4.0 + 1.0;
            let mut newy = -xp + yp / 2.0 + 1.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        (0, 0, false) | (3, 1, false) => {
            let xp = xpos / 2.0;
            let yp = 1.0 - ypos;
            let mut newx = -xp / 2.0 - 3.0 * yp / 4.0 + 1.0;
            let mut newy = -xp + yp / 2.0 + 1.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        (1, 0, true) | (4, 1, true) => {
            let xp = (xpos / 2.0) + 0.5;
            let yp = 1.0 - ypos;
            let mut newx = -xp / 2.0 - 3.0 * yp / 4.0 + 1.0;
            let mut newy = -xp + yp / 2.0 + 1.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        (2, 1, false) | (5, 0, false) => {
            let xp = xpos / 2.0;
            let yp = ypos;
            let mut newx = -xp / 2.0 + 3.0 * yp / 4.0 + 0.5;
            let mut newy = xp + yp / 2.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        (3, 1, true) | (0, 0, true) => {
            let xp = (xpos / 2.0) + 0.5;
            let yp = ypos;
            let mut newx = -xp / 2.0 + 3.0 * yp / 4.0 + 0.5;
            let mut newy = xp + yp / 2.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        (2, 0, false) | (5, 1, false) => {
            let xp = xpos / 2.0;
            let yp = 1.0 - ypos;
            let mut newx = -xp / 2.0 + 3.0 * yp / 4.0 + 0.5;
            let mut newy = xp + yp / 2.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        (3, 0, true) | (0, 1, true) => {
            let xp = (xpos / 2.0) + 0.5;
            let yp = 1.0 - ypos;
            let mut newx = -xp / 2.0 + 3.0 * yp / 4.0 + 0.5;
            let mut newy = xp + yp / 2.0;
            newx = newx.clamp(0.0, 1.0);
            newy = newy.clamp(0.0, 1.0);
            (newx, newy)
        }
        _ => (0.0, 0.0),
    }
}

/**
 * Wallpaper group P6m (same source rectangle as p3m1(), but
 * exposing only the left half of the triangle mentioned there).
* No requirements on the source to generate seamless images with this group function.
 *  */
pub fn p6m(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1(x, y);
    if rx > 0.5 {
        (1.0 - rx, ry)
    } else {
        (rx, ry)
    }
}

/**
 *  Wallpaper group P6m, alternative definition (same source rectangle
 * as p3m1(), but exposing only the right half of the triangle mentioned
 * there). 
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p6malt(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1(x, y);
    if rx < 0.5 {
        (1.0 - rx, ry)
    } else {
        (rx, ry)
    }
}

/**
 *  Wallpaper group P3m1, alternative definition.
 * Source triangle is isosceles and is formed from a rectangle
 * by using the left edge as the triangle's
 * and the right-hand point as the rectangle's
 * right-hand midpoint, assuming x-axis points
 * to the right and the y-axis down. 
 * Source triangle is part of a scaled regular hexagon that is oriented
 * such that the hexagon's left edge is vertical; the triangle's right-hand
 * point is at the hexagon's center, and the triangle's left edge is the
 * same as the hexagon's left edge.
* No requirements on the source to generate seamless images with this group function.
*/
pub fn p3m1alt1(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1(y, 1.0 - x);
    (1.0 - ry, rx)
}

/**
 *  Wallpaper group P3m1, alternative definition.
 * Source triangle is isosceles and is formed from a rectangle
 * by using the right edge as the triangle's
 * and the left-hand point as the rectangle's
 * left-hand midpoint, assuming x-axis points
 * to the right and the y-axis down. 
 * Source triangle is part of a scaled regular hexagon that is oriented
 * such that the hexagon's right-hand edge is vertical; the triangle's left
 * point is at the hexagon's center, and the triangle's right-hand edge is the
 * same as the hexagon's right-hand edge.
* No requirements on the source to generate seamless images with this group function.
*/
pub fn p3m1alt2(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1(y, x);
    (ry, rx)
}

/**
 *  Wallpaper group P6m, alternative definition
 * (same source rectangle as p3m1alt1(), but exposing
 * only the upper half of the triangle described there).
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p6malt1a(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1alt1(x, y);
    if ry > 0.5 {
        (rx, 1.0 - ry)
    } else {
        (rx, ry)
    }
}
/**
 * Wallpaper group P6m, alternative definition
 * (same source rectangle as p3m1alt1(), but exposing
 * only the lower half of the triangle described there).
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p6malt1b(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1alt1(x, y);
    if ry < 0.5 {
        (rx, 1.0 - ry)
    } else {
        (rx, ry)
    }
}

/**
 * Wallpaper group P6m, alternative definition
 * (same source rectangle as p3m1alt2(), but exposing
 * only the upper half of the triangle described there).
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p6malt2a(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1alt2(x, y);
    if ry > 0.5 {
        (rx, 1.0 - ry)
    } else {
        (rx, ry)
    }
}
/**
 * Wallpaper group P6m, alternative definition
 * (same source rectangle as p3m1alt2(), but exposing
 * only the lower half of the triangle described there).
* No requirements on the source to generate seamless images with this group function.
 */
pub fn p6malt2b(x: f64, y: f64) -> (f64, f64) {
    let (rx, ry) = p3m1alt2(x, y);
    if ry < 0.5 {
        (rx, 1.0 - ry)
    } else {
        (rx, ry)
    }
}

/**
* Creates an image based on a portion of a source
* image, with the help of a wallpaper group function.
* 'sourceRect' marks the source rectangle, which is
* allowed to wrap around the source image.
* 'width' and 'height' are the width and height of the image to create.
* 'groupFunc' is a wallpaper group function that translates output image
* coordinates to input image (source image) coordinates; default is pmm().
* 'groupFunc' takes two parameters: 'x' and 'y' are each 0 or greater
* and 1 or less, and are in relation to the destination image; 0 is leftmost
* or uppermost, and 1 is rightmost or bottommost, assuming that the positive x-axis points
* to the right and the positive y-axis points downward.  'groupFunc' returns a tuple indicating
* a point in relation to the source rectangle. The tuple has two elements,
* each 0 or greater and 1 or less: the first is the x-coordinate and the
* second, the y-coordinate; 0 is leftmost or uppermost, and 1 is
* rightmost or bottommost, with the assumption given earlier.
* The following wallpaper group functions in this module are intended to
* result in seamless tileable images from areas with arbitrary contents:
* pmm(), p4m(), p4malt(), p3m1(), p6m(), p6malt(), p3m1alt1(), p3m1alt2(),
* p6malt1a(), p6malt1b(), p6malt2a(), p6malt2b().  The functions implement
* variations of wallpaper groups Pmm, P4m, P3m1, and P6m, which are the only
* four that produce seamless images from areas with arbitrary contents.
* The documentation for those and other wallpaper
* group functions in this module assumes that the positive x-axis points to
* the right and the positive y-axis points downward.
*/
pub fn wallpaper_image<T: BasicRgbImage>(
    dest_width: u32,
    dest_height: u32,
    src_image: &T,
    source_rect: [f64; 4],
    group_func: fn(f64, f64) -> (f64, f64),
) -> T {
    let mut img = T::new(dest_width, dest_height);
    for y in 0..img.height() {
        for x in 0..img.width() {
            let (px, py) = group_func(
                (x as f64) / (dest_width as f64),
                (y as f64) / (dest_height as f64),
            );
            let sx: f64 = source_rect[0] + (source_rect[2] - source_rect[0]) * px;
            let sy: f64 = source_rect[1] + (source_rect[3] - source_rect[1]) * py;
            let pixel = imagept(src_image, sx, sy);
            img.put_pixel(x, y, pixel);
        }
    }
    img
}

pub fn borderedbox<T: BasicRgbImage>(
    image: &mut T,
    border: Option<[u8; 3]>,
    color1: [u8; 3],
    color2: [u8; 3],
    rect: [i32; 4],
    wraparound: bool,
) {
    let mut x0 = rect[0];
    let mut y0 = rect[1];
    let mut x1 = rect[2];
    let mut y1 = rect[3];
    if x1 < x0 || y1 < y0 {
        panic!();
    }
    if image.width() == 0 || image.height() == 0 {
        return;
    }
    if x0 == x1 || y0 == y1 {
        return;
    }
    if !wraparound {
        x0 = max(x0, 0);
        y0 = max(y0, 0);
        x1 = _min32(x1, image.width());
        y1 = _min32(y1, image.height());
        if x0 >= x1 || y0 >= y1 {
            return;
        }
    }
    for y in y0..y1 {
        let ypp: u32 = _mod32(y, image.height());
        for x in x0..x1 {
            let xp: u32 = _mod32(x, image.width());
            let is_border = match border {
                Some(_) => y == y0 || y == y1 - 1 || x == x0 || x == x1 - 1,
                None => false,
            };
            if is_border {
                // Draw border color
                image.put_pixel(xp, ypp, border.unwrap());
            } else if ypp % 2 == xp % 2 {
                // Draw first color
                image.put_pixel(xp, ypp, color1);
            } else {
                // Draw second color
                image.put_pixel(xp, ypp, color2);
            }
        }
    }
}
