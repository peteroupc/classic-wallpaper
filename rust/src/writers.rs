use crate::basicrgbimage::*;
use std::fs::File;
use std::io;
use std::io::{BufWriter, Write};
use std::path::Path;

macro_rules! lepackdata {
    ($x:tt) => {
        match $x {
            // unsigned 8-bit integer
            ("B", v) => vec![v as u8],
            // unsigned 16-bit integer
            ("H", v) => vec![((v as u16) & 0xFF) as u8, (((v as u16) >> 8) & 0xFF) as u8],
            // signed 16-bit integer
            ("h", v) => vec![((v as i16) & 0xFF) as u8, (((v as i16) >> 8) & 0xFF) as u8],
            // unsigned 32-bit integer
            ("L", v) => vec![
                ((v as u32) & 0xFF) as u8,
                (((v as u32) >> 8) & 0xFF) as u8,
                (((v as u32) >> 16) & 0xFF) as u8,
                (((v as u32) >> 24) & 0xFF) as u8,
            ],
            // signed 32-bit integer
            ("l", v) => vec![
                ((v as i32) & 0xFF) as u8,
                (((v as i32) >> 8) & 0xFF) as u8,
                (((v as i32) >> 16) & 0xFF) as u8,
                (((v as i32) >> 24) & 0xFF) as u8,
            ],
            (&_, _) => todo!(),
        }
    };
}

/**
 *  Generates a u8 vector consisting of structured data
 *  in little-endian byte order.
 *  Example: `lepack!(("H",0x3344), ("L",0x33445566));`.
 */
#[macro_export]
macro_rules! lepack {
  ($($x:expr_2021),*) => {
    {
    let mut v=vec![];
    $({
      v.append(&mut lepackdata!($x));
    })*
    v
    }
  }
}
fn pcx_encode_byte(file: &mut std::fs::File, b: u8, c: u8) -> Result<(), io::Error> {
    if c > 0 {
        if c == 1 && (b & 0xC0) != 0xC0 {
            file.write_all(&[b])?;
        } else {
            file.write_all(&[c | 0xc0, b])?;
        }
    }
    Ok(())
}

fn pcx_encode_line(file: &mut std::fs::File, vec: &[u8]) -> Result<(), io::Error> {
    if vec.is_empty() {
        return Ok(());
    }
    let mut runcount: u8 = 1;
    let mut last: u8 = vec[0];
    for this_value in vec.iter().skip(1) {
        if *this_value == last {
            runcount += 1;
            if runcount == 63 {
                pcx_encode_byte(file, last, runcount)?;
                runcount = 0;
            }
        } else {
            if runcount > 0 {
                pcx_encode_byte(file, last, runcount)?;
            }
            last = *this_value;
            runcount = 1;
        }
    }
    if runcount > 0 {
        pcx_encode_byte(file, last, runcount)?;
    }
    Ok(())
}

/**
 * Writes an RGB image to the Paintbrush (PCX) format.
 */
pub fn writepcx<T: BasicRgbImage>(image: &T, filename: String) -> Result<(), io::Error> {
    let mut file = std::fs::File::create(filename)?;
    let iwidth: u32 = image.width();
    let iheight: u32 = image.height();
    if iwidth == 0 || iheight == 0 {
        return Err(std::io::Error::other("invalid size"));
    }
    file.write_all(&lepack!(
        ("B", 10),          // Manufacturer
        ("B", 5),           // Version
        ("B", 1),           // Encoding
        ("B", 8),           // BitsPerPixel
        ("H", 0),           // Xmin
        ("H", 0),           // Ymin
        ("H", iwidth - 1),  // Xmax
        ("H", iheight - 1), // Ymax
        ("H", 96),          // XDpi
        ("H", 96)           // YDpi
    ))?;
    // Blank color map
    file.write_all(&[0; 48])?;
    let bytes_per_line: u16 = (((iwidth * 8 + 15) >> 4) << 1).try_into().unwrap();
    file.write_all(&lepack!(
        ("B", 0),              // Reserved
        ("B", 3),              // NPlanes
        ("H", bytes_per_line), // BytesPerLine
        ("H", 1),              // PaletteInfo
        ("H", 0),              // HscreenSize
        ("H", 0)               // VscreenSize
    ))?;
    file.write_all(&[0; 54])?; // filler
    let mut r = vec![0; bytes_per_line.into()];
    let mut g = vec![0; bytes_per_line.into()];
    let mut b = vec![0; bytes_per_line.into()];
    for y in 0..image.height() {
        for x in 0..image.width() {
            let cr = image.get_pixel(x, y);
            let usx: usize = x.try_into().unwrap();
            r[usx] = cr[0];
            g[usx] = cr[1];
            b[usx] = cr[2];
        }
        pcx_encode_line(&mut file, &r)?;
        pcx_encode_line(&mut file, &g)?;
        pcx_encode_line(&mut file, &b)?;
    }
    Ok(())
}

/**
 * Writes an RGB image to the portable pixelmap (PPM) format.
 */
#[allow(dead_code)]
pub fn writeppm<T: BasicRgbImage>(image: &T, filename: String) -> Result<(), io::Error> {
    let mut file = std::fs::File::create(filename)?;
    write!(&mut file, "P6\n{} {}\n255\n", image.width(), image.height())?;
    for y in 0..image.height() {
        for x in 0..image.width() {
            let cr = image.get_pixel(x, y);
            file.write_all(&cr)?;
        }
    }
    Ok(())
}

pub fn writepng<T: BasicRgbImage>(image: &T, filename: String) -> Result<(), io::Error> {
    let file = File::create(Path::new(&filename))?;
    let w = &mut BufWriter::new(file);
    let mut encoder = png::Encoder::new(w, image.width(), image.height());
    encoder.set_color(png::ColorType::Rgb);
    encoder.set_depth(png::BitDepth::Eight);
    let mut writer = encoder.write_header()?;
    let mut row = vec![0; (image.width() * image.height() * 3).try_into().unwrap()];
    let mut pos: usize = 0;
    for y in 0..image.height() {
        for x in 0..image.width() {
            let cr = image.get_pixel(x, y);
            row[pos] = cr[0];
            row[pos + 1] = cr[1];
            row[pos + 2] = cr[2];
            pos += 3;
        }
    }
    writer.write_image_data(&row)?;
    writer.finish()?;
    Ok(())
}
