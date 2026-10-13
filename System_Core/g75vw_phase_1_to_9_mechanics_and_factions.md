# G75VW Phase 1–9 Engine Mechanics, Mastery Perks, Grafts & Geopolitical Factions

Canonical mechanical architecture from `backend/mechanics.py` on `ROG_G75VW`.

## `AETHER_WEATHER` (5 entries)
```json
{
  "clear_skies": {
    "id": "clear_skies",
    "name": "Clear Aether-Skies",
    "label": "☀️ Clear Aether-Skies",
    "icon": "☀️",
    "desc": "Temperate atmospheric conditions across Warren County. Normal movement and combat parameters.",
    "effect": "Standard baseline. Fast-travel and exploration operate at normal speed.",
    "ranged_atk_mod": 0,
    "stealth_mod": 0,
    "spell_dmg_pct": 0,
    "travel_allowed": true
  },
  "runic_mist": {
    "id": "runic_mist",
    "name": "Runic Mist",
    "label": "🌫️ Runic Mist",
    "icon": "🌫️",
    "desc": "Dense, glowing mana-vapor blankets the valley floor, distorting distances and acoustic telemetry.",
    "effect": "-4 to Ranged Attack rolls, +3 to Stealth checks. Fast travel disabled through thick fog.",
    "ranged_atk_mod": -4,
    "stealth_mod": 3,
    "spell_dmg_pct": 0,
    "travel_allowed": false
  },
  "leyline_storm": {
    "id": "leyline_storm",
    "name": "Leyline Overload Storm",
    "label": "⚡ Leyline Overload Storm",
    "icon": "⚡",
    "desc": "Violent arcane discharge cascades between mountain ridge towers. Atmospheric static crackles.",
    "effect": "+25% Spell and Arcane damage. Cyber-constructs and golems are enraged (+2 ATK).",
    "ranged_atk_mod": -2,
    "stealth_mod": -2,
    "spell_dmg_pct": 25,
    "travel_allowed": true
  },
  "crimson_ash": {
    "id": "crimson_ash",
    "name": "Crimson Ash Fall",
    "label": "🌋 Crimson Ash Fall",
    "icon": "🌋",
    "desc": "Blood-red fallout drifts from high-altitude rift fissures, signaling a roaming Apex World-Boss.",
    "effect": "Healing efficiency halved (-50% HP recovery). Wandering boss aggression quadrupled.",
    "ranged_atk_mod": -1,
    "stealth_mod": 1,
    "healing_mult": 0.5,
    "travel_allowed": true
  },
  "glitch_freeze": {
    "id": "glitch_freeze",
    "name": "Glitch-Freeze Blizzard",
    "label": "❄️ Glitch-Freeze Blizzard",
    "icon": "❄️",
    "desc": "Crystalline polygon snow and sub-zero aetheric cold. Movement halved; cold exposure hazard.",
    "effect": "Movement halved. Extreme cold damage unless insulated (Banki's Dire-Wolf Mantle protects him!).",
    "ranged_atk_mod": -2,
    "stealth_mod": -1,
    "speed_mult": 0.5,
    "cold_exposure": true,
    "travel_allowed": false
  }
}
```

## `ARCHETYPE_HP_GROWTH` (8 entries)
```json
{
  "warrior": 35,
  "cleric": 28,
  "engineer": 28,
  "ranger": 28,
  "thief": 24,
  "psion": 24,
  "mage": 20,
  "pathless": 25
}
```

## `BODY_GRAFT_SLOTS` (13 entries)
```json
[
  "arm_left",
  "arm_right",
  "leg_left",
  "leg_right",
  "spine",
  "ocular",
  "dermal",
  "neural",
  "head",
  "torso",
  "left_arm",
  "right_arm",
  "legs"
]
```

## `CAMPFIRE_RECIPES` (4 entries)
```json
{
  "wolf_heart_stew": {
    "id": "wolf_heart_stew",
    "name": "Wolf-Heart Marrow Stew",
    "desc": "Thick, steaming marrow broth infused with wild roots that supercharges physical vigor.",
    "ingredients": {
      "Wolf Marrow": 1,
      "Wild Roots": 1
    },
    "buff": {
      "name": "[Wolf-Heart Vigor]",
      "desc": "+15 Maximum HP and +2 STR for 5 turns.",
      "hp_bonus": 15,
      "str_bonus": 2,
      "duration": 5
    }
  },
  "roasted_boar_ribs": {
    "id": "roasted_boar_ribs",
    "name": "Roasted Boar Ribs",
    "desc": "Crispy charred ribs seasoned with salted rock-moss, packing dense caloric fortification.",
    "ingredients": {
      "Raw Boar Flank": 1,
      "Salted Moss": 1
    },
    "buff": {
      "name": "[Boar's Resilience]",
      "desc": "+20 Temporary HP and +2 Physical Damage for 5 turns.",
      "temp_hp": 20,
      "phys_dmg_bonus": 2,
      "duration": 5
    }
  },
  "spiced_herb_broth": {
    "id": "spiced_herb_broth",
    "name": "Spiced Aether-Herb Broth",
    "desc": "Fragrant herbal infusion that clears mental strain and accelerates combat momentum.",
    "ingredients": {
      "Aether-Herb": 1,
      "Bottled Water": 1
    },
    "buff": {
      "name": "[Aetheric Focus]",
      "desc": "+20% Resource generation and cleanses fatigue.",
      "resource_regen_pct": 20,
      "cleanses_fatigue": true,
      "duration": 5
    }
  },
  "dire_scavenger_skewer": {
    "id": "dire_scavenger_skewer",
    "name": "Dire Scavenger Skewer",
    "desc": "Quick field skewer seasoned with runic lichen, heightening predatory reflex.",
    "ingredients": {
      "Scrap Meat": 1,
      "Runic Lichen": 1
    },
    "buff": {
      "name": "[Scavenger's Grit]",
      "desc": "+10 HP recovery and +10% Critical strike chance for 5 turns.",
      "hp_recovery": 10,
      "crit_chance_pct": 10,
      "duration": 5
    }
  }
}
```

## `CANONICAL_GRAFTS` (12 entries)
```json
{
  "golem_hydraulic_arm": {
    "key": "golem_hydraulic_arm",
    "name": "Golem Hydraulic Arm",
    "allowed_slots": [
      "arm_left",
      "arm_right"
    ],
    "strain": 15,
    "col_cost": 2500,
    "stat_bonuses": {
      "STR": 2
    },
    "description": "Titan-hydraulic pistons allow single-handed structural crushing and grant +2 STR checks.",
    "effect": "+2 STR, +10 unarmed bludgeoning damage"
  },
  "aether_resonant_ocular": {
    "key": "aether_resonant_ocular",
    "name": "Aether-Resonant Ocular",
    "allowed_slots": [
      "ocular"
    ],
    "strain": 10,
    "col_cost": 1800,
    "stat_bonuses": {
      "WIS": 2
    },
    "description": "Crystalline runic lens revealing invisible entities, secret conduits, and ley-line currents.",
    "effect": "+2 WIS, Darkvision (120ft) & Ley-Line Sight (+3 to investigate secrets)"
  },
  "subdermal_carapace_weave": {
    "key": "subdermal_carapace_weave",
    "name": "Subdermal Carapace Weave",
    "allowed_slots": [
      "dermal"
    ],
    "strain": 20,
    "col_cost": 3500,
    "stat_bonuses": {
      "CON": 1
    },
    "description": "Flexible graphene-chitin mesh woven beneath skin layers, blunting incoming ballistic and slashing impacts.",
    "effect": "+2 AC, Damage Reduction (DR 2 Physical), +1 CON"
  },
  "spring_loaded_golem_greaves": {
    "key": "spring_loaded_golem_greaves",
    "name": "Spring-Loaded Golem Greaves",
    "allowed_slots": [
      "leg_left",
      "leg_right"
    ],
    "strain": 12,
    "col_cost": 2000,
    "stat_bonuses": {
      "DEX": 1
    },
    "description": "Pneumatic kickback joints amplifying leap distance, running velocity, and acrobatic recovery.",
    "effect": "+10ft Movement Speed, +2 to DEX saving throws, +1 DEX"
  },
  "neural_overclock_cortex": {
    "key": "neural_overclock_cortex",
    "name": "Neural Overclock Cortex",
    "allowed_slots": [
      "neural"
    ],
    "strain": 18,
    "col_cost": 4000,
    "stat_bonuses": {
      "INT": 2
    },
    "description": "Liquid-crystal synaptic booster allowing multi-threaded thought processes and expanded ability memory.",
    "effect": "+2 INT, +1 Active Ability Slot in Matrix Memory"
  },
  "leyline_conduit_spine": {
    "key": "leyline_conduit_spine",
    "name": "Leyline Conduit Spine",
    "allowed_slots": [
      "spine"
    ],
    "strain": 14,
    "col_cost": 3000,
    "stat_bonuses": {
      "WIS": 1,
      "INT": 1
    },
    "description": "Gold-threaded spinal shunt maintaining pure mana flow around metallic limbs, shielding spellcasters from graft interference.",
    "effect": "Harmonizes 2 installed grafts (negates spellcaster penalty), +15 Max Combat Resource"
  },
  "basalt_carapace_plating": {
    "key": "basalt_carapace_plating",
    "name": "Basalt Carapace Plating",
    "type": "biological",
    "allowed_slots": [
      "dermal",
      "torso"
    ],
    "strain": 12,
    "col_cost": 1500,
    "stat_bonuses": {
      "CON": 2
    },
    "description": "Dense calcified scales harvested from quarry behemoths, providing earth-attuned blunt resistance.",
    "effect": "+2 AC, DR 2 Physical, immune to subterranean tremors"
  },
  "silt_marrow_geothermal_core": {
    "key": "silt_marrow_geothermal_core",
    "name": "Silt-Marrow Geothermal Core",
    "type": "biological",
    "allowed_slots": [
      "spine",
      "torso",
      "dermal"
    ],
    "strain": 15,
    "col_cost": 2000,
    "stat_bonuses": {
      "STR": 1,
      "CON": 1
    },
    "description": "An energetic beast heart ventricle pulsing with geothermal steam and volcanic vitality.",
    "effect": "Thermal venting: 1d6 fire retaliation on melee attackers, +10 Fire Resistance"
  },
  "basilisk_venom_gland": {
    "key": "basilisk_venom_gland",
    "name": "Basilisk Venom Gland",
    "type": "biological",
    "allowed_slots": [
      "arm_left",
      "arm_right",
      "left_arm",
      "right_arm"
    ],
    "strain": 10,
    "col_cost": 1800,
    "stat_bonuses": {
      "DEX": 1
    },
    "description": "A harvested serpentine gland wired into arterial ducts to coat blades with necrotic venom.",
    "effect": "Envenomed Strikes: Weapon attacks inflict 1d8 poison damage (DC 14 CON or Poisoned)"
  },
  "wyrm_scale_sheath": {
    "key": "wyrm_scale_sheath",
    "name": "Wyrm-Scale Sheath",
    "type": "biological",
    "allowed_slots": [
      "dermal",
      "torso"
    ],
    "strain": 14,
    "col_cost": 2800,
    "stat_bonuses": {
      "CON": 1,
      "CHA": 1
    },
    "description": "Iridescent draconic epidermal grafting that refracts elemental spells.",
    "effect": "+2 AC, +15 Fire/Lightning resistance, Intimidation advantage"
  },
  "stalker_shadow_tendon": {
    "key": "stalker_shadow_tendon",
    "name": "Stalker Shadow-Tendon",
    "type": "biological",
    "allowed_slots": [
      "leg_left",
      "leg_right",
      "legs"
    ],
    "strain": 10,
    "col_cost": 1600,
    "stat_bonuses": {
      "DEX": 2
    },
    "description": "Elongated predatory muscle fibers woven into leg joints for silent sprint leaps.",
    "effect": "+15ft speed, +4 to Stealth checks, Silent Step perk"
  },
  "chimeric_beast_claws": {
    "key": "chimeric_beast_claws",
    "name": "Chimeric Beast Claws",
    "type": "biological",
    "allowed_slots": [
      "arm_left",
      "arm_right",
      "left_arm",
      "right_arm"
    ],
    "strain": 8,
    "col_cost": 1200,
    "stat_bonuses": {
      "STR": 1
    },
    "description": "Razor-honed obsidian talon sheaths anchored directly into finger phalanges.",
    "effect": "1d8 Slashing Unarmed strike with Bleed (2 bleeding dmg/turn for 3 turns)"
  }
}
```

## `CANONICAL_MILESTONES` (4 entries)
```json
{
  "One-Handed Axes": {
    "50": {
      "name": "Hewing Edge",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 50,
      "skill_name": "One-Handed Axes",
      "tier": "Apprentice",
      "description": "Your strikes find structural seams in armor and hide with ruthless economy of motion.",
      "effect": "+1 to Attack rolls with one-handed axes; attacks deal +2 flat slashing damage and gain 10% critical strike chance against unarmored or light targets."
    },
    "100": {
      "name": "Gale Cleave",
      "type": "Active Sword Skill",
      "target_slot": "spells",
      "threshold": 100,
      "skill_name": "One-Handed Axes",
      "tier": "Journeyman",
      "description": "A 2-hit horizontal centrifugal spin that tears through enemy hitboxes with accelerated momentum.",
      "effect": "Action: 2 consecutive axe strikes at +2 to hit, dealing weapon damage + 1d8 slashing and inflicting [Hemorrhage] (3 bleed/turn for 2 turns)."
    },
    "250": {
      "name": "Bearded Hook",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 250,
      "skill_name": "One-Handed Axes",
      "tier": "Adept",
      "description": "Utilize the recessed beard of your axe blade to catch enemy shields, parry weapons, and manipulate hitboxes.",
      "effect": "Disarming or tripping gains Advantage. When an enemy misses in melee, retaliate with an off-balance hook that reduces target AC by -2 for 1 round."
    },
    "500": {
      "name": "Executioner's Descent",
      "type": "Active Sword Skill / Finisher",
      "target_slot": "spells",
      "threshold": 500,
      "skill_name": "One-Handed Axes",
      "tier": "Master",
      "description": "A devastating overhead vertical leap-cleave focused entirely on the target's primary structural core or neck joint.",
      "effect": "Action: Leap 15 ft; deals 4d10 + STR slashing damage. Ignores 50% DR. If target is below 25% HP, triggers DC 18 CON save vs instant decapitation."
    },
    "750": {
      "name": "Einherjar's Blood-Frenzy",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 750,
      "skill_name": "One-Handed Axes",
      "tier": "Grandmaster",
      "description": "The spirit of the fallen Nordic vanguard infuses your neural interface; physical pain accelerates attack rate.",
      "effect": "For every 10% max HP lost, gain +1 to hit, +2 damage, and +5% attack speed. Critical hits trigger a free cleave on a nearby enemy within 5 ft."
    },
    "1000": {
      "name": "Fenrir's Howling Ruin",
      "type": "Active Sword Skill / Ultimate",
      "target_slot": "spells",
      "threshold": 1000,
      "skill_name": "One-Handed Axes",
      "tier": "Transcendence",
      "description": "A reality-fracturing 5-hit phantom axe combo that shears directly into Cardinal's collision geometry, leaving spatial vacuum tears.",
      "effect": "Action: 5 strikes delivering 10d12 spatial/slashing damage. Bypasses 100% armor/invulnerability. Disables target regeneration for 1 min and creates a 15-ft vortex."
    }
  },
  "Trench Hammers": {
    "50": {
      "name": "Concussive Impact",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 50,
      "skill_name": "Trench Hammers",
      "tier": "Apprentice",
      "description": "Heavy blunt force vibrates through solid protection, transferring trauma directly to interior organs and chassis.",
      "effect": "Blunt attacks ignore 2 points of target AC and deal +2 bludgeoning damage. Successful hits inflict [Disoriented] (-1 on target's next roll)."
    },
    "100": {
      "name": "Pneumatic Back-Pick",
      "type": "Active Sword Skill",
      "target_slot": "spells",
      "threshold": 100,
      "skill_name": "Trench Hammers",
      "tier": "Journeyman",
      "description": "Reversing swing direction, drive the diamond-hard armor-piercing raven-bill or pick into a pressurized joint.",
      "effect": "Action: Strike with rear pick at +2 to hit. Deals 2d8 + STR piercing damage, inflicts -3 permanent AC debuff, and forces DC 14 STR save vs Knockdown."
    },
    "250": {
      "name": "Kinetic Rebound",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 250,
      "skill_name": "Trench Hammers",
      "tier": "Adept",
      "description": "Channel massive recoil vibration of dense alloy strikes back into posture and subsequent swings.",
      "effect": "Blocking/parrying absorbs up to STR mod incoming kinetic damage. Next attack within 1 turn deals +1d6 bonus kinetic damage."
    },
    "500": {
      "name": "Seismic Fracture",
      "type": "Active Sword Skill",
      "target_slot": "spells",
      "threshold": 500,
      "skill_name": "Trench Hammers",
      "tier": "Master",
      "description": "Slam the weighted head of the hammer into bedrock or pavement, propagating a directional piezoelectric seismic shockwave.",
      "effect": "Action: 20-ft cone shockwave. Entities take 4d8 bludgeoning damage and must pass DC 16 DEX save or be knocked Prone and Stunned for 1 turn. Destroys light cover."
    },
    "750": {
      "name": "Colossus Breaker",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 750,
      "skill_name": "Trench Hammers",
      "tier": "Grandmaster",
      "description": "Heavy blunt impacts deform high-density exo-chassis, boss-grade carapace, and golem-grafts on a molecular level.",
      "effect": "Double damage to structures, constructs, golems, and armored chitin. Crits inflict [Fractured Exoskeleton] (+50% damage from all physical sources for 2 turns)."
    },
    "1000": {
      "name": "Mjölnir-Null Singularity",
      "type": "Active Sword Skill / Ultimate",
      "target_slot": "spells",
      "threshold": 1000,
      "skill_name": "Trench Hammers",
      "tier": "Transcendence",
      "description": "Overcharging the depleted-uranium core, bring the hammer down with the crushing gravitational weight of a collapsing star.",
      "effect": "Action: Deals 12d10 dense gravitational bludgeoning damage in a 30-ft radius. Shatters barriers/shields and imposes 100% Gravity Stasis for 3 turns."
    }
  },
  "Field Trapping": {
    "50": {
      "name": "Hair-Trigger Rigging",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 50,
      "skill_name": "Field Trapping",
      "tier": "Apprentice",
      "description": "Rapid deployment techniques allow setting mechanical snares, anchors, and tripwires in seconds.",
      "effect": "Traps deploy 50% faster (deploy tripwires/snares as Bonus Action). +2 to Trap Concealment DC (base DC 14)."
    },
    "100": {
      "name": "Serrated Deadfall Snare",
      "type": "Active Technique",
      "target_slot": "spells",
      "threshold": 100,
      "skill_name": "Field Trapping",
      "tier": "Journeyman",
      "description": "Rig a spring-loaded carbon-line snare armed with micro-serrated barbs and weighted tension pins across a transit path.",
      "effect": "Action: 10-ft snare zone. First creature entering must pass DC 15 DEX save or be [Rooted] for 2 turns, taking 2d6 piercing + 3 bleed/turn."
    },
    "250": {
      "name": "Pheromone Baiting & Marrow-Grafting",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 250,
      "skill_name": "Field Trapping",
      "tier": "Adept",
      "description": "Imbue trap triggers with synthesized marrow mash and biological attractants to manipulate monster aggro scripts.",
      "effect": "Beasts and cyber-monsters within 60 ft must pass DC 15 WIS save or be drawn to baited kill-zones. Traps triggered by baited targets gain +100% crit damage."
    },
    "500": {
      "name": "Micro-Capacitor Overload Trap",
      "type": "Active Technique",
      "target_slot": "spells",
      "threshold": 500,
      "skill_name": "Field Trapping",
      "tier": "Master",
      "description": "Splice a corroded micro-capacitor and copper wiring into a tension net, discharging high-voltage EMP lightning when tripped.",
      "effect": "Action: Detonates in 15-ft radius for 5d8 Lightning damage, paralyzing biologicals (DC 17 CON save) and disabling golems/automatons for 2 turns."
    },
    "750": {
      "name": "Tactical Ambush Mastery",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 750,
      "skill_name": "Field Trapping",
      "tier": "Grandmaster",
      "description": "Seamlessly integrate multiple trap lines into overlapping crossfire kill-boxes.",
      "effect": "Maintain up to 5 active trap zones simultaneously. Party gains Advantage on attack rolls against trapped enemies, with +3d6 sneak attack damage."
    },
    "1000": {
      "name": "Cardinal Net: Spatial Quarantine",
      "type": "Active Technique / Ultimate",
      "target_slot": "spells",
      "threshold": 1000,
      "skill_name": "Field Trapping",
      "tier": "Transcendence",
      "description": "Project a hard-light spatial quarantine grid anchored by anchor pins, sealing an entire battlefield node from the Cardinal network.",
      "effect": "Action: 50-ft containment dome. Prevents teleportation/reinforcements. Enemies take 3d10 neural static damage/turn, lose passive buffs, and cannot evade for 1 min."
    }
  },
  "Cartography": {
    "50": {
      "name": "Topographic Awareness",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 50,
      "skill_name": "Cartography",
      "tier": "Apprentice",
      "description": "Your eye parses elevation gradients, contour lines, and natural choke points with effortless clarity.",
      "effect": "Passive Fog of War reveal radius on Sector 1 Map increased by +25%. Automatically detects low-tier hidden caches and elevation advantage (+1 hit from high ground)."
    },
    "100": {
      "name": "Sub-Level Nav-Mesh Bypass",
      "type": "Active Technique",
      "target_slot": "spells",
      "threshold": 100,
      "skill_name": "Cartography",
      "tier": "Journeyman",
      "description": "Analyze glitching geometry to identify decommissioned maintenance ducts, old subway shafts, and unindexed paths.",
      "effect": "Action (Exploration): Reveals hidden connections and bypasses on the map. Party travel through bypasses reduces encounter threat by 50% and avoids Stalker aggro."
    },
    "250": {
      "name": "Geodetic Triangulation",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 250,
      "skill_name": "Cartography",
      "tier": "Adept",
      "description": "Cross-reference satellite telemetry, radio pings, and ancient colonial survey markers to locate valuable anomalies.",
      "effect": "Detects high-yield resource nodes, hidden vendor caches, and Aether-Wells within a 10-grid radius. Grants Advantage on Initiative checks in mapped sectors."
    },
    "500": {
      "name": "Chorographer's Sight: Ley-Line Mapping",
      "type": "Active Technique",
      "target_slot": "spells",
      "threshold": 500,
      "skill_name": "Cartography",
      "tier": "Master",
      "description": "Project an arcane aetheric compass overlay that traces subterranean mana-currents and firewall boundaries.",
      "effect": "Action: Reveals dungeon bosses, firewall pylons, and corrupted nodes across the sector. Dispels visual illusions, spatial mirages, and false landmarks within 100 ft."
    },
    "750": {
      "name": "Macro-Territory Cartogram",
      "type": "Passive Feat",
      "target_slot": "feats",
      "threshold": 750,
      "skill_name": "Cartography",
      "tier": "Grandmaster",
      "description": "Read macro-geopolitical faction shifts, troop movements, and global glitch-horde migrations before they strike.",
      "effect": "Global Threat Intelligence uplink provides advance warning (1 turn ahead) of roaming elite bosses. Travel across explored nodes consumes 0 supplies; map speed doubled."
    },
    "1000": {
      "name": "Architect's Omniscient Overlay",
      "type": "Active Technique / Ultimate",
      "target_slot": "spells",
      "threshold": 1000,
      "skill_name": "Cartography",
      "tier": "Transcendence",
      "description": "Interface directly with Cardinal's root coordinate engine, rendering the entire world map in transparent wireframe.",
      "effect": "Passive & Active: Permanently lifts 100% Fog of War across all sectors. Reveals every hidden cache, backdoor, and enemy coordinate in real time. Can open Phase Portal once/rest."
    }
  }
}
```

