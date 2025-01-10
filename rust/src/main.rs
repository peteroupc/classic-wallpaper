use std::io;
use std::io::Write;
mod basicrgbimage;
use basicrgbimage::BasicRgbImage;
use basicrgbimage::BasicRgbImageData;
mod imageop;
mod parfor;
mod randomwp;

/**
 * Writes an RGB image to the portable pixelmap (PPM) format.
 */
fn writeppm<T: BasicRgbImage>(image: &T, filename: String) -> Result<(), io::Error> {
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

/*
fn writepcx(image: &RgbImage, filename: String) -> Result<(), io::Error> {
    let mut writer=pcx::WriterRgb::create_file(filename,(image.width().try_into().unwrap(),
         image.height().try_into().unwrap()), (96, 96))?;
    let mut row=vec![0;(image.width()*3).try_into().unwrap()];
    for y in 0..image.height() {
        for x in 0..image.width() {
            let cr = image.get_pixel(x, y);
            let usx:usize = x.try_into().unwrap();
            row[usx*3]=cr[0];
            row[usx*3+1]=cr[1];
            row[usx*3+2]=cr[2];
        }
        writer.write_row(&row)?;
    }
    writer.finish()?;
    Ok(())
}*/

fn main() {
    parfor::parfor(200, |i| {
        let wp: BasicRgbImageData = randomwp::randomwallpaper();
        let filename = format!("{}/image{}.ppm", std::env::temp_dir().display(), i);
        writeppm(&wp, filename).expect("Failure");
        // wp.save().expect("Failure");
    });
}
