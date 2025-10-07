# 🎯 **DECKPORT BATTLE ABILITIES REFERENCE**

Complete catalog of all card abilities in the Deckport battle system.

---

## 📋 **Ability Categories**

### **⚔️ DAMAGE ABILITIES**

#### **deal_damage**
- **Description**: Deal X damage to target
- **Parameters**: `amount`, `target_type`
- **Animation**: `damage_burst`
- **Video**: `abilities/deal_damage.mp4`
- **Example**: Deal 3 damage to any target

#### **fire_damage**
- **Description**: Deal X fire damage to target
- **Parameters**: `amount`, `target_type`
- **Animation**: `fire_burst`
- **Video**: `abilities/fire_damage.mp4`
- **Arena Synergy**: +1 damage in CRIMSON arenas

#### **water_damage**
- **Description**: Deal X water damage to target
- **Parameters**: `amount`, `target_type`
- **Animation**: `water_burst`
- **Video**: `abilities/water_damage.mp4`
- **Arena Synergy**: +1 damage in AZURE arenas

#### **piercing_damage**
- **Description**: Deal X damage that ignores armor
- **Parameters**: `amount`, `target_type`
- **Animation**: `pierce_strike`
- **Video**: `abilities/piercing_damage.mp4`
- **Special**: Bypasses defense bonuses

#### **area_damage**
- **Description**: Deal X damage to all enemies
- **Parameters**: `amount`
- **Animation**: `explosion`
- **Video**: `abilities/area_damage.mp4`
- **Target**: All enemy creatures

---

### **💚 HEALING ABILITIES**

#### **heal**
- **Description**: Restore X health to target
- **Parameters**: `amount`, `target_type`
- **Animation**: `healing_light`
- **Video**: `abilities/heal.mp4`
- **Example**: Heal 5 health to any ally

#### **regeneration**
- **Description**: Heal X health at start of each turn
- **Parameters**: `amount`, `duration`
- **Animation**: `regen_aura`
- **Video**: `abilities/regeneration.mp4`
- **Duration**: Lasts for specified turns

#### **area_heal**
- **Description**: Heal X to all allies
- **Parameters**: `amount`
- **Animation**: `healing_wave`
- **Video**: `abilities/area_heal.mp4`
- **Target**: All allied creatures

---

### **📈 BUFF ABILITIES**

#### **buff_attack**
- **Description**: Increase target's attack by X
- **Parameters**: `amount`, `duration`, `target_type`
- **Animation**: `power_up`
- **Video**: `abilities/buff_attack.mp4`
- **Example**: +2 attack for 3 turns

#### **buff_defense**
- **Description**: Increase target's defense by X
- **Parameters**: `amount`, `duration`, `target_type`
- **Animation**: `shield_up`
- **Video**: `abilities/buff_defense.mp4`
- **Example**: +3 defense for 2 turns

---

### **📉 DEBUFF ABILITIES**

#### **debuff_attack**
- **Description**: Decrease target's attack by X
- **Parameters**: `amount`, `duration`, `target_type`
- **Animation**: `weakness`
- **Video**: `abilities/debuff_attack.mp4`
- **Example**: -2 attack for 2 turns

#### **debuff_defense**
- **Description**: Decrease target's defense by X
- **Parameters**: `amount`, `duration`, `target_type`
- **Animation**: `armor_break`
- **Video**: `abilities/debuff_defense.mp4`
- **Example**: -1 defense for 3 turns

---

### **🔥 STATUS EFFECTS**

#### **burn**
- **Description**: Deal X fire damage at start of each turn
- **Parameters**: `amount`, `duration`
- **Animation**: `burning_effect`
- **Video**: `abilities/burn.mp4`
- **Example**: 2 fire damage for 3 turns

#### **freeze**
- **Description**: Target cannot act for X turns
- **Parameters**: `duration`
- **Animation**: `ice_prison`
- **Video**: `abilities/freeze.mp4`
- **Effect**: Skip turns completely

#### **poison**
- **Description**: Deal X damage at start of each turn
- **Parameters**: `amount`, `duration`
- **Animation**: `poison_cloud`
- **Video**: `abilities/poison.mp4`
- **Example**: 1 poison damage for 4 turns

#### **stun**
- **Description**: Target skips next turn
- **Parameters**: `duration`
- **Animation**: `lightning_stun`
- **Video**: `abilities/stun.mp4`
- **Duration**: Usually 1 turn

---

### **⚡ RESOURCE ABILITIES**

#### **gain_energy**
- **Description**: Gain X energy this turn
- **Parameters**: `amount`
- **Animation**: `energy_surge`
- **Video**: `abilities/gain_energy.mp4`
- **Example**: Gain 2 extra energy

#### **gain_mana**
- **Description**: Gain X mana of specified color
- **Parameters**: `amount`, `color`
- **Animation**: `mana_crystal`
- **Video**: `abilities/gain_mana.mp4`
- **Example**: Gain 1 CRIMSON mana

#### **mana_burn**
- **Description**: Remove X mana from opponent
- **Parameters**: `amount`, `color`
- **Animation**: `mana_drain`
- **Video**: `abilities/mana_burn.mp4`
- **Effect**: Disrupts opponent's strategy

---

### **🃏 CARD MANIPULATION**

#### **draw_card**
- **Description**: Draw X cards from deck
- **Parameters**: `amount`
- **Animation**: `card_draw`
- **Video**: `abilities/draw_card.mp4`
- **Note**: Physical card game - simulated effect

#### **discard_card**
- **Description**: Force opponent to discard X cards
- **Parameters**: `amount`
- **Animation**: `card_discard`
- **Video**: `abilities/discard_card.mp4`
- **Effect**: Reduces opponent's options

