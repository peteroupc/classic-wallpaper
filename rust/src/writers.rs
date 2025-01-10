use crate::basicrgbimage::*;
use std::fs::File;
use std::io;
use std::io::{BufWriter, Write};
use std::path::Path;

/**
 * Writes an RGB image to the Paintbrush (PCX) format.
 */
#[allow(dead_code)]
pub fn writepcx<T: BasicRgbImage>(image: &T, filename: String) -> Result<(), io::Error> {
    let mut writer = pcx::WriterRgb::create_file(
        filename,
        (
            image.width().try_into().unwrap(),
            image.height().try_into().unwrap(),
        ),
        (96, 96),
    )?;
    let mut row = vec![0; (image.width() * 3).try_into().unwrap()];
    for y in 0..image.height() {
        for x in 0..image.width() {
            let cr = image.get_pixel(x, y);
            let usx: usize = x.try_into().unwrap();
            row[usx * 3] = cr[0];
            row[usx * 3 + 1] = cr[1];
            row[usx * 3 + 2] = cr[2];
        }
        writer.write_row(&row)?;
    }
    writer.finish()?;
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
