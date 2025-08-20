# Deckport.ai Game Development Plan

## 🎮 Vision Alignment

### Core Game Experience
- **Console-Focused Interface**: All gameplay happens on Godot console with NFC reader
- **Video Storytelling**: Rich narrative through locally stored video clips
- **Real-time Interactivity**: Instant response to NFC card scans
- **Arena-Based Matches**: Each arena has unique story, advantages, and atmosphere
- **Physical-Digital Integration**: NFC cards trigger immediate visual/audio feedback

### User Journey
```
Power On → Deckport Logo → QR Login → Main Menu → Match Game → Hero Selection → Arena Assignment → Gameplay → Match Results
```

## 🏗️ Development Structure

### Phase 2 Completion: Console Game Interface

#### 1. Console Game Scenes (Priority 1)
```
console/scenes/
├── MainMenu.tscn          # Post-login menu with Match Game option
├── HeroSelection.tscn     # Choose starting hero with NFC scan
├── ArenaReveal.tscn       # Arena introduction with video and stats
├── GameBoard.tscn         # Main gameplay interface
├── MatchResults.tscn      # Post-match statistics and rewards
└── CardActivation.tscn    # Card activation flow for new cards
```

#### 2. Game Logic Engine
```
console/scripts/
├── GameManager.gd         # Core game state and rules engine
├── TurnManager.gd         # Turn phases and timing
├── ArenaManager.gd        # Arena effects and storytelling
├── CardManager.gd         # Card actions and effects
├── NFCManager.gd          # NFC card scanning and validation
└── VideoManager.gd        # Video clip management and playback
```

#### 3. Arena System
```
Database Tables:
- arenas (name, color, passive, objective, hazard, video_clips, story_text)
- arena_clips (arena_id, clip_type, file_path, trigger_condition)

Console Assets:
- assets/videos/arenas/{arena_name}/
  ├── intro.mp4           # Arena introduction
  ├── ambient.mp4         # Background loop during match
  ├── advantage.mp4       # When player gets arena advantage
  └── victory.mp4         # Arena-specific victory clip
```

## 🎯 Game Flow Implementation

### 1. User Authentication & Setup
```
QR Login → Phone Confirmation → Console Unlocked → Main Menu
```

**Console Implementation:**
- Display QR code with branded animation
- Poll server for confirmation
- Smooth transition to main menu with user info
- Show player level, recent matches, owned cards count

### 2. Card Activation Flow
```
New Card → NFC Scan → Activation Code Entry → Video Reveal → Card Added to Collection
```

**Features:**
- **Instant NFC Response**: Card scan triggers immediate visual feedback
- **Video Reveals**: Each card has unique reveal animation/video
- **Collection Integration**: Cards immediately available for play
- **Error Handling**: Clear feedback for invalid/already activated cards

### 3. Match Game Flow
```
Match Game → Hero Selection → Opponent Matching → Arena Reveal → Gameplay → Results
```

#### A. Hero Selection
- **NFC Scan Required**: Player must scan a Creature or Structure card
- **Hero Preview**: Show card stats, abilities, energy generation
- **Confirmation**: Visual confirmation before locking in choice
- **Opponent Waiting**: Show "Waiting for opponent..." with animations

#### B. Arena Assignment & Reveal
- **Random Generation**: Server selects arena after both heroes chosen
- **Video Introduction**: 30-60 second arena introduction video
- **Arena Advantages**: Visual display of mana color advantages
- **Storytelling**: Lore text and atmospheric details
- **Transition**: Smooth fade to game board

#### C. Gameplay Interface
```
Game Board Layout:
┌─────────────────────────────────────────────────────────────┐
│ Opponent Info: Health, Energy, Mana, Equipment             │
├─────────────────────────────────────────────────────────────┤
│ Arena Info: Name, Color, Current Objective, Timer          │
├─────────────────────────────────────────────────────────────┤
│ Game Board: Hero Zones, Equipment Slots, Active Effects    │
├─────────────────────────────────────────────────────────────┤
│ Your Info: Health, Energy, Mana, Equipment                 │
├─────────────────────────────────────────────────────────────┤
│ Turn Info: Phase, Timer, Available Actions                 │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Turn Structure Implementation

### Turn Phases (60 seconds total)
1. **Start Phase** (5-10 seconds)
   - **Mana Generation**: Visual animation of mana crystals appearing
   - **Energy Generation**: Hero glows, energy counter updates
   - **Arena Effects**: Apply passive effects with visual feedback
   - **Status Updates**: Show any ongoing effects, timers

2. **Main Phase** (35-45 seconds)
   - **Hero Summoning**: Scan new hero card to replace current
   - **Action Cards**: Scan Instant/Sorcery cards for immediate effects
   - **Equipment**: Scan Relic cards to attach to hero
   - **Abilities**: Touch hero to activate special abilities

3. **Attack Phase** (5-10 seconds)
   - **Attack Declaration**: Touch hero to declare attack
   - **Reaction Window**: Opponent has 10 seconds for Instant reactions
   - **Damage Resolution**: Animated combat with visual effects

4. **End Phase** (5 seconds)
   - **Focus Banking**: Choose to save unused energy
   - **End Effects**: Resolve any end-of-turn triggers
   - **Turn Transition**: Pass to opponent with visual handoff

### NFC Integration Points
- **Hero Selection**: Scan creature/structure for starting hero
- **Card Play**: Scan any card during appropriate phase
- **Equipment**: Scan relics to attach to hero
- **Arsenal Building**: Pre-match scanning of available cards

## 🎬 Video System Architecture

### Video Clip Categories
```
assets/videos/
├── arenas/
│   ├── sunspire_plateau/
│   │   ├── intro.mp4
│   │   ├── ambient.mp4
│   │   ├── advantage_radiant.mp4
│   │   └── victory.mp4
│   └── shadow_depths/
│       ├── intro.mp4
│       ├── ambient.mp4
│       ├── advantage_obsidian.mp4
│       └── victory.mp4
├── cards/
│   ├── reveals/
│   │   ├── RADIANT-001_reveal.mp4
│   │   └── AZURE-014_reveal.mp4
│   └── actions/
│       ├── summon_creature.mp4
│       └── cast_spell.mp4
├── ui/
│   ├── turn_transitions/
│   ├── phase_changes/
│   └── victory_animations/
└── story/
    ├── intro_sequence.mp4
    └── tutorial_clips/