## `CANONICAL_TRAPS` (4 entries)
```json
{
  "serrated_tripwire": {
    "key": "serrated_tripwire",
    "name": "Serrated Monofilament Tripwire",
    "base_dc": 12,
    "prep_turns": 1,
    "damage_dice": "2d6",
    "condition": "Bleed & Prone",
    "description": "Ultra-sharp monofilament strung across natural choke-points. Trips target prone and inflicts 2d6 slashing damage plus Bleed.",
    "materials": {
      "Serrated Tripwire Coils": 1,
      "Anchors and Tension Pins": 1
    }
  },
  "heavy_highway_snare": {
    "key": "heavy_highway_snare",
    "name": "Heavy Highway Snare",
    "base_dc": 14,
    "prep_turns": 1,
    "damage_dice": "1d8",
    "condition": "Tethered",
    "description": "High-tension braided cable hoist. Yanks target into suspension, inflicting Tethered condition (0 movement, attacks against target have advantage).",
    "materials": {
      "Heavy Highway Snares": 1,
      "Carbon Line Spools": 1
    }
  },
  "marrow_aggro_corridor": {
    "key": "marrow_aggro_corridor",
    "name": "Rendered Marrow Scent Corridor",
    "base_dc": 13,
    "prep_turns": 2,
    "damage_dice": "None",
    "condition": "Aggro Lure & Surprise Ambush",
    "description": "Smears 500m pheromone corridor to funnel beasts directly into pre-sighted kill zones. Grants automatic Surprise Round (+5 initiative, guaranteed critical strike).",
    "materials": {
      "Crate of Marrow-Jars": 1,
      "Carbon Line Spools": 1
    }
  },
  "emp_shock_mine": {
    "key": "emp_shock_mine",
    "name": "Improvised EMP Shock-Mine",
    "base_dc": 15,
    "prep_turns": 1,
    "damage_dice": "3d8",
    "condition": "Stunned & Ionized",
    "description": "Repurposed micro-capacitor detonating on pressure. Inflicts 3d8 electrical damage in a 10ft radius; DC 14 CON save or Stunned for 1 turn.",
    "materials": {
      "Corroded Micro-Capacitor": 1,
      "Frayed Copper Wiring": 1
    }
  }
}
```

## `CHRONO_PERIODS` (5 entries)
```json
{
  "dawn": {
    "key": "dawn",
    "label": "🌅 Dawn",
    "hours": [
      6,
      8
    ],
    "desc": "Morning light pierces the fractured data-haze. Visibility normal; creatures stirring.",
    "perception_mod": 0,
    "stealth_mod": 0
  },
  "day": {
    "key": "day",
    "label": "☀️ Midday",
    "hours": [
      8,
      18
    ],
    "desc": "Bright aetheric sun overhead. Optimal visibility; active regional trade routes.",
    "perception_mod": 0,
    "stealth_mod": 0
  },
  "dusk": {
    "key": "dusk",
    "label": "🌆 Dusk",
    "hours": [
      18,
      21
    ],
    "desc": "Sun sinks beneath Pohatcong Mountain. Lengthening shadows impose -2 to Perception checks.",
    "perception_mod": -2,
    "stealth_mod": 1
  },
  "night": {
    "key": "night",
    "label": "🌙 Midnight",
    "hours": [
      21,
      4
    ],
    "desc": "Pitch black wilderness. Torches or aether-lanterns required. Apex stalkers gain +2 Stealth.",
    "perception_mod": -4,
    "stealth_mod": 2
  },
  "witching_hour": {
    "key": "witching_hour",
    "label": "🌌 Witching Hour",
    "hours": [
      4,
      6
    ],
    "desc": "The thin hour before sunrise. Dimensional seam friction; anomalous glitched entities stir.",
    "perception_mod": -2,
    "stealth_mod": 1
  }
}
```

## `CLASS_FEATS_TREE` (12 entries)
```json
{
  "warrior": {
    "title": "Warrior (Frontline Anchor)",
    "resource": {
      "name": "Poise & Threat",
      "max": 100,
      "start": 0,
      "type": "poise"
    },
    "level_1": [
      "Shield Wall Stance (Active): Enter fortified defensive stance; gain +3 AC and Advantage on CON saves, movement halved.",
      "Taunting War-Cry (Active): Spend 20 Poise to force enemies within 30ft to make a WIS save (DC 13) or focus attacks on you."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Unyielding Mass",
        "type": "Passive",
        "desc": "Max Poise increased by +25. You cannot be knocked down or moved against your will by creatures equal or smaller."
      },
      {
        "id": "B",
        "name": "Retaliatory Bulwark",
        "type": "Passive",
        "desc": "Successfully blocking an attack reflects 1d6 + CON mod kinetic damage back to attacker."
      },
      {
        "id": "C",
        "name": "Inspiring Bastion",
        "type": "Active",
        "desc": "Spend 30 Poise to rally companions within 30ft; grants +10 temporary HP for 3 turns."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Guard Break",
        "type": "Active",
        "desc": "Spend 40 Poise on melee strike to shatter enemy defenses, reducing target AC by -3 for 2 turns."
      },
      {
        "id": "B",
        "name": "Bodyguard Intercept",
        "type": "Reaction",
        "desc": "When an adjacent ally is struck, instantly swap positions and absorb the hit using your Armor Class."
      },
      {
        "id": "C",
        "name": "Seismic Tremor",
        "type": "Active",
        "desc": "Slam weapon into ground, dealing 2d8 bludgeoning damage and knocking down enemies in 10ft."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Unbreakable Bastion",
        "type": "Passive",
        "desc": "Gain 10% resistance to all physical damage. Max Poise increased to 125."
      },
      {
        "id": "B",
        "name": "Colossus Cleave",
        "type": "Active",
        "desc": "Spend 50 Poise to swing in a 180-degree arc, dealing weapon damage + 2d10 to all adjacent foes."
      },
      {
        "id": "C",
        "name": "Battlefield Commander",
        "type": "Active",
        "desc": "Spend 40 Poise to command all party members to strike simultaneously with Advantage."
      }
    ]
  },
  "mage": {
    "title": "Mage (Aether-Weaver)",
    "resource": {
      "name": "Aetheric Flux",
      "max": 50,
      "start": 50,
      "type": "flux"
    },
    "level_1": [
      "Arcane Ward (Active): Conjure aetheric barrier absorbing up to 25 + (5 x Lvl) damage.",
      "Aetheric Dart (Active): Fire concentrated force bolt dealing 1d8 + INT mod force damage (costs 5 Flux)."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Mana Forking",
        "type": "Passive",
        "desc": "Single-target offensive spells have a 35% chance to fork and strike a second adjacent target for half damage."
      },
      {
        "id": "B",
        "name": "Leyline Conduit",
        "type": "Passive",
        "desc": "Standing within 15ft of an aether conduit doubles Flux regeneration to +20 Flux/turn."
      },
      {
        "id": "C",
        "name": "Kinetic Repulsion Pulse",
        "type": "Reaction",
        "desc": "When an enemy enters melee reach, spend 15 Flux to trigger a shockwave pushing them back 15ft."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Overcharge Singularity",
        "type": "Active",
        "desc": "Spend 40 Flux to unleash a localized gravity vortex dealing 3d10 force damage in 15ft radius."
      },
      {
        "id": "B",
        "name": "Dimensional Blink",
        "type": "Active",
        "desc": "Spend 20 Flux to instantaneously teleport up to 30ft to an unoccupied space in line of sight."
      },
      {
        "id": "C",
        "name": "Crystalline Rail-Lance",
        "type": "Active",
        "desc": "Spend 25 Flux to fire a crystalline beam piercing up to 3 enemies in a straight line."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Arcane Conduit Overdrive",
        "type": "Passive",
        "desc": "Spells deal 20% increased force/elemental damage when cast at or above 30 Flux."
      },
      {
        "id": "B",
        "name": "Event Horizon",
        "type": "Active",
        "desc": "Spend 45 Flux to create a gravitational collapse that pulls enemies in 30ft and immobilizes them."
      },
      {
        "id": "C",
        "name": "Aetheric Aegis",
        "type": "Active",
        "desc": "Spend 35 Flux to grant all party members a 30 HP protective energy barrier for 3 turns."
      }
    ]
  },
  "cleric": {
    "title": "Cleric (Spire Templar)",
    "resource": {
      "name": "Devotion & Grace",
      "max": 100,
      "start": 50,
      "type": "devotion"
    },
    "level_1": [
      "Sanctified Ward (Active Stance): Project 15ft aura; allies within gain +2 to saving throws and +1 AC.",
      "Purifying Grace (Active): Spend 25 Devotion to heal ally for 2d8 + WIS mod and cleanse one bleed/poison."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Consecrated Smite",
        "type": "Passive",
        "desc": "Melee strikes generate +10 Devotion and deal +1d6 radiant damage against corrupt/undead foes."
      },
      {
        "id": "B",
        "name": "Martyr's Exchange",
        "type": "Reaction",
        "desc": "When an ally in 30ft takes lethal damage, spend 30 Devotion to absorb 50% onto yourself."
      },
      {
        "id": "C",
        "name": "Cleansing Radiance",
        "type": "Active",
        "desc": "Spend 35 Devotion to emit a pulse that blinds adjacent enemies and grants allies +15 temp HP."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Aegis of the Spire",
        "type": "Active",
        "desc": "Spend 50 Devotion to project a golden dome for 2 turns preventing all enemy projectile entry."
      },
      {
        "id": "B",
        "name": "Rebuke the Corrupt",
        "type": "Active",
        "desc": "Unleash pillar of light dealing 3d8 + WIS mod radiant damage and knocking down aberrant targets."
      },
      {
        "id": "C",
        "name": "Divine Resurgence",
        "type": "Passive",
        "desc": "Once per day, when HP drops to 0, instantly revive at 25% HP and emit radial heal pulse."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Wrath of the Heavens",
        "type": "Active",
        "desc": "Spend 50 Devotion to call down radiant storm dealing 4d8 radiant damage and applying Blindness."
      },
      {
        "id": "B",
        "name": "Hand of Salvation",
        "type": "Active",
        "desc": "Spend 45 Devotion to fully heal an ally below 25% HP and grant them Immunity to all damage for 1 turn."
      },
      {
        "id": "C",
        "name": "Aura of the Incorruptible",
        "type": "Passive",
        "desc": "All party members within 30ft gain +3 to all saving throws and immune to Fear and Charm."
      }
    ]
  },
  "thief": {
    "title": "Thief (Shadow Infiltrator)",
    "resource": {
      "name": "Momentum Dice",
      "max": 5,
      "start": 1,
      "type": "momentum"
    },
    "level_1": [
      "Shadow Footwork (Active Stance): Gain +2 to Dodge DC and ignore terrain movement penalties.",
      "Serrated Backstab (Active): Spend 1 Momentum to strike from stealth or flank for +2d6 precision bleed damage."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Fluid Evasion",
        "type": "Passive",
        "desc": "Whenever an enemy misses an attack against you, immediately generate +1 Momentum die."
      },
      {
        "id": "B",
        "name": "Pocket Blind",
        "type": "Active",
        "desc": "Spend 1 Momentum die to blind target eyes; target suffers Disadvantage on attack rolls for 2 turns."
      },
      {
        "id": "C",
        "name": "Opportunistic Sprint",
        "type": "Active",
        "desc": "Spend 1 Momentum die to take Dash and Disengage simultaneously as a free bonus action."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Shadow-Vanish",
        "type": "Active",
        "desc": "Spend 2 Momentum dice to drop smoke pellet and re-enter full Stealth in plain sight."
      },
      {
        "id": "B",
        "name": "Severing Tendon",
        "type": "Active",
        "desc": "Spend 2 Momentum on critical strike to reduce target movement to 0 and disable reaction attacks."
      },
      {
        "id": "C",
        "name": "Cunning Double-Strike",
        "type": "Passive",
        "desc": "Dual-wielding off-hand strikes have a 50% chance not to consume an action when spending Momentum."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Death Lotus",
        "type": "Active",
        "desc": "Spend 3 Momentum to teleport between up to 4 enemies in 30ft, striking each for critical damage."
      },
      {
        "id": "B",
        "name": "Phase Shadow",
        "type": "Passive",
        "desc": "When dropping below 30% HP, automatically vanish into shadow for 2 turns without taking damage."
      },
      {
        "id": "C",
        "name": "Expose Fatal Flaw",
        "type": "Active",
        "desc": "Spend 2 Momentum to analyze target; all party members deal +50% critical damage to target for 2 turns."
      }
    ]
  },
  "ranger": {
    "title": "Ranger (Wilderness Marksman)",
    "resource": {
      "name": "Focus & Vantage",
      "max": 5,
      "start": 3,
      "type": "focus"
    },
    "level_1": [
      "Hunter's Mark (Active): Mark target within 60ft as quarry; attacks deal +1d6 damage and ignore cover.",
      "Deadeye Aim (Passive): Ranged attacks ignore cover and gain +2 to hit when standing still."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Predator's Camouflage",
        "type": "Passive",
        "desc": "Advantage on Stealth in wild/ruined biomes; first shot from stealth does not break cover."
      },
      {
        "id": "B",
        "name": "Crippling Pin",
        "type": "Active",
        "desc": "Spend 1 Focus charge to shoot enemy servo/leg; target movement reduced to 0 for 1 turn."
      },
      {
        "id": "C",
        "name": "Quick-Step Disengage",
        "type": "Reaction",
        "desc": "When enemy closes to melee, spend 1 Focus to vault backward 15ft without provoking attacks of opportunity."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Culling Shot",
        "type": "Active",
        "desc": "Spend 2 Focus charges to fire execution shot; deals triple damage against targets below 30% HP."
      },
      {
        "id": "B",
        "name": "Shrapnel Rain",
        "type": "Active",
        "desc": "Spend 2 Focus charges to blanket 20ft area with explosive shrapnel dealing 3d6 bleed damage."
      },
      {
        "id": "C",
        "name": "Wild Instincts",
        "type": "Passive",
        "desc": "You can never be surprised in combat, and automatically roll with Advantage on Initiative checks."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Apex Predator",
        "type": "Passive",
        "desc": "Attacks against quarry expand critical threat range to 18-20 and deal x3 critical damage."
      },
      {
        "id": "B",
        "name": "Ballistic Barrage",
        "type": "Active",
        "desc": "Spend 3 Focus charges to fire a stream of 5 piercing arrows into a single target."
      },
      {
        "id": "C",
        "name": "Perimeter Lockdown",
        "type": "Active",
        "desc": "Spend 2 Focus charges to deploy a network of concealed trip-mines covering 40ft."
      }
    ]
  },
  "engineer": {
    "title": "Engineer / Artificer",
    "resource": {
      "name": "Heat & Overclock",
      "max": 100,
      "start": 0,
      "type": "heat"
    },
    "level_1": [
      "Deploy Sentry Turret (Active): Deploy kinetic/shock turret that fires 1d6 damage each turn (builds 20 Heat).",
      "Vent Overclock (Active): Vent Heat in 10ft frontal cone dealing damage equal to 50% of vented Heat."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Conductive Wiretap",
        "type": "Passive",
        "desc": "Hacking enemy terminal/construct reveals sector stats and grants +2 to hit mechanized foes."
      },
      {
        "id": "B",
        "name": "Heat-Sink Plating",
        "type": "Passive",
        "desc": "While Heat is above 50%, armor gains +3 AC and radiates 1d6 fire damage to melee attackers."
      },
      {
        "id": "C",
        "name": "Overclock Surge",
        "type": "Active",
        "desc": "Spend 40 Heat to take an additional Standard Action on your current combat turn."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Automated Decoy Drones",
        "type": "Active",
        "desc": "Deploy 2 holographic decoy drones that draw enemy attacks away from party for 2 turns."
      },
      {
        "id": "B",
        "name": "EMP Shock-Discharge",
        "type": "Active",
        "desc": "Spend 50 Heat to discharge EMP burst that stuns constructs for 1 turn and disables energy weapons."
      },
      {
        "id": "C",
        "name": "Recursive Logic Virus",
        "type": "Active",
        "desc": "Upload corrupt logic into cybernetic/golem enemy, forcing it to attack nearest ally for 1 turn."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Automated Siege Golem",
        "type": "Active",
        "desc": "Deploy heavy mechanized combat turret with 60 HP that taunts enemies and fires flak cannons."
      },
      {
        "id": "B",
        "name": "Core Melt Downcharge",
        "type": "Active",
        "desc": "Vent 100% Heat into tactical blast dealing 5d10 thermal/kinetic damage in 20ft radius."
      },
      {
        "id": "C",
        "name": "Nanite Patch Field",
        "type": "Passive",
        "desc": "Deploying gadgets or venting heat automatically repairs party armor and restores 10 HP."
      }
    ]
  },
  "psion": {
    "title": "Psion / Phrenic",
    "resource": {
      "name": "Psi-Strain",
      "max": 100,
      "start": 0,
      "type": "strain"
    },
    "level_1": [
      "Kinetic Repulsion Barrier (Active Stance): Deflect projectiles (+3 AC vs ranged), builds +10% Strain/turn.",
      "Mind Spike (Active): Unleash psychic jolt dealing 1d10 + INT mod damage, bypassing armor (builds +15% Strain)."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "High-Strain Resonance",
        "type": "Passive",
        "desc": "While Psi-Strain is above 50%, all psychic abilities deal +25% bonus damage and +2 save DC."
      },
      {
        "id": "B",
        "name": "Telekinetic Toss",
        "type": "Active",
        "desc": "Hurl an enemy or heavy terrain object up to 30ft for 2d8 bludgeoning damage (builds +20% Strain)."
      },
      {
        "id": "C",
        "name": "Neural Dampening",
        "type": "Reaction",
        "desc": "When an ally suffers mental debuff, charm, or fear, spend 15% Strain to negate it instantly."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Psychokinetic Implosion",
        "type": "Active",
        "desc": "Compress atmosphere in 15ft sphere, crushing for 3d10 force damage and pulling foes together (+35% Strain)."
      },
      {
        "id": "B",
        "name": "Neural Overwrite",
        "type": "Active",
        "desc": "Invade organic enemy motor cortex; contested WIS check to control target action for 1 turn (+40% Strain)."
      },
      {
        "id": "C",
        "name": "Subconscious Flush",
        "type": "Active",
        "desc": "Once per combat, instantly vent all Psi-Strain to 0%, deafening adjacent foes for 1 turn."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Mind Over Matter",
        "type": "Passive",
        "desc": "You can use INT modifier in place of STR or DEX for attack rolls, physical saves, and AC."
      },
      {
        "id": "B",
        "name": "Psionic Cataclysm",
        "type": "Active",
        "desc": "Suffer 40% Strain to detonate psychic shockwave dealing 5d8 force damage and stunning foes in 25ft."
      },
      {
        "id": "C",
        "name": "Neural Puppet Master",
        "type": "Active",
        "desc": "Suffer 35% Strain to seize complete control of an enemy commander or elite construct for 2 full turns."
      }
    ]
  },
  "pathless": {
    "title": "Pathless (Freeform Anomaly)",
    "resource": {
      "name": "Anomaly Resonance",
      "max": 100,
      "start": 0,
      "type": "resonance"
    },
    "level_1": [
      "Adaptive Weapon Mastery (Passive): Equip and dual-wield any weapon combination without off-hand penalties.",
      "Unshackled Potential (Passive): Can choose any 1 starting ability from any of the 7 anchor classes."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Cross-Discipline Synergy",
        "type": "Passive",
        "desc": "Executing a melee attack grants +2 to hit and +1d6 damage on your next ranged or magical action."
      },
      {
        "id": "B",
        "name": "Adaptive Will",
        "type": "Passive",
        "desc": "Max Anomaly Resonance increased to 125. Reroll one failed saving throw per combat encounter."
      },
      {
        "id": "C",
        "name": "System Glitch Step",
        "type": "Active",
        "desc": "Spend 25 Resonance to phase-shift through collision for 1 turn, passing through obstacles."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Stolen Doctrine",
        "type": "Passive",
        "desc": "Choose any 1 Level 3 or Level 6 Class Feat from any of the seven anchor classes."
      },
      {
        "id": "B",
        "name": "Glitched Blade Edge",
        "type": "Active",
        "desc": "Spend 40 Resonance to coat weapons in null-void data; attacks bypass physical AC for 1 turn."
      },
      {
        "id": "C",
        "name": "Dual-Core Overclock",
        "type": "Active",
        "desc": "Spend 50 Resonance to gain an extra Standard Action this turn."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Sovereign Glitch",
        "type": "Passive",
        "desc": "Equip weapons and armor of any grade or category without stat prerequisites or penalties."
      },
      {
        "id": "B",
        "name": "Dimensional Tear",
        "type": "Active",
        "desc": "Spend 50 Resonance to slash reality, dealing 4d12 null-void damage that bypasses all defenses."
      },
      {
        "id": "C",
        "name": "Limitless Resonance",
        "type": "Passive",
        "desc": "Max Resonance increased to 150. Generating Resonance restores 5% of max HP per trigger."
      }
    ]
  },
  "vanguard": {
    "title": "Warrior (Frontline Anchor)",
    "resource": {
      "name": "Poise & Threat",
      "max": 100,
      "start": 0,
      "type": "poise"
    },
    "level_1": [
      "Shield Wall Stance (Active): Enter fortified defensive stance; gain +3 AC and Advantage on CON saves, movement halved.",
      "Taunting War-Cry (Active): Spend 20 Poise to force enemies within 30ft to make a WIS save (DC 13) or focus attacks on you."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Unyielding Mass",
        "type": "Passive",
        "desc": "Max Poise increased by +25. You cannot be knocked down or moved against your will by creatures equal or smaller."
      },
      {
        "id": "B",
        "name": "Retaliatory Bulwark",
        "type": "Passive",
        "desc": "Successfully blocking an attack reflects 1d6 + CON mod kinetic damage back to attacker."
      },
      {
        "id": "C",
        "name": "Inspiring Bastion",
        "type": "Active",
        "desc": "Spend 30 Poise to rally companions within 30ft; grants +10 temporary HP for 3 turns."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Guard Break",
        "type": "Active",
        "desc": "Spend 40 Poise on melee strike to shatter enemy defenses, reducing target AC by -3 for 2 turns."
      },
      {
        "id": "B",
        "name": "Bodyguard Intercept",
        "type": "Reaction",
        "desc": "When an adjacent ally is struck, instantly swap positions and absorb the hit using your Armor Class."
      },
      {
        "id": "C",
        "name": "Seismic Tremor",
        "type": "Active",
        "desc": "Slam weapon into ground, dealing 2d8 bludgeoning damage and knocking down enemies in 10ft."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Unbreakable Bastion",
        "type": "Passive",
        "desc": "Gain 10% resistance to all physical damage. Max Poise increased to 125."
      },
      {
        "id": "B",
        "name": "Colossus Cleave",
        "type": "Active",
        "desc": "Spend 50 Poise to swing in a 180-degree arc, dealing weapon damage + 2d10 to all adjacent foes."
      },
      {
        "id": "C",
        "name": "Battlefield Commander",
        "type": "Active",
        "desc": "Spend 40 Poise to command all party members to strike simultaneously with Advantage."
      }
    ]
  },
  "magi_saboteur": {
    "title": "Engineer / Artificer",
    "resource": {
      "name": "Heat & Overclock",
      "max": 100,
      "start": 0,
      "type": "heat"
    },
    "level_1": [
      "Deploy Sentry Turret (Active): Deploy kinetic/shock turret that fires 1d6 damage each turn (builds 20 Heat).",
      "Vent Overclock (Active): Vent Heat in 10ft frontal cone dealing damage equal to 50% of vented Heat."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Conductive Wiretap",
        "type": "Passive",
        "desc": "Hacking enemy terminal/construct reveals sector stats and grants +2 to hit mechanized foes."
      },
      {
        "id": "B",
        "name": "Heat-Sink Plating",
        "type": "Passive",
        "desc": "While Heat is above 50%, armor gains +3 AC and radiates 1d6 fire damage to melee attackers."
      },
      {
        "id": "C",
        "name": "Overclock Surge",
        "type": "Active",
        "desc": "Spend 40 Heat to take an additional Standard Action on your current combat turn."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Automated Decoy Drones",
        "type": "Active",
        "desc": "Deploy 2 holographic decoy drones that draw enemy attacks away from party for 2 turns."
      },
      {
        "id": "B",
        "name": "EMP Shock-Discharge",
        "type": "Active",
        "desc": "Spend 50 Heat to discharge EMP burst that stuns constructs for 1 turn and disables energy weapons."
      },
      {
        "id": "C",
        "name": "Recursive Logic Virus",
        "type": "Active",
        "desc": "Upload corrupt logic into cybernetic/golem enemy, forcing it to attack nearest ally for 1 turn."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Automated Siege Golem",
        "type": "Active",
        "desc": "Deploy heavy mechanized combat turret with 60 HP that taunts enemies and fires flak cannons."
      },
      {
        "id": "B",
        "name": "Core Melt Downcharge",
        "type": "Active",
        "desc": "Vent 100% Heat into tactical blast dealing 5d10 thermal/kinetic damage in 20ft radius."
      },
      {
        "id": "C",
        "name": "Nanite Patch Field",
        "type": "Passive",
        "desc": "Deploying gadgets or venting heat automatically repairs party armor and restores 10 HP."
      }
    ]
  },
  "aether_slinger": {
    "title": "Mage (Aether-Weaver)",
    "resource": {
      "name": "Aetheric Flux",
      "max": 50,
      "start": 50,
      "type": "flux"
    },
    "level_1": [
      "Arcane Ward (Active): Conjure aetheric barrier absorbing up to 25 + (5 x Lvl) damage.",
      "Aetheric Dart (Active): Fire concentrated force bolt dealing 1d8 + INT mod force damage (costs 5 Flux)."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Mana Forking",
        "type": "Passive",
        "desc": "Single-target offensive spells have a 35% chance to fork and strike a second adjacent target for half damage."
      },
      {
        "id": "B",
        "name": "Leyline Conduit",
        "type": "Passive",
        "desc": "Standing within 15ft of an aether conduit doubles Flux regeneration to +20 Flux/turn."
      },
      {
        "id": "C",
        "name": "Kinetic Repulsion Pulse",
        "type": "Reaction",
        "desc": "When an enemy enters melee reach, spend 15 Flux to trigger a shockwave pushing them back 15ft."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Overcharge Singularity",
        "type": "Active",
        "desc": "Spend 40 Flux to unleash a localized gravity vortex dealing 3d10 force damage in 15ft radius."
      },
      {
        "id": "B",
        "name": "Dimensional Blink",
        "type": "Active",
        "desc": "Spend 20 Flux to instantaneously teleport up to 30ft to an unoccupied space in line of sight."
      },
      {
        "id": "C",
        "name": "Crystalline Rail-Lance",
        "type": "Active",
        "desc": "Spend 25 Flux to fire a crystalline beam piercing up to 3 enemies in a straight line."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Arcane Conduit Overdrive",
        "type": "Passive",
        "desc": "Spells deal 20% increased force/elemental damage when cast at or above 30 Flux."
      },
      {
        "id": "B",
        "name": "Event Horizon",
        "type": "Active",
        "desc": "Spend 45 Flux to create a gravitational collapse that pulls enemies in 30ft and immobilizes them."
      },
      {
        "id": "C",
        "name": "Aetheric Aegis",
        "type": "Active",
        "desc": "Spend 35 Flux to grant all party members a 30 HP protective energy barrier for 3 turns."
      }
    ]
  },
  "wilderness_ranger": {
    "title": "Ranger (Wilderness Marksman)",
    "resource": {
      "name": "Focus & Vantage",
      "max": 5,
      "start": 3,
      "type": "focus"
    },
    "level_1": [
      "Hunter's Mark (Active): Mark target within 60ft as quarry; attacks deal +1d6 damage and ignore cover.",
      "Deadeye Aim (Passive): Ranged attacks ignore cover and gain +2 to hit when standing still."
    ],
    "level_3": [
      {
        "id": "A",
        "name": "Predator's Camouflage",
        "type": "Passive",
        "desc": "Advantage on Stealth in wild/ruined biomes; first shot from stealth does not break cover."
      },
      {
        "id": "B",
        "name": "Crippling Pin",
        "type": "Active",
        "desc": "Spend 1 Focus charge to shoot enemy servo/leg; target movement reduced to 0 for 1 turn."
      },
      {
        "id": "C",
        "name": "Quick-Step Disengage",
        "type": "Reaction",
        "desc": "When enemy closes to melee, spend 1 Focus to vault backward 15ft without provoking attacks of opportunity."
      }
    ],
    "level_6": [
      {
        "id": "A",
        "name": "Culling Shot",
        "type": "Active",
        "desc": "Spend 2 Focus charges to fire execution shot; deals triple damage against targets below 30% HP."
      },
      {
        "id": "B",
        "name": "Shrapnel Rain",
        "type": "Active",
        "desc": "Spend 2 Focus charges to blanket 20ft area with explosive shrapnel dealing 3d6 bleed damage."
      },
      {
        "id": "C",
        "name": "Wild Instincts",
        "type": "Passive",
        "desc": "You can never be surprised in combat, and automatically roll with Advantage on Initiative checks."
      }
    ],
    "level_10": [
      {
        "id": "A",
        "name": "Apex Predator",
        "type": "Passive",
        "desc": "Attacks against quarry expand critical threat range to 18-20 and deal x3 critical damage."
      },
      {
        "id": "B",
        "name": "Ballistic Barrage",
        "type": "Active",
        "desc": "Spend 3 Focus charges to fire a stream of 5 piercing arrows into a single target."
      },
      {
        "id": "C",
        "name": "Perimeter Lockdown",
        "type": "Active",
        "desc": "Spend 2 Focus charges to deploy a network of concealed trip-mines covering 40ft."
      }
    ]
  }
}
```

