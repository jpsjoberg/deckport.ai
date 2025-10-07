# 🎴 Dynamic Card System - Godot Implementation Guide

## 📋 Overview

This guide explains how to implement the dynamic card system in Godot, combining video backgrounds with transparent frame overlays for immersive animated card experiences.

---

## 🎬 Dynamic Card Architecture

### **Two-Layer System**
```
Video Background Layer → Transparent Frame Overlay → Final Animated Card
        🎥                      🎴                        ✨
```

### **Asset Types**
- **Video Backgrounds**: 3-second seamless loops (MP4)
- **Transparent Frames**: Frame + UI elements with transparent background (PNG)
- **Static Composites**: Complete cards for fallback/performance (PNG)
- **Thumbnails**: Small previews for lists (PNG)

---

## 📁 Asset Structure

### **CDN Directory Layout**
```
static/cards/
├── videos/                    # Video backgrounds
│   ├── hero_crimson_140.mp4   # 3-second loops
│   └── creature_azure_001.mp4
├── frames/                    # Transparent frame overlays
│   ├── hero_crimson_140_frame.png
│   └── creature_azure_001_frame.png
├── composite/                 # Full static cards (fallback)
│   ├── hero_crimson_140_full.png
│   └── creature_azure_001_full.png
└── thumbnails/               # Small previews
    ├── hero_crimson_140_thumb.png
    └── creature_azure_001_thumb.png
```

### **Godot Asset Organization**
```
console/assets/cards/
├── videos/                   # Imported MP4 files
├── frames/                   # Transparent PNG overlays
├── static/                   # Static fallback cards
└── thumbnails/              # Preview images
```

---

## 🎮 Godot Implementation

### **1. Dynamic Card Display Scene**

```gdscript
# DynamicCard.gd
extends Control
class_name DynamicCard

@onready var video_background: VideoStreamPlayer = $VideoBackground
@onready var frame_overlay: TextureRect = $FrameOverlay
@onready var static_fallback: TextureRect = $StaticFallback

var card_data: Dictionary = {}
var quality_level: String = "high"  # high, medium, low

func display_card(card_id: String, animated: bool = true):
    """Display card with optional animation"""
    
    # Load card data from database/API
    card_data = await load_card_data(card_id)
    
    if animated and quality_level != "low":
        display_animated_card()
    else:
        display_static_card()

func display_animated_card():
    """Display card with video background + transparent frame overlay"""
    
    # Hide static fallback
    static_fallback.visible = false
    
    # Load and play video background
    var video_path = get_video_path(card_data.product_sku)
    if FileAccess.file_exists(video_path):
        var video_stream = load(video_path)
        video_background.stream = video_stream
        video_background.visible = true
        video_background.play()
        
        print("🎬 Playing video background: ", video_path)
    else:
        print("⚠️ Video not found, using static fallback")
        display_static_card()
        return
    
    # Load transparent frame overlay
    var frame_path = get_frame_path(card_data.product_sku)
    if FileAccess.file_exists(frame_path):
        var frame_texture = load(frame_path)
        frame_overlay.texture = frame_texture
        frame_overlay.visible = true
        
        print("🎴 Overlaying transparent frame: ", frame_path)
    else:
        print("⚠️ Frame overlay not found")
    
    # Add special effects for legendary cards
    if card_data.rarity == "legendary":
        add_legendary_effects()

func display_static_card():
    """Display pre-rendered static card (performance fallback)"""
    
    # Hide video components
    video_background.visible = false
    frame_overlay.visible = false
    
    # Show static composite
    var static_path = get_static_path(card_data.product_sku)
    if FileAccess.file_exists(static_path):
        var static_texture = load(static_path)
        static_fallback.texture = static_texture
        static_fallback.visible = true
        
        print("🖼️ Displaying static card: ", static_path)
    else:
        print("❌ No card assets found for: ", card_data.product_sku)

func get_video_path(product_sku: String) -> String:
    """Get video background path"""
    return "res://assets/cards/videos/" + product_sku.to_lower() + ".mp4"

func get_frame_path(product_sku: String) -> String:
    """Get transparent frame overlay path"""
    return "res://assets/cards/frames/" + product_sku.to_lower() + "_frame.png"

func get_static_path(product_sku: String) -> String:
    """Get static composite path"""
    return "res://assets/cards/static/" + product_sku.to_lower() + "_full.png"

func add_legendary_effects():
    """Add special effects for legendary cards"""
    
    # Particle effects
    var particles = preload("res://effects/LegendaryParticles.tscn").instantiate()
    add_child(particles)
    
    # Glow shader on frame
    var shader_material = ShaderMaterial.new()
    shader_material.shader = preload("res://shaders/LegendaryGlow.gdshader")
    frame_overlay.material = shader_material
    
    # Pulsing animation
    var tween = create_tween()
    tween.set_loops()
    tween.tween_property(frame_overlay, "modulate:a", 0.8, 1.0)
    tween.tween_property(frame_overlay, "modulate:a", 1.0, 1.0)

func load_card_data(card_id: String) -> Dictionary:
    """Load card data from API"""
    var http_request = HTTPRequest.new()
    add_child(http_request)
    
    var url = "http://127.0.0.1:8002/v1/catalog/cards/" + card_id
    var error = http_request.request(url)
    
    if error != OK:
        print("❌ Failed to request card data")
        return {}
    
    var response = await http_request.request_completed
    http_request.queue_free()
    
    var http_code = response[1]
    var body = response[3]
    
    if http_code == 200:
        var json = JSON.new()
        var parse_result = json.parse(body.get_string_from_utf8())
        
        if parse_result == OK:
            return json.data
    
    return {}
```

