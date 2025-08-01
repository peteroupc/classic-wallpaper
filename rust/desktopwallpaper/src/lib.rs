mod basicrgbimage;
mod imageop;
mod parfor;
mod randomwp;
mod random;
mod writers;

//////////////////

use winit::event::WindowEvent;
use winit::event_loop::{ControlFlow, EventLoop, ActiveEventLoop};
#[cfg(target_arch="wasm32")]
use winit::platform::web::WindowAttributesExtWebSys;
use winit::window::{Window, WindowId};

use std::num::NonZeroU32;
use std::rc::Rc;

use softbuffer::Buffer;

#[cfg(target_arch="wasm32")]
use wasm_bindgen::prelude::*;

#[cfg(target_arch="wasm32")]
#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
    #[wasm_bindgen(js_namespace = document)]
    fn write(s: &str);
    #[wasm_bindgen(js_namespace = document)]
    fn getElementById(s: &str) -> web_sys::HtmlCanvasElement;
}


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
    started: bool,
    frame: u32,
    pub wp: basicrgbimage::BasicRgbImageData,
}

impl winit::application::ApplicationHandler for AppState {
    fn resumed(&mut self, event_loop: &ActiveEventLoop) {
        let mut attribs=Window::default_attributes()
                .with_inner_size(
                    winit::dpi::LogicalSize::new(640,480)).with_resizable(false).with_visible(true);
        
        #[cfg(target_arch="wasm32")]
        {
               if(!self.started) {
                   write("<canvas width=640 height=480 id=wasmcanvas></canvas>");
               }
               attribs=attribs.with_canvas(Some(getElementById("wasmcanvas")));
        }
        self.window = Some(Rc::new(
              event_loop.create_window(attribs).unwrap()
        ));
        self.context = Some(softbuffer::Context::new(self.window.as_ref().unwrap().clone()).unwrap());
        self.surface = Some(softbuffer::Surface::new(self.context.as_ref().unwrap(),
              self.window.as_ref().unwrap().clone()).unwrap());
        self.started = true;
    }

    fn about_to_wait(&mut self, _evloop: &ActiveEventLoop) {
       self.window.as_ref().unwrap().request_redraw();
    }

    fn window_event(&mut self, evloop: &ActiveEventLoop, _id: WindowId, event: WindowEvent) {
        //println!("Window event");
        match event {
            WindowEvent::RedrawRequested => {
                //println!("Redraw requested");
                let Some(surface) = self.surface.as_mut() else {
                   eprintln!("Too soon or too late to redraw: surface");
                   return;
                };
                let Some(window) = self.window.as_ref() else {
                   eprintln!("Too soon or too late to redraw: window");
                   return;
                };
                let (width, height) = {
                    let size = window.inner_size();
                    (size.width, size.height)
                };
                let Some(w)=NonZeroU32::new(width) else {
                   eprintln!("Invalid width: {}",width);
                   return;
                };
                let Some(h)=NonZeroU32::new(height) else {
                   eprintln!("Invalid height: {}",height);
                   return;
                };
                surface.resize(w,h).unwrap();
                if self.frame%60==0{
                   let fps=(self.frame as f64) / self.start.elapsed().as_secs_f64();
                   eprintln!("{} fps",fps);
                }
                self.frame+=1;
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

#[cfg_attr(target_arch="wasm32", wasm_bindgen(start))]
pub fn start(){
    let event_loop = EventLoop::new().unwrap();
    event_loop.set_control_flow(ControlFlow::Wait);
    let mut app = AppState {
         window: None,
         context: None,
         surface: None,
         started: false,
         frame: 0,
         start: web_time::Instant::now(),
         wp: randomwp::randomwallpaper(),
    };
    event_loop.run_app(&mut app).unwrap();
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
