# Player Dashboard Background Videos

Place player dashboard background videos in this directory.

## Supported Video Files

The player dashboard scene will automatically look for videos in this priority order:

1. **`portal_dashboard_background.ogv`** (Recommended) - Portal-themed dashboard background
2. **`portal_dashboard_background.mp4`** - Portal-themed dashboard background (fallback)
3. **`player_menu_background.ogv`** - General player menu background
4. **`player_menu_background.mp4`** - General player menu background (fallback)
5. **`../ui/dashboard_background.ogv`** - UI fallback video
6. **`../ui/dashboard_background.mp4`** - UI fallback video

## Video Specifications

- **Format**: OGV (Ogg Theora) **PREFERRED** - Godot 4.2+ native support
- **Fallback**: MP4 (H.264) - for broader compatibility
- **Resolution**: 1920x1080 or higher
- **Aspect Ratio**: 16:9 (will be scaled to fit screen)
- **Duration**: 30-120 seconds (will loop automatically)
- **File Size**: Keep under 150MB for best performance

## Theme Suggestions

For the best player dashboard experience, consider videos with:
- Dynamic portal energy effects
- Mystical, adventurous atmosphere
- Rich, immersive environments
- Floating particles or energy streams
- Dimensional rifts or portals
- Magical ambiance
- Deep space or fantasy themes
- Subtle UI-friendly contrast

## Video Settings

- **Autoplay**: Yes (starts immediately)
- **Loop**: Yes (repeats continuously)
- **Audio**: Muted (video only)
- **Scaling**: Expands to fill entire screen
- **Layer**: Behind UI elements

If no video file is found, the system will fall back to an animated color-cycling background with portal themes.