## `COMMODITY_MARKET` (5 entries)
```json
{
  "refined_aether_alloy": {
    "name": "Refined Aether-Alloy",
    "base_price": 250,
    "category": "Ore & Ingot"
  },
  "scrap_metal": {
    "name": "Scrap Metal & Wiring",
    "base_price": 50,
    "category": "Scrap & Salvage"
  },
  "aether_herb": {
    "name": "Wild Aether-Herbs",
    "base_price": 75,
    "category": "Botanical"
  },
  "wolf_marrow": {
    "name": "Wolf Marrow",
    "base_price": 100,
    "category": "Monster Part"
  },
  "repair_flux": {
    "name": "Aetheric Repair Flux",
    "base_price": 120,
    "category": "Alchemy"
  }
}
```

## `COMPANION_LEVEL_PERKS` (5 entries)
```json
{
  "2": {
    "name": "Telemetry Ping v1.0",
    "type": "Passive",
    "desc": "+1 to Banki's attack rolls against scanned targets via mana resonance."
  },
  "3": {
    "name": "Mesh Exploitation Mastery",
    "type": "Technique",
    "desc": "Ren can perceive hidden aetheric doors and safe-zone mana fountains."
  },
  "4": {
    "name": "Aetheric Shield Pulse",
    "type": "Reaction",
    "desc": "When Banki takes lethal damage, Ren emits an arcane kinetic pulse granting +20 temporary HP."
  },
  "5": {
    "name": "Overclocked Stun Burst",
    "type": "Active",
    "desc": "MageTech caster discharge jumps to 2 additional adjacent targets with crackling aether."
  },
  "6": {
    "name": "Geometry Desync Hack",
    "type": "Ultimate",
    "desc": "Locks an enemy construct in a localized temporal stasis rune for 1 turn."
  }
}
```

## `COMPANION_TACTICAL_STANCES` (4 entries)
```json
{
  "overwatch_hacking": {
    "key": "overwatch_hacking",
    "name": "Leyline Overwatch",
    "label": "👁️ Leyline Overwatch",
    "icon": "👁️",
    "short_desc": "Scans enemy mana-signatures and physical seams using runic lens.",
    "tactical_effect": "Debuffs targeted enemy AC by -2 and reveals structural mana-fractures.",
    "combat_log_tag": "[REN OVERWATCH]",
    "stat_bonus": {
      "target_ac_mod": -2,
      "crit_threat_bonus": 1
    }
  },
  "suppression_fire": {
    "key": "suppression_fire",
    "name": "MageTech Arc Suppression",
    "label": "⚡ MageTech Arc Suppression",
    "icon": "⚡",
    "short_desc": "Fires crackling lightning-mana runes from his brass MageTech Caster firearm.",
    "tactical_effect": "Enemies rushing into melee must make a DC 13 CON save or become Staggered.",
    "combat_log_tag": "[REN SUPPRESSION]",
    "stat_bonus": {
      "disruption_dc": 13,
      "condition": "Staggered"
    }
  },
  "full_evasion": {
    "key": "full_evasion",
    "name": "Aetheric Phase-Veil",
    "label": "🌫️ Aetheric Phase-Veil",
    "icon": "🌫️",
    "short_desc": "Weaves spatial camouflage and takes cover behind ancient stone masonry.",
    "tactical_effect": "Ren is immune to single-target attacks; +4 to all defensive saves.",
    "combat_log_tag": "[REN EVASION]",
    "stat_bonus": {
      "defense_save_bonus": 4,
      "untargetable": true
    }
  },
  "utility_rigging": {
    "key": "utility_rigging",
    "name": "Arcane Artificing & Mending",
    "label": "✨ Arcane Artificing & Mending",
    "icon": "✨",
    "short_desc": "Channels mending runes into gear, sets traps, or harvests crystallite scrap.",
    "tactical_effect": "Restores +15 gear durability to worn weapon/armor or scavenges +1 extra crafting part.",
    "combat_log_tag": "[REN UTILITY]",
    "stat_bonus": {
      "durability_patch": 15,
      "salvage_bonus": 1
    }
  }
}
```

## `CURSOR_TIERS` (3 entries)
```json
{
  "green": {
    "status": "green",
    "label": "🟢 Lawful (Green Cursor)",
    "badge": "🟢 Green",
    "description": "Innocent citizen and lawful adventurer. Full protection under Safe-Zone barrier matrices. Respected by merchants and regional guards.",
    "infamy_range": [
      0,
      0
    ],
    "merchant_surcharge": 0.0,
    "safe_zone_clearance": true
  },
  "orange": {
    "status": "orange",
    "label": "🟠 Criminal (Orange Cursor)",
    "badge": "🟠 Orange",
    "description": "Flagged for unprovoked assault, theft, or trap tampering. Safe-zone merchants impose a +25% Col surcharge. Townsfolk are guarded.",
    "infamy_range": [
      1,
      9
    ],
    "merchant_surcharge": 0.25,
    "safe_zone_clearance": true
  },
  "red": {
    "status": "red",
    "label": "🔴 Outlaw PK (Red Cursor)",
    "badge": "🔴 Red",
    "description": "Murderer and outlaw player-killer! Safe-Zone barrier matrices will incinerate Red players on sight. High-tier NPC Wardens actively hunt them.",
    "infamy_range": [
      10,
      999
    ],
    "merchant_surcharge": 1.0,
    "safe_zone_clearance": false
  }
}
```

## `DEFAULT_CORE_SKILLS` (4 entries)
```json
{
  "One-Handed Axes": {
    "mastery": 15,
    "tier": "Novice",
    "description": "Mastery over single-handed hatchets, bearded axes, and tactical cleavers.",
    "milestones_unlocked": []
  },
  "Trench Hammers": {
    "mastery": 15,
    "tier": "Novice",
    "description": "Proficiency with war hammers, trench clubs, and heavy blunt implements.",
    "milestones_unlocked": []
  },
  "Field Trapping": {
    "mastery": 10,
    "tier": "Novice",
    "description": "Techniques for rigging mechanical snares, tripwires, and tactical ambush zones.",
    "milestones_unlocked": []
  },
  "Cartography": {
    "mastery": 10,
    "tier": "Novice",
    "description": "Topographical parsing, hazard triangulation, and navigation of fractured sectors.",
    "milestones_unlocked": []
  }
}
```

## `DEFAULT_WEIGHT_MAP` (35 entries)
```json
{
  "axe": 4.5,
  "sword": 3.5,
  "hammer": 6.0,
  "dagger": 1.0,
  "bow": 3.0,
  "pistol": 2.5,
  "rifle": 8.0,
  "spear": 5.0,
  "rig": 30.0,
  "hauberk": 25.0,
  "plate": 45.0,
  "leather": 12.0,
  "chain": 28.0,
  "cloak": 3.0,
  "pelt": 5.0,
  "boots": 4.0,
  "helm": 5.0,
  "shield": 8.0,
  "spool": 12.0,
  "cord": 8.0,
  "line": 6.0,
  "tripwire": 3.0,
  "snare": 5.0,
  "trap": 7.0,
  "jar": 3.5,
  "marrow": 2.5,
  "water": 1.5,
  "ration": 1.0,
  "clipboard": 2.0,
  "deck": 3.0,
  "usb": 0.1,
  "scroll": 0.5,
  "ore": 5.0,
  "scrap": 1.0,
  "anchor": 35.0
}
```

