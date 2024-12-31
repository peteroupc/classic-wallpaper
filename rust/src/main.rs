use std::cmp::max;
use std::cmp::min;
use image::{RgbImage, Rgb};

// Minimum of a 32-bit signed integer
// and a 32-bit unsigned integer,
// expressed as a 32-bit signed integer
fn min32(a: i32, b: u32) -> i32 {
  if a<0 {
    // If negative, return 'a', since no
    // u32 value can be negative
    return a
  } else {
    let au32:u32 = a.wrapping_abs() as u32;
    return min(au32,b) as i32;
  }
}

// Modulus of a 32-bit signed integer
// and a 32-bit unsigned integer
fn mod32(a: i32, b: u32) -> u32 {
  if a<0 {
    let au32:u32 = a.wrapping_abs() as u32;
    let mut ret:u32 = au32 % b;
    if ret != 0 {
      ret = b - ret
    }
    return ret;
  } else {
    let au32:u32 = a.try_into().unwrap();
    return au32 % b;   
  }
}

fn classiccolors() -> Vec<[u8;3]> {
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

fn blankimage(width:u32, height:u32, color: [u8;3]) -> RgbImage {
  let mut image=RgbImage::new(width,height);
  let rc=Rgb(color);
  for y in 0..height {
    for x in 0..width {
      image.put_pixel(x,y,rc);
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
) -> Result<i32, i32> {
    let mut x0 = x0;
    let mut x1 = x1;
    let mut y0 = y0;
    let mut y1 = y1;
    if x1 < x0 || y1 < y0 {
        return Err(0);
    }
    if image.width() <= 0 || image.height() <= 0 {
        return Err(0);
    }
    if x0 == x1 || y0 == y1 {
        return Ok(0);
    }
    if !wraparound {
        x0 = max(x0, 0);
        y0 = max(y0, 0);
        x1=min32(x1,image.width());
        y1=min32(y1,image.height());
        if x0 >= x1 || y0 >= y1 {
            return Ok(0);
        }
    }
    let rc1=Rgb(color1);
    let rc2=Rgb(color2);
    for y in y0..y1 {
        let ypp: u32 = mod32(y,image.height());
        for x in x0..x1 {
            let xp: u32 = mod32(x,image.width());
            let is_border=match border {
              Some(_) => {
                if y == y0 || y == y1 - 1 || x == x0 || x == x1 - 1 {
                  true
                } else {
                  false
                }
              },
              None=>false
            };
            if is_border {
                // Draw border color
                image.put_pixel(xp,ypp,Rgb(border.unwrap()));
            } else if ypp % 2 == xp % 2 {
                // Draw first color
                image.put_pixel(xp,ypp,rc1);
            } else {
                // Draw second color
                image.put_pixel(xp,ypp,rc2);
            }
        }
    }
    return Ok(1);
}

fn main() {
    let w:u32 = 64;
    let h:u32 = 64;
    let mut image = blankimage(w,h,[0,0,0]);
    let vga=classiccolors();
    let c0=(rand::random::<u8>()&0x0F) as usize;
    let c1=(rand::random::<u8>()&0x0F) as usize;
    borderedbox(
        &mut image,
        None,
        vga[c0],
        vga[c1],
        0,
        0,
        w.try_into().unwrap(),
        h.try_into().unwrap(),
        true,
    ).expect("failure");
    image.save("/tmp/image.png").expect("failure");
}
