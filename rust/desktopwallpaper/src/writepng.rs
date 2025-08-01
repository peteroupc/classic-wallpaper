use crate::basicrgbimage::*;
use std::fs::File;
use std::io;
use std::io::{BufWriter, Write};
use std::path::Path;

/**
 * Writes an RGB image to the portable network graphics (PNG) format.
 */
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
