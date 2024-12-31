use image::{Rgb, RgbImage};
use rand::distributions::Distribution;
use rand::distributions::Uniform;
use std::cmp::max;
use std::cmp::min;

// Minimum of a 32-bit signed integer
// and a 32-bit unsigned integer,
// expressed as a 32-bit signed integer
fn min32(a: i32, b: u32) -> i32 {
    if a < 0 {
        // If negative, return 'a', since no
        // u32 value can be negative
        return a;
    } else {
        let au32: u32 = a.wrapping_abs() as u32;
        return min(au32, b) as i32;
    }
}

// Modulus of a 32-bit signed integer
// and a 32-bit unsigned integer
fn mod32(a: i32, b: u32) -> u32 {
    if a < 0 {
        let au32: u32 = a.wrapping_abs() as u32;
        let mut ret: u32 = au32 % b;
        if ret != 0 {
            ret = b - ret
        }
        return ret;
    } else {
        let au32: u32 = a.try_into().unwrap();
        return au32 % b;
    }
}
/*
fn classiccolors() -> Vec<[u8; 3]> {
    return vec![
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
    ];
}
*/

static DITHER_MATRIX: [u8; 64] = [
    // Bayer 8 &times; 8 ordered dither matrix
    0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26, 12, 44, 4, 36, 14, 46, 6, 38, 60,
    28, 52, 20, 62, 30, 54, 22, 3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25, 15,
    47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21,
];

fn blankimage(width: u32, height: u32, color: [u8; 3]) -> RgbImage {
    let mut image = RgbImage::new(width, height);
    let rc = Rgb(color);
    for y in 0..height {
        for x in 0..width {
            image.put_pixel(x, y, rc);
        }
    }
    return image;
}

fn websafedither(image: &mut RgbImage, include_vga: bool) -> &mut RgbImage {
    for y in 0..image.height() {
        for x in 0..image.width() {
            let rc = image.get_pixel(x, y);
            let mut rr: u32 = rc.0[0].into();
            let mut rg: u32 = rc.0[1].into();
            let mut rb: u32 = rc.0[2].into();
            if include_vga {
                // Leave unchanged any colors in the VGA palette
                // but not in the "safety palette".
                let c0 = rr;
                if c0 == 0xC0 {
                    if rg == 0xC0 && rb == 0xC0 {
                        continue;
                    }
                } else if c0 == 0x80 || c0 == 0 {
                    if (rg == 0 || rg == 0x80) && (rb == 0 || rb == 0x80) {
                        continue;
                    }
                }
            }
            let mut cm: u32 = rr % 51;
            let bdither: u32 = DITHER_MATRIX[((y & 7) * 8 + (x & 7)) as usize].into();
            if bdither < (cm * 64) / 51 {
                rr = (rr - cm) + 51;
            } else {
                rr = rr - cm;
            }
            cm = rg % 51;
            if bdither < (cm * 64) / 51 {
                rg = (rg - cm) + 51;
            } else {
                rg = rg - cm;
            }
            cm = rb % 51;
            if bdither < (cm * 64) / 51 {
                rb = (rb - cm) + 51;
            } else {
                rb = rb - cm;
            }
            image.put_pixel(x, y, Rgb([rr as u8, rg as u8, rb as u8]));
        }
    }
    return image;
}

fn borderedbox(
    image: &mut RgbImage,
    border: Option<[u8; 3]>,
    color1: [u8; 3],
    color2: [u8; 3],
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    wraparound: bool,
) -> &mut RgbImage {
    let mut x0 = x0;
    let mut x1 = x1;
    let mut y0 = y0;
    let mut y1 = y1;
    if x1 < x0 || y1 < y0 {
        panic!();
    }
    if image.width() == 0 || image.height() == 0 {
        return image;
    }
    if x0 == x1 || y0 == y1 {
        return image;
    }
    if !wraparound {
        x0 = max(x0, 0);
        y0 = max(y0, 0);
        x1 = min32(x1, image.width());
        y1 = min32(y1, image.height());
        if x0 >= x1 || y0 >= y1 {
            return image;
        }
    }
    let rc1 = Rgb(color1);
    let rc2 = Rgb(color2);
    for y in y0..y1 {
        let ypp: u32 = mod32(y, image.height());
        for x in x0..x1 {
            let xp: u32 = mod32(x, image.width());
            let is_border = match border {
                Some(_) => y == y0 || y == y1 - 1 || x == x0 || x == x1 - 1,
                None => false,
            };
            if is_border {
                // Draw border color
                image.put_pixel(xp, ypp, Rgb(border.unwrap()));
            } else if ypp % 2 == xp % 2 {
                // Draw first color
                image.put_pixel(xp, ypp, rc1);
            } else {
                // Draw second color
                image.put_pixel(xp, ypp, rc2);
            }
        }
    }
    return image;
}

fn randomboxes(image: &mut RgbImage) -> &mut RgbImage {
    let ux0 = Uniform::new_inclusive(0, image.width() - 1);
    let uy0 = Uniform::new_inclusive(3, max(3, image.width() * 3 / 4));
    let ux1 = Uniform::new_inclusive(0, image.height() - 1);
    let uy1 = Uniform::new_inclusive(3, max(3, image.height() * 3 / 4));
    let mut rng = rand::thread_rng();
    for _i in 0..20 {
        let x0 = ux0.sample(&mut rng);
        let x1 = x0 + uy0.sample(&mut rng);
        let y0 = ux1.sample(&mut rng);
        let y1 = y0 + uy1.sample(&mut rng);
        let c0 = [
            rand::random::<u8>(),
            rand::random::<u8>(),
            rand::random::<u8>(),
        ];
        borderedbox(
            image,
            Some([0, 0, 0]),
            c0,
            c0,
            x0 as i32,
            y0 as i32,
            x1 as i32,
            y1 as i32,
            true,
        );
    }
    return image;
}

fn main() {
    let w: u32 = 128;
    let h: u32 = 128;
    let mut image = blankimage(w, h, [0, 0, 0]);
    randomboxes(&mut image);
    websafedither(&mut image, true);
    image
        .save_with_format("/tmp/image.png", image::ImageFormat::Png)
        .expect("failure");
}