---

### **✨ SPECIAL ABILITIES**

#### **teleport**
- **Description**: Move target to different position
- **Parameters**: `target_type`
- **Animation**: `teleport_flash`
- **Video**: `abilities/teleport.mp4`
- **Effect**: Repositioning on battlefield

#### **reflect_damage**
- **Description**: Return X% of damage taken to attacker
- **Parameters**: `percentage`, `duration`
- **Animation**: `mirror_shield`
- **Video**: `abilities/reflect_damage.mp4`
- **Example**: 50% damage reflection for 2 turns

#### **immunity**
- **Description**: Immune to specified damage type
- **Parameters**: `damage_type`, `duration`
- **Animation**: `immunity_aura`
- **Video**: `abilities/immunity.mp4`
- **Types**: fire, water, physical, magical

#### **life_steal**
- **Description**: Heal for X% of damage dealt
- **Parameters**: `percentage`
- **Animation**: `life_drain`
- **Video**: `abilities/life_steal.mp4`
- **Example**: Heal for 25% of damage dealt

---

### **🌟 ULTIMATE ABILITIES**

#### **ultimate_fire_storm**
- **Description**: Deal massive fire damage to all enemies
- **Parameters**: `base_damage`
- **Animation**: `fire_storm`
- **Video**: `abilities/ultimate_fire_storm.mp4`
- **Cost**: High energy + CRIMSON mana
- **Effect**: 8+ damage to all enemies

#### **ultimate_ice_age**
- **Description**: Freeze all enemies for multiple turns
- **Parameters**: `duration`
- **Animation**: `ice_age`
- **Video**: `abilities/ultimate_ice_age.mp4`
- **Cost**: High energy + AZURE mana
- **Effect**: Freeze all enemies for 2-3 turns

#### **ultimate_nature_wrath**
- **Description**: Massive healing and damage over time
- **Parameters**: `heal_amount`, `damage_amount`, `duration`
- **Animation**: `nature_wrath`
- **Video**: `abilities/ultimate_nature_wrath.mp4`
- **Cost**: High energy + VERDANT mana
- **Effect**: Heal allies, damage enemies over time

---

## 🎯 **Target Types**

| Target Type | Description |
|-------------|-------------|
| `self` | The card/creature itself |
| `ally` | Any allied target |
| `enemy` | Any enemy target |
| `any` | Any target on battlefield |
| `all_allies` | All allied creatures |
| `all_enemies` | All enemy creatures |
| `all` | All creatures on battlefield |
| `random_enemy` | Randomly selected enemy |
| `random_ally` | Randomly selected ally |

---

## 🎬 **Animation System**

### **Animation Types**
- **damage_burst**: Quick damage flash effect
- **fire_burst**: Fire explosion with particles
- **water_burst**: Water splash with ripples
- **healing_light**: Golden healing glow
- **power_up**: Red strength aura
- **shield_up**: Blue defensive barrier
- **burning_effect**: Continuous fire damage
- **ice_prison**: Freezing ice crystallization
- **energy_surge**: Lightning energy boost
- **mana_crystal**: Colored mana manifestation
- **explosion**: Large area explosion
- **teleport_flash**: Instant movement effect

### **Video Integration**
- Each ability has a **2-second video clip**
- Videos play in **transparent card overlay**
- **Sequential playback** for multiple abilities
- **Fallback animations** if video unavailable

---

## 🏟️ **Arena Interactions**

### **Arena Bonuses**
- **CRIMSON Arena**: Fire abilities +1 damage
- **AZURE Arena**: Water abilities +1 damage, spell cost -1
- **VERDANT Arena**: Healing abilities +1 effectiveness
- **GOLDEN Arena**: Buff abilities +1 duration
- **SHADOW Arena**: Debuff abilities +1 effectiveness
- **AETHER Arena**: No specific bonuses (neutral)

### **Arena Penalties**
- **Opposing colors** get -1 effectiveness
- **Wrong arena** may increase mana costs
- **Hero mismatch** reduces ability power

---

## 🔧 **Implementation Notes**

### **Dynamic Ability System**
- All abilities are **catalogued** in `CardAbilitiesCatalog`
- **Validation** ensures only defined abilities are used
- **Parameter checking** prevents invalid ability configurations
- **Video paths** are automatically resolved

### **Card Validation**
```gdscript
# Example card with abilities
{
    "name": "Fire Elemental",
    "energy_cost": 3,
    "mana_cost": {"CRIMSON": 2},
    "abilities": [
        {
            "name": "fire_damage",
            "parameters": {"amount": 4, "target_type": "enemy"}
        },
        {
            "name": "burn",
            "parameters": {"amount": 2, "duration": 2}
        }
    ]
}
```

### **Ability Execution**
1. **Validate** ability exists in catalog
2. **Check** required parameters
3. **Apply** game effects
4. **Play** animation and video
5. **Update** game state

---

## 📊 **Balance Guidelines**

### **Energy Costs**
- **Low Energy (1-2)**: Simple effects, low damage
- **Medium Energy (3-4)**: Moderate effects, good damage
- **High Energy (5+)**: Powerful effects, high damage

### **Mana Requirements**
- **Single Color**: Focused, powerful effects
- **Multi-Color**: Versatile, balanced effects
- **Colorless (AETHER)**: Neutral, utility effects

### **Duration Balance**
- **Instant**: Immediate impact, no ongoing effect
- **Short (1-2 turns)**: Quick tactical advantage
- **Long (3+ turns)**: Strategic positioning, higher cost

---

**This comprehensive ability system creates deep, strategic gameplay while maintaining the physical card experience that makes Deckport unique!** 🎯⚔️✨











