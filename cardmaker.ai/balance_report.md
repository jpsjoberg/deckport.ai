## Deckport Balance Report

### Totals
- Totals: ACTION: 600, CREATURE: 599, STRUCTURE: 594

### Efficiency (power/(mana+energy))
- mean: 1.10
- median: 1.23
- sd: 0.44
- q10/q50/q90: 0.33 / 1.23 / 1.60

### Lowest efficiency (15)
- Polar Break Crush: 0.33
- Star Lance Shatter: 0.33
- Frost Pulse Pierce: 0.33
- Mist Step Shatter: 0.33
- Polar Break Flow: 0.33
- Tide Surge Sweep: 0.33
- Echo Wave Spiral: 0.33
- Echo Wave Pierce: 0.33
- Nimbus Arc Sweep: 0.33
- Frost Pulse Shatter: 0.33
- Tide Surge Pierce: 0.33
- Mist Step Sweep: 0.33
- Nimbus Arc Spiral: 0.33
- Echo Wave Flow: 0.33
- Frost Pulse Cascade: 0.33

### Highest efficiency (15)
- Star Observatory: 1.93
- Frost Harbor: 1.93
- Crystal Library: 1.93
- Nimbus Array: 1.93
- Echo Library: 1.93
- Sky Harbor: 1.93
- Wave Causeway: 1.93
- Star Library: 1.93
- Frost Causeway: 1.93
- Echo Gate: 1.93
- Crystal Causeway: 1.93
- Wave Atrium: 1.93
- Aether Harbor: 1.93
- Crystal Harbor: 1.93
- Polar Gate: 1.93

### Energy Economy
- Average base energy per turn (heroes): 1.97
- Actions playable with 1 energy: 200/600 (33.3%)
- Actions playable with 2 energy: 382/600 (63.7%)
- Actions playable with 3 energy: 600/600 (100.0%)
- Actions playable with 4 energy: 600/600 (100.0%)
- Hero time-to-afford (no arena bonus): mean 1.00, median 1
- Hero time-to-afford (+1 arena): mean 1.00, median 1

### Mana Economy (Summoning Heroes)
- Mana cost (heroes): mean 4.46, median 4, q10/q50/q90: 3/4/6
- Turns to summon (baseline, +1 mana/turn, no discount): mean 4.46, median 4
- Turns to summon (arena discount -1): mean 3.46, median 3
- Turns to summon (arena -1 + channel when EPT>=2): mean 2.19, median 2
- Heroes summonable by turn 2: base 9.5%, arena 30.8%, arena+channel 72.0%
- Heroes summonable by turn 3: base 30.8%, arena 51.5%, arena+channel 100.0%

### Color Breakdown
Color-level stats for costs and efficiency.
- AETHER:
  - cards: 300 (heroes 200, actions 100)
  - mana_cost mean/median: 2.99/3
  - energy_cost mean/median: 1.76/2
  - efficiency mean/median: 1.10/1.23
  - actions playable with 1 energy: 35/100 (35.0%)
  - actions playable with 2 energy: 59/100 (59.0%)
  - actions playable with 3 energy: 100/100 (100.0%)
- AZURE:
  - cards: 299 (heroes 199, actions 100)
  - mana_cost mean/median: 2.93/3
  - energy_cost mean/median: 1.76/2
  - efficiency mean/median: 1.10/1.23
  - actions playable with 1 energy: 29/100 (29.0%)
  - actions playable with 2 energy: 59/100 (59.0%)
  - actions playable with 3 energy: 100/100 (100.0%)
- CRIMSON:
  - cards: 294 (heroes 194, actions 100)
  - mana_cost mean/median: 2.98/3
  - energy_cost mean/median: 1.73/2
  - efficiency mean/median: 1.09/1.23
  - actions playable with 1 energy: 32/100 (32.0%)
  - actions playable with 2 energy: 71/100 (71.0%)
  - actions playable with 3 energy: 100/100 (100.0%)
- OBSIDIAN:
  - cards: 300 (heroes 200, actions 100)
  - mana_cost mean/median: 2.97/3
  - energy_cost mean/median: 1.73/2
  - efficiency mean/median: 1.11/1.23
  - actions playable with 1 energy: 33/100 (33.0%)
  - actions playable with 2 energy: 62/100 (62.0%)
  - actions playable with 3 energy: 100/100 (100.0%)
- RADIANT:
  - cards: 300 (heroes 200, actions 100)
  - mana_cost mean/median: 2.89/3
  - energy_cost mean/median: 1.70/2
  - efficiency mean/median: 1.11/1.23
  - actions playable with 1 energy: 34/100 (34.0%)
  - actions playable with 2 energy: 66/100 (66.0%)
  - actions playable with 3 energy: 100/100 (100.0%)
- VERDANT:
  - cards: 300 (heroes 200, actions 100)
  - mana_cost mean/median: 3.02/3
  - energy_cost mean/median: 1.71/2
  - efficiency mean/median: 1.10/1.23
  - actions playable with 1 energy: 37/100 (37.0%)
  - actions playable with 2 energy: 65/100 (65.0%)
  - actions playable with 3 energy: 100/100 (100.0%)

### Rules Appendix: Mana Production
- Each turn, you gain 1 Mana per color you have in play (baseline).
- Arena Advantage: the first matching-color card you play each turn costs 1 less Mana (minimum 1).
- Channel (smoothing): once per turn, convert 2 Energy → 1 Mana of your hero’s color.
- Focus (smoothing): at end of turn, you may bank 1 unused Energy as a Focus counter (max 2) to spend later as Energy.