### **2. Performance Manager**

```gdscript
# CardPerformanceManager.gd
extends Node
class_name CardPerformanceManager

enum QualityLevel {
    LOW,      # Static images only
    MEDIUM,   # Pre-rendered composites
    HIGH      # Real-time video + frame overlay
}

var current_quality: QualityLevel = QualityLevel.HIGH
var fps_threshold: float = 45.0

func _ready():
    # Monitor performance
    var timer = Timer.new()
    timer.wait_time = 1.0
    timer.timeout.connect(_check_performance)
    add_child(timer)
    timer.start()

func _check_performance():
    """Monitor performance and adjust quality"""
    var current_fps = Engine.get_frames_per_second()
    
    if current_fps < fps_threshold and current_quality > QualityLevel.LOW:
        downgrade_quality()
    elif current_fps > fps_threshold + 10 and current_quality < QualityLevel.HIGH:
        upgrade_quality()

func downgrade_quality():
    """Reduce quality for better performance"""
    match current_quality:
        QualityLevel.HIGH:
            current_quality = QualityLevel.MEDIUM
            print("📉 Card quality: HIGH → MEDIUM")
        QualityLevel.MEDIUM:
            current_quality = QualityLevel.LOW
            print("📉 Card quality: MEDIUM → LOW")
    
    # Update all active cards
    get_tree().call_group("dynamic_cards", "update_quality", current_quality)

func upgrade_quality():
    """Increase quality when performance allows"""
    match current_quality:
        QualityLevel.LOW:
            current_quality = QualityLevel.MEDIUM
            print("📈 Card quality: LOW → MEDIUM")
        QualityLevel.MEDIUM:
            current_quality = QualityLevel.HIGH
            print("📈 Card quality: MEDIUM → HIGH")
    
    get_tree().call_group("dynamic_cards", "update_quality", current_quality)
```

### **3. Card Display Manager Integration**