## `DUAL_TECH_COMBOS` (18 entries)
```json
{
  "runic_axe_storm": {
    "id": "runic_axe_storm",
    "name": "Runic Axe Storm",
    "partners": [
      "Banki",
      "Ren"
    ],
    "req_affinity": 50,
    "desc": "Banki executes a furious whirlwind cleave while Ren fires lightning runes directly into the axe head, unleashing a 360° chain-lightning cyclone.",
    "damage": "4d10+8 Slashing + 2d8 Lightning AOE",
    "effect": "Hits all surrounding enemies, deals 4d10+8 Slashing + 2d8 Lightning DMG and inflicts Stagger on secondary targets.",
    "log_tag": "[DUAL-TECH: BANKI + REN -> RUNIC AXE STORM]"
  },
  "titans_anvil_shockwave": {
    "id": "titans_anvil_shockwave",
    "name": "Titan's Anvil Shockwave",
    "partners": [
      "Banki",
      "Torvald"
    ],
    "req_affinity": 50,
    "desc": "Torvald plants his adamant tower shield while Banki strikes the shield's runic center with his Trench Hammer, detonating a sonic kinetic shockwave.",
    "damage": "3d12+10 Force DMG",
    "effect": "Inflicts 3d12+10 Force DMG and shatters 60 Break Gauge points (guaranteed boss STAGGER).",
    "log_tag": "[DUAL-TECH: BANKI + TORVALD -> TITAN'S ANVIL SHOCKWAVE]"
  },
  "spellblade_vortex": {
    "id": "spellblade_vortex",
    "name": "Spellblade Vortex",
    "partners": [
      "Banki",
      "Elora"
    ],
    "req_affinity": 50,
    "desc": "Banki hurls his bearded axe into Elora's dimensional spatial rift; the blade ricochets between 3 targets enveloped in cold aether-flames.",
    "damage": "3d8 Slashing + 3d8 Frost-Burn to 3 targets",
    "effect": "Cleaves through 3 enemies bypassing 50% Armor Class.",
    "log_tag": "[DUAL-TECH: BANKI + ELORA -> SPELLBLADE VORTEX]"
  },
  "shadow_flank_execution": {
    "id": "shadow_flank_execution",
    "name": "Shadow-Flank Execution",
    "partners": [
      "Banki",
      "Kibs"
    ],
    "req_affinity": 50,
    "desc": "Kibs throws an aetheric flash-smoke bomb blinding the primary foe while Banki steps through the blind spot for a guaranteed decapitation strike.",
    "damage": "5d10+12 Critical Slashing DMG",
    "effect": "Guaranteed critical hit dealing 5d10+12 Slashing DMG and severe Bleed (10 DMG/turn).",
    "log_tag": "[DUAL-TECH: BANKI + KIBS -> SHADOW-FLANK EXECUTION]"
  },
  "valkyries_wrath": {
    "id": "valkyries_wrath",
    "name": "Valkyrie's Sky-Cleave",
    "partners": [
      "Banki",
      "Valeria"
    ],
    "req_affinity": 50,
    "desc": "Valeria lifts Banki into an aerial trajectory before hurling him downward in a terminal-velocity dive-bomb while unleashing radiant spear salvos.",
    "damage": "4d10+10 Radiant Slashing + 2d8 Piercing AOE",
    "effect": "Inflicts 4d10+10 Radiant Slashing DMG to primary target and 2d8 Piercing to surrounding foes with guaranteed Knockdown.",
    "log_tag": "[DUAL-TECH: BANKI + VALERIA -> VALKYRIE'S SKY-CLEAVE]"
  },
  "grave_lord_cleave": {
    "id": "grave_lord_cleave",
    "name": "Grave-Lord Soul Reaver",
    "partners": [
      "Banki",
      "Morrigan"
    ],
    "req_affinity": 50,
    "desc": "Morrigan binds the enemy's life-force in necrotic soul-chains as Banki cleaves through the tether, detonating a necrotic siphon that leeches vital essence.",
    "damage": "4d10+8 Slashing + 3d8 Necrotic DMG",
    "effect": "Deals 4d10+8 Slashing + 3d8 Necrotic DMG; heals Banki and Morrigan for 50% of necrotic damage dealt.",
    "log_tag": "[DUAL-TECH: BANKI + MORRIGAN -> GRAVE-LORD SOUL REAVER]"
  },
  "seismic_cataclysm": {
    "id": "seismic_cataclysm",
    "name": "Seismic Cataclysm",
    "partners": [
      "Banki",
      "Garrick"
    ],
    "req_affinity": 50,
    "desc": "Garrick channels ki into a seismic earth-breaker slam while Banki drives his Trench Hammer into the fractured faultline, launching explosive tectonic debris.",
    "damage": "5d10+12 Bludgeoning Force DMG",
    "effect": "Shatters 75 Break Gauge points (guaranteed boss STUN), dealing 5d10+12 Bludgeoning Force DMG in a 20ft radius.",
    "log_tag": "[DUAL-TECH: BANKI + GARRICK -> SEISMIC CATACLYSM]"
  },
  "cyclone_arrow_storm": {
    "id": "cyclone_arrow_storm",
    "name": "Cyclone Arrow Tempest",
    "partners": [
      "Banki",
      "Sariel"
    ],
    "req_affinity": 50,
    "desc": "Sariel fires a spiral gale-force volley pinning the targets to the earth while Banki charges through the vortex with twin-axe whirlwind cleaves.",
    "damage": "3d10+6 Slashing + 4d6 Wind-Piercing DMG",
    "effect": "Pins targets for 1 turn (Immobilized) and deals 3d10+6 Slashing + 4d6 Piercing DMG across the line.",
    "log_tag": "[DUAL-TECH: BANKI + SARIEL -> CYCLONE ARROW TEMPEST]"
  },
  "dawn_breaker_smite": {
    "id": "dawn_breaker_smite",
    "name": "Dawn-Breaker Radiant Smite",
    "partners": [
      "Banki",
      "Kaelen"
    ],
    "req_affinity": 50,
    "desc": "Brother Kaelen invokes the Sol-Altar's zenith light, wrapping Banki's weapons in blinding solar fire as Banki delivers an overhead solar execution strike.",
    "damage": "4d10+10 Radiant/Fire DMG",
    "effect": "Deals 4d10+10 Radiant DMG (+4d10 bonus vs Undead/Corrupted), Blinds targets for 2 turns, and restores 25 HP to all allies.",
    "log_tag": "[DUAL-TECH: BANKI + KAELEN -> DAWN-BREAKER RADIANT SMITE]"
  },
  "volt_tempest_detonation": {
    "id": "volt_tempest_detonation",
    "name": "Volt-Tempest Plasma Detonation",
    "partners": [
      "Banki",
      "Zedd"
    ],
    "req_affinity": 50,
    "desc": "Zedd hurls a high-voltage plasma sphere into the target's center-mass, which Banki violently detonates with a thunderous kinetic hammer impact.",
    "damage": "3d10+8 Bludgeoning + 4d8 Chain-Lightning DMG",
    "effect": "Detonates in a chain-lightning shockwave leaping to up to 4 nearby hostiles, inflicting Stunned on a failed DC 15 CON save.",
    "log_tag": "[DUAL-TECH: BANKI + ZEDD -> VOLT-TEMPEST PLASMA DETONATION]"
  },
  "valkyrie_war_chorus": {
    "id": "valkyrie_war_chorus",
    "name": "Valkyrie Battle Anthem",
    "partners": [
      "Banki",
      "Daphne"
    ],
    "req_affinity": 50,
    "desc": "Daphne weaves a resounding skaldic war-chant that synchronizes heartbeats and multiplies adrenaline, propelling Banki into a hyper-accelerated strike frenzy.",
    "damage": "6d8+12 Sonic-Empowered Slashing DMG",
    "effect": "Grants Banki +2 extra attacks this turn, deals 6d8+12 Sonic Slashing DMG, and grants all party members +4 Attack and +15 Temp HP for 3 turns.",
    "log_tag": "[DUAL-TECH: BANKI + DAPHNE -> VALKYRIE BATTLE ANTHEM]"
  },
  "blood_twin_cleave": {
    "id": "blood_twin_cleave",
    "name": "Blood-Twin Berserker Cleave",
    "partners": [
      "Banki",
      "Rok"
    ],
    "req_affinity": 50,
    "desc": "Banki and Rok roar in feral unison, executing synchronised spinning greataxe and broadaxe cleaves that tear through armor like parchment.",
    "damage": "6d12+16 Brutal Slashing DMG",
    "effect": "Bypasses 100% of enemy Damage Reduction, inflicts 6d12+16 Slashing DMG and severe Arterial Bleed (15 DMG/turn for 3 turns).",
    "log_tag": "[DUAL-TECH: BANKI + ROK -> BLOOD-TWIN BERSERKER CLEAVE]"
  },
  "temporal_shatter_strike": {
    "id": "temporal_shatter_strike",
    "name": "Temporal Stasis Shatter",
    "partners": [
      "Banki",
      "Lyra"
    ],
    "req_affinity": 50,
    "desc": "Lyra locks the enemy within a 3-second localized time-stop capsule; Banki unleashes four devastating attacks that detonate simultaneously the instant time resumes.",
    "damage": "8d8+16 Chrono-Kinetic Force DMG",
    "effect": "Enemy is helpless during setup; deals 8d8+16 Force DMG and resets enemy initiative/turn order to the very bottom.",
    "log_tag": "[DUAL-TECH: BANKI + LYRA -> TEMPORAL STASIS SHATTER]"
  },
  "foundry_forge_smash": {
    "id": "foundry_forge_smash",
    "name": "Foundry Hydraulic Overdrive",
    "partners": [
      "Banki",
      "Titus"
    ],
    "req_affinity": 50,
    "desc": "Titus locks the target in steam-powered pneumatic vise-clamps while Banki strikes Titus's chest-anvil, driving a superheated hydraulic piston through the target.",
    "damage": "5d10+14 Fire & Bludgeoning DMG",
    "effect": "Deals 5d10+14 Fire/Bludgeoning DMG, permanently shreds target Armor Class by -4, and leaves the foe Prone.",
    "log_tag": "[DUAL-TECH: BANKI + TITUS -> FOUNDRY HYDRAULIC OVERDRIVE]"
  },
  "pack_hunt_ambush": {
    "id": "pack_hunt_ambush",
    "name": "Apex Pack-Hunt Ambush",
    "partners": [
      "Banki",
      "Nyssa"
    ],
    "req_affinity": 50,
    "desc": "Nyssa takes Dire-Wolf aspect to drag the target down by the throat while Banki closes the pincer from the blindside with a merciless downward execution stroke.",
    "damage": "4d10+10 Slashing + 3d8 Beast-Tear Piercing DMG",
    "effect": "Knocks target Prone, inflicts Crippled status (-50% movement speed), and deals 4d10+10 Slashing + 3d8 Piercing DMG.",
    "log_tag": "[DUAL-TECH: BANKI + NYSSA -> APEX PACK-HUNT AMBUSH]"
  },
  "void_abyss_cleave": {
    "id": "void_abyss_cleave",
    "name": "Void-Singularity Cleave",
    "partners": [
      "Banki",
      "Malakor"
    ],
    "req_affinity": 50,
    "desc": "Malakor rips open an eldritch void anomaly that collapses space and draws all surrounding foes into a singular vortex, right into Banki's full-force whirlwind sweep.",
    "damage": "5d8 Slashing + 4d8 Void-Cold DMG (AOE)",
    "effect": "Pulls all enemies in 30ft into melee range, deals 5d8 Slashing + 4d8 Void DMG, and inflicts -3 to all enemy attack rolls for 2 turns.",
    "log_tag": "[DUAL-TECH: BANKI + MALAKOR -> VOID-SINGULARITY CLEAVE]"
  },
  "corrosive_shatter_bomb": {
    "id": "corrosive_shatter_bomb",
    "name": "Corrosive Slag Shatter",
    "partners": [
      "Banki",
      "Thorne"
    ],
    "req_affinity": 50,
    "desc": "Dr. Thorne hurls a concentrated vial of alchemical vitriol onto the enemy's armor plate, followed instantly by Banki's concussive hammer strike that shatters the brittle slag.",
    "damage": "3d10+8 Bludgeoning + 4d6 Acid DMG",
    "effect": "Completely dissolves enemy Damage Reduction (DR reduced to 0), deals 3d10+8 Bludgeoning + 4d6 Acid DMG, and leaves a lingering acid pool.",
    "log_tag": "[DUAL-TECH: BANKI + THORNE -> CORROSIVE SLAG SHATTER]"
  },
  "inquisition_execution": {
    "id": "inquisition_execution",
    "name": "Grand Inquisitor's Execution",
    "partners": [
      "Banki",
      "Teresa"
    ],
    "req_affinity": 50,
    "desc": "Sister Teresa pins the condemned hostile to the earth with a consecrated heavy silver stake and recites the final rite while Banki delivers a thunderous decapitation blow.",
    "damage": "6d10+15 Holy Slashing DMG",
    "effect": "Instant execution threshold against foes below 25% HP; otherwise deals 6d10+15 Holy Slashing DMG and permanently prevents resurrection or undead reanimation.",
    "log_tag": "[DUAL-TECH: BANKI + TERESA -> GRAND INQUISITOR'S EXECUTION]"
  }
}
```

## `GREENHOUSE_TIERS` (3 entries)
```json
{
  "1": {
    "yield": {
      "Wild Roots": 2,
      "Aether-Herb": 1
    },
    "upgrade_cost": 1000
  },
  "2": {
    "yield": {
      "Wild Roots": 3,
      "Aether-Herb": 2,
      "Salted Moss": 2
    },
    "upgrade_cost": 2500
  },
  "3": {
    "yield": {
      "Wild Roots": 4,
      "Aether-Herb": 3,
      "Salted Moss": 3,
      "Runic Lichen": 2
    },
    "upgrade_cost": 5000
  }
}
```

## `HARMONIZATION_FEATS` (3 entries)
```json
{
  "leyline_conduits": {
    "name": "Leyline Conduits",
    "tier": 1,
    "description": "Gold-threaded conduits woven through bone negate the spellcasting interference of 1 installed Golem-Graft.",
    "effect": "Negates the -2 Arcane DC penalty for 1 installed Golem-Graft."
  },
  "aether_infused_prosthetic": {
    "name": "Aether-Infused Prosthetic",
    "tier": 2,
    "description": "Channel spells directly through metallic limbs, turning golem prosthetics into arcane focuses.",
    "effect": "+1d4 force/elemental damage to touch and ranged spells channeled through grafts."
  },
  "overclocked_matrix": {
    "name": "Overclocked Matrix",
    "tier": 3,
    "description": "Temporarily push cybernetic capacity past safe limits to cast without standard resource drain.",
    "effect": "Once per encounter, spend 10 Graft Strain to cast an active spell without consuming mana/flux."
  }
}
```

## `HOMESTEAD_ESTATES` (1 entries)
```json
{
  "washington_manor": {
    "id": "washington_manor",
    "name": "The Iron-Spoke Sovereign Estate",
    "location": "Washington Borough Safe Zone (Sector 1 Ridge)",
    "purchase_cost_col": 3500,
    "description": "An expansive pre-Integration stone manor on the southern ridge of Washington Borough, fortified with ancient dwarven ward-stones, deep cellars, and an aether-well."
  }
}
```

## `HOMESTEAD_TROPHIES` (4 entries)
```json
{
  "gilded_overlord_core": {
    "id": "gilded_overlord_core",
    "name": "Overlord's Gilded Core",
    "buff_name": "[Aegis of the Spire]",
    "desc": "+2 Armor Class and +5% Col drop rate across all encounters.",
    "ac_bonus": 2,
    "col_drop_pct": 5
  },
  "alpha_razorhound_skull": {
    "id": "alpha_razorhound_skull",
    "name": "Alpha Razor-Hound Plated Skull",
    "buff_name": "[Apex Pack-Instinct]",
    "desc": "+2 Initiative and +10% Movement speed.",
    "initiative_bonus": 2,
    "speed_pct": 10
  },
  "clockwork_golem_heart": {
    "id": "clockwork_golem_heart",
    "name": "Clockwork Golem Geared Heart",
    "buff_name": "[Clockwork Fortitude]",
    "desc": "+15 Maximum HP and +1 Damage Resistance.",
    "hp_bonus": 15,
    "dr_bonus": 1
  },
  "direwolf_alpha_pelt": {
    "id": "direwolf_alpha_pelt",
    "name": "Roaring Rock Dire-Wolf Alpha Pelt",
    "buff_name": "[Primal Ferocity]",
    "desc": "+10% Critical Strike Chance on Melee Attacks.",
    "crit_pct": 10
  }
}
```

## `ITEM_GRADE_SCALING` (5 entries)
```json
{
  "1": {
    "name": "Common Scrap",
    "multiplier": 1.0,
    "default_durability": 50,
    "gem_slots": 0,
    "badge": "⚪ Grade 1 (Common Scrap)",
    "rarity": "Common"
  },
  "2": {
    "name": "Reinforced",
    "multiplier": 1.25,
    "default_durability": 75,
    "gem_slots": 0,
    "badge": "🟢 Grade 2 (Reinforced)",
    "rarity": "Uncommon"
  },
  "3": {
    "name": "Aether-Forged",
    "multiplier": 1.5,
    "default_durability": 100,
    "gem_slots": 1,
    "badge": "🔵 Grade 3 (Aether-Forged)",
    "rarity": "Rare"
  },
  "4": {
    "name": "Runic Masterwork",
    "multiplier": 2.0,
    "default_durability": 150,
    "gem_slots": 2,
    "badge": "🟣 Grade 4 (Runic Masterwork)",
    "rarity": "Epic"
  },
  "5": {
    "name": "Einherjar / Boss Tier",
    "multiplier": 2.5,
    "default_durability": 200,
    "gem_slots": 3,
    "badge": "🟠 Grade 5 (Einherjar)",
    "rarity": "Legendary"
  }
}
```

## `MILESTONE_THRESHOLDS` (6 entries)
```json
[
  50,
  100,
  250,
  500,
  750,
  1000
]
```

## `MYTHIC_RECIPES` (3 entries)
```json
{
  "fenrirs_howl": {
    "id": "fenrirs_howl",
    "name": "Fenrir's Howl (Grade 6 Mythic Great-Axe)",
    "grade": 6,
    "slot": "main_hand",
    "durability": 350,
    "atk_bonus": 6,
    "damage_dice": "2d12",
    "active_technique": {
      "name": "Crystalline Frost Wave",
      "type": "Active Sword Skill",
      "desc": "Unleashes a 20ft cone of sub-zero frost dealing 3d8 cold damage and freezing targets for 1 turn (0 movement, -2 AC)."
    },
    "base_item_query": "Fenrir's Tusk",
    "boss_core_query": "Overlord's Gilded Core",
    "materials": {
      "Refined Aether-Alloy": 2,
      "Carbon Line Spools": 1
    },
    "fee_col": 2000,
    "description": "A legendary black-iron bearded greataxe infused with frozen aetheric frost and the resonance of the Gilded Overlord."
  },
  "mjolnir_prime": {
    "id": "mjolnir_prime",
    "name": "Mjölnir-Prime (Grade 6 Mythic Titan-Hammer)",
    "grade": 6,
    "slot": "off_hand",
    "durability": 350,
    "atk_bonus": 5,
    "damage_dice": "3d8",
    "active_technique": {
      "name": "Kinetic Armor Shatter",
      "type": "Active Sword Skill",
      "desc": "Shatters target defenses: -4 AC debuff and disables construct Damage Resistance for 2 turns."
    },
    "base_item_query": "Mjöllnir-Null",
    "boss_core_query": "Overlord's Gilded Core",
    "materials": {
      "Corroded Micro-Capacitor": 2,
      "Refined Aether-Alloy": 1
    },
    "fee_col": 2000,
    "description": "An earth-shattering trench hammer surging with overcharged magnetic kinetic conduits."
  },
  "einherjar_sovereign_aegis": {
    "id": "einherjar_sovereign_aegis",
    "name": "Einherjar Sovereign Aegis (Grade 6 Mythic Power-Rig)",
    "grade": 6,
    "slot": "chest",
    "durability": 400,
    "ac_bonus": 10,
    "dr": 3,
    "active_technique": {
      "name": "Aetheric Citadel Fortress",
      "type": "Active Stance",
      "desc": "Stance: Gain +4 AC, Advantage on CON saves, and reflect 1d10 force damage to melee attackers for 3 turns."
    },
    "base_item_query": "Einherjar Rig",
    "boss_core_query": "Overlord's Gilded Core",
    "materials": {
      "Refined Aether-Alloy": 3
    },
    "fee_col": 2500,
    "description": "Impenetrable masterwork runic plate engineered with living aether-conduits and sovereign ward lattices."
  }
}
```

