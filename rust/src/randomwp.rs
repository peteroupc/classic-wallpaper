use crate::basicrgbimage::*;
use crate::imageop::*;
use rand::distributions::Distribution;
use rand::distributions::Uniform;
use std::cmp::max;

pub fn randomboxes<T: BasicRgbImage>(image: &mut T) -> &mut T {
    let ux0 = Uniform::new_inclusive(0, image.width() - 1);
    let uy0 = Uniform::new_inclusive(3, max(3, image.width() * 3 / 4));
    let ux1 = Uniform::new_inclusive(0, image.height() - 1);
    let uy1 = Uniform::new_inclusive(3, max(3, image.height() * 3 / 4));
    let mut rng = rand::thread_rng();
    for _ in 0..30 {
        let x0 = ux0.sample(&mut rng);
        let x1 = x0 + ux1.sample(&mut rng);
        let y0 = uy0.sample(&mut rng);
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
            [x0 as i32, y0 as i32, x1 as i32, y1 as i32],
            true,
        );
    }
    image
}

pub fn randomwallpaper<T: BasicRgbImage>() -> T {
    let zero_or_one = Uniform::new_inclusive(0, 1);
    let mut rng = rand::thread_rng();
    let w: u32 = Uniform::new_inclusive(128, 256).sample(&mut rng) & !7;
    let h: u32 = Uniform::new_inclusive(128, 256).sample(&mut rng) & !7;
    let mut image = T::new(w, h);
    randomboxes(&mut image);
    if zero_or_one.sample(&mut rng) == 0 {
        let w2: u32 = Uniform::new_inclusive(128, 256).sample(&mut rng) & !7;
        let h2: u32 = Uniform::new_inclusive(128, 256).sample(&mut rng) & !7;
        let group = match Uniform::new_inclusive(0, 13).sample(&mut rng) {
            0 => p4m,
            1 => p4malt,
            2 => p3m1,
            3 => p6m,
            4 => p6malt,
            5 => p3m1alt1,
            6 => p3m1alt2,
            7 => p6malt1a,
            8 => p6malt1b,
            9 => p6malt2a,
            10 => p6malt2b,
            11 => p4m,
            12 => p4malt,
            _ => pmm,
        };
        image = wallpaper_image(w2, h2, &image, [0.0, 0.0, w as f64, h as f64], group);
    }
    // if zero_or_one.sample(&mut rng) == 0 {
    websafedither(&mut image, true);
    //} else {
    //    let cc = classiccolors();
    //    floyd_steinberg_dither(&mut image, &cc);
    //}
    image
}
