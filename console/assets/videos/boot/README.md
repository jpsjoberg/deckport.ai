# Boot Background Videos

Place your portal/boot background videos in this directory.

## Supported Video Files

The boot screen will automatically look for videos in this priority order:

1. **`portal_background.ogv`** (Recommended) - Main portal presentation video (OGV format)
2. **`portal_background.mp4`** - Main portal presentation video (MP4 fallback) 
3. **`boot_background.ogv`** - Alternative boot video (OGV format)
4. **`boot_background.mp4`** - Alternative boot video (MP4 fallback)
5. **`../ui/boot_portal.ogv`** - Fallback UI video (OGV format)
6. **`../ui/boot_portal.mp4`** - Fallback UI video (MP4 fallback)

## Video Specifications

- **Format**: OGV (Ogg Theora) **REQUIRED** - Godot 4.2 only supports OGV for VideoStreamPlayer
- **Fallback**: MP4 (H.264) - for conversion reference only
- **Resolution**: 1920x1080 or higher
- **Aspect Ratio**: 16:9 (will be scaled to fit screen)
- **Duration**: 10-30 seconds (will loop automatically)
- **File Size**: Keep under 50MB for best performance

## Portal Theme Suggestions

For the best "portal presentation" effect, consider videos with:
- Swirling energy effects
- Particle systems
- Glowing portals or gateways
- Sci-fi/futuristic themes
- Smooth looping animation
- Dark backgrounds with bright accents

## Video Settings

- **Autoplay**: Yes (starts immediately)
- **Loop**: Yes (repeats continuously)
- **Audio**: Will be ignored (use video without audio or mute)
- **Scaling**: Expands to fill entire screen

If no video file is found, the system will fall back to an animated color-cycling background with portal-themed colors.
