# QR Login Background Videos

Place QR login background videos in this directory.

## Supported Video Files

The QR login scene will automatically look for videos in this priority order:

1. **`qr_portal_background.ogv`** (Recommended) - Portal-themed QR login background
2. **`qr_portal_background.mp4`** - Portal-themed QR login background (fallback)
3. **`qr_login_background.ogv`** - General QR login background
4. **`qr_login_background.mp4`** - General QR login background (fallback)
5. **`../ui/qr_background.ogv`** - UI fallback video
6. **`../ui/qr_background.mp4`** - UI fallback video

## Video Specifications

- **Format**: OGV (Ogg Theora) **PREFERRED** - Godot 4.2+ native support
- **Fallback**: MP4 (H.264) - for broader compatibility
- **Resolution**: 1920x1080 or higher
- **Aspect Ratio**: 16:9 (will be scaled to fit screen)
- **Duration**: 10-60 seconds (will loop automatically)
- **File Size**: Keep under 100MB for best performance

## Theme Suggestions

For the best QR login experience, consider videos with:
- Subtle portal energy effects
- Calming, focused atmosphere
- Minimal distraction from QR code
- Clean, professional appearance
- Soft particle effects
- Gentle color transitions
- Dark backgrounds with bright accents

## Video Settings

- **Autoplay**: Yes (starts immediately)
- **Loop**: Yes (repeats continuously)
- **Audio**: Muted (video only)
- **Scaling**: Expands to fill entire screen
- **Layer**: Behind UI elements

If no video file is found, the system will fall back to an animated color-cycling background.