## `POHATCONG_LABYRINTH` (6 entries)
```json
{
  "id": "pohatcong_labyrinth",
  "name": "The Pohatcong Depths",
  "sector": "Sector 1 (Warren County / Washington Regional Grid)",
  "description": "An ancient subterranean aether-excavation winding deep beneath Pohatcong Mountain. Guarded by automated runic defense matrixes and culminating in the sealed throne room of the Sector 1 Overlord.",
  "entry_room": "entry_hall",
  "rooms": {
    "entry_hall": {
      "id": "entry_hall",
      "name": "Subsurface Ingress & Descent",
      "type": "sanctuary",
      "badge": "🏕️ Sanctuary Gate",
      "description": "A massive arched basalt portal carved with dampening runes. Ambient leylines hum with protective frequencies, preventing hostile incursions.",
      "connections": [
        "calcified_mine_gallery"
      ],
      "cleared": true,
      "can_rest": true
    },
    "calcified_mine_gallery": {
      "id": "calcified_mine_gallery",
      "name": "Calcified Mine Gallery",
      "type": "monster_den",
      "badge": "⚔️ Monster Den",
      "description": "Abandoned narrow-gauge rail tracks choked with calcified aether-stalagmites. Glitched burrower constructs and iron-jawed crawler chimeras skulk between the collapsed timber supports.",
      "connections": [
        "entry_hall",
        "runic_trip_corridor"
      ],
      "cleared": false,
      "monsters": [
        {
          "name": "Glitched Excavator Drone",
          "hp": 40,
          "max_hp": 40,
          "ac": 13,
          "atk": 5,
          "dmg": "1d8+2 Piercing"
        },
        {
          "name": "Aether-Corrupted Cave Stalker",
          "hp": 48,
          "max_hp": 48,
          "ac": 14,
          "atk": 6,
          "dmg": "1d10+3 Slashing"
        }
      ],
      "reward_col": 350,
      "reward_xp": 250
    },
    "runic_trip_corridor": {
      "id": "runic_trip_corridor",
      "name": "Runic Tripwire Corridor",
      "type": "trapped_corridor",
      "badge": "🪤 Trapped Corridor",
      "description": "A claustrophobic corridor embedded with luminescent cyan tripwires, recessed pendulum-scythe slots, and pressure-sensitive pressure plates wired to mana-dart ports.",
      "connections": [
        "calcified_mine_gallery",
        "drainage_junction"
      ],
      "cleared": false,
      "trap": {
        "name": "Cyan Mana-Dart & Pendulum Matrix",
        "disarm_dc": 14,
        "damage_dice": "2d10 Force",
        "disarmed": false,
        "disarm_skill": "Field Trapping or Cartography",
        "description": "Interlocking runic pressure cords primed to discharge localized force-shock waves."
      }
    },
    "drainage_junction": {
      "id": "drainage_junction",
      "name": "Subterranean Drainage Junction",
      "type": "hub",
      "badge": "🏛️ Central Hub",
      "description": "A colossal octagonal reservoir hall where mineral water cascades through massive bronze iron grates. Heavy adamant archways branch toward the reservoir, the sanctuary, and the deeper vault.",
      "connections": [
        "runic_trip_corridor",
        "echoing_reservoir",
        "crystal_sanctuary",
        "puzzle_chamber"
      ],
      "cleared": true
    },
    "echoing_reservoir": {
      "id": "echoing_reservoir",
      "name": "Echoing Subterranean Reservoir",
      "type": "monster_den",
      "badge": "⚔️ Monster Den",
      "description": "Black reflective water ripples around sunken stone pillars. An aetheric mire-beast lurks beneath the surface, guarding an ancient runic chest.",
      "connections": [
        "drainage_junction"
      ],
      "cleared": false,
      "monsters": [
        {
          "name": "Mire-Titan Carapace Lurker",
          "hp": 75,
          "max_hp": 75,
          "ac": 15,
          "atk": 7,
          "dmg": "2d8+4 Crushing"
        }
      ],
      "reward_col": 600,
      "reward_xp": 450,
      "loot": [
        {
          "name": "Resonator Tuning Prism",
          "rarity": "Rare",
          "grade": 3,
          "qty": 1,
          "desc": "A faceted prism tuned to ancient Dwarven leyline frequencies. Facilitates puzzle alignment in the vault."
        }
      ]
    },
    "crystal_sanctuary": {
      "id": "crystal_sanctuary",
      "name": "Crystal Antechamber (Haven)",
      "type": "sanctuary",
      "badge": "🏕️ Sanctuary Haven",
      "description": "Warm golden light radiates from a cluster of harmonic amber leylines. The air smells of ozone and clean rain; hostile entities cannot breach this threshold.",
      "connections": [
        "drainage_junction"
      ],
      "cleared": true,
      "can_rest": true
    },
    "puzzle_chamber": {
      "id": "puzzle_chamber",
      "name": "Harmonic Frequency Vault",
      "type": "puzzle_chamber",
      "badge": "🧩 Runic Puzzle Chamber",
      "description": "Three monolithic Dwarven resonator pillars dominate the chamber before a towering crystalline seal. Dial runes (Alpha, Delta, Omega) must be harmonized to match the local tectonic harmonic (Frequency: 3 - 1 - 4).",
      "connections": [
        "drainage_junction",
        "overlord_throne_gate"
      ],
      "cleared": false,
      "puzzle": {
        "name": "Tri-Resonant Leyline Alignment",
        "target_sequence": [
          3,
          1,
          4
        ],
        "current_sequence": [
          0,
          0,
          0
        ],
        "solved": false,
        "solve_dc": 14,
        "description": "Align the 3 Resonator Pillars to frequencies [3, 1, 4] to break the crystalline seal."
      }
    },
    "overlord_throne_gate": {
      "id": "overlord_throne_gate",
      "name": "The Gilded Overlord's Threshold",
      "type": "boss_gate",
      "badge": "🚪 Boss Gate",
      "description": "A monumental gate of blackened cold-iron reinforced with gilded filigree. Immense magical runes seal the threshold shut, vibrating with titanic aetheric pressure.",
      "connections": [
        "puzzle_chamber",
        "gilded_overlord_arena"
      ],
      "cleared": false,
      "unlocked": false
    },
    "gilded_overlord_arena": {
      "id": "gilded_overlord_arena",
      "name": "The Gilded Spire Throne Room",
      "type": "boss_arena",
      "badge": "👑 Sector Boss Arena",
      "description": "A soaring subterranean cathedral beneath the roots of Pohatcong Mountain. Suspended above an aetheric rift floats the apex guardian of Sector 1: The Gilded Spire Overlord.",
      "connections": [
        "overlord_throne_gate"
      ],
      "cleared": false,
      "boss_id": "gilded_overlord"
    }
  }
}
```

