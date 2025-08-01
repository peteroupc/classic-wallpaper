use crate::basicrgbimage::*;
use crate::imageop::*;
use crate::new_uniform;
use crate::new_rng;
use crate::sample_rng;
use std::cmp::max;

#[cfg(not(target_arch="wasm32"))]
use rand::distributions::Distribution;
#[cfg(not(target_arch="wasm32"))]
use rand::distributions::Uniform;

pub fn randomboxes<T: BasicRgbImage>(image: &mut T) -> &mut T {
    let ux0 = new_uniform!(0, image.width() - 1);
    let uy0 = new_uniform!(3, max(3, image.width() * 3 / 4));
    let ux1 = new_uniform!(0, image.height() - 1);
    let uy1 = new_uniform!(3, max(3, image.height() * 3 / 4));
    let ubyte = new_uniform!(0, 255);
    let mut rng = new_rng!();
    for _ in 0..30 {
        let x0 = sample_rng!(ux0,&mut rng);
        let x1 = x0 + sample_rng!(ux1,&mut rng);
        let y0 = sample_rng!(uy0,&mut rng);
        let y1 = y0 + sample_rng!(uy1,&mut rng);
        let c0 = [
            sample_rng!(ubyte,&mut rng) as u8,
            sample_rng!(ubyte,&mut rng) as u8,
            sample_rng!(ubyte,&mut rng) as u8,
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
    let zero_or_one = new_uniform!(0, 1);
    let mut rng = new_rng!();
    let w: u32 = sample_rng!(new_uniform!(128, 256),&mut rng) & !7;
    let h: u32 = sample_rng!(new_uniform!(128, 256),&mut rng) & !7;
    let mut image = T::new(w, h);
    randomboxes(&mut image);
    if sample_rng!(zero_or_one,&mut rng) == 0 {
        let w2: u32 = sample_rng!(new_uniform!(128, 256),&mut rng) & !7;
        let h2: u32 = sample_rng!(new_uniform!(128, 256),&mut rng) & !7;
        let group = match sample_rng!(new_uniform!(0, 13),&mut rng) {
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
    // if sample_rng!(zero_or_one, &mut rng) == 0 {
    websafedither(&mut image, true);
    //} else {
    //    let cc = classiccolors();
    //    floyd_steinberg_dither(&mut image, &cc);
    //}
    image
}