```

### Video Triggers
- **Arena Introduction**: When arena is revealed
- **Card Reveals**: When new cards are activated
- **Turn Transitions**: Between players
- **Phase Changes**: Start/Main/Attack/End phases
- **Special Events**: Critical hits, special abilities
- **Match Results**: Victory/defeat animations

## 🗄️ Database Schema Extensions

### Arena System
```sql
-- Arena definitions
CREATE TABLE arenas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    mana_color VARCHAR(20) NOT NULL,
    passive_effect JSONB,
    objective JSONB,
    hazard JSONB,
    story_text TEXT,
    video_intro_path VARCHAR(255),
    video_ambient_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Arena video clips
CREATE TABLE arena_clips (
    id SERIAL PRIMARY KEY,
    arena_id INTEGER REFERENCES arenas(id),
    clip_type VARCHAR(50), -- 'intro', 'ambient', 'advantage', 'victory'
    file_path VARCHAR(255),
    trigger_condition JSONB,
    duration_seconds INTEGER
);

-- Match arena assignments
ALTER TABLE matches ADD COLUMN arena_id INTEGER REFERENCES arenas(id);
```

### Turn System
```sql
-- Turn tracking
CREATE TABLE match_turns (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    turn_number INTEGER,
    current_player_team INTEGER,
    phase VARCHAR(20), -- 'start', 'main', 'attack', 'end'
    phase_start_at TIMESTAMP,
    phase_duration_ms INTEGER,
    actions_taken JSONB[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Card actions in matches
CREATE TABLE match_card_actions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    turn_id INTEGER REFERENCES match_turns(id),
    player_id INTEGER REFERENCES players(id),
    nfc_card_id INTEGER REFERENCES nfc_cards(id),
    action_type VARCHAR(50), -- 'summon', 'cast', 'equip', 'activate'
    action_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    response_time_ms INTEGER -- Time from scan to action
);
```

## 🎮 Console Implementation Plan

### 1. Main Menu Scene
```gdscript
# MainMenu.gd
extends Control

@onready var player_info = $PlayerInfo
@onready var match_button = $MatchGameButton
@onready var collection_button = $CollectionButton
@onready var nfc_status = $NFCStatus

func _ready():
    setup_player_info()
    start_nfc_monitoring()
    
func setup_player_info():
    player_info.get_node("Name").text = Global.player_display_name
    player_info.get_node("Level").text = "Level " + str(Global.player_level)
    player_info.get_node("ELO").text = "ELO: " + str(Global.player_elo)
```

### 2. Hero Selection Scene
```gdscript
# HeroSelection.gd
extends Control

signal hero_selected(card_data)

@onready var instruction_label = $Instructions
@onready var scanned_card_display = $ScannedCard
@onready var confirm_button = $ConfirmButton

func _ready():
    instruction_label.text = "Scan your starting Hero (Creature or Structure)"
    NFCManager.card_scanned.connect(_on_card_scanned)
    
func _on_card_scanned(card_data):
    if card_data.category in ["CREATURE", "STRUCTURE"]:
        display_hero_preview(card_data)
        confirm_button.visible = true
    else:
        show_error("Please scan a Creature or Structure card")
```

### 3. Arena Reveal Scene
```gdscript
# ArenaReveal.gd
extends Control

@onready var video_player = $VideoPlayer
@onready var arena_info = $ArenaInfo
@onready var advantage_display = $AdvantageDisplay

func reveal_arena(arena_data):
    # Play arena introduction video
    var video_path = "res://assets/videos/arenas/" + arena_data.name.to_lower() + "/intro.mp4"
    video_player.stream = load(video_path)
    video_player.play()
    
    # Show arena information
    arena_info.get_node("Name").text = arena_data.name
    arena_info.get_node("Color").text = arena_data.mana_color
    
    # Check for arena advantage
    if Global.player_hero_color == arena_data.mana_color:
        show_arena_advantage()
```

### 4. Game Board Scene
```gdscript
# GameBoard.gd
extends Control

@onready var opponent_zone = $OpponentZone
@onready var arena_zone = $ArenaZone  
@onready var player_zone = $PlayerZone
@onready var turn_timer = $TurnTimer
@onready var phase_indicator = $PhaseIndicator

var current_game_state = {}
var nfc_scan_enabled = false

func _ready():
    RealtimeClient.message_received.connect(_on_realtime_message)
    NFCManager.card_scanned.connect(_on_card_scanned)
    
func _on_realtime_message(message):
    match message.type:
        "match.start":
            initialize_match(message)
        "state.apply":
            apply_state_update(message.patch)
        "timer.tick":
            update_timer_display(message)
        "card.played":
            animate_card_action(message)
```

## 📋 Implementation Todos

<function_calls>
<invoke name="todo_write">
<parameter name="merge">false
