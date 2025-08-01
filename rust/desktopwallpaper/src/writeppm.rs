use crate::basicrgbimage::*;
use std::fs::File;
use std::io;
use std::io::{BufWriter, Write};
use std::path::Path;

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

