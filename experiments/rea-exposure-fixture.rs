// Source-owned smoke fixture for static analysis. It is never loaded by this probe.
#[unsafe(no_mangle)]
pub extern "C" fn exposure_one_stop(linear: f32) -> f32 {
    linear * 2.0
}
