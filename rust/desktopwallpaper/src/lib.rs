mod basicrgbimage;
mod imageop;
mod parfor;
mod randomwp;
mod random;

//////////////////

use winit::event::{WindowEvent, KeyEvent, ElementState};
use winit::keyboard::{Key, NamedKey};
use winit::event_loop::{ControlFlow, EventLoop, ActiveEventLoop};
#[cfg(target_arch="wasm32")]
use winit::platform::web::WindowAttributesExtWebSys;
use winit::window::{Window, WindowId};

use std::num::NonZeroU32;
use std::rc::Rc;

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

pub struct SoftbufferData<'a> {
  width: u32,
  height: u32,
  // https://github.com/rust-windowing/softbuffer/issues/274
  data: &'a mut [u32],
}

impl<'a> basicrgbimage::BasicRgbImage for SoftbufferData<'a> {
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
    fn new(_width: u32, _height: u32) -> SoftbufferData<'a> {
        panic!("Not supported");
    }
}

macro_rules! softbuffer_data_mut {
  ($buffer:expr, $width:expr, $height:expr) => {
    &mut SoftbufferData{width:$width,height:$height,
                 data:&mut *$buffer as &mut [u32]}
  }
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


fn _length(a: f32, b: f32) -> f32{
  (a*a+b*b).sqrt()
}

#[cfg(not(target_arch="wasm32"))]
use rand::distributions::Distribution;

// Benchmark function that draws 100 random rectangles
// to a frame buffer.
fn randomrects<T: basicrgbimage::BasicRgbImage>(image: &mut T){
  let unifx=new_uniform!(0,image.width());
  let unify=new_uniform!(0,image.height());
  let unifbyte=new_uniform!(0,255);
  let mut rng=new_rng!();
  let mut pixels:u64=0;
  for _ in 0..100 {
    let color=[
      sample_rng!(unifbyte,&mut rng) as u8,
      sample_rng!(unifbyte,&mut rng) as u8,
      sample_rng!(unifbyte,&mut rng) as u8];
    let x0=sample_rng!(unifx,&mut rng);
    let x1=sample_rng!(unifx,&mut rng);
    let y0=sample_rng!(unify,&mut rng);
    let y1=sample_rng!(unify,&mut rng);
    let rx0=std::cmp::min(x0,x1);
    let ry0=std::cmp::min(y0,y1);
    let rx1=std::cmp::max(x0,x1);
    let ry1=std::cmp::max(y0,y1);
    pixels+=((rx1-rx0) as u64)*((ry1-ry0) as u64);
    imageop::rectangle(image, rx0,ry0,rx1,ry1,color);
  }
}

// Benchmark function that draws 512 random "sprites"
// to a frame buffer.
fn randomsprites<T: basicrgbimage::BasicRgbImage>(image: &mut T){
  let unifx=new_uniform!(0,if image.width()<64 { 0 } else {image.width()-64} );
  let unify=new_uniform!(0,if image.height()<64 { 0 } else {image.height()-64} );
  let unifbyte=new_uniform!(0,255);
  let mut rng=new_rng!();
  let mut pixels:u64=0;
  for _ in 0..512 {
    let color=[
      sample_rng!(unifbyte,&mut rng) as u8,
      sample_rng!(unifbyte,&mut rng) as u8,
      sample_rng!(unifbyte,&mut rng) as u8];
    let x0=sample_rng!(unifx,&mut rng);
    let x1=std::cmp::min(image.width(), ((x0+64) as u64).try_into().unwrap());
    let y0=sample_rng!(unify,&mut rng);
    let y1=std::cmp::min(image.height(), ((y0+64) as u64).try_into().unwrap());
    let rx0=std::cmp::min(x0,x1);
    let ry0=std::cmp::min(y0,y1);
    let rx1=std::cmp::max(x0,x1);
    let ry1=std::cmp::max(y0,y1);
    pixels+=((rx1-rx0) as u64)*((ry1-ry0) as u64);
    imageop::rectangle(image, rx0,ry0,rx1,ry1,color);
  }
}


fn blacken<T: basicrgbimage::BasicRgbImage>(image: &mut T){
                let height=image.height();
                let width=image.width();
                for y in 0..height {
                  for x in 0..width {
                    image.put_pixel(x,y,[0,0,0]);
                  }
                }
}

fn shader_draw<T: basicrgbimage::BasicRgbImage>(image: &mut T, startTime: &web_time::Instant){
                let f32elapsed:f32 = startTime.elapsed().as_secs_f32();
                let height=image.height();
                let width=image.width();
                for y in 0..height {
                  let yp:f32=(y as f32)/(height as f32);
                  for x in 0..width {
                    let xp:f32=(x as f32)/(width as f32);
                    let sh:[f32;3]=[0.0,0.0,0.0]; //shader(width,height,xp,yp,f32elapsed);
                    let r:u8=(sh[0].clamp(0.0,1.0)*255.0) as u8;
                    let g:u8=(sh[1].clamp(0.0,1.0)*255.0) as u8;
                    let b:u8=(sh[2].clamp(0.0,1.0)*255.0) as u8;
                    image.put_pixel(x,y,[r,g,b]);
                  }
                }
}

impl winit::application::ApplicationHandler for AppState {
    fn resumed(&mut self, event_loop: &ActiveEventLoop) {
        let mut attribs=Window::default_attributes()
                .with_inner_size(
                    winit::dpi::LogicalSize::new(320,240)).with_resizable(false)
                .with_title("Desktop Wallpaper App");
        #[cfg(target_arch="wasm32")]
        {
               if !self.started {
                   write("<canvas width=320 height=240 id=wasmcanvas></canvas>");
               }
               attribs=attribs.with_canvas(Some(getElementById("wasmcanvas")));
        }
        attribs=attribs.with_visible(true);
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
            WindowEvent::KeyboardInput {
               event:
                  KeyEvent { logical_key: Key::Named(NamedKey::Enter),
                                 state: ElementState::Pressed, .. },
               ..
            } => {
               // Change the wallpaper
               self.wp = randomwp::randomwallpaper();
               self.window.as_ref().unwrap().request_redraw();
            }
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
                /*if self.frame%60==0{
                   let fps=(self.frame as f64) / self.start.elapsed().as_secs_f64();
                   eprintln!("{} fps",fps);
                }*/
                self.frame+=1;
                let mut buffer = surface.buffer_mut().unwrap();
                // Draw on buffer
                let elapsedu64: u64 = (self.start.elapsed().as_secs_f64()*60.0) as u64;
                let realframe=(elapsedu64 & 0xFFFFFFFF) as u32;
                //imageop::copy_to_buffer_tiled(softbuffer_data_mut!(buffer,width,height),&self.wp,realframe,realframe);
                randomsprites(softbuffer_data_mut!(buffer,width,height));
                imageop::websafedither(softbuffer_data_mut!(buffer,width,height), true);
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
