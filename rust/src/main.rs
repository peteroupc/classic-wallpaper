mod basicrgbimage;
mod imageop;
mod parfor;
mod randomwp;
mod writers;

//////////////////



use winit::event::WindowEvent;
use winit::event_loop::{ControlFlow, EventLoop, ActiveEventLoop};
use winit::window::{Window, WindowId};

use std::num::NonZeroU32;
use std::rc::Rc;

use softbuffer::Buffer;

struct BasicImageData32<'a> {
  width: u32,
  height: u32,
  data: &'a mut Buffer<'a, Rc<Window>, Rc<Window>>,
}

impl<'a> basicrgbimage::BasicRgbImage for BasicImageData32<'a> {
    fn width(&self) -> u32 {
        self.width
    }
    fn height(&self) -> u32 {
        self.height
    }
    fn get_pixel(&self, x: u32, y: u32) -> [u8; 3] {
        let us: usize = (y * self.width + x).try_into().unwrap();
        let du=self.data[us];
        [((du>>16)&0xFF) as u8, ((du>>8)&0xFF) as u8, (du&0xFF) as u8]
    }
    fn put_pixel(&mut self, x: u32, y: u32, pixel: [u8; 3]) {
        let us: usize = (y * self.width + x).try_into().unwrap();
        self.data[us] = (pixel[2] as u32)|((pixel[1] as u32)<<8)|((pixel[0] as u32)<<16);
    }
    fn new(_width: u32, _height: u32) -> BasicImageData32<'a> {
        panic!("Not supported");
    }
}

fn copy_to_buffer<T: basicrgbimage::BasicRgbImage>(
   image: &mut Buffer<Rc<Window>, Rc<Window>>, width:u32, height:u32,
   srcimage: &T) {
  let srcwidth: u32=srcimage.width();
  let srcheight: u32=srcimage.height();
  for y in 0..std::cmp::min(srcheight,height) {
     for x in 0..std::cmp::min(srcwidth,width) {
        putpixel(image,width,height,x,y,srcimage.get_pixel(x,y));
     }
  }
}

fn copy_to_buffer_tiled<T: basicrgbimage::BasicRgbImage>(
   image: &mut Buffer<Rc<Window>, Rc<Window>>, width:u32, height:u32,
   srcimage: &T, ox:u32, oy:u32) {
  let srcwidth: u32=srcimage.width();
  let srcheight: u32=srcimage.height();
  for y in 0..(height) {
     let yp = (y+oy) % srcheight;
     for x in 0..(width) {
        let xp = (x+ox) % srcwidth;
        putpixel(image,width,height,x,y,srcimage.get_pixel(xp,yp));
     }
  }
}


fn getpixel(image: &mut Buffer<Rc<Window>, Rc<Window>>, width:u32, _height:u32, x:u32, y:u32) -> [u8;3]{
        let us: usize = (y * width + x).try_into().unwrap();
        let d=image[us];
        [((d>>16)&0xFF) as u8, ((d>>8)&0xFF) as u8, (d&0xFF) as u8]
}

fn putpixel(image: &mut Buffer<Rc<Window>, Rc<Window>>, width:u32, _height:u32, x:u32, y:u32, pixel:[u8;3]){
        let us: usize = (y * width + x).try_into().unwrap();
        image[us] = (pixel[2] as u32)|((pixel[1] as u32)<<8)|((pixel[0] as u32)<<16);
}

struct AppState {
    window: Option<Rc<Window>>,
    context: Option<softbuffer::Context<Rc<Window>>>,
    surface: Option<softbuffer::Surface<Rc<Window>, Rc<Window>>>,
    start: web_time::Instant,
    pub wp: basicrgbimage::BasicRgbImageData,
}

impl winit::application::ApplicationHandler for AppState {
    fn resumed(&mut self, event_loop: &ActiveEventLoop) {
        self.window = Some(Rc::new(
              event_loop.create_window(Window::default_attributes().with_inner_size(
                    winit::dpi::LogicalSize::new(640,480)).with_resizable(false).with_visible(true)).unwrap()
        ));
        self.context = Some(softbuffer::Context::new(self.window.as_ref().unwrap().clone()).unwrap());
        self.surface = Some(softbuffer::Surface::new(self.context.as_ref().unwrap(), self.window.as_ref().unwrap().clone()).unwrap());
    }

    fn about_to_wait(&mut self, _evloop: &ActiveEventLoop) {
       self.window.as_ref().unwrap().request_redraw();
    }

    fn window_event(&mut self, evloop: &ActiveEventLoop, _id: WindowId, event: WindowEvent) {
        match event {
            WindowEvent::RedrawRequested => {
                let surface = self.surface.as_mut().unwrap();
                let (width, height) = {
                    let size = self.window.as_ref().unwrap().inner_size();
                    (size.width, size.height)
                };
                let w=NonZeroU32::new(width).unwrap();
                let h=NonZeroU32::new(height).unwrap();
                surface.resize(w,h).unwrap();
                let mut buffer = surface.buffer_mut().unwrap();
                // Draw on buffer
                copy_to_buffer_tiled(&mut buffer,width,height,&self.wp,0,0);
                // End drawing on buffer
                buffer.present().unwrap();
            }
            WindowEvent::CloseRequested => {
                evloop.exit();
            },
            _ => (),
        }
    }
}

fn main() -> Result<(), winit::error::EventLoopError>{
    let event_loop = EventLoop::new().unwrap();
    event_loop.set_control_flow(ControlFlow::Wait);
    let mut app = AppState {
         window: None,
         context: None,
         surface: None,
         start: web_time::Instant::now(),
         wp: randomwp::randomwallpaper(),
    };
    event_loop.run_app(&mut app).unwrap();
    Ok(())
}

//////////////////

fn main0() {
    parfor::parfor(10, |i| {
        let wp: basicrgbimage::BasicRgbImageData = randomwp::randomwallpaper();
        let filename = format!("{}/image{}.png", std::env::temp_dir().display(), i);
        writers::writepng(&wp, filename).expect("Failure");
        let pcx = format!("{}/image{}.pcx", std::env::temp_dir().display(), i);
        writers::writepcx(&wp, pcx).expect("Failure");
    });
}