## `RECRUITABLE_COMPANIONS` (18 entries)
```json
{
  "Ren": {
    "id": "ren_sasaki",
    "name": "Ren Sasaki",
    "class": "Aether-Scholar & MageTech Artificer",
    "title": "Aether-Scholar & MageTech Artificer",
    "role": "Support, Aura Scanning, Lightning Stuns & Field Artificing",
    "level": 3,
    "hp": 35,
    "max_hp": 35,
    "xp": 450,
    "next_level_xp": 900,
    "stance": "overwatch_hacking",
    "morale": "Steady",
    "affinity": 35,
    "affinity_tier": "Ally",
    "recruited": true,
    "active": true,
    "recruitment_location": "Washington Borough Safe-Zone (Starting Companion / Vanguard)",
    "recruitment_requirements": {
      "min_level": 1,
      "col_cost": 0,
      "description": "Form a co-op pact in Sector 1."
    },
    "bio": "A studious 17-year-old survivor and trapped game tester who fused his engineering background with esoteric aetheric rune-matrices. Wields a custom brass-and-crystal MageTech caster firearm.",
    "loadout": {
      "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
      "tool": "Runic Scribe Slate (Aether-Grid Focus)",
      "deck": "Runic Scribe Slate (Aether-Grid Focus)",
      "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
      "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
    },
    "equipped": {
      "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
      "tool": "Runic Scribe Slate (Aether-Grid Focus)",
      "deck": "Runic Scribe Slate (Aether-Grid Focus)",
      "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
      "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
    },
    "skills": {
      "Mesh Exploitation": {
        "mastery": 190,
        "tier": "Journeyman",
        "description": "Perceiving spatial seams and leylines.",
        "milestones_unlocked": [
          "Logic Buffer Exploit"
        ]
      },
      "Stun-Pistol Marksmanship": {
        "mastery": 95,
        "tier": "Apprentice",
        "description": "Discharging lightning runes from MageTech firearm.",
        "milestones_unlocked": []
      },
      "Diagnostic Triage": {
        "mastery": 110,
        "tier": "Journeyman",
        "description": "Channelling restorative aether-salves.",
        "milestones_unlocked": [
          "Patch Script v1.0"
        ]
      }
    },
    "abilities": [
      "Aura Weakpoint Scan (-2 Enemy AC)",
      "MageTech Stun-Arc Salvo (DC 13 CON save vs Stun)",
      "Aether-Scrap Extraction (+25% salvage yield)"
    ],
    "stances": {
      "overwatch_hacking": {
        "name": "Leyline Overwatch",
        "label": "👁️ Leyline Overwatch",
        "tag": "[REN OVERWATCH]",
        "tactical_effect": "-2 Enemy AC debuff to primary target via weakpoint telemetry.",
        "desc": "Scans leylines and structural telemetry, debuffing target AC."
      },
      "suppression_fire": {
        "name": "MageTech Arc Suppression",
        "label": "⚡ MageTech Arc Suppression",
        "tag": "[REN SUPPRESSION]",
        "tactical_effect": "Discharges lightning-mana salvos; forces DC 13 CON save vs Staggered.",
        "desc": "Suppresses targets with crackling lightning bolts."
      },
      "full_evasion": {
        "name": "Aetheric Phase-Veil",
        "label": "🌫️ Aetheric Phase-Veil",
        "tag": "[REN EVASION]",
        "tactical_effect": "Weaves spatial distortion cloak; completely immune to single-target attacks.",
        "desc": "Blinks out of direct reality."
      },
      "utility_rigging": {
        "name": "Arcane Artificing & Mending",
        "label": "✨ Arcane Artificing & Mending",
        "tag": "[REN UTILITY]",
        "tactical_effect": "Restores +15 durability to worn equipment or scavenges bonus crystallite.",
        "desc": "Channels mending runes into ally equipment."
      }
    },
    "dual_tech_id": "runic_axe_storm"
  },
  "Elora": {
    "id": "elora_thorne",
    "name": "Elora Thorne",
    "class": "Aether-Slinger / Spellblade",
    "title": "Aether-Slinger / Spellblade",
    "role": "Ranged Burst DPS, Elemental Mana Infusion & Phase Mobility",
    "level": 3,
    "hp": 32,
    "max_hp": 32,
    "xp": 400,
    "next_level_xp": 900,
    "stance": "spellblade_flurry",
    "morale": "Steady",
    "affinity": 20,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "The Iron Spoke Tavern (Washington Borough, X:50, Y:50)",
    "recruitment_requirements": {
      "min_level": 2,
      "col_cost": 100,
      "description": "Meet Elora at the Iron Spoke Tavern and provide 100 Col for expedition rations."
    },
    "bio": "A nimble spellblade who channels raw mana into rapid-firing crystal-tipped rapiers. Dr. Thorne's estranged niece, seeking a frontline raiding party in Sector 1.",
    "loadout": {
      "main_hand": "Starlight Aether-Rapier (Enchanted Steel, 1d8+3 Piercing)",
      "off_hand": "Resonating Caster Gauntlet (Focus)",
      "armor": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)",
      "chest": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)"
    },
    "equipped": {
      "main_hand": "Starlight Aether-Rapier (Enchanted Steel, 1d8+3 Piercing)",
      "off_hand": "Resonating Caster Gauntlet (Focus)",
      "armor": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)",
      "chest": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)"
    },
    "skills": {
      "Spellblade Fencing": {
        "mastery": 175,
        "tier": "Journeyman",
        "description": "Fluid martial strikes infused with raw mana.",
        "milestones_unlocked": [
          "Lunge & Pierce"
        ]
      },
      "Aether Siphoning": {
        "mastery": 130,
        "tier": "Journeyman",
        "description": "Harvesting stray leyline charges to empower abilities.",
        "milestones_unlocked": [
          "Mana Flow"
        ]
      },
      "Acrobatic Skirmishing": {
        "mastery": 140,
        "tier": "Journeyman",
        "description": "Dancing between melee and ranged kill zones.",
        "milestones_unlocked": [
          "Quickstep"
        ]
      }
    },
    "abilities": [
      "Spellblade Flurry (3-Hit Piercing Combo)",
      "Aetheric Weapon Infusion (+1d8 Elemental DMG to Ally)",
      "Dimensional Blinkstep (Disengage without provoking opportunity attacks)"
    ],
    "stances": {
      "spellblade_flurry": {
        "name": "Spellblade Flurry",
        "label": "🗡️ Spellblade Flurry",
        "tag": "[ELORA FLURRY]",
        "tactical_effect": "Unleashes rapid piercing strikes dealing 2d8+4 Arcane DMG and +2 Attack bonus to party.",
        "desc": "High offensive DPS mode."
      },
      "aether_overcharge": {
        "name": "Aether Overcharge",
        "label": "🔮 Aether Overcharge",
        "tag": "[ELORA OVERCHARGE]",
        "tactical_effect": "Channels radiant mana into Banki's weapons; Banki deals +1d10 bonus Radiant/Lightning DMG.",
        "desc": "Weapon buffing stance."
      },
      "blink_skirmish": {
        "name": "Blink Skirmish",
        "label": "🌀 Blink Skirmish",
        "tag": "[ELORA BLINK]",
        "tactical_effect": "Teleports erratically across the perimeter; evades incoming attacks and roots a target (DC 14 DEX save).",
        "desc": "Evasive control stance."
      }
    },
    "dual_tech_id": "spellblade_vortex"
  },
  "Torvald": {
    "id": "torvald_ironvein",
    "name": "Torvald Iron-Vein",
    "class": "Deepforged Vanguard",
    "title": "Deepforged Vanguard",
    "role": "Heavy Tower Shield Tank, Frontline Threat Generation & Seismic Stuns",
    "level": 4,
    "hp": 55,
    "max_hp": 55,
    "xp": 750,
    "next_level_xp": 1200,
    "stance": "aegis_bulwark",
    "morale": "Steady",
    "affinity": 25,
    "affinity_tier": "Ally",
    "recruited": false,
    "active": false,
    "recruitment_location": "The Iron Spoke Tavern / Oxford Ridge Outpost (X:52, Y:48)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 150,
      "description": "Prove your vanguard mettle in battle and pay 150 Col for deepforged gear upkeep."
    },
    "bio": "A veteran dwarven mercenary and barkeep of the Iron Spoke. Possesses runic cyber-plated armor and a tower shield wide as a castle gate.",
    "loadout": {
      "main_hand": "Deepforged War-Axe (Heavy Runic Iron, 1d10+4 Slashing)",
      "off_hand": "Adamant Bulwark Tower Shield (+4 AC, DR 2)",
      "armor": "Runic Plate Carapace (Heavy Armor, DR 3)",
      "chest": "Runic Plate Carapace (Heavy Armor, DR 3)"
    },
    "equipped": {
      "main_hand": "Deepforged War-Axe (Heavy Runic Iron, 1d10+4 Slashing)",
      "off_hand": "Adamant Bulwark Tower Shield (+4 AC, DR 2)",
      "armor": "Runic Plate Carapace (Heavy Armor, DR 3)",
      "chest": "Runic Plate Carapace (Heavy Armor, DR 3)"
    },
    "skills": {
      "Tower Shield Phalanx": {
        "mastery": 240,
        "tier": "Journeyman",
        "description": "Mastery of defensive interlocking shield stances.",
        "milestones_unlocked": [
          "Shield Wall",
          "Brace Impact"
        ]
      },
      "Deepforged Smithing": {
        "mastery": 210,
        "tier": "Journeyman",
        "description": "Knowledge of runic alloys, temper lines, and repairs.",
        "milestones_unlocked": [
          "Field Tempering"
        ]
      },
      "Battlefield Provocation": {
        "mastery": 180,
        "tier": "Journeyman",
        "description": "Commanding hostile attention through force of presence.",
        "milestones_unlocked": [
          "Roar of Challenge"
        ]
      }
    },
    "abilities": [
      "Interception Ward (+4 AC to adjacent ally)",
      "Challenge of the Anvil (Forced Taunt)",
      "Seismic Tremor (Frontal Knockdown)"
    ],
    "stances": {
      "aegis_bulwark": {
        "name": "Aegis Bulwark",
        "label": "🛡️ Aegis Bulwark",
        "tag": "[TORVALD AEGIS]",
        "tactical_effect": "Locks tower shield on frontline; grants Banki +4 AC and absorbs 50% of incoming physical damage.",
        "desc": "Frontline damage interception."
      },
      "iron_taunt": {
        "name": "Iron Challenge",
        "label": "🗣️ Iron Challenge",
        "tag": "[TORVALD TAUNT]",
        "tactical_effect": "Bangs war-axe against adamant shield; forces all active foes to attack Torvald instead of allies.",
        "desc": "Aggro and threat control."
      },
      "seismic_slam": {
        "name": "Seismic Slam",
        "label": "💥 Seismic Slam",
        "tag": "[TORVALD SLAM]",
        "tactical_effect": "Slams shield into the earth for 2d10+5 Force DMG; chips target Break Gauge by -30.",
        "desc": "Heavy bludgeoning stun."
      }
    },
    "dual_tech_id": "titans_anvil_shockwave"
  },
  "Kibs": {
    "id": "kibs_ninefingers",
    "name": "Kibs Nine-Fingers",
    "class": "Scrapper Rogue / Infiltrator",
    "title": "Scrapper Rogue / Infiltrator",
    "role": "Shadow-Meld, Critical Backstabs, Poison Coatings & Trap Disarming",
    "level": 3,
    "hp": 30,
    "max_hp": 30,
    "xp": 350,
    "next_level_xp": 900,
    "stance": "shadow_meld",
    "morale": "Steady",
    "affinity": 15,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Meiji Dump Scrap Warrens (X:48, Y:54)",
    "recruitment_requirements": {
      "min_level": 2,
      "col_cost": 75,
      "description": "Rescue Kibs from perimeter scavengers or trade 75 Col worth of scrap parts."
    },
    "bio": "A crafty goblinoid scavenger operating out of the Meiji Dump. Possesses uncanny instincts for stealth, neurotoxin synthesis, and lockpicking.",
    "loadout": {
      "main_hand": "Serrated Scrap Dagger (1d6+3 Piercing + Bleed)",
      "off_hand": "Spring-Loaded Wrist Shank (1d4+3 Piercing)",
      "armor": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)",
      "chest": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)"
    },
    "equipped": {
      "main_hand": "Serrated Scrap Dagger (1d6+3 Piercing + Bleed)",
      "off_hand": "Spring-Loaded Wrist Shank (1d4+3 Piercing)",
      "armor": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)",
      "chest": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)"
    },
    "skills": {
      "Scrapper Infiltration": {
        "mastery": 185,
        "tier": "Journeyman",
        "description": "Unseen movement and exploitation of sightlines.",
        "milestones_unlocked": [
          "Silent Step"
        ]
      },
      "Neurotoxin Synthesis": {
        "mastery": 140,
        "tier": "Journeyman",
        "description": "Distilling monster venom into weapon coatings.",
        "milestones_unlocked": [
          "Paralytic Blend"
        ]
      },
      "Lockpick & Bypass": {
        "mastery": 205,
        "tier": "Journeyman",
        "description": "Circumventing tumblers and runic electronic latches.",
        "milestones_unlocked": [
          "Skeleton Keying"
        ]
      }
    },
    "abilities": [
      "Shadow Strike (+3d6 Critical Bleed)",
      "Corrosive Neurotoxin Coating (-2 Enemy Saves)",
      "Scavenger's Eye (+30% bonus Col find)"
    ],
    "stances": {
      "shadow_meld": {
        "name": "Shadow Meld",
        "label": "👤 Shadow Meld",
        "tag": "[KIBS SNEAK]",
        "tactical_effect": "Melds into shadows; unleashes guaranteed sneak attack for 3d6+6 Piercing DMG + Bleed.",
        "desc": "High critical stealth DPS."
      },
      "venom_coating": {
        "name": "Venom Coating",
        "label": "🧪 Venom Coating",
        "tag": "[KIBS VENOM]",
        "tactical_effect": "Coats party weapons in neurotoxin; attacks deal +1d6 Acid damage and inflict -2 to enemy saving throws.",
        "desc": "Poison debuff support."
      },
      "lockpick_salvage": {
        "name": "Lockpick & Salvage",
        "label": "🗝️ Lockpick & Salvage",
        "tag": "[KIBS SALVAGE]",
        "tactical_effect": "Grants +4 bonus on all trap disarm and chest checks; increases party Col yield by +20%.",
        "desc": "Exploration and looting utility."
      }
    },
    "dual_tech_id": "shadow_flank_execution"
  },
  "Valeria": {
    "id": "companion_valeria",
    "name": "Valeria Vane",
    "class": "Primal Valkyrie / Aerial Skirmisher",
    "title": "Primal Valkyrie / Aerial Skirmisher",
    "role": "Aerial High-Ground Recon, Dive-Bomb Impalement & Radiant Shielding",
    "level": 4,
    "hp": 48,
    "max_hp": 48,
    "xp": 800,
    "next_level_xp": 1200,
    "stance": "aerial_divebomb",
    "morale": "Steady",
    "affinity": 25,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Warren County Barony Watchtower (Washington Borough, X:52, Y:50)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "faction": "Warren County Barony",
      "min_rep": 15,
      "description": "Reach Level 3 and achieve Respected standing (15+ Rep) with Warren County Barony."
    },
    "bio": "A phrenic human aerial skirmisher whose spine fused with aerodynamic aether-glider struts. Serves as Barony aerial perimeter commander.",
    "loadout": {
      "main_hand": "Winged Aether-Spear (1d10+4 Piercing)",
      "off_hand": "Solar Aegis Shield (+3 AC, Radiant Blind)",
      "armor": "Falcon Crest Mail (DR 2, Flight)",
      "chest": "Falcon Crest Mail (DR 2, Flight)"
    },
    "equipped": {
      "main_hand": "Winged Aether-Spear (1d10+4 Piercing)",
      "off_hand": "Solar Aegis Shield (+3 AC, Radiant Blind)",
      "armor": "Falcon Crest Mail (DR 2, Flight)",
      "chest": "Falcon Crest Mail (DR 2, Flight)"
    },
    "skills": {
      "Aerial Spear Technique": {
        "mastery": 260,
        "tier": "Adept",
        "description": "High-velocity vertical thrusts.",
        "milestones_unlocked": [
          "Dive-Strike Impact",
          "Falcon Lunge"
        ]
      },
      "Aether Gliding": {
        "mastery": 240,
        "tier": "Journeyman",
        "description": "Mastery of thermal drafts and aetheric lift.",
        "milestones_unlocked": [
          "Thermal Glide"
        ]
      },
      "Aegis Phalanx": {
        "mastery": 180,
        "tier": "Journeyman",
        "description": "Radiant shield positioning.",
        "milestones_unlocked": [
          "Blinding Glare"
        ]
      }
    },
    "abilities": [
      "Solar Dive-Bomb (3d10 Radiant/Piercing + Knockdown)",
      "Skyward Interception (+3 AC to ground ally)",
      "Blinding Sunburst (DC 14 CON vs Blinded)"
    ],
    "stances": {
      "aerial_divebomb": {
        "name": "Aerial Dive-Bomb",
        "label": "🦅 Aerial Dive-Bomb",
        "tag": "[VALERIA DIVE]",
        "tactical_effect": "Dives from the sky dealing 2d10+4 Piercing DMG and knocking targets prone.",
        "desc": "High offensive aerial assault."
      },
      "radiant_bulwark": {
        "name": "Radiant Bulwark",
        "label": "🛡️ Radiant Bulwark",
        "tag": "[VALERIA BULWARK]",
        "tactical_effect": "Hovers above the vanguard, granting Banki +3 AC and absorbing projectile fire.",
        "desc": "Aerial defensive perimeter."
      },
      "high_overwatch": {
        "name": "High-Ground Overwatch",
        "label": "👁️ High-Ground Overwatch",
        "tag": "[VALERIA RECON]",
        "tactical_effect": "Scouts the perimeter from cloud altitude, revealing concealed enemies and granting +3 party Initiative.",
        "desc": "Aerial reconnaissance."
      }
    },
    "dual_tech_id": "valkyries_wrath"
  },
  "Morrigan": {
    "id": "companion_morrigan",
    "name": "Morrigan Black-Thorn",
    "class": "Abyssal Grave-Binder / Necrotic Hexer",
    "title": "Abyssal Grave-Binder / Necrotic Hexer",
    "role": "Necrotic Crowd Control, Soul-Siphon Drain & Bone Barricades",
    "level": 3,
    "hp": 34,
    "max_hp": 34,
    "xp": 450,
    "next_level_xp": 900,
    "stance": "soul_siphon",
    "morale": "Steady",
    "affinity": 20,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Musconetcong Crypts - Sunken Ossuary (X:45, Y:62)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "quest": "crypt_reanimator",
      "description": "Defeat the Crypt Reanimator in the Musconetcong Crypts and recover the Shattered Veil Tome."
    },
    "bio": "An umbral tiefling shadow-weaver who harvests digital soul-residue and deceased bio-mana from fallen monsters.",
    "loadout": {
      "main_hand": "Bone-Chime Scythe (1d8+3 Slashing + 1d6 Necrotic)",
      "off_hand": "Soul-Vessel Phylactery (Focus)",
      "armor": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)",
      "chest": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)"
    },
    "equipped": {
      "main_hand": "Bone-Chime Scythe (1d8+3 Slashing + 1d6 Necrotic)",
      "off_hand": "Soul-Vessel Phylactery (Focus)",
      "armor": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)",
      "chest": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)"
    },
    "skills": {
      "Necrotic Siphoning": {
        "mastery": 210,
        "tier": "Journeyman",
        "description": "Draining vitality from decaying tissue.",
        "milestones_unlocked": [
          "Soul Tap",
          "Life Leech"
        ]
      },
      "Bone Matrix Weaving": {
        "mastery": 180,
        "tier": "Journeyman",
        "description": "Erecting calcified bone barriers.",
        "milestones_unlocked": [
          "Ossuary Shield"
        ]
      },
      "Abyssal Hexes": {
        "mastery": 195,
        "tier": "Journeyman",
        "description": "Debilitating enemy metabolic functions.",
        "milestones_unlocked": [
          "Withering Curse"
        ]
      }
    },
    "abilities": [
      "Soul-Siphon Lash (1d8 Necrotic DMG + restores 8 HP to lowest ally)",
      "Grave-Wall Erection (absorbs 30 incoming damage)",
      "Miasma of the Tomb (-2 Enemy Saves)"
    ],
    "stances": {
      "soul_siphon": {
        "name": "Soul-Siphon Drain",
        "label": "💀 Soul-Siphon Drain",
        "tag": "[MORRIGAN SIPHON]",
        "tactical_effect": "Drains 2d6 Necrotic DMG from target, transferring health to Banki.",
        "desc": "Lifesteal support stance."
      },
      "skeletal_wall": {
        "name": "Skeletal Wall",
        "label": "🦴 Skeletal Wall",
        "tag": "[MORRIGAN BONEWALL]",
        "tactical_effect": "Raises calcified bone palisades that intercept up to 30 damage from incoming enemy attacks.",
        "desc": "Barrier defense."
      },
      "miasma_curse": {
        "name": "Miasma Hex Aura",
        "label": "🌫️ Miasma Hex Aura",
        "tag": "[MORRIGAN MIASMA]",
        "tactical_effect": "Surrounds the enemy line in choking grave-mist; enemies suffer -2 to saving throws and lose 5 HP/turn.",
        "desc": "AOE necrotic debuff."
      }
    },
    "dual_tech_id": "grave_lord_cleave"
  },
  "Garrick": {
    "id": "companion_garrick",
    "name": "Garrick Stone-Grip",
    "class": "Seismic Brawler / Ki-Siphon Pugilist",
    "title": "Seismic Brawler / Ki-Siphon Pugilist",
    "role": "Unarmed Frontline Pressure, Kinetic Deflection & Break Gauge Stun",
    "level": 4,
    "hp": 52,
    "max_hp": 52,
    "xp": 750,
    "next_level_xp": 1200,
    "stance": "mountain_crusher",
    "morale": "Steady",
    "affinity": 25,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Pequest River Limestone Quarry (X:38, Y:42)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "stat_check": "STR 14 or Athletics 100",
      "description": "Defeat or spar with Garrick to a standstill in the Quarry fighting ring."
    },
    "bio": "An Earth Genasi structural ironworker whose knuckles and skin calcified into dense granite. Dominates the Pequest quarries.",
    "loadout": {
      "main_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
      "off_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
      "armor": "Iron-Thread Gi (Unarmored, DR 2)",
      "chest": "Iron-Thread Gi (Unarmored, DR 2)"
    },
    "equipped": {
      "main_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
      "off_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
      "armor": "Iron-Thread Gi (Unarmored, DR 2)",
      "chest": "Iron-Thread Gi (Unarmored, DR 2)"
    },
    "skills": {
      "Unarmed Pummeling": {
        "mastery": 280,
        "tier": "Adept",
        "description": "Bone-cracking pugilism.",
        "milestones_unlocked": [
          "Iron Fist",
          "Staggering Hook",
          "Haymaker"
        ]
      },
      "Seismic Grounding": {
        "mastery": 220,
        "tier": "Journeyman",
        "description": "Rooting into tectonic bedrock.",
        "milestones_unlocked": [
          "Unyielding Stance"
        ]
      },
      "Ki Kinetic Deflection": {
        "mastery": 190,
        "tier": "Journeyman",
        "description": "Deflecting incoming missiles with bare hands.",
        "milestones_unlocked": [
          "Missile Snatch"
        ]
      }
    },
    "abilities": [
      "Tectonic Tremor Palm (2d8+5 Force + Stagger)",
      "Iron Shirt Deflection (Absorbs 15 Bludgeoning/Piercing)",
      "Earthquake Stomp (Prone all enemies in 10ft)"
    ],
    "stances": {
      "mountain_crusher": {
        "name": "Mountain-Crusher Stance",
        "label": "⛰️ Mountain-Crusher",
        "tag": "[GARRICK CRUSHER]",
        "tactical_effect": "Strikes target with 2d8+5 Bludgeoning DMG; chips boss Break Gauge by -35.",
        "desc": "High stun and break gauge pressure."
      },
      "ki_deflection": {
        "name": "Ki-Deflection Weave",
        "label": "🥋 Ki-Deflection Weave",
        "tag": "[GARRICK DEFLECT]",
        "tactical_effect": "Swats aside incoming projectiles and melee strikes, granting himself and Banki +3 AC.",
        "desc": "Martial defensive weave."
      },
      "seismic_slam": {
        "name": "Earth-Shatter Flurry",
        "label": "💥 Earth-Shatter Flurry",
        "tag": "[GARRICK FLURRY]",
        "tactical_effect": "Unleashes 3 rapid concussive palm strikes dealing 3d6+6 Force DMG and forcing DC 14 STR check vs Prone.",
        "desc": "Multi-hit knockdown flurry."
      }
    },
    "dual_tech_id": "seismic_cataclysm"
  },
  "Sariel": {
    "id": "companion_sariel",
    "name": "Sariel Swift-Wind",
    "class": "Verdant Deadeye / Beast-Stalker",
    "title": "Verdant Deadeye / Beast-Stalker",
    "role": "Extreme-Range Sniping, Crippling Arrow Volleys & Wilderness Tracking",
    "level": 3,
    "hp": 32,
    "max_hp": 32,
    "xp": 400,
    "next_level_xp": 900,
    "stance": "canopy_snipe",
    "morale": "Steady",
    "affinity": 20,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Jenny Jump Forest Canopy - Roaming Glade (X:58, Y:35)",
    "recruitment_requirements": {
      "min_level": 2,
      "col_cost": 0,
      "item_delivery": [
        "Venison Ration",
        "Wild Forest Herbs x2"
      ],
      "description": "Track her scent through Jenny Jump Forest (Perception DC 13) and deliver forest rations."
    },
    "bio": "A wild wood elf ranger who nests in the 400-foot ironwood trees of Jenny Jump. Unerring sniper with living ironwood recurve bow.",
    "loadout": {
      "main_hand": "Living Ironwood Recurve Bow (1d10+4 Piercing)",
      "off_hand": "None (Two-Handed)",
      "armor": "Camouflage Ghillie-Cloak (Light, +4 Stealth)",
      "chest": "Camouflage Ghillie-Cloak (Light, +4 Stealth)"
    },
    "equipped": {
      "main_hand": "Living Ironwood Recurve Bow (1d10+4 Piercing)",
      "off_hand": "None (Two-Handed)",
      "armor": "Camouflage Ghillie-Cloak (Light, +4 Stealth)",
      "chest": "Camouflage Ghillie-Cloak (Light, +4 Stealth)"
    },
    "skills": {
      "Archery Mastery": {
        "mastery": 270,
        "tier": "Adept",
        "description": "Pinpoint extreme-range shooting.",
        "milestones_unlocked": [
          "Double Shot",
          "Ocular Piercing",
          "Eagle Eye"
        ]
      },
      "Wilderness Stalking": {
        "mastery": 240,
        "tier": "Journeyman",
        "description": "Moving without disturbing leaf or twig.",
        "milestones_unlocked": [
          "Forest Ghost"
        ]
      },
      "Beast Anatomy": {
        "mastery": 180,
        "tier": "Journeyman",
        "description": "Targeting beast tendon and heart nodes.",
        "milestones_unlocked": [
          "Cripple Tendon"
        ]
      }
    },
    "abilities": [
      "Heartseeker Snipe (3d10 Piercing DMG from stealth)",
      "Barbed Hamstring Volley (Roots target for 1 turn)",
      "Wind-Guidance Aura (+2 Ranged ATK to party)"
    ],
    "stances": {
      "canopy_snipe": {
        "name": "Canopy Snipe",
        "label": "🏹 Canopy Snipe",
        "tag": "[SARIEL SNIPE]",
        "tactical_effect": "Fires from maximum concealment dealing 2d10+4 Piercing DMG, ignoring 50% enemy armor.",
        "desc": "High critical range sniping."
      },
      "suppression_volley": {
        "name": "Barbed Suppression Volley",
        "label": "🌧️ Barbed Volley",
        "tag": "[SARIEL VOLLEY]",
        "tactical_effect": "Rains barbed arrows in an arc; slows all advancing enemies and inflicts Bleed (6 DMG/turn).",
        "desc": "Area crowd control."
      },
      "stealth_ambush": {
        "name": "Woodland Camouflage",
        "label": "🌿 Woodland Camouflage",
        "tag": "[SARIEL CAMO]",
        "tactical_effect": "Melds into foliage; completely untargetable until next attack which is an automatic Critical Hit.",
        "desc": "Stealth setup."
      }
    },
    "dual_tech_id": "cyclone_arrow_storm"
  },
  "Kaelen": {
    "id": "companion_kaelen",
    "name": "Brother Kaelen",
    "class": "Sol-Templar / Radiant Apothecary",
    "title": "Sol-Templar / Radiant Apothecary",
    "role": "Frontline Healing, Radiant Flail Burst & Condition Cleansing",
    "level": 3,
    "hp": 40,
    "max_hp": 40,
    "xp": 450,
    "next_level_xp": 900,
    "stance": "radiant_bastion",
    "morale": "Steady",
    "affinity": 30,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "St. Luke's Chapel Ruins (High Bridge Safe-Node, X:65, Y:55)",
    "recruitment_requirements": {
      "min_level": 2,
      "col_cost": 200,
      "description": "Donate 200 Col to the High Bridge hospice or restore the Sunstone Altar."
    },
    "bio": "An aasimar parish deacon and former EMT whose veins pulse with solar mana. Wields a heavy sunstone flail to protect the wounded.",
    "loadout": {
      "main_hand": "Radiant War-Flail (1d8+3 Bludgeoning + 1d8 Radiant)",
      "off_hand": "Sunstone Focus Censer (Holy Focus)",
      "armor": "Gilded Crusader Mail (Heavy, DR 2)",
      "chest": "Gilded Crusader Mail (Heavy, DR 2)"
    },
    "equipped": {
      "main_hand": "Radiant War-Flail (1d8+3 Bludgeoning + 1d8 Radiant)",
      "off_hand": "Sunstone Focus Censer (Holy Focus)",
      "armor": "Gilded Crusader Mail (Heavy, DR 2)",
      "chest": "Gilded Crusader Mail (Heavy, DR 2)"
    },
    "skills": {
      "Radiant Restoration": {
        "mastery": 250,
        "tier": "Adept",
        "description": "Channelling restorative solar fire.",
        "milestones_unlocked": [
          "Solar Mending",
          "Purifying Pulse"
        ]
      },
      "War-Flail Discipline": {
        "mastery": 190,
        "tier": "Journeyman",
        "description": "Swinging spiked morningstar chains.",
        "milestones_unlocked": [
          "Shield Bypass"
        ]
      },
      "Aura of Protection": {
        "mastery": 220,
        "tier": "Journeyman",
        "description": "Radiant protective aegis for allies.",
        "milestones_unlocked": [
          "Sanctuary Ward"
        ]
      }
    },
    "abilities": [
      "Sun-Burst Heal (+25 HP to ally + cleanses poison/bleed)",
      "Solar Smite (+2d8 Radiant DMG vs Undead/Fiends)",
      "Aegis of the Brass Sun (+3 AC to adjacent allies)"
    ],
    "stances": {
      "radiant_bastion": {
        "name": "Radiant Bastion Aura",
        "label": "☀️ Radiant Bastion",
        "tag": "[KAELEN BASTION]",
        "tactical_effect": "Radiates solar protection; restores +8 HP to Banki each turn and grants +2 to all saving throws.",
        "desc": "Persistent healing aura."
      },
      "cleansing_sunburst": {
        "name": "Cleansing Sunburst",
        "label": "✨ Cleansing Sunburst",
        "tag": "[KAELEN SUNBURST]",
        "tactical_effect": "Unleashes blinding solar flash for 2d8+3 Radiant DMG; removes all debuffs from party.",
        "desc": "Damage and cleanse."
      },
      "crusader_smite": {
        "name": "Crusader Smite",
        "label": "🔨 Crusader Smite",
        "tag": "[KAELEN SMITE]",
        "tactical_effect": "Swings radiant flail dealing 1d10+4 Bludgeoning + 2d8 Radiant DMG, ignoring enemy shields.",
        "desc": "Offensive shield-breaker."
      }
    },
    "dual_tech_id": "dawn_breaker_smite"
  },
  "Zedd": {
    "id": "companion_zedd",
    "name": "Zeddicus Volt-Spark",
    "class": "Plasma-Mage / Galvanic Dynamo",
    "title": "Plasma-Mage / Galvanic Dynamo",
    "role": "Chain-Lightning AOE, Superconductor Field & Armor Splicing",
    "level": 3,
    "hp": 30,
    "max_hp": 30,
    "xp": 420,
    "next_level_xp": 900,
    "stance": "plasma_arc",
    "morale": "Steady",
    "affinity": 25,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Decommissioned Edison Substation (Belvidere Junction, X:30, Y:50)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "puzzle": "substation_grid",
      "description": "Solve the Substation Power-Grid puzzle (INT DC 13) or deliver 2 Voltaic Cores."
    },
    "bio": "A high-voltage lineman who survived a 500kV discharge when the Crucible hit. Fused with dorsal capacitors, he commands plasma arcs.",
    "loadout": {
      "main_hand": "Galvanic Arc Staff (1d6+3 Bludgeoning + 2d6 Lightning)",
      "off_hand": "Capacitor Battery Rig (Focus)",
      "armor": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)",
      "chest": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)"
    },
    "equipped": {
      "main_hand": "Galvanic Arc Staff (1d6+3 Bludgeoning + 2d6 Lightning)",
      "off_hand": "Capacitor Battery Rig (Focus)",
      "armor": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)",
      "chest": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)"
    },
    "skills": {
      "Galvanic Sorcery": {
        "mastery": 240,
        "tier": "Journeyman",
        "description": "Channelling high-voltage aetheric arcs.",
        "milestones_unlocked": [
          "Chain Lightning",
          "Static Overload"
        ]
      },
      "Capacitor Engineering": {
        "mastery": 210,
        "tier": "Journeyman",
        "description": "Storing and regulating energetic voltage.",
        "milestones_unlocked": [
          "Overcharge Valve"
        ]
      },
      "Dielectric Piercing": {
        "mastery": 180,
        "tier": "Journeyman",
        "description": "Melting metal armor with plasma heat.",
        "milestones_unlocked": [
          "Arc Weld"
        ]
      }
    },
    "abilities": [
      "Ball Lightning Discharge (3d8 Lightning AOE)",
      "Static Overcharge (Weapon buff: +1d10 Shock DMG to Banki)",
      "Dielectric EMP (Stuns constructs for 1 turn)"
    ],
    "stances": {
      "plasma_arc": {
        "name": "Overcharge Plasma Arc",
        "label": "⚡ Plasma Arc",
        "tag": "[ZEDD PLASMA]",
        "tactical_effect": "Discharges chain lightning dealing 2d10+4 Shock DMG that arcs across up to 3 targets.",
        "desc": "Multi-target lightning assault."
      },
      "superconductor_field": {
        "name": "Superconductor Field",
        "label": "🌐 Superconductor Field",
        "tag": "[ZEDD FIELD]",
        "tactical_effect": "Deploys crackling electric perimeter; any enemy entering melee takes 1d8 Shock DMG and loses 10ft movement.",
        "desc": "Defensive area denial."
      },
      "capacitive_burst": {
        "name": "Static Discharge Burst",
        "label": "💥 Static Burst",
        "tag": "[ZEDD BURST]",
        "tactical_effect": "Vents all dorsal capacitors into a single concussive shockwave dealing 3d8 Force/Lightning DMG and knocking foes back 15ft.",
        "desc": "Point-blank peel."
      }
    },
    "dual_tech_id": "volt_tempest_detonation"
  },
  "Daphne": {
    "id": "companion_daphne",
    "name": "Daphne Leclair",
    "class": "Spellsinger / Skaldic Virtuoso",
    "title": "Spellsinger / Skaldic Virtuoso",
    "role": "Vocal Attack Buffs, Sonic Stuns & Skaldic Battle Anthems",
    "level": 3,
    "hp": 32,
    "max_hp": 32,
    "xp": 380,
    "next_level_xp": 900,
    "stance": "berserker_hymn",
    "morale": "Steady",
    "affinity": 25,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "The Rusty Flagon Speakeasy (Easton Riverfront Node, X:22, Y:55)",
    "recruitment_requirements": {
      "min_level": 2,
      "col_cost": 350,
      "description": "Pay off her 350 Col tavern tab OR perform a collaborative battle ballad (CHA DC 14)."
    },
    "bio": "A half-elf siren-kin jazz singer whose vocal harmonies bend sound waves into sonic concussions and battle-buffs.",
    "loadout": {
      "main_hand": "Silvered Stiletto (1d4+3 Piercing)",
      "off_hand": "Resonating Aether-Lute (Focus)",
      "armor": "Velvet Performer's Doublet (+2 CHA, DR 1)",
      "chest": "Velvet Performer's Doublet (+2 CHA, DR 1)"
    },
    "equipped": {
      "main_hand": "Silvered Stiletto (1d4+3 Piercing)",
      "off_hand": "Resonating Aether-Lute (Focus)",
      "armor": "Velvet Performer's Doublet (+2 CHA, DR 1)",
      "chest": "Velvet Performer's Doublet (+2 CHA, DR 1)"
    },
    "skills": {
      "Spellsinging": {
        "mastery": 250,
        "tier": "Adept",
        "description": "Weaving acoustic vibrations into magic.",
        "milestones_unlocked": [
          "Sonic Boom",
          "Song of Valor"
        ]
      },
      "Acoustic Manipulation": {
        "mastery": 200,
        "tier": "Journeyman",
        "description": "Bending resonance to disrupt spellcasting.",
        "milestones_unlocked": [
          "Counter-Melody"
        ]
      },
      "Streetwise Performance": {
        "mastery": 180,
        "tier": "Journeyman",
        "description": "Extracting rumors and winning tavern crowds.",
        "milestones_unlocked": [
          "Silver Tongue"
        ]
      }
    },
    "abilities": [
      "Song of Sovereign Might (+4 DMG & +2 ATK to Party)",
      "Discordant Screech (DC 14 CON vs Stun)",
      "Lullaby of the Void (Puts non-elite target to sleep)"
    ],
    "stances": {
      "berserker_hymn": {
        "name": "Hymn of the Berserker",
        "label": "🎶 Berserker Hymn",
        "tag": "[DAPHNE HYMN]",
        "tactical_effect": "Sings a thunderous battle chant; grants Banki +3 Attack rolls and +1d8 weapon damage.",
        "desc": "High offensive party buff."
      },
      "discordant_screech": {
        "name": "Discordant Screech",
        "label": "🔊 Discordant Screech",
        "tag": "[DAPHNE SCREECH]",
        "tactical_effect": "Plucks a shattering resonant chord dealing 2d6 Thunder DMG and forcing DC 14 CON check vs Disoriented.",
        "desc": "Sonic disruption."
      },
      "fleeting_shadows": {
        "name": "Song of Fleeting Shadows",
        "label": "🌫️ Fleeting Shadows",
        "tag": "[DAPHNE SHADOWS]",
        "tactical_effect": "Weaves acoustic dampening; grants all allies +4 Stealth and +2 Dodge AC.",
        "desc": "Evasive party defense."
      }
    },
    "dual_tech_id": "valkyrie_war_chorus"
  },
  "Rok": {
    "id": "companion_rok",
    "name": "Ragnarok 'Rok'",
    "class": "Juggernaut Marauder / Blood-Rager",
    "title": "Juggernaut Marauder / Blood-Rager",
    "role": "Berserk Melee Fury, High Physical DR & Twin Cleaver Slaughter",
    "level": 4,
    "hp": 58,
    "max_hp": 58,
    "xp": 850,
    "next_level_xp": 1200,
    "stance": "blood_frenzy",
    "morale": "Bloodthirsty",
    "affinity": 20,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Blood-Pit Arena (Oxford Iron Mines Slag Heaps, X:55, Y:45)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "duel": "slag_pit_brawl",
      "description": "Defeat Rok in the Slag Pit duel OR match him drink-for-drink in dwarven gut-burner ale (CON DC 15)."
    },
    "bio": "A half-orc bio-chimeric marauder who wields twin jagged slag-cleavers. Becomes exponentially deadlier as his health drops.",
    "loadout": {
      "main_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
      "off_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
      "armor": "Troll-Hide Kilt (Heavy Leathers, DR 3)",
      "chest": "Troll-Hide Kilt (Heavy Leathers, DR 3)"
    },
    "equipped": {
      "main_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
      "off_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
      "armor": "Troll-Hide Kilt (Heavy Leathers, DR 3)",
      "chest": "Troll-Hide Kilt (Heavy Leathers, DR 3)"
    },
    "skills": {
      "Dual-Axe Slaughter": {
        "mastery": 290,
        "tier": "Adept",
        "description": "Relentless twin-weapon onslaught.",
        "milestones_unlocked": [
          "Whirlwind Rake",
          "Decapitate",
          "Blood Fountain"
        ]
      },
      "Pain Tolerance": {
        "mastery": 270,
        "tier": "Adept",
        "description": "Converting physical trauma into adrenaline.",
        "milestones_unlocked": [
          "Thick Skinned",
          "Berserk Vigor"
        ]
      },
      "Intimidating Roar": {
        "mastery": 210,
        "tier": "Journeyman",
        "description": "Terrifying lesser foes with primal bellows.",
        "milestones_unlocked": [
          "Battle Shriek"
        ]
      }
    },
    "abilities": [
      "Blood-Frenzy Charge (3d10+8 Slashing + Knocks Prone)",
      "Unyielding Rage (Cannot drop below 1 HP for 1 turn)",
      "Meat-Hook Cleave (Pulls enemy into melee range)"
    ],
    "stances": {
      "blood_frenzy": {
        "name": "Blood-Frenzy Rampage",
        "label": "🩸 Blood Frenzy",
        "tag": "[ROK FRENZY]",
        "tactical_effect": "Swings twin cleavers wildly dealing 2d10+6 Slashing DMG; gains +2 DMG for every 10 HP missing.",
        "desc": "Ramping berserk damage."
      },
      "unyielding_flesh": {
        "name": "Unyielding Flesh",
        "label": "🛡️ Unyielding Flesh",
        "tag": "[ROK FLESH]",
        "tactical_effect": "Tenses troll-grafted muscles; gains DR 4 against physical damage and taunts all active foes.",
        "desc": "Frontline berserk tanking."
      },
      "cleaver_whirl": {
        "name": "Whirlwind Slag-Torn",
        "label": "🌪️ Slag Whirlwind",
        "tag": "[ROK WHIRL]",
        "tactical_effect": "Spins in a tight circle dealing 2d8+4 Slashing DMG to all adjacent enemies with guaranteed Bleed.",
        "desc": "Melee AOE cleave."
      }
    },
    "dual_tech_id": "blood_twin_cleave"
  },
  "Lyra": {
    "id": "companion_lyra",
    "name": "Lyra Stargaze",
    "class": "Chronomancer / Temporal Weaver",
    "title": "Chronomancer / Temporal Weaver",
    "role": "Timeline Dilation, Haste Buffs, Slow Fields & Wound Reversal",
    "level": 4,
    "hp": 28,
    "max_hp": 28,
    "xp": 780,
    "next_level_xp": 1200,
    "stance": "temporal_haste",
    "morale": "Steady",
    "affinity": 25,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "High Point Observatory Spire (Sussex Overlook, X:48, Y:12)",
    "recruitment_requirements": {
      "min_level": 4,
      "col_cost": 0,
      "item": "Refined Aether-Crystal",
      "description": "Reach Level 4 and calibrate the Astrolabe Focal Prism using an Aether-Crystal."
    },
    "bio": "An aether-born stargazer astrophysicist who manipulates timeline foam to speed allies, freeze foes, and rewind lethal wounds.",
    "loadout": {
      "main_hand": "Chrono-Staff of Moments (1d6+3 Bludgeoning + Time Warp)",
      "off_hand": "Hourglass Focus (Cosmic Focus)",
      "armor": "Star-Silk Robes (+2 INT, DR 1)",
      "chest": "Star-Silk Robes (+2 INT, DR 1)"
    },
    "equipped": {
      "main_hand": "Chrono-Staff of Moments (1d6+3 Bludgeoning + Time Warp)",
      "off_hand": "Hourglass Focus (Cosmic Focus)",
      "armor": "Star-Silk Robes (+2 INT, DR 1)",
      "chest": "Star-Silk Robes (+2 INT, DR 1)"
    },
    "skills": {
      "Chronomancy": {
        "mastery": 290,
        "tier": "Adept",
        "description": "Accelerating and decelerating causal flow.",
        "milestones_unlocked": [
          "Haste Glyphs",
          "Time Dilation",
          "Temporal Anchor"
        ]
      },
      "Stargazing Telemetry": {
        "mastery": 240,
        "tier": "Journeyman",
        "description": "Calculating celestial alignment and odds.",
        "milestones_unlocked": [
          "Fate Reading"
        ]
      },
      "Temporal Mending": {
        "mastery": 210,
        "tier": "Journeyman",
        "description": "Reversing physical damage into past states.",
        "milestones_unlocked": [
          "Rewind Tissue"
        ]
      }
    },
    "abilities": [
      "Chrono-Stasis Bubble (Freezes target for 1 turn)",
      "Haste Surge (Grants Banki an extra standard action)",
      "Temporal Rewind (Reverses last turn's damage on ally)"
    ],
    "stances": {
      "temporal_haste": {
        "name": "Haste Surge Acceleration",
        "label": "⏳ Haste Surge",
        "tag": "[LYRA HASTE]",
        "tactical_effect": "Bends time around Banki; grants Banki +4 Initiative and an extra attack every other turn.",
        "desc": "Speed and action accelerator."
      },
      "time_dilation": {
        "name": "Time Dilation Field",
        "label": "🌀 Dilation Field",
        "tag": "[LYRA SLOW]",
        "tactical_effect": "Traps enemy frontliners in viscous time; enemies suffer -4 to AC and lose their reactions.",
        "desc": "Enemy time freeze."
      },
      "wound_echo": {
        "name": "Rewind Wound Echoes",
        "label": "⏪ Wound Rewind",
        "tag": "[LYRA REWIND]",
        "tactical_effect": "Rewinds time on the most damaged ally, restoring 20 HP from injuries sustained this combat.",
        "desc": "Temporal healing."
      }
    },
    "dual_tech_id": "temporal_shatter_strike"
  },
  "Titus": {
    "id": "companion_titus",
    "name": "Titus Sterling",
    "class": "Aegis-Automaton / Iron-Clad Sentinel",
    "title": "Aegis-Automaton / Iron-Clad Sentinel",
    "role": "Impenetrable Interception Tank, Blast Furnace Armor & Steam Concussion",
    "level": 4,
    "hp": 65,
    "max_hp": 65,
    "xp": 850,
    "next_level_xp": 1200,
    "stance": "iron_curtain",
    "morale": "Dignified",
    "affinity": 30,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Abandoned Bethlehem Steel Foundry (Lehigh Basin Node, X:18, Y:65)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "repair_items": [
        "Refined Aether-Alloy x2",
        "Clockwork Gyroscope"
      ],
      "description": "Repair his fractured boiler core (Crafting DC 12) with alloy and clockwork parts."
    },
    "bio": "A sentient Victorian-era steam golem from Bethlehem Steel. Formally polite butler who absorbs up to 75% of party damage.",
    "loadout": {
      "main_hand": "Pneumatic Slag-Hammer (1d12+5 Bludgeoning)",
      "off_hand": "Steam-Buffered Kinetic Barrier (+4 AC, DR 2)",
      "armor": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)",
      "chest": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)"
    },
    "equipped": {
      "main_hand": "Pneumatic Slag-Hammer (1d12+5 Bludgeoning)",
      "off_hand": "Steam-Buffered Kinetic Barrier (+4 AC, DR 2)",
      "armor": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)",
      "chest": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)"
    },
    "skills": {
      "Sentinel Interception": {
        "mastery": 300,
        "tier": "Adept",
        "description": "Placing iron chassis between allies and harm.",
        "milestones_unlocked": [
          "Bodyguard Intercept",
          "Shield Ward",
          "Kinetic Absorption"
        ]
      },
      "Blast Furnace Engineering": {
        "mastery": 250,
        "tier": "Adept",
        "description": "Regulating steam pressure and thermal vents.",
        "milestones_unlocked": [
          "Overheat Discharge"
        ]
      },
      "Pneumatic Warfare": {
        "mastery": 220,
        "tier": "Journeyman",
        "description": "Heavy hammer strikes propelled by pistons.",
        "milestones_unlocked": [
          "Piston Slam"
        ]
      }
    },
    "abilities": [
      "Iron Curtain Intercept (Absorbs 75% of damage intended for Banki)",
      "Steam Vent Blind (DC 14 CON vs Scalded/Blind)",
      "Pneumatic Crater Slam (3d10 Bludgeoning + Stun)"
    ],
    "stances": {
      "iron_curtain": {
        "name": "Iron-Curtain Interception",
        "label": "🛡️ Iron Curtain",
        "tag": "[TITUS INTERCEPT]",
        "tactical_effect": "Interposes iron frame; intercepts 75% of incoming damage to Banki, reducing it by DR 4.",
        "desc": "Ultimate damage protection."
      },
      "steam_flare": {
        "name": "Steam Exhaust Flare",
        "label": "💨 Steam Flare",
        "tag": "[TITUS STEAM]",
        "tactical_effect": "Vents boiling steam in a 15ft cone; deals 2d8 Fire DMG and inflicts -3 to enemy attack rolls.",
        "desc": "Area blindness and burn."
      },
      "concussive_smash": {
        "name": "Pneumatic Slag Slam",
        "label": "🔨 Slag Slam",
        "tag": "[TITUS SMASH]",
        "tactical_effect": "Brings slag-hammer down with 2d12+5 Bludgeoning DMG; destroys 40 points of Boss Break Gauge.",
        "desc": "Heavy bludgeoning stagger."
      }
    },
    "dual_tech_id": "foundry_forge_smash"
  },
  "Nyssa": {
    "id": "companion_nyssa",
    "name": "Nyssa Thorn-Weft",
    "class": "Primal Shapeshifter / Beast-Warden",
    "title": "Primal Shapeshifter / Beast-Warden",
    "role": "Fluid Form-Shifting (Sabre-Cat Pounce DPS / Cave-Bear Fortitude)",
    "level": 3,
    "hp": 38,
    "max_hp": 38,
    "xp": 450,
    "next_level_xp": 900,
    "stance": "cat_pounce",
    "morale": "Steady",
    "affinity": 25,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Delaware Water Gap Wolf Den (X:32, Y:30)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "skill_check": "Survival 120 or Animal Empathy",
      "description": "Tame or cure the infected Alpha Dire-Wolf pack leader alongside Nyssa."
    },
    "bio": "A beast-kin felis shapeshifter who flows between a deadly stealth sabre-cat and an armored, raging cave-bear.",
    "loadout": {
      "main_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing + Bleed)",
      "off_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing)",
      "armor": "Living Bramble Armor (DR 2, Thorns)",
      "chest": "Living Bramble Armor (DR 2, Thorns)"
    },
    "equipped": {
      "main_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing + Bleed)",
      "off_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing)",
      "armor": "Living Bramble Armor (DR 2, Thorns)",
      "chest": "Living Bramble Armor (DR 2, Thorns)"
    },
    "skills": {
      "Primal Shapeshifting": {
        "mastery": 270,
        "tier": "Adept",
        "description": "Metamorphic biology into apex predators.",
        "milestones_unlocked": [
          "Feline Quickstep",
          "Ursine Thickhide",
          "Predator Instinct"
        ]
      },
      "Bramble Entanglement": {
        "mastery": 200,
        "tier": "Journeyman",
        "description": "Summoning thorny vines from soil.",
        "milestones_unlocked": [
          "Grasping Roots"
        ]
      },
      "Predator Tracking": {
        "mastery": 220,
        "tier": "Journeyman",
        "description": "Scenting prey and tracking blood trails.",
        "milestones_unlocked": [
          "Blood Scent"
        ]
      }
    },
    "abilities": [
      "Sabre-Cat Pounce (3d8 Slashing + Knocks Prone + Bleed)",
      "Cave-Bear Roar (Gains +25 Temporary HP + Taunts)",
      "Thorn Bramble Spikes (Entangles foes, 1d8 Piercing/turn)"
    ],
    "stances": {
      "cat_pounce": {
        "name": "Sabre-Cat Pounce",
        "label": "🐆 Sabre-Cat Pounce",
        "tag": "[NYSSA POUNCE]",
        "tactical_effect": "Pounces on vulnerable targets dealing 2d8+5 Slashing DMG and inflicting severe Bleed (8 DMG/turn).",
        "desc": "High critical burst mode."
      },
      "bear_form": {
        "name": "Bear-Form Fortitude",
        "label": "🐻 Bear Fortitude",
        "tag": "[NYSSA BEAR]",
        "tactical_effect": "Shifts into giant cave-bear; gains +20 Temp HP, DR 3, and forces hostiles to focus on her.",
        "desc": "Tanking form."
      },
      "bramble_trap": {
        "name": "Bramble Entangle",
        "label": "🌿 Bramble Entangle",
        "tag": "[NYSSA ROOTS]",
        "tactical_effect": "Summons living briars that root up to 2 enemies in place for 1 turn, preventing movement.",
        "desc": "Area crowd control."
      }
    },
    "dual_tech_id": "pack_hunt_ambush"
  },
  "Malakor": {
    "id": "companion_malakor",
    "name": "Malakor",
    "class": "Eldritch Hexblade / Void-Pact Siphon",
    "title": "Eldritch Hexblade / Void-Pact Siphon",
    "role": "Anti-Mage Execution, Resource Siphon & Shadow Teleportation",
    "level": 4,
    "hp": 42,
    "max_hp": 42,
    "xp": 800,
    "next_level_xp": 1200,
    "stance": "void_edge",
    "morale": "Steady",
    "affinity": 20,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Decommissioned Limestone Caverns (Pohatcong Sinkholes, X:42, Y:56)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "item": "Corrupted Void-Shard",
      "description": "Deliver a Corrupted Void-Shard from an Elite Abyssal mob to seal a blood-oath binding pact."
    },
    "bio": "A void-touched tiefling whose Greatsword 'Scourge-Drinker' drains enemy mana, active spell slots, and kinetic shielding.",
    "loadout": {
      "main_hand": "Void-Etched Greatsword (2d6+4 Slashing + Void Siphon)",
      "off_hand": "Null-Glyph Buckler (+2 AC, Spell Absorber)",
      "armor": "Shadow-Steel Hauberk (DR 2, Magic Resist)",
      "chest": "Shadow-Steel Hauberk (DR 2, Magic Resist)"
    },
    "equipped": {
      "main_hand": "Void-Etched Greatsword (2d6+4 Slashing + Void Siphon)",
      "off_hand": "Null-Glyph Buckler (+2 AC, Spell Absorber)",
      "armor": "Shadow-Steel Hauberk (DR 2, Magic Resist)",
      "chest": "Shadow-Steel Hauberk (DR 2, Magic Resist)"
    },
    "skills": {
      "Hexblade Greatsword": {
        "mastery": 280,
        "tier": "Adept",
        "description": "Heavy two-handed strikes imbued with void.",
        "milestones_unlocked": [
          "Void Cleave",
          "Severing Arc",
          "Soul Drinker"
        ]
      },
      "Eldritch Invocation": {
        "mastery": 240,
        "tier": "Journeyman",
        "description": "Channelling dark patronage from beyond.",
        "milestones_unlocked": [
          "Armor of Agathys"
        ]
      },
      "Anti-Magic Severing": {
        "mastery": 210,
        "tier": "Journeyman",
        "description": "Dispelling magical barriers and shields.",
        "milestones_unlocked": [
          "Nullify Matrix"
        ]
      }
    },
    "abilities": [
      "Void-Blade Smite (3d10 Void DMG + drains 20% enemy resource)",
      "Spell-Eater Ward (Absorbs 1 spell and converts to 15 HP)",
      "Shadow Step (Teleports 30ft behind target)"
    ],
    "stances": {
      "void_edge": {
        "name": "Void-Edge Siphon",
        "label": "🌌 Void-Edge Siphon",
        "tag": "[MALAKOR VOID]",
        "tactical_effect": "Cleaves through target for 2d6+5 Void DMG, draining enemy combat resources and buffing Banki.",
        "desc": "Anti-resource damage."
      },
      "spell_eater": {
        "name": "Spell-Eater Ward",
        "label": "🔮 Spell-Eater Ward",
        "tag": "[MALAKOR WARD]",
        "tactical_effect": "Raises void buckler; absorbs all magical projectile damage directed at the party this turn.",
        "desc": "Magic damage negation."
      },
      "shadow_rend": {
        "name": "Abyssal Step Execution",
        "label": "👤 Abyssal Step",
        "tag": "[MALAKOR SHADOW]",
        "tactical_effect": "Blinks through reality into the backline, executing an unblockable strike dealing 3d8+4 Critical DMG.",
        "desc": "Backline assassin strike."
      }
    },
    "dual_tech_id": "void_abyss_cleave"
  },
  "Thorne": {
    "id": "companion_thorne",
    "name": "Dr. Alistair Thorne",
    "class": "Alchemical Saboteur / Toxicologist",
    "title": "Alchemical Saboteur / Toxicologist",
    "role": "Armor-Stripping Vitriol, Toxic Cloud Control & Adrenaline Injections",
    "level": 3,
    "hp": 30,
    "max_hp": 30,
    "xp": 450,
    "next_level_xp": 900,
    "stance": "vitriol_salvo",
    "morale": "Maniacal",
    "affinity": 25,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Abandoned Chemical Works (Phillipsburg Flats, X:26, Y:60)",
    "recruitment_requirements": {
      "min_level": 3,
      "col_cost": 0,
      "quest": "chemical_leak",
      "description": "Neutralize the chemical vat leak (Crafting/Perception DC 13) and recover his stolen journals."
    },
    "bio": "A manic chemical engineer and Elora's eccentric uncle. Dissolves monster armor with hyper-vitriol and juices allies with adrenaline.",
    "loadout": {
      "main_hand": "Pneumatic Acid-Siphon Cannon (1d8+3 Acid + Armor Melt)",
      "off_hand": "Bandolier of Corrosive Flasks (Alchemical Focus)",
      "armor": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)",
      "chest": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)"
    },
    "equipped": {
      "main_hand": "Pneumatic Acid-Siphon Cannon (1d8+3 Acid + Armor Melt)",
      "off_hand": "Bandolier of Corrosive Flasks (Alchemical Focus)",
      "armor": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)",
      "chest": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)"
    },
    "skills": {
      "Volatile Chemistry": {
        "mastery": 270,
        "tier": "Adept",
        "description": "Mixing unstable exothermic acids and gases.",
        "milestones_unlocked": [
          "Corrosive Brew",
          "Nitro Flask",
          "Thermite Compound"
        ]
      },
      "Toxicology": {
        "mastery": 230,
        "tier": "Journeyman",
        "description": "Formulating paralytic neurotoxins.",
        "milestones_unlocked": [
          "Neuro-Darts"
        ]
      },
      "Combat Bio-Stimulants": {
        "mastery": 210,
        "tier": "Journeyman",
        "description": "Adrenaline and stamina injections.",
        "milestones_unlocked": [
          "Adrenal Rush"
        ]
      }
    },
    "abilities": [
      "Hyper-Vitriol Acid Bomb (Melt target AC by -4 permanently)",
      "Toxic Cloudkill Flask (15ft choking gas, 2d6 Poison/turn)",
      "Adrenaline Bio-Stim (+4 STR/DEX to Banki for 2 turns)"
    ],
    "stances": {
      "vitriol_salvo": {
        "name": "Corrosive Acid Salvo",
        "label": "🧪 Vitriol Salvo",
        "tag": "[THORNE ACID]",
        "tactical_effect": "Hurls bubbling acid flasks dealing 2d6+3 Acid DMG and permanently degrading target AC by -2.",
        "desc": "Armor-shredding debuff."
      },
      "toxic_smokescreen": {
        "name": "Cloudkill Smokescreen",
        "label": "🌫️ Toxic Cloudkill",
        "tag": "[THORNE SMOKE]",
        "tactical_effect": "Detonates thick chemical smoke; blinds hostiles (-3 to hit) while party gains full concealment.",
        "desc": "Obscuring defense."
      },
      "adrenal_injection": {
        "name": "Adrenaline Stim Injection",
        "label": "💉 Adrenal Stim",
        "tag": "[THORNE STIM]",
        "tactical_effect": "Injects Banki with hyper-adrenaline; Banki deals +1d10 bonus physical damage on all attacks this turn.",
        "desc": "Allied damage booster."
      }
    },
    "dual_tech_id": "corrosive_shatter_bomb"
  },
  "Teresa": {
    "id": "companion_teresa",
    "name": "Sister Teresa",
    "class": "Inquisitor / Witch-Hunter",
    "title": "Inquisitor / Witch-Hunter",
    "role": "Silver Ranged Execution, Weakness Exposure & Anti-Aberration Stake",
    "level": 3,
    "hp": 36,
    "max_hp": 36,
    "xp": 450,
    "next_level_xp": 900,
    "stance": "silver_snipe",
    "morale": "Resolute",
    "affinity": 30,
    "affinity_tier": "Acquaintance",
    "recruited": false,
    "active": false,
    "recruitment_location": "Old Moravian Mission Ruins (Hope Township, X:50, Y:30)",
    "recruitment_requirements": {
      "min_level": 2,
      "col_cost": 0,
      "dialogue": "truth_glyph",
      "description": "Pass her truth-testing glyph (WIS DC 13) or assist in exposing a cultist spy in Hope Township."
    },
    "bio": "A former criminal prosecutor turned Silver Flame Inquisitor. Uses silver truth-runes and heavy stake crossbows to execute heretics.",
    "loadout": {
      "main_hand": "Silver-Chambered Crossbow (1d10+3 Piercing + Silver)",
      "off_hand": "Blessed Consecrated Estoc (1d8+3 Piercing)",
      "armor": "Inquisitor's Leather Duster (+2 WIS, DR 1)",
      "chest": "Inquisitor's Leather Duster (+2 WIS, DR 1)"
    },
    "equipped": {
      "main_hand": "Silver-Chambered Crossbow (1d10+3 Piercing + Silver)",
      "off_hand": "Blessed Consecrated Estoc (1d8+3 Piercing)",
      "armor": "Inquisitor's Leather Duster (+2 WIS, DR 1)",
      "chest": "Inquisitor's Leather Duster (+2 WIS, DR 1)"
    },
    "skills": {
      "Inquisitorial Crossbow": {
        "mastery": 260,
        "tier": "Adept",
        "description": "Driving heavy consecrated silver stakes.",
        "milestones_unlocked": [
          "Silver Stake",
          "Pinning Bolt",
          "Judgment Volley"
        ]
      },
      "Discernment of Truth": {
        "mastery": 240,
        "tier": "Journeyman",
        "description": "Seeing through illusions and shapeshifters.",
        "milestones_unlocked": [
          "True Sight"
        ]
      },
      "Cestus & Estoc Fencing": {
        "mastery": 190,
        "tier": "Journeyman",
        "description": "Close-range execution maneuvers.",
        "milestones_unlocked": [
          "Parry & Riposte"
        ]
      }
    },
    "abilities": [
      "Silver Stake Execution (3d10 Piercing vs Aberration/Undead)",
      "Witch-Hunter's Brand (Target cannot turn invisible or heal for 2 turns)",
      "Solemn Verdict (+3 Critical threat range to party)"
    ],
    "stances": {
      "silver_snipe": {
        "name": "Silver-Bolt Snipe",
        "label": "🏹 Silver Snipe",
        "tag": "[TERESA SNIPE]",
        "tactical_effect": "Fires a silver-tipped stake dealing 2d8+4 Piercing DMG (+2d8 vs Aberrations/Undead) and pinning target.",
        "desc": "Anti-fiend/undead sniper."
      },
      "truth_judgment": {
        "name": "True-Sight Judgment",
        "label": "⚖️ True-Sight Judgment",
        "tag": "[TERESA JUDGMENT]",
        "tactical_effect": "Paints target with silver flame; exposes physical weaknesses, increasing Banki's crit chance to 18-20.",
        "desc": "Critical threat amplifier."
      },
      "witch_hunter_brand": {
        "name": "Witch-Hunter's Brand",
        "label": "🔥 Witch Brand",
        "tag": "[TERESA BRAND]",
        "tactical_effect": "Brands target with holy fire; target loses 8 HP/turn and cannot regenerate health or phase shift.",
        "desc": "Anti-healing brand."
      }
    },
    "dual_tech_id": "inquisition_execution"
  }
}
```

