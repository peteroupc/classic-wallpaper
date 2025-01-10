pub trait BasicRgbImage {
    fn width(&self) -> u32;
    fn height(&self) -> u32;
    fn new(width: u32, height: u32) -> Self;
    fn get_pixel(&self, x: u32, y: u32) -> [u8; 3];
    fn put_pixel(&mut self, x: u32, y: u32, pixel: [u8; 3]);
}

pub struct BasicRgbImageData {
    width: u32,
    height: u32,
    data: Vec<u8>,
}

impl BasicRgbImage for BasicRgbImageData {
    fn width(&self) -> u32 {
        self.width
    }
    fn height(&self) -> u32 {
        self.height
    }
    fn get_pixel(&self, x: u32, y: u32) -> [u8; 3] {
        let us: usize = ((y * self.width + x) * 3).try_into().unwrap();
        [self.data[us], self.data[us + 1], self.data[us + 2]]
    }
    fn put_pixel(&mut self, x: u32, y: u32, pixel: [u8; 3]) {
        let us: usize = ((y * self.width + x) * 3).try_into().unwrap();
        self.data[us] = pixel[0];
        self.data[us + 1] = pixel[1];
        self.data[us + 2] = pixel[2];
    }
    fn new(width: u32, height: u32) -> BasicRgbImageData {
        BasicRgbImageData {
            width,
            height,
            data: vec![0; (width * height * 3).try_into().unwrap()],
        }
    }
}
