# Logo Assets

Place your Deckport logo files in this directory.

## Supported Logo Files

The boot screen will automatically look for logo files in this priority order:

1. **`deckport_logo.png`** (Recommended) - Main logo with transparency
2. **`deckport_logo.jpg`** - JPEG version of main logo
3. **`deckport_logo.svg`** - Vector version (if supported)
4. **`logo.png`** - Generic logo name
5. **`logo.jpg`** - Generic logo JPEG

## Logo Specifications

- **Format**: PNG (recommended for transparency), JPG, or SVG
- **Resolution**: 300x150 pixels (2:1 aspect ratio recommended)
- **Background**: Transparent PNG preferred
- **File Size**: Keep under 5MB

## Logo Positioning

The logo appears in the **center-top** area of the boot screen:
- **Container Size**: 400x200 pixels
- **Image Size**: 300x150 pixels (will scale to fit)
- **Position**: Horizontally and vertically centered within container
- **Scaling**: Maintains aspect ratio, expands to fit container

## Logo Layout

```
┌─────────────────────────────────────┐
│                                     │
│              [LOGO]                 │  ← Logo appears here
│                                     │
│         "Starting up..."            │  ← Status text
│         [Progress Bar]              │  ← Progress bar
│                                     │
└─────────────────────────────────────┘
```

## Fallback Behavior

If no logo image file is found, the system will display "DECKPORT CONSOLE" as text instead.

## Tips

- Use a logo that looks good on dark/video backgrounds
- Consider adding a subtle glow or outline for better visibility
- Test with your portal video to ensure good contrast
- Keep the design clean and readable at the specified size