```gdscript
# Enhanced CardDisplayManager.gd
extends Node
class_name CardDisplayManager

signal card_animation_started(card_data: Dictionary)
signal card_animation_finished(card_data: Dictionary)

var dynamic_card_scene = preload("res://scenes/DynamicCard.tscn")
var performance_manager: CardPerformanceManager

func _ready():
    performance_manager = CardPerformanceManager.new()
    add_child(performance_manager)

func display_played_card(card_data: Dictionary):
    """Display a card with full animation system"""
    
    # Create dynamic card instance
    var dynamic_card = dynamic_card_scene.instantiate()
    dynamic_card.add_to_group("dynamic_cards")
    add_child(dynamic_card)
    
    # Get quality level from performance manager
    var use_animation = performance_manager.current_quality != CardPerformanceManager.QualityLevel.LOW
    
    # Display the card
    dynamic_card.display_card(card_data.product_sku, use_animation)
    
    # Emit signals
    card_animation_started.emit(card_data)
    
    # Auto-remove after display duration
    await get_tree().create_timer(3.0).timeout
    dynamic_card.queue_free()
    
    card_animation_finished.emit(card_data)
```

---

## 🔧 Implementation Steps

### **Step 1: Asset Import**
```bash
# Copy assets from CDN to Godot project
cp /home/jp/deckport.ai/static/cards/videos/* console/assets/cards/videos/
cp /home/jp/deckport.ai/static/cards/frames/* console/assets/cards/frames/
cp /home/jp/deckport.ai/static/cards/composite/* console/assets/cards/static/
```

### **Step 2: Scene Setup**
1. Create `DynamicCard.tscn` scene:
   - `Control` (root)
   - `VideoStreamPlayer` (video background)
   - `TextureRect` (transparent frame overlay)
   - `TextureRect` (static fallback)

### **Step 3: Script Integration**
1. Add `DynamicCard.gd` script to scene
2. Update `CardDisplayManager.gd` to use dynamic cards
3. Add `CardPerformanceManager.gd` for quality control

### **Step 4: API Integration**
```gdscript
# Load card data from database
func get_card_from_api(product_sku: String) -> Dictionary:
    var http_request = HTTPRequest.new()
    add_child(http_request)
    
    var url = "http://127.0.0.1:8002/v1/catalog/cards/" + product_sku
    var response = await http_request.request_completed
    
    # Parse response and return card data
    return parse_card_response(response)
```

---

## 🎯 Quality Levels

### **HIGH Quality (Default)**
- ✅ Video backgrounds playing
- ✅ Transparent frame overlays
- ✅ Real-time compositing
- ✅ Particle effects for legendary cards

### **MEDIUM Quality (Performance Mode)**
- ❌ No video backgrounds
- ✅ Pre-rendered composite cards
- ✅ Basic animations
- ❌ Reduced particle effects

### **LOW Quality (Compatibility Mode)**
- ❌ No animations
- ✅ Static card images only
- ✅ Instant display
- ❌ No special effects

---

## 🎬 Video Background Requirements

### **Video Specifications**
- **Duration**: 3 seconds exactly
- **Loop**: Seamless (frame 1 = frame 90)
- **Format**: MP4 (H.264)
- **Resolution**: 1024x1024 or 512x512
- **FPS**: 30fps
- **Compression**: Medium quality for file size

### **Video Content Guidelines**
- **Subtle Motion**: Breathing, gentle movement, ambient effects
- **No Abrupt Changes**: Smooth continuous motion only
- **Consistent Lighting**: No flickering or dramatic light changes
- **Cinemagraph Style**: Most of image static, specific elements animated

---

## 🎨 Frame Overlay Requirements

### **Transparent Frame Specifications**
- **Background**: Fully transparent (alpha=0)
- **Frame Elements**: Opaque with proper alpha
- **Format**: PNG with alpha channel
- **Resolution**: 1500x2100 (card dimensions)
- **Quality**: High (no compression artifacts)

### **Frame Components**
- ✅ **Card Border**: Main frame design
- ✅ **Mana Icons**: Color-specific mana symbols
- ✅ **Rarity Elements**: Common/Rare/Epic/Legendary indicators
- ✅ **Text Elements**: Card name, category, stats
- ✅ **Set Icons**: Card set branding

---

## 🎮 Console Integration Examples

