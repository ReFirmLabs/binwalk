use binwalk::hexdiff::{
    classify_block, classify_position, flags_for_classes, should_display_flags, ByteClass,
    HexdiffOptions,
};

#[test]
fn classify_position_two_files() {
    assert_eq!(
        classify_position(&[Some(0x41), Some(0x41)]),
        ByteClass::Green
    );
    assert_eq!(
        classify_position(&[Some(0x41), Some(0x42)]),
        ByteClass::Red
    );
    assert_eq!(classify_position(&[Some(0x41), None]), ByteClass::Red);
}

#[test]
fn classify_position_three_files() {
    // Two same, one different => blue (mixture)
    assert_eq!(
        classify_position(&[Some(0x41), Some(0x41), Some(0x42)]),
        ByteClass::Blue
    );

    // All distinct => red
    assert_eq!(
        classify_position(&[Some(0x41), Some(0x42), Some(0x43)]),
        ByteClass::Red
    );

    // One file EOF, other two same => blue (mixture)
    assert_eq!(
        classify_position(&[None, Some(0x41), Some(0x41)]),
        ByteClass::Blue
    );
}

#[test]
fn classify_block_and_filtering() {
    let f1: &[u8] = b"ABCD";
    let f2: &[u8] = b"ABcD";
    let f3: &[u8] = b"ABCD";

    let classes = classify_block(&[f1, f2, f3], 0, 4);
    assert_eq!(classes.len(), 4);

    // Expect: A,B are green (all same); C differs only in one file => blue; D green.
    assert_eq!(classes[0], ByteClass::Green);
    assert_eq!(classes[1], ByteClass::Green);
    assert_eq!(classes[2], ByteClass::Blue);
    assert_eq!(classes[3], ByteClass::Green);

    let flags = flags_for_classes(&classes);
    assert_eq!(flags, (false, true, true)); // (has_red, has_green, has_blue)

    let mut opts = HexdiffOptions::default();
    opts.show_red = true;
    opts.show_green = false;
    opts.show_blue = false;
    assert!(!should_display_flags(flags, &opts));

    opts.show_red = false;
    opts.show_green = true;
    opts.show_blue = false;
    assert!(should_display_flags(flags, &opts));

    opts.show_red = false;
    opts.show_green = false;
    opts.show_blue = true;
    assert!(should_display_flags(flags, &opts));
}


