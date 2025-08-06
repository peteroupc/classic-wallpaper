use orx_parallel::IntoParIter;
use orx_parallel::ParIter;

/**
 * Run `count` many of the given task (`func`) in parallel.
 */
pub fn parfor(count: usize, func: fn(usize) -> ()) {
    match count {
        0 => (),
        1 => func(0),
        _ => assert_eq!(
            count,
            (0..count)
                .into_par()
                .map(|i| {
                    func(i);
                    1
                })
                .sum()
        ),
    };
}

/**
 * Run `count` many of the given task (`func`) in parallel,
 * with a parameter 'obj' that implements Sync.
 */
pub fn parfor2<T: Sync>(count: usize, func: fn(usize, &T) -> (), obj: &T) {
    match count {
        0 => (),
        1 => func(0, obj),
        _ => assert_eq!(
            count,
            (0..count)
                .into_par()
                .map(|i| {
                    func(i, obj);
                    1
                })
                .sum()
        ),
    };
}