## `REGIONAL_FACTIONS` (3 entries)
```json
{
  "vanguard_coalition": {
    "id": "vanguard_coalition",
    "name": "The Vanguard Coalition",
    "leader": "Commander Kaelen Vance",
    "headquarters": "Washington Fortress Bastion",
    "icon": "⚔️",
    "description": "Dedicated frontline raid coalition committed to breaking the regional labyrinth bosses and ascending the regional spires.",
    "perks": {
      "25": "+10% bonus damage against Dungeon and Sector Bosses; Coalition Quartermaster access.",
      "50": "+15% Maximum HP and military requisition grade armor."
    }
  },
  "iron_syndicate": {
    "id": "iron_syndicate",
    "name": "The Iron Syndicate",
    "leader": "Guildmaster Silas Bron",
    "headquarters": "Oxford Forge & Smelting Vaults",
    "icon": "⚒️",
    "description": "Mercantile crafting cartel that monopolizes regional raw materials, forge leylines, and trade routes across Warren County.",
    "perks": {
      "25": "15% wholesale discount on all store purchases and repair services.",
      "50": "Masterwork forging blueprints and priority auction trade access."
    }
  },
  "blood_shroud": {
    "id": "blood_shroud",
    "name": "The Blood Shroud",
    "leader": "The Pale Whisper",
    "headquarters": "Scotts Mountain Glitch-Vaults",
    "icon": "🩸",
    "description": "Secretive outlaw guild operating in dark sectors (Laughing Coffin analog); orchestrates ambushes and black market trade.",
    "perks": {
      "25": "Immunity to wilderness outlaw ambushes; access to illicit poison blueprints.",
      "50": "Black-market teleporters and outlaw contract bounties."
    }
  }
}
```

