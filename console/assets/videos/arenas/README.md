# Arena Background Videos

Place arena-specific background videos in their respective directories.

## Arena Types

Each arena has its own subdirectory with unique background videos:

### **Mystic Forest** (`mystic_forest/`)
- Ancient trees, magical mists
- Floating lights, nature spirits
- Verdant, mystical atmosphere

### **Crystal Caverns** (`crystal_caverns/`)
- Glowing crystals, underground chambers
- Prismatic light effects
- Mineral formations, cave ambiance

### **Shadow Realm** (`shadow_realm/`)
- Dark, ethereal landscapes
- Shadowy figures, void energy
- Mysterious, ominous atmosphere

### **Celestial Temple** (`celestial_temple/`)
- Divine architecture, heavenly light
- Floating platforms, cosmic energy
- Sacred, majestic environment

### **Volcanic Forge** (`volcanic_forge/`)
- Lava flows, molten metal
- Fire effects, industrial elements
- Intense, fiery atmosphere

## Video File Naming Convention

Each arena directory should contain:

1. **`arena_background.ogv`** (Primary) - Main arena background
2. **`arena_background.mp4`** (Fallback) - MP4 version
3. **`battle_background.ogv`** (Optional) - Intense battle version
4. **`battle_background.mp4`** (Optional) - MP4 battle version

## Video Specifications

- **Format**: OGV (Ogg Theora) **PREFERRED**
- **Fallback**: MP4 (H.264)
- **Resolution**: 1920x1080 minimum
- **Aspect Ratio**: 16:9
- **Duration**: 60-300 seconds (seamless loop)
- **File Size**: 200MB max per video

## Battle Integration

Arena videos should:
- **Loop seamlessly** during battles
- **Match arena theme** and atmosphere
- **Enhance immersion** without distraction
- **Support UI overlay** with good contrast
- **Maintain performance** during real-time gameplay

## Dynamic Selection

The battle system will:
1. **Weight arena selection** based on player preferences
2. **Load appropriate video** for chosen arena
3. **Transition smoothly** from menu to battle
4. **Maintain video** throughout entire match
5. **Return to dashboard** after battle completion

If no arena video is found, the system will use a generic battle background or animated fallback.
