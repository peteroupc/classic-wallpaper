#[cfg(target_arch="wasm32")]
use crate::wasm_bindgen;

#[cfg(target_arch="wasm32")]
#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
    #[wasm_bindgen(js_namespace = Math)]
    fn random() -> f64;
}


#[cfg(target_arch="wasm32")]
#[macro_export]
macro_rules! new_uniform {
  ($x:expr, $y:expr) => {
    [$x as u32, $y as u32]
  }
}

#[cfg(target_arch="wasm32")]
#[macro_export]
macro_rules! new_rng {
  () => {
    vec!{0 as u32}
  }
}

#[cfg(target_arch="wasm32")]
pub fn do_sample_rng(unif: [u32;2], rng: &mut Vec<u32>) -> u32 {
     if unif[0]>unif[1] {
       panic!("invalid range of random numbers");
     }
     if unif[0]==unif[1] {
       return unif[0];
     }
     let diff=unif[1]-unif[0];
     if diff==4294967295 {
       return ((unif[0] as f64) + (random() * 4294967296.0)) as u32;
     }
     // Lumbroso's Fast Dice Roller
     let mut x:u64=1;
     let mut y:u64=0;
     let mut next_bit=32;
     let mut rngv:u32=0;
     let max_inc_minus_one:u64=(diff as u64)-1;
     loop {
        if next_bit>=32 {
          next_bit=0;
          rngv=(random() * 4294967296.0) as u32;
        }
        next_bit+=1;
        let bit:u64=(rngv as u64)&1;
        x*=2;
        y=(y*2)|bit;
        rngv>>=1;
        if x>diff.into() {
           x=x-max_inc_minus_one;
           x-=2;
           if y<=diff.into() { return ((unif[0] as u64)+y) as u32 }
           else {
              y=y-max_inc_minus_one;
              y-=2;
           }
        }
     }
}

#[cfg(target_arch="wasm32")]
#[macro_export]
macro_rules! sample_rng {
  ($x:expr, $y:expr) => {
     crate::random::do_sample_rng($x, $y)
  }
}


#[cfg(not(target_arch="wasm32"))]
#[macro_export]
macro_rules! new_uniform {
  ($x:expr, $y:expr) => {
    rand::distributions::Uniform::new_inclusive($x, $y)
  }
}

#[cfg(not(target_arch="wasm32"))]
#[macro_export]
macro_rules! new_rng {
  () => {
    rand::thread_rng()
  }
}

#[cfg(not(target_arch="wasm32"))]
#[macro_export]
macro_rules! sample_rng {
  ($x:expr, $y:expr) => {
    $x.sample($y)
  }
}