## `SECTOR_BOSSES` (1 entries)
```json
{
  "gilded_overlord": {
    "id": "gilded_overlord",
    "name": "The Gilded Spire Overlord",
    "title": "Sector 1 Apex Construct (Aether-Titan)",
    "max_hp": 300,
    "current_hp": 300,
    "phase": 1,
    "max_break": 100,
    "current_break": 100,
    "is_staggered": false,
    "stagger_rounds_remaining": 0,
    "active_telegraph": null,
    "phases": {
      "1": {
        "name": "Phase 1: Runic Bulwark",
        "hp_range": "100% – 60% HP (300 – 180 HP)",
        "ac": 18,
        "dr": 3,
        "description": "Heavy gilded aegis active. Gilded armor plating deflects glancing attacks. Wields a colossal twin-headed maul with sweeping 180-degree cleaves.",
        "attacks": [
          {
            "name": "Gilded Maul Cleave",
            "atk": 8,
            "dmg": "2d10+4 Physical",
            "type": "single"
          },
          {
            "name": "Bulwark Shield Bash",
            "atk": 7,
            "dmg": "1d12+4 Force",
            "type": "stagger"
          }
        ],
        "telegraph_pool": [
          {
            "name": "Colossal Seismic Cleave",
            "dc": 15,
            "stat": "DEX",
            "damage": "3d10+6 Force",
            "warning": "Raises titanic gilded maul high overhead, channeling kinetic leyline pressure in a sweeping 180° frontal arc!"
          }
        ]
      },
      "2": {
        "name": "Phase 2: Aetheric Core Overload",
        "hp_range": "60% – 20% HP (180 – 60 HP)",
        "ac": 15,
        "dr": 1,
        "description": "Outer armor shatters with an explosive shockwave! The glowing blue aetheric core exposes itself, radiating lightning arcs and summoning repair-drone conduits.",
        "attacks": [
          {
            "name": "Arcane Lightning Discharge",
            "atk": 9,
            "dmg": "3d8+5 Lightning",
            "type": "ranged"
          },
          {
            "name": "Aether-Infused Greatsword Swipe",
            "atk": 8,
            "dmg": "2d8+5 Slashing",
            "type": "single"
          }
        ],
        "telegraph_pool": [
          {
            "name": "Aetheric Overload Cascade",
            "dc": 16,
            "stat": "DEX",
            "damage": "4d8+8 Lightning",
            "warning": "Core pulses with blinding cyan voltage! Ground floor grids begin crackling with lethal electrical discharge!"
          }
        ]
      },
      "3": {
        "name": "Phase 3: Desperation Spatial Tear",
        "hp_range": "20% – 0% HP (60 – 0 HP)",
        "ac": 13,
        "dr": 0,
        "description": "Enraged and disintegrating! Attack speed doubles, its collision mesh fractures into glitching red polygons, and spatial vortexes tear through the arena pulling combatants inward.",
        "attacks": [
          {
            "name": "Frenzied Glitch Slash",
            "atk": 11,
            "dmg": "3d10+6 Chaos",
            "type": "dual"
          },
          {
            "name": "Spatial Rift Pulse",
            "atk": 10,
            "dmg": "2d12+6 Force",
            "type": "gravity"
          }
        ],
        "telegraph_pool": [
          {
            "name": "Cataclysmic Spatial Collapse",
            "dc": 17,
            "stat": "STR",
            "damage": "5d10+10 Chaos",
            "warning": "Unleashes an uncontrollable gravitational singularity that fractures the arena ceiling downward!"
          }
        ]
      }
    },
    "rewards": {
      "xp": 2500,
      "col": 5000,
      "items": [
        {
          "name": "Overlord's Gilded Core",
          "rarity": "Legendary",
          "grade": 5,
          "durability": 200,
          "max_durability": 200,
          "qty": 1,
          "desc": "The pulsating apex heart of the Floor 1 Sector Boss. Used at the Deepforged Master-Anvil to forge Grade 6 Mythic armaments."
        },
        {
          "name": "Gilded Spire Great-Axe",
          "rarity": "Legendary",
          "grade": 5,
          "durability": 200,
          "max_durability": 200,
          "qty": 1,
          "desc": "A colossal golden-crested battleaxe forged from aether-infused adamant. Grants +4 to Attack rolls and innate Shockwave Cleave."
        }
      ],
      "unlocked_zone": "Sector 2: The Musconetcong & Delaware Water Gap Expanse",
      "title": "Sector 1 Conqueror"
    }
  }
}
```

## `SKILL_TIER_THRESHOLDS` (7 entries)
```json
[
  [
    1000,
    "Transcendence",
    "👑 [Transcendence]"
  ],
  [
    750,
    "Grandmaster",
    "⚜️ [Grandmaster]"
  ],
  [
    500,
    "Master",
    "🌟 [Master]"
  ],
  [
    250,
    "Adept",
    "🔷 [Adept]"
  ],
  [
    100,
    "Journeyman",
    "🔶 [Journeyman]"
  ],
  [
    50,
    "Apprentice",
    "🟢 [Apprentice]"
  ],
  [
    1,
    "Novice",
    "⚪ [Novice]"
  ]
]
```

## `SLOT_ALIASES` (7 entries)
```json
{
  "head": "neural",
  "eyes": "ocular",
  "torso": "dermal",
  "chest": "dermal",
  "left_arm": "arm_left",
  "right_arm": "arm_right",
  "legs": "leg_left"
}
```

## `VAULT_TIERS` (3 entries)
```json
{
  "1": {
    "capacity_lbs": 1000,
    "slots": 50,
    "upgrade_cost": 0
  },
  "2": {
    "capacity_lbs": 2500,
    "slots": 100,
    "upgrade_cost": 2000
  },
  "3": {
    "capacity_lbs": 10000,
    "slots": 250,
    "upgrade_cost": 5000
  }
}
```

## `WARREN_COUNTY_BOUNTIES` (3 entries)
```json
[
  {
    "id": "bounty_pohatcong_construct",
    "title": "Slay the Rogue Timber-Goliath on Pohatcong Mountain",
    "desc": "A 14-foot corrupted logging construct has gone berserk along the Pohatcong ridge trails, smashing supply wagons.",
    "target": "Rogue Timber-Goliath (Level 3 Field Construct)",
    "location": "Pohatcong Mountain Ridge",
    "reward": "1,200 Col, 450 XP, Grade 2 Titanium Plating x2"
  },
  {
    "id": "bounty_oxford_cables",
    "title": "Recover Stolen Aether-Cables from Oxford Wastes",
    "desc": "Grafted scavengers have severed the municipal power conduits leading into Oxford. Eliminate the marauder squad and secure the cables.",
    "target": "Grafted Scavenger Pack (4x Scrappers)",
    "location": "Oxford Mining District",
    "reward": "850 Col, 350 XP, High-Voltage Capacitor x1"
  },
  {
    "id": "bounty_roaring_rock_stalker",
    "title": "Cull the Glitched Razor-Hound Pack in Roaring Rock",
    "desc": "A feral pack of cyber-mutated canines has established a den near the Roaring Rock reservoir, ambushing couriers.",
    "target": "Alpha Razor-Hound + 3 Packmates",
    "location": "Roaring Rock Park",
    "reward": "1,500 Col, 500 XP, Chitin Fur Mantle x1"
  }
]
```

## `WASHINGTON_FACILITIES` (3 entries)
```json
{
  "iron_spoke_taphouse": {
    "id": "iron_spoke_taphouse",
    "name": "The Iron Spoke Taphouse",
    "icon": "🍺",
    "proprietor": "Torvald Iron-Vein (Deepforged Bouncer & Barkeep)",
    "description": "A fortified roadside tavern built into the stone foundations of an abandoned rail depot. Runic heat-pipes warm the heavy timber tables where mercenaries and scavengers trade rumors.",
    "services": [
      {
        "id": "stew_and_rest",
        "name": "Hearty Marrow Stew & Roasted Grain Draught",
        "cost_col": 150,
        "effect": "Restores 50 HP to Banki, cleanses fatigue, restores companion morale to 'Confident' (+10% accuracy), and grants [Well-Fed] buff."
      },
      {
        "id": "bounty_board",
        "name": "Sector 1 Regional Bounty Board",
        "cost_col": 0,
        "effect": "Inspect available local contracts and barony bounties for Warren County."
      }
    ]
  },
  "arcane_med_bay": {
    "id": "arcane_med_bay",
    "name": "The Arcane Med-Bay & Bio-Clinic",
    "icon": "🏥",
    "proprietor": "Dr. Varek Thorne (Displaced Cyber-Physician)",
    "description": "A sterile, pressurized field clinic humming with life-support conduits and diagnostic holograms. Specializes in emergency flesh repair and bio-mechanical graft integration.",
    "services": [
      {
        "id": "bio_purification",
        "name": "Full Bio-Purification & Flesh Trauma Suture",
        "cost_col": 250,
        "effect": "Completely restores HP to Max, cleanses Bleed, Poison, and Overload conditions, and stabilizes cyber-strain."
      },
      {
        "id": "cyber_surgery",
        "name": "Deepforger Artificer Surgery (Graft Installation)",
        "cost_col": 0,
        "effect": "Install or extract Golem-Grafts using clinical tools."
      }
    ]
  },
  "meiji_scavenger_dump": {
    "id": "meiji_scavenger_dump",
    "name": "The Meiji Scavenger Dump & Material Exchange",
    "icon": "🛒",
    "proprietor": "Kibs 'Nine-Fingers' (Goblinoid Scrap Broker)",
    "description": "A sprawling junkyard warehouse filled with salvaged aether-tech, chassis parts, and raw crafting commodities gathered from Highway 31 and the Oxford line.",
    "inventory": [
      {
        "name": "Serrated Tripwire Coils",
        "cost_col": 75,
        "qty": 5,
        "desc": "Pre-coiled high-tensile monofilament wire.",
        "type": "crafting"
      },
      {
        "name": "Heavy Highway Snares",
        "cost_col": 120,
        "qty": 4,
        "desc": "High-durability pneumatic limb-clamp snares.",
        "type": "crafting"
      },
      {
        "name": "Anchors and Tension Pins",
        "cost_col": 50,
        "qty": 8,
        "desc": "Steel ground spikes with locking spring-pins.",
        "type": "crafting"
      },
      {
        "name": "Corroded Micro-Capacitor",
        "cost_col": 150,
        "qty": 3,
        "desc": "High-discharge pulse capacitor salvaged from drones.",
        "type": "crafting"
      },
      {
        "name": "Frayed Copper Wiring",
        "cost_col": 40,
        "qty": 10,
        "desc": "Standard conductive copper wiring.",
        "type": "crafting"
      },
      {
        "name": "Rendered Chimera Marrow",
        "cost_col": 200,
        "qty": 2,
        "desc": "Potent scented tallow that lures predatory beasts.",
        "type": "bait"
      }
    ]
  }
}
```
