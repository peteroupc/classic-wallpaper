mod basicrgbimage;
mod imageop;
mod parfor;
mod randomwp;
mod writers;

fn main() {
    parfor::parfor(10, |i| {
        let wp: basicrgbimage::BasicRgbImageData = randomwp::randomwallpaper();
        let filename = format!("{}/image{}.png", std::env::temp_dir().display(), i);
        writers::writepng(&wp, filename).expect("Failure");
        let pcx = format!("{}/image{}.pcx", std::env::temp_dir().display(), i);
        writers::writepcx(&wp, pcx).expect("Failure");
    });
}