### **Battle Scene Integration**
```gdscript
# BattleScene.gd
extends Node

func play_card(card_data: Dictionary):
    """Play a card with dynamic animation"""
    
    var card_display = get_node("CardDisplayManager")
    
    # Show card with animation
    card_display.display_played_card(card_data)
    
    # Wait for animation to complete
    await card_display.card_animation_finished
    
    # Apply card effects to game state
    apply_card_effects(card_data)
```

### **Collection View Integration**
```gdscript
# CollectionView.gd
extends Control

func show_card_preview(product_sku: String):
    """Show card preview in collection"""
    
    var preview_card = dynamic_card_scene.instantiate()
    add_child(preview_card)
    
    # Use medium quality for collection (no video)
    preview_card.quality_level = "medium"
    preview_card.display_card(product_sku, false)
```

### **Hero Selection Integration**
```gdscript
# HeroSelection.gd
extends Control

func display_hero_options(hero_cards: Array):
    """Display hero cards with full animation"""
    
    for i in range(hero_cards.size()):
        var hero_card = dynamic_card_scene.instantiate()
        hero_selection_container.add_child(hero_card)
        
        # Legendary heroes get full animation
        var is_legendary = hero_cards[i].rarity == "legendary"
        hero_card.display_card(hero_cards[i].product_sku, is_legendary)
```

---

## 🔧 Performance Optimization

### **Quality Management**
```gdscript
# Automatic quality adjustment based on FPS
func _check_performance():
    var fps = Engine.get_frames_per_second()
    
    if fps < 45 and quality_level == "high":
        # Too many video cards, switch to medium
        quality_level = "medium"
        reload_all_cards()
    elif fps > 55 and quality_level == "medium":
        # Performance good, upgrade to high
        quality_level = "high"
        reload_all_cards()
```

### **Memory Management**
```gdscript
# Cache management for video assets
var video_cache: Dictionary = {}
var max_cached_videos: int = 10

func cache_video(product_sku: String, video_stream: VideoStream):
    """Cache video with LRU eviction"""
    if video_cache.size() >= max_cached_videos:
        # Remove oldest entry
        var oldest_key = video_cache.keys()[0]
        video_cache.erase(oldest_key)
    
    video_cache[product_sku] = video_stream
```

### **Asset Preloading**
```gdscript
func preload_battle_cards(deck: Array):
    """Preload assets for cards in player's deck"""
    for card in deck:
        var video_path = get_video_path(card.product_sku)
        var frame_path = get_frame_path(card.product_sku)
        
        # Preload in background
        ResourceLoader.load_threaded_request(video_path)
        ResourceLoader.load_threaded_request(frame_path)
```

---

## 🎯 API Integration

### **Card Data Loading**
```gdscript
func load_card_from_api(product_sku: String) -> Dictionary:
    """Load card data from Deckport API"""
    var http_request = HTTPRequest.new()
    add_child(http_request)
    
    var headers = ["Content-Type: application/json"]
    var url = "http://127.0.0.1:8002/v1/catalog/cards/" + product_sku
    
    var error = http_request.request(url, headers)
    if error != OK:
        print("❌ API request failed")
        return {}
    
    var response = await http_request.request_completed
    http_request.queue_free()
    
    var http_code = response[1]
    var body = response[3]
    
    if http_code == 200:
        var json = JSON.new()
        var parse_result = json.parse(body.get_string_from_utf8())
        
        if parse_result == OK:
            return json.data
    
    print("❌ Failed to load card: ", product_sku)
    return {}
```

### **Abilities Integration**
```gdscript
func load_card_abilities(card_id: int) -> Array:
    """Load card abilities from database"""
    var url = "http://127.0.0.1:8002/v1/cards/" + str(card_id) + "/abilities"
    
    # Make API request for abilities
    var abilities_data = await make_api_request(url)
    
    return abilities_data.get("abilities", [])
```

---

## 🎬 Video Background Guidelines

### **Content Creation**
- **Hero Cards**: Character breathing, armor gleaming, cape flowing
- **Creature Cards**: Natural movements, environmental responses
- **Action Cards**: Energy building, magical effects forming
- **Equipment Cards**: Magical gleaming, energy pulsing
- **Structure Cards**: Ambient atmosphere, architectural elements

