# 🎮 Deckport Card System Architecture

## 🏗️ **Two-Tier System Overview**

The Deckport card system uses a **two-tier architecture** that separates card designs from physical card instances:

### **Tier 1: Card Templates (Raw Cards)**
- **Purpose**: Base card designs and sets created by admins
- **AI Generated**: Artwork created via ComfyUI integration
- **Reusable**: One template can create many NFC card instances
- **Managed**: Through admin panel card management system

### **Tier 2: NFC Card Instances (Unique Physical Cards)**
- **Purpose**: Unique physical cards owned by players
- **Evolutionary**: Can gain experience and evolve beyond base template
- **Trackable**: Complete history of matches, evolutions, and ownership
- **Tradeable**: Can change owners while maintaining history

---

## 📊 **Database Structure**

### **🎨 Card Templates (Admin-Managed)**

```sql
-- Card Sets (Collections like "Open Portal", "Shadow Realm", etc.)
card_sets
├── id, slug, name, description, version
├── is_active, created_by_admin
└── created_at, updated_at

-- Base Card Templates (AI-Generated Designs)
card_templates
├── id, card_set_id, slug, name
├── category, rarity, legendary, primary_color
├── energy_cost, equipment_slots, keywords
├── description, flavor_text
├── is_active, is_published
└── created_by_admin, created_at, updated_at

-- Template Properties
card_template_stats          → attack, defense, health, energy_per_turn
card_template_mana_costs     → color-specific mana requirements
card_template_targeting      → targeting rules (friendly/enemy/self)
card_template_limits         → usage limits and charge rules
card_template_effects        → gameplay effects and triggers
card_template_abilities      → special abilities and ultimates
card_template_art_generations → ComfyUI generation history
```

### **🎴 NFC Card Instances (Player-Owned)**

```sql
-- Unique Physical Cards
nfc_card_instances
├── id, template_id, ntag_uid (unique NFC identifier)
├── instance_name, serial_number
├── current_owner_id, status
├── evolution_level, experience_points
├── total_matches_played, total_wins
├── custom_stats, custom_abilities, custom_effects
└── mint_date, first_activation, last_used

-- Evolution History
card_evolutions
├── id, card_instance_id
├── evolution_trigger, evolution_level
├── stat_changes, ability_changes, effect_changes
├── evolution_description, trigger_context
└── evolution_date, triggered_by_admin

-- Match Performance Tracking
card_match_participations
├── id, card_instance_id, match_id
├── damage_dealt, damage_taken, abilities_used
├── match_won, experience_gained
└── played_at

-- Card Fusion Events
card_fusions
├── id, source_card_ids[], result_card_id
├── fusion_type, fusion_recipe
├── fusion_date, performed_by_player
```

---

## 🔄 **Workflow Examples**

### **1. Admin Creates New Card Design**
```
1. Admin uses /admin/cards/generate
2. Enters card properties and AI art prompt
3. System creates CardTemplate with base stats
4. ComfyUI generates artwork
5. Template is ready for NFC production
```

### **2. NFC Card Production**
```
1. Template is marked as "published"
2. Physical NFC cards are manufactured
3. Each NFC gets unique ntag_uid
4. NFCCardInstance created linking to template
5. Cards are distributed to players
```

### **3. Player Uses Card**
```
1. Player scans NFC card at console
2. System loads NFCCardInstance data
3. If first use, inherits all template properties
4. If evolved, uses custom_stats/abilities
5. Match performance tracked in card_match_participations
```

### **4. Card Evolution**
```
1. Card gains experience from matches
2. Triggers evolution event (XP threshold, special achievement)
3. CardEvolution record created with changes
4. NFCCardInstance.custom_stats updated
5. Card now differs from original template
```

---

## 🎯 **Key Benefits**

### **For Admins:**
- ✅ **Efficient Design**: Create one template, mint many cards
- ✅ **Version Control**: Track template changes across sets
- ✅ **AI Integration**: Automated artwork generation
- ✅ **Set Management**: Organize cards into themed collections

### **For Players:**
- ✅ **Unique Cards**: Each NFC card can become truly unique
- ✅ **Evolution**: Cards grow stronger through play
- ✅ **History**: Complete record of card's journey
- ✅ **Trading Value**: Evolved cards more valuable than base

### **For System:**
- ✅ **Scalability**: Efficient storage and querying
- ✅ **Flexibility**: Support complex game mechanics
- ✅ **Analytics**: Rich data for balance and engagement
- ✅ **Integrity**: Proper relationships and constraints

---

## 🔧 **Admin Panel Integration**

### **Template Management** (`/admin/cards`)
- **Dashboard**: Overview of all templates and sets
- **Generate**: Create new templates with AI art
- **Review**: Browse, edit, and manage templates
- **Publish**: Mark templates ready for NFC production

### **Instance Management** (`/admin/nfc-cards`)
- **Production**: Create NFC instances from templates
- **Tracking**: Monitor card distribution and ownership
- **Evolution**: View and manage card evolution events
- **Analytics**: Performance and usage statistics

---

## 🚀 **Migration Path**

1. **Run Migration**: `python migrations/setup_card_system.py`
2. **Import Existing**: Migrate current SQLite cards to templates
3. **Create Instances**: Convert existing NFC cards to new system
4. **Test Integration**: Verify admin panel functionality
5. **Go Live**: Start using two-tier system for new cards

This architecture ensures that your card system can handle both the creative design process (templates) and the unique physical card lifecycle (instances) while maintaining data integrity and supporting complex game mechanics! 🎮✨