### **Technical Requirements**
```
Resolution: 1024x1024 (square for flexibility)
Duration: Exactly 3.000 seconds
FPS: 30
Format: MP4 (H.264 codec)
Loop: Seamless (first frame = last frame)
File Size: <5MB per video
```

---

## 🎨 Frame Overlay Guidelines

### **Transparency Requirements**
- **Background**: 100% transparent (alpha=0)
- **Frame Elements**: Proper alpha blending
- **Text**: High contrast with stroke/outline
- **Icons**: Clear visibility over any background

### **Design Considerations**
- **Readable Text**: Works over light and dark backgrounds
- **Clear Icons**: Mana symbols visible over video
- **Frame Design**: Doesn't obscure important video content
- **Rarity Effects**: Special treatments for epic/legendary

---

## 🚀 Deployment Checklist

### **Asset Preparation**
- [ ] Generate video backgrounds for all cards
- [ ] Create transparent frame overlays
- [ ] Test transparency on various backgrounds
- [ ] Optimize file sizes for performance

### **Godot Setup**
- [ ] Import all video and frame assets
- [ ] Set up DynamicCard scene
- [ ] Implement performance management
- [ ] Test on target hardware

### **Integration Testing**
- [ ] Test card display in battle scene
- [ ] Verify API connectivity
- [ ] Check performance on low-end hardware
- [ ] Validate memory usage

### **Quality Assurance**
- [ ] Test all quality levels
- [ ] Verify seamless video loops
- [ ] Check frame transparency
- [ ] Validate legendary card effects

---

## 🎯 Usage Examples

### **Display Legendary Hero**
```gdscript
var legendary_hero = {
    "product_sku": "HERO_CRIMSON_140",
    "name": "Burn Knight",
    "rarity": "legendary",
    "category": "hero"
}

var card_display = DynamicCard.new()
add_child(card_display)
card_display.display_card(legendary_hero.product_sku, true)  # Animated
```

### **Show Card Collection**
```gdscript
func display_collection(cards: Array):
    for card in cards:
        var card_display = DynamicCard.new()
        collection_grid.add_child(card_display)
        
        # Use static for collection view (performance)
        card_display.display_card(card.product_sku, false)
```

### **Battle Card Animation**
```gdscript
func animate_card_play(card_data: Dictionary):
    var battle_card = DynamicCard.new()
    battle_overlay.add_child(battle_card)
    
    # Full animation for dramatic effect
    battle_card.display_card(card_data.product_sku, true)
    
    # Play ability videos
    var abilities = await load_card_abilities(card_data.id)
    for ability in abilities:
        play_ability_video(ability.video_path)
```

---

## 📊 Performance Metrics

### **Target Performance**
- **60 FPS**: With 1-2 animated cards on screen
- **45 FPS**: With 3-4 animated cards on screen
- **30 FPS**: Fallback to medium quality
- **<30 FPS**: Fallback to static cards

### **Memory Usage**
- **Video Cache**: Max 10 videos (≈50MB)
- **Frame Cache**: Max 20 frames (≈20MB)
- **Total**: <100MB for card system

---

## 🎉 Final Result

### **Dynamic Card Experience**
1. **🎬 Video Background**: Subtle 3-second animation loop
2. **🎴 Transparent Frame**: Perfect overlay with all UI elements
3. **✨ Special Effects**: Legendary cards get particle effects
4. **⚡ Performance**: Automatic quality adjustment
5. **🎮 Immersive**: Cards feel alive and magical

### **Production Ready**
- ✅ **2,600 Cards**: Complete database with abilities
- ✅ **ComfyUI Service**: Remote art generation working
- ✅ **Transparent Frames**: Perfect overlay system
- ✅ **CDN Storage**: Professional asset management
- ✅ **Console Integration**: Dynamic card display system

**Your dynamic card system is now production-ready for an immersive gaming experience!** 🎴✨🎮

---

*Last Updated: December 28, 2024*
*Status: Production Ready*
