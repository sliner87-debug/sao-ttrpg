# G75VW Character Creation Compendium (5-Stage Initialization Protocol)

Canonical character generation data from the Asus ROG G75VW primary engine (`backend/character_generator.py`).

## `CLASS_PATHS` (12 entries)

### Warrior (Frontline Anchor) (`warrior`)
```json
{
  "title": "Warrior (Frontline Anchor)",
  "description": "Specialized in absorbing enemy aggro, breaking shields, controlling battlefield positioning, and anchoring frontlines.",
  "starting_feats": [
    "Shield Wall Stance",
    "Taunting War-Cry"
  ],
  "combat_resource": {
    "name": "Poise & Threat",
    "max": 100,
    "current": 0,
    "type": "poise"
  },
  "base_hp": 120,
  "hp_per_lvl": 35,
  "native_armor": [
    "Heavy",
    "Medium"
  ],
  "favored_skills": [
    "Trench Hammers",
    "One-Handed Axes",
    "Field Smithing"
  ]
}
```

### Mage (Aether-Weaver) (`mage`)
```json
{
  "title": "Mage (Aether-Weaver)",
  "description": "Channels raw atmospheric mana into concentrated force projectiles, protective wards, and catastrophic elemental singularities.",
  "starting_feats": [
    "Arcane Ward",
    "Aetheric Dart"
  ],
  "combat_resource": {
    "name": "Aetheric Flux",
    "max": 50,
    "current": 50,
    "type": "flux"
  },
  "base_hp": 80,
  "hp_per_lvl": 20,
  "native_armor": [
    "Cloth",
    "Light"
  ],
  "favored_skills": [
    "Aether-Weaving",
    "Arcane Triage",
    "Provisions & Alchemy"
  ]
}
```

### Cleric (Spire Templar) (`cleric`)
```json
{
  "title": "Cleric (Spire Templar)",
  "description": "Battlefield medic and sanctified inquisitor wielding protective auras, emergency trauma restoration, and crushing mace strikes.",
  "starting_feats": [
    "Sanctified Ward",
    "Purifying Grace"
  ],
  "combat_resource": {
    "name": "Devotion & Grace",
    "max": 100,
    "current": 50,
    "type": "devotion"
  },
  "base_hp": 105,
  "hp_per_lvl": 28,
  "native_armor": [
    "Medium",
    "Heavy"
  ],
  "favored_skills": [
    "Arcane Triage",
    "Trench Hammers",
    "Provisions & Alchemy"
  ]
}
```

### Thief (Shadow Infiltrator) (`thief`)
```json
{
  "title": "Thief (Shadow Infiltrator)",
  "description": "Acrobatic guerrilla rogue executing serrated backstabs, smoke-screen evasions, and fluid momentum chaining.",
  "starting_feats": [
    "Shadow Footwork",
    "Serrated Backstab"
  ],
  "combat_resource": {
    "name": "Momentum Dice",
    "max": 5,
    "current": 1,
    "type": "momentum"
  },
  "base_hp": 90,
  "hp_per_lvl": 24,
  "native_armor": [
    "Light"
  ],
  "favored_skills": [
    "One-Handed Axes",
    "Tactical Reflexes",
    "Field Trapping"
  ]
}
```

### Ranger (Wilderness Marksman) (`ranger`)
```json
{
  "title": "Ranger (Wilderness Marksman)",
  "description": "Scout and sniper dominating extreme range, deploying lethal wire snares, and exploiting elevated vantage points.",
  "starting_feats": [
    "Hunter's Mark",
    "Deadeye Aim"
  ],
  "combat_resource": {
    "name": "Focus & Vantage",
    "max": 5,
    "current": 3,
    "type": "focus"
  },
  "base_hp": 95,
  "hp_per_lvl": 28,
  "native_armor": [
    "Light",
    "Medium"
  ],
  "favored_skills": [
    "Field Trapping",
    "Cartography",
    "Tactical Reflexes"
  ]
}
```

### Engineer / Artificer (`engineer`)
```json
{
  "title": "Engineer / Artificer",
  "description": "Combat mechanist deploying automated sentry turrets, explosive traps, and venting superheated overclock steam.",
  "starting_feats": [
    "Deploy Sentry Turret",
    "Vent Overclock"
  ],
  "combat_resource": {
    "name": "Heat & Overclock",
    "max": 100,
    "current": 0,
    "type": "heat"
  },
  "base_hp": 100,
  "hp_per_lvl": 28,
  "native_armor": [
    "Medium",
    "Heavy"
  ],
  "favored_skills": [
    "Field Smithing",
    "Golem-Graft Rigging",
    "Magi-Tech Hacking"
  ]
}
```

### Psion / Phrenic (`psion`)
```json
{
  "title": "Psion / Phrenic",
  "description": "Awakened mentalist projecting mind-shattering kinetic repulsion and psychic lances, walking the edge of cognitive strain.",
  "starting_feats": [
    "Kinetic Repulsion Barrier",
    "Mind Spike"
  ],
  "combat_resource": {
    "name": "Psi-Strain",
    "max": 100,
    "current": 0,
    "type": "strain"
  },
  "base_hp": 85,
  "hp_per_lvl": 24,
  "native_armor": [
    "Cloth",
    "Light"
  ],
  "favored_skills": [
    "Aether-Circuit Query",
    "Tactical Reflexes"
  ]
}
```

### Pathless (Freeform Anomaly) (`pathless`)
```json
{
  "title": "Pathless (Freeform Anomaly)",
  "description": "Refuses to be bound by system constraints. Free to combine any weapons, spells, and doctrines across every level.",
  "starting_feats": [
    "Adaptive Weapon Mastery",
    "Unshackled Potential"
  ],
  "combat_resource": {
    "name": "Anomaly Resonance",
    "max": 100,
    "current": 0,
    "type": "resonance"
  },
  "base_hp": 100,
  "hp_per_lvl": 25,
  "native_armor": [
    "Adaptive"
  ],
  "favored_skills": [
    "Universal Versatility"
  ]
}
```

### Vanguard (Heavy Frontliner) (`vanguard`)
```json
{
  "title": "Vanguard (Heavy Frontliner)",
  "description": "Specialized in absorbing enemy aggro, breaking shields, controlling battlefield positioning, and anchoring frontlines.",
  "starting_feats": [
    "Shield Wall Stance",
    "Taunting War-Cry"
  ],
  "combat_resource": {
    "name": "Poise & Threat",
    "max": 100,
    "current": 0,
    "type": "poise"
  },
  "base_hp": 100,
  "hp_per_lvl": 35,
  "native_armor": [
    "Heavy",
    "Medium"
  ],
  "favored_skills": [
    "Trench Hammers",
    "One-Handed Axes",
    "Field Smithing"
  ]
}
```

### Magi-Tech Saboteur (`magi_saboteur`)
```json
{
  "title": "Magi-Tech Saboteur",
  "description": "Combat mechanist deploying automated sentry turrets, explosive traps, and venting superheated overclock steam.",
  "starting_feats": [
    "Deploy Sentry Turret",
    "Vent Overclock"
  ],
  "combat_resource": {
    "name": "Heat & Overclock",
    "max": 100,
    "current": 0,
    "type": "heat"
  },
  "base_hp": 100,
  "hp_per_lvl": 28,
  "native_armor": [
    "Medium",
    "Heavy"
  ],
  "favored_skills": [
    "Field Smithing",
    "Golem-Graft Rigging",
    "Magi-Tech Hacking"
  ]
}
```

### Aether-Slinger (`aether_slinger`)
```json
{
  "title": "Aether-Slinger",
  "description": "Channels raw atmospheric mana into concentrated force projectiles, protective wards, and catastrophic elemental singularities.",
  "starting_feats": [
    "Arcane Ward",
    "Aetheric Dart"
  ],
  "combat_resource": {
    "name": "Aetheric Flux",
    "max": 50,
    "current": 50,
    "type": "flux"
  },
  "base_hp": 80,
  "hp_per_lvl": 20,
  "native_armor": [
    "Cloth",
    "Light"
  ],
  "favored_skills": [
    "Aether-Weaving",
    "Arcane Triage",
    "Provisions & Alchemy"
  ]
}
```

### Wilderness Ranger (`wilderness_ranger`)
```json
{
  "title": "Wilderness Ranger",
  "description": "Scout and sniper dominating extreme range, deploying lethal wire snares, and exploiting elevated vantage points.",
  "starting_feats": [
    "Hunter's Mark",
    "Deadeye Aim"
  ],
  "combat_resource": {
    "name": "Focus & Vantage",
    "max": 5,
    "current": 3,
    "type": "focus"
  },
  "base_hp": 95,
  "hp_per_lvl": 28,
  "native_armor": [
    "Light",
    "Medium"
  ],
  "favored_skills": [
    "Field Trapping",
    "Cartography",
    "Tactical Reflexes"
  ]
}
```

## `CLASS_WEAPONS` (12 entries)

### warrior (`warrior`)
```json
{
  "main_hand": "Heavy Scavenged Mace",
  "off_hand": "Scrap-Plate Shield",
  "desc": "A dense rebar-reinforced iron mace paired with a riveted industrial scrap shield."
}
```

### mage (`mage`)
```json
{
  "main_hand": "Aetheric Focusing Wand",
  "off_hand": "None",
  "desc": "A conductive brass-and-quartz resonator wand designed to project raw kinetic spells."
}
```

### cleric (`cleric`)
```json
{
  "main_hand": "Sanctified Flail",
  "off_hand": "Scrap-Plate Shield",
  "desc": "A heavy iron flail engraved with cleansing wards, paired with a reinforced scrap shield."
}
```

### thief (`thief`)
```json
{
  "main_hand": "Concealed Trench Daggers",
  "off_hand": "Tanto Combat Knife",
  "desc": "Dual razor-sharp carbon trench blades tailored for high-speed puncture strikes."
}
```

### ranger (`ranger`)
```json
{
  "main_hand": "Recurve Hunting Bow",
  "off_hand": "Chipped Wood-Axe",
  "desc": "A composite outdoor hunting bow (with 20 carbon arrows) and a utility wood-axe."
}
```

### engineer (`engineer`)
```json
{
  "main_hand": "Arcane Stun-Pistol",
  "off_hand": "Tanto Combat Knife",
  "desc": "A low-charge shock-pulse sidearm paired with a serrated carbon combat knife."
}
```

### psion (`psion`)
```json
{
  "main_hand": "Kinetic Shock-Staff",
  "off_hand": "None",
  "desc": "A resonant quartz-tipped walking staff that projects and channels telekinetic pulses."
}
```

### pathless (`pathless`)
```json
{
  "main_hand": "Rusted Iron Sword",
  "off_hand": "None",
  "desc": "A jagged, balance-heavy salvage blade scavenged from highway guardrails."
}
```

### vanguard (`vanguard`)
```json
{
  "main_hand": "Heavy Scavenged Mace",
  "off_hand": "Scrap-Plate Shield",
  "desc": "A dense rebar-reinforced iron mace paired with a riveted industrial scrap shield."
}
```

### magi_saboteur (`magi_saboteur`)
```json
{
  "main_hand": "Arcane Stun-Pistol",
  "off_hand": "Tanto Combat Knife",
  "desc": "A low-charge shock-pulse sidearm paired with a serrated carbon combat knife."
}
```

### aether_slinger (`aether_slinger`)
```json
{
  "main_hand": "Aetheric Focusing Wand",
  "off_hand": "None",
  "desc": "A conductive brass-and-quartz resonator wand designed to project raw kinetic spells."
}
```

### wilderness_ranger (`wilderness_ranger`)
```json
{
  "main_hand": "Recurve Hunting Bow",
  "off_hand": "Chipped Wood-Axe",
  "desc": "A composite outdoor hunting bow (with 20 carbon arrows) and a utility wood-axe."
}
```

## `PERSONAL_RELICS` (17 entries)

### Earth Smartphone (99% Battery, No Signal) (`smartphone`)
```json
{
  "name": "Earth Smartphone (99% Battery, No Signal)",
  "rarity": "Unique",
  "category": "Psychological Anchor & Illuminator",
  "durability": 99,
  "max_durability": 100,
  "qty": 1,
  "desc": "A personal flagship smartphone with a spiderweb fracture across the Gorilla Glass screen. Held in an otterbox case, it displays 99% battery, zero cellular bars, and the offline calendar locked onto the final afternoon before the Rift collapse. Its memory stores unread text messages from family ('Where are you? Dinner is cold'), offline music playlists, photos of pets, and an encrypted corporate employee app.",
  "mechanics": "Psychological Anchor: Gazing at family photos during a short rest cures 1 level of cognitive stress / psychological despair and provides advantage on the next saving throw against cosmic madness or horror. Emergency Lumens: Emits a 20ft cone of LED light without open flame. Encrypted Cache: Once per day, querying offline notes grants +2 on an INT check regarding pre-collapse Earth history or engineering. Battery drains 1% per 10 active uses (99 charges total; cannot recharge until MageTech dynamo power is discovered)."
}
```

### Mechanic's Heavy Multi-Tool (`multitool`)
```json
{
  "name": "Mechanic's Heavy Multi-Tool",
  "rarity": "Uncommon",
  "category": "Field Crafting & Rigging",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Hardened carbon-steel pliers, wire-strippers, carbide wire-cutters, serrated wood/bone saw, can opener, and magnetic bit driver with hardened hex heads in a ballistic nylon belt sheath.",
  "mechanics": "Field Maintenance: Permanent +2 bonus on all Field Smithing and mechanical repair checks. Reduces Col repair costs at field anvils by 25%. Improvised Rigging: Deploy or disarm mechanical wire traps and snares without requiring specialized thieves' tools (+5 to disarm trap checks). Pry & Lever: Advantage on STR checks to pry open jammed vehicle doors, locked junction boxes, and rusted scrap grates."
}
```

### Trauma First-Aid Pouch (`first_aid_pouch`)
```json
{
  "name": "Trauma First-Aid Pouch",
  "rarity": "Uncommon",
  "category": "Emergency Medical Triage",
  "durability": 3,
  "max_durability": 3,
  "qty": 1,
  "desc": "A zippered olive-drab ripstop nylon medical pouch stamped with a faded red cross. Contains sterile trauma dressings, celox hemostatic clotting powder, a compact windlass tourniquet, antiseptic burn wash, and nitrile gloves.",
  "mechanics": "Rapid Hemostasis (3 Charges): Bonus action or reaction in combat to immediately cure [Bleeding] or [Hemorrhage] on self or adjacent ally, and restore 1d8+2 HP. Antiseptic Wash: Applying wash to infected wounds grants immediate advantage on target's next saving throw against gangrene, sepsis, or monster biological venom. Depletes 1 durability charge per field triage use."
}
```

### Laminated Regional Topo-Map (`city_map`)
```json
{
  "name": "Laminated Regional Topo-Map",
  "rarity": "Uncommon",
  "category": "Tactical Navigation & Cartography",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Waterproof, double-sided USGS topographical quadrangle map of Warren County, New Jersey (covering Washington Borough, Pohatcong Mountain, Oxford, and Delaware Water Gap) marked with elevation contour lines, river basins, power substations, and grease pencil circles.",
  "mechanics": "Terrain Mastery: Grants +5 starting mastery to Cartography and reveals hidden topographical waypoints, freshwater springs, and high-ground vantage points on the Sector 1 Map overlay. Overland Efficiency: Party overland travel speed across Sector 1 is increased by 15%; immune to becoming naturally lost in non-magical terrain. Tactical Chokepoints: Studying map before combat grants +2 to party initiative."
}
```

### Heirloom Pocket-Watch (`pocket_watch`)
```json
{
  "name": "Heirloom Pocket-Watch",
  "rarity": "Rare",
  "category": "Spatial & Temporal Detection",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Heavy, hand-wound Swiss mechanical pocket-watch in an antiqued solid brass hunter case with Albert chain. Its ruby-jeweled movement ticks with rhythmic precision, immune to electromagnetic pulses or atmospheric aether static.",
  "mechanics": "Glitch-Rift Resonance: The escapement wheel vibrates and chimes loudly within 100ft of an unstable Aetheric Rift, spatial anomaly, or phased entity, preventing surprise attacks. Chrono-Pacing: Displays exact astronomical time and minutes to dawn/dusk, ensuring party is never caught unprepared by night-cycle difficulty escalations. Temporal Focus (1/Long Rest): Gain +2 on all Reaction saving throws for 10 minutes."
}
```

### Noise-Cancelling Headphones (`noise_cancelling_headphones`)
```json
{
  "name": "Noise-Cancelling Headphones",
  "rarity": "Uncommon",
  "category": "Auditory & Sensory Defense",
  "durability": 80,
  "max_durability": 100,
  "qty": 1,
  "desc": "Over-ear cushioned headset with memory foam protein leather ear pads and active hybrid acoustic noise-cancellation circuitry. Scuffed along the headband from rapid evacuation.",
  "mechanics": "Acoustic Dampening: Complete immunity to auditory sensory overload, disorienting supersonic bangs, and monster sonic shrieks (Banshee wails, Harpy calls, Bat-fiend pulses). Psychological Bubble: Wearing while resting blocks out distressing environmental noises (howling wind, dark dungeon growls), ensuring uninterrupted rest. Trade-off: Suffers -2 penalty on passive Perception checks reliant strictly on ambient sound."
}
```

### Military Tritium Lensatic Compass (`tritium_compass`)
```json
{
  "name": "Military Tritium Lensatic Compass",
  "rarity": "Uncommon",
  "category": "Leyline & Night Navigation",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Rugged olive-drab aluminum casing lensatic compass with sighting wire and self-luminous radioactive gaseous tritium vials (green glow) that require no sunlight exposure or battery power to glow in total darkness.",
  "mechanics": "Leyline Divergence Gauge: Magnetic needle responds to both Earth's magnetic poles and ambient mana gradients; wobbles and points toward nearest leyline convergence or magical node. Night Navigation: Green tritium vials permit silent, zero-light compass navigation in pitch-black caves without torches. Dead-Reckoning: Advantage on Survival checks to navigate through blinding blizzards, fogs, and toxic ash clouds."
}
```

### Engraved Brass Zippo Lighter (`zippo_lighter`)
```json
{
  "name": "Engraved Brass Zippo Lighter",
  "rarity": "Uncommon",
  "category": "Pyrotechnic & Gas Detection",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Windproof brushed brass lighter with a satisfying snap-lid click and engraved motto ('Keep Moving Forward'). Smelling faintly of naphtha fuel, its cotton wick and flint spark wheel are battle-tested and reliable.",
  "mechanics": "Instant Ignition: Lights campfires, torches, and stoves instantly in any weather conditions, bypassing wind, rain, and damp wood penalties. Vapor Detection: Holding flame low detects invisible natural gas, methane pockets, and swamp fumes before detonation (flame flares bright blue to warn party). Combat Spark: Free action in combat to ignite oil flasks, molotov cocktails, or alchemical haze pellets."
}
```

### Dog-Eared Sci-Fi Paperback (`dogeared_novel`)
```json
{
  "name": "Dog-Eared Sci-Fi Paperback",
  "rarity": "Uncommon",
  "category": "Psychological Refresh & Ingenuity",
  "durability": 50,
  "max_durability": 50,
  "qty": 1,
  "desc": "A battered mass-market paperback novel (classic speculative fiction) with creased yellow pulp pages, split spine glue, and penciled margins. Smells of vanilla paper lignin and old-world bookstore nostalgia.",
  "mechanics": "Cognitive Refresh: Reading one chapter during a short rest (30 min) clears mental fatigue, granting +10 Focus/Mana and a +1 bonus to INT and WIS saving throws for 2 hours. Imaginative Blueprinting: Exposure to speculative tropes grants +1 bonus to Magi-Tech Hacking and unconventional puzzle solving. Emergency Tinder: In sub-zero emergencies, pages can be torn out to kindle 5 separate emergency fires (+2 to frostbite survival checks)."
}
```

### Climber's Carabiners & Chalk Bag (`chalk_carabiners`)
```json
{
  "name": "Climber's Carabiners & Chalk Bag",
  "rarity": "Uncommon",
  "category": "Athletics & Weapon Grip",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Two heavy-duty, screw-gate asymmetrical D-shaped aluminum climbing carabiners paired with a fleece-lined ripstop waist pouch filled with compressed magnesium carbonate chalk powder.",
  "mechanics": "Grip Assurance: Chalking hands ensures a secure hold, preventing held weapons from being disarmed or dropped due to monster slime, slick blood, or torrential rain. Climbing Anchor: Advantage on Athletics checks to ascend sheer rock faces, elevator shafts, and collapsed highway overpasses. Silent Rappel Rigging: Reduces time required to set up a safe rope descent by 50%."
}
```

### Vintage Polaroid Camera (3 Films Left) (`polaroid_camera`)
```json
{
  "name": "Vintage Polaroid Camera (3 Films Left)",
  "rarity": "Rare",
  "category": "Paranormal Detection & Flash Stun",
  "durability": 3,
  "max_durability": 3,
  "qty": 1,
  "desc": "An analog instant camera from the late 1980s with textured gray housing, rainbow stripe logo, and built-in optical flash bar. Loaded with an authentic vintage film cartridge with exactly 3 remaining chemical exposures.",
  "mechanics": "Specter-Capture Exposure (3 Charges): Snapping a photo and developing the chemical print (60 sec) captures invisible entities, phased stalkers, hidden illusion doors, or arcane sigils invisible to the naked human eye. Flash Stun (Reaction): Pyrotechnic flash can be discharged in combat to inflict [Blinded] on an adjacent attacker for 1 turn (costs 1 film charge). Photos become permanent inventory proof of paranormal encounters."
}
```

### 2000-Lumen Tactical Strobe Flashlight (`tactical_flashlight`)
```json
{
  "name": "2000-Lumen Tactical Strobe Flashlight",
  "rarity": "Uncommon",
  "category": "Illumination & Combat Disorientation",
  "durability": 75,
  "max_durability": 100,
  "qty": 1,
  "desc": "Matte black aircraft-grade anodized aluminum tactical flashlight featuring an ultra-bright Cree XHP LED emitter, strike bezel ring with glass-breaker crenellations, and IP68 waterproof tail-switch.",
  "mechanics": "Target Dazzle / Strobe: 15Hz strobe forces a DC 14 CON save on light-sensitive subterranean beasts or humanoids within 30ft; on failure, target suffers [Dazzled] (-2 to attack rolls for 2 rounds). Deep High-Beam: Illuminates 150ft beam of daylight-equivalent white light, penetrating supernatural gloom. Strike Bezel: Functions as an improvised light bludgeoning weapon in melee dealing 1d4+STR damage (10% stun chance on crit). 75/100 battery remaining."
}
```

### Harmonic Steel Tuning Fork (440Hz) (`guitar_tuning_fork`)
```json
{
  "name": "Harmonic Steel Tuning Fork (440Hz)",
  "rarity": "Uncommon",
  "category": "Acoustic Disruption & Sonar",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Precision-machined, nickel-plated surgical steel acoustic tuning fork calibrated to Concert Pitch A (440 Hz). Produces a pure, crystalline sine wave that hums through bone and air when struck.",
  "mechanics": "Resonant Disruptor: Striking fork and holding near active magical ward, barrier, or rune trap creates destructive acoustic interference, reducing DC to dispel/disarm by 3. False-Wall Sonar: Placing vibrating stem against dungeon walls detects hollow chambers and hidden doors via frequency shifts. Aetheric Calibration: Grants +5% bonus experience gain to all sound-based or sonic magic skills."
}
```

### Vacuum-Insulated Coffee Thermos (`thermos_coffee`)
```json
{
  "name": "Vacuum-Insulated Coffee Thermos",
  "rarity": "Uncommon",
  "category": "Thermal Sustenance & Cold Ward",
  "durability": 3,
  "max_durability": 3,
  "qty": 1,
  "desc": "Heavy double-walled 18/8 kitchen-grade stainless steel thermos bottle with powder-coated hunter green finish. Miraculously, its airtight silicone seal preserved piping-hot dark roast drip coffee from the morning of Integration.",
  "mechanics": "Thermal Stamina Draught (3 Sips Left): Taking a hot sip in the field instantly restores 15 Stamina/Mana, clears 1 level of physical exhaustion, and provides a +2 bonus to Initiative rolls for 1 hour. Hypothermia Ward: Consuming a sip during freezing weather or Glitch Freeze grants complete immunity to Frostbite damage for 4 hours. Indestructible Flask: Empty container can be refilled with boiling liquids or broths without degrading."
}
```

### Black Ceramic Chef's Santoku Knife (`santoku_knife`)
```json
{
  "name": "Black Ceramic Chef's Santoku Knife",
  "rarity": "Uncommon",
  "category": "Non-Metallic Stealth & Butchery",
  "durability": 60,
  "max_durability": 60,
  "qty": 1,
  "desc": "7-inch Japanese-style culinary knife made from ultra-hard zirconium oxide ceramic with an ebony composite handle. Mirror-smooth and impervious to rust, acids, or biological rot, with a razor edge.",
  "mechanics": "Non-Metallic Stealth Weapon: Undetectable by metal detectors, magnetic traps, and ferro-kinetic magic. Equippable as off-hand blade dealing 1d6 piercing/slashing damage. Pristine Edge: Does not lose durability cutting flesh or herbs; grants +2 on all Field Butchery and skinning checks to harvest pristine beast hides. Brittle Seam: Striking solid steel plate armor or stone causes 5 points of durability damage."
}
```

### Keychain USB (Home Videos & Photos) (`usb_family_drive`)
```json
{
  "name": "Keychain USB (Home Videos & Photos)",
  "rarity": "Rare",
  "category": "Psychological Bastion & Defiance",
  "durability": 100,
  "max_durability": 100,
  "qty": 1,
  "desc": "Waterproof, shockproof aluminum thumb drive on a split-ring key loop labeled 'Family Archive 2010-2024'. Stores 64GB of home videos, Thanksgiving dinners, wedding vows, road trips, and baby laughs.",
  "mechanics": "Sentimental Bastion: Advantage on all saving throws against mind control, psychic horror, despair, and sanity erosion. Unbreakable Hope (1/Encounter Reaction): When player HP is reduced to 0 by a lethal attack, grasping the drive allows a DC 12 WIS check; on success, player clings to life with 1 HP instead. Terminal Compatibility: Can be plugged into pre-collapse Earth computers to unlock personal lore logs."
}
```

### Hunting Laser Rangefinder (`laser_rangefinder`)
```json
{
  "name": "Hunting Laser Rangefinder",
  "rarity": "Uncommon",
  "category": "Ballistic Telemetry & Ranging",
  "durability": 85,
  "max_durability": 100,
  "qty": 1,
  "desc": "Rubber-armored digital monocular laser rangefinder used by precision marksmen. Features an LCD reticle displaying line-of-sight distance in yards, true horizontal angle compensation, and scan mode.",
  "mechanics": "Ballistic Ranging: Spending a minor action to range an enemy before firing eliminates distance penalties for bows, crossbows, and firearms up to 200 yards, and grants +2 on the next ranged attack roll. True Elevation: Automatically calculates horizontal distance when aiming up or down steep cliffs or towers. Operates on CR2 lithium cell with 85/100 battery remaining (1 charge per 10 range scans)."
}
```

## `PRESET_BACKGROUNDS` (20 entries)

### Software Engineer / Sysadmin (`software_engineer`)
```json
{
  "title": "Software Engineer / Sysadmin",
  "description": "Spent years analyzing network protocols, debugging logic leaks, and writing terminal scripts.",
  "stat_recommendations": {
    "INT": 3,
    "WIS": 2,
    "STR": 0,
    "DEX": 0,
    "CON": 0,
    "CHA": 0
  },
  "skills": {
    "Magi-Tech Hacking": {
      "mastery": 45,
      "tier": "Novice",
      "description": "Bypassing arcane firewalls, terminal encryption, and logic wards.",
      "milestones_unlocked": []
    },
    "Aether-Circuit Query": {
      "mastery": 30,
      "tier": "Novice",
      "description": "Tracing leyline data flows and construct signal routing.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Logic Probe (Passive): Enhanced perception when analyzing corrupted terminals, cyber-doors, and security subroutines."
}
```

### Nurse / Paramedic / EMT (`nurse_paramedic`)
```json
{
  "title": "Nurse / Paramedic / EMT",
  "description": "Trained under intense trauma conditions to triage wounds, administer emergency aid, and maintain calm under pressure.",
  "stat_recommendations": {
    "WIS": 3,
    "CON": 2,
    "INT": 1,
    "STR": 0,
    "DEX": 0,
    "CHA": 0
  },
  "skills": {
    "Arcane Triage": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Stabilizing biological vitals, treating traumatic bleeding, and neutralizing aetheric shock.",
      "milestones_unlocked": [
        50
      ]
    },
    "Field Surgery": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Physical repair of damaged tissue and extraction of crystalline shrapnel.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Tourniquet Protocol (Passive): Treating bleeding or trauma wounds consumes 50% fewer medical supplies."
}
```

### Machinist / Auto-Mechanic (`mechanic_machinist`)
```json
{
  "title": "Machinist / Auto-Mechanic",
  "description": "Hands-on mastery of mechanical assemblies, torque specs, hydraulic rigging, and metal fabrication.",
  "stat_recommendations": {
    "STR": 2,
    "CON": 2,
    "INT": 2,
    "DEX": 0,
    "WIS": 0,
    "CHA": 0
  },
  "skills": {
    "Field Smithing": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Reforging weapons, repairing armor plates, and maintaining mechanical gear.",
      "milestones_unlocked": [
        50
      ]
    },
    "Golem-Graft Rigging": {
      "mastery": 35,
      "tier": "Novice",
      "description": "Tuning prosthetic joints, hydraulic seals, and aether-couplings.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Structural Assessment (Passive): Instantly evaluate fracture points on armor, barricades, and constructs."
}
```

### Hunter / Outdoor Guide (`hunter_tracker`)
```json
{
  "title": "Hunter / Outdoor Guide",
  "description": "Lifelong experience tracking game, surviving freezing wilderness, reading terrain, and rigging snares.",
  "stat_recommendations": {
    "WIS": 3,
    "DEX": 2,
    "CON": 1,
    "STR": 0,
    "INT": 0,
    "CHA": 0
  },
  "skills": {
    "Field Trapping": {
      "mastery": 60,
      "tier": "Apprentice",
      "description": "Deployment and concealment of wire snares, tripwires, and perimeter traps.",
      "milestones_unlocked": [
        50
      ]
    },
    "Cartography": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Topographical parsing, terrain mapping, and landmark navigation.",
      "milestones_unlocked": [
        50
      ]
    }
  },
  "innate_perk": "Snare Concealment (Passive): Deployed traps and ambushes receive a +3 bonus to their stealth detection DC."
}
```

### Heavy Construction / Tradesperson (`construction_trades`)
```json
{
  "title": "Heavy Construction / Tradesperson",
  "description": "Conditioned by heavy physical labor, tool operation, and high-impact structural demolition.",
  "stat_recommendations": {
    "STR": 4,
    "CON": 3,
    "DEX": 0,
    "INT": 0,
    "WIS": 0,
    "CHA": 0
  },
  "skills": {
    "Trench Hammers": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Bludgeoning armor-crush strikes and heavy structural demolition attacks.",
      "milestones_unlocked": [
        50
      ]
    },
    "Structural Breach": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Targeting load-bearing structures, stone barriers, and reinforced bulkheads.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Kinetic Impact (Passive): Bludgeoning attacks against constructs, golems, and armored carapaces deal +2 bonus damage."
}
```

### Martial Artist / Combat Veteran (`martial_artist_veteran`)
```json
{
  "title": "Martial Artist / Combat Veteran",
  "description": "Rigorous tactical discipline, weapon choreography, instinctive reaction times, and situational awareness.",
  "stat_recommendations": {
    "STR": 3,
    "DEX": 3,
    "CON": 2,
    "INT": 0,
    "WIS": 0,
    "CHA": 0
  },
  "skills": {
    "One-Handed Axes": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Fast, brutal chops, hooks, and cleaves with single-handed blades.",
      "milestones_unlocked": [
        50
      ]
    },
    "Tactical Reflexes": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Close-quarters footwork and split-second dodging.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Hewing Grip (Passive): Off-hand accuracy penalty is reduced by 50% when dual-wielding light or medium weapons."
}
```

### Corporate Executive / Sales Lead (`corporate_negotiator`)
```json
{
  "title": "Corporate Executive / Sales Lead",
  "description": "Master of leverage, contract phrasing, reading psychological tells, and resource valuation.",
  "stat_recommendations": {
    "CHA": 4,
    "WIS": 2,
    "INT": 1,
    "STR": 0,
    "DEX": 0,
    "CON": 0
  },
  "skills": {
    "Resource Barter": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Assessing market value, haggling with scavengers, and securing favorable trade contracts.",
      "milestones_unlocked": [
        50
      ]
    },
    "Faction Diplomacy": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Navigating guild politics, feudal alliances, and executive syndicates.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Extortion Bypass (Passive): Safe-zone automated merchant casualty markups are permanently discounted by 15%."
}
```

### Artist / Musician / Culinary Chef (`artist_chef`)
```json
{
  "title": "Artist / Musician / Culinary Chef",
  "description": "Trained in sensory perception, delicate hand-eye coordination, emotional resonance, and nutritional synthesis.",
  "stat_recommendations": {
    "DEX": 2,
    "WIS": 2,
    "CHA": 2,
    "STR": 0,
    "CON": 0,
    "INT": 0
  },
  "skills": {
    "Aether-Weaving": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Spinning ambient mana threads into protective meshes, musical resonances, and visual illusions.",
      "milestones_unlocked": []
    },
    "Provisions & Alchemy": {
      "mastery": 45,
      "tier": "Novice",
      "description": "Brewing restorative elixirs, preserving aetheric ingredients, and preparing nutritious stamina rations.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Comforting Ration (Passive): Consumed food buffs grant double stamina recovery and restore +5 focus."
}
```

### Electrician / High-Voltage Lineworker (`electrician_lineworker`)
```json
{
  "title": "Electrician / High-Voltage Lineworker",
  "description": "Scaled utility poles and worked with lethal voltages, high-amperage breakers, and transformer coils.",
  "stat_recommendations": {
    "DEX": 2,
    "CON": 2,
    "INT": 2,
    "STR": 0,
    "WIS": 0,
    "CHA": 0
  },
  "skills": {
    "Magi-Tech Wiring": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Rigging electrical conduits, grounding leyline circuits, and channeling static mana.",
      "milestones_unlocked": [
        50
      ]
    },
    "Kinetic Insulation": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Insulating apparel and weaponry against electro-shock and lightning surges.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Dielectric Grounding (Passive): Suffer 25% reduced lightning/shock damage and never suffer paralysis from stun-traps."
}
```

### Veterinarian / Animal Care Specialist (`veterinarian_handler`)
```json
{
  "title": "Veterinarian / Animal Care Specialist",
  "description": "Decades of diagnostic medicine, vaccine preparation, and surgical triage on feral and domestic beasts.",
  "stat_recommendations": {
    "WIS": 3,
    "INT": 2,
    "CHA": 1,
    "STR": 0,
    "DEX": 0,
    "CON": 0
  },
  "skills": {
    "Beast Empathy": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Pacifying agitated monsters, reading predator body language, and taming mounts.",
      "milestones_unlocked": [
        50
      ]
    },
    "Field Xenobiology": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Dissecting monster anatomies and identifying organ gland vulnerabilities.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Beast-Whisperer (Passive): Wild predators hesitate before attacking; +3 bonus to all animal handling and taming checks."
}
```

### Locksmith / Physical Security Specialist (`locksmith_security`)
```json
{
  "title": "Locksmith / Physical Security Specialist",
  "description": "Decoded pin tumblers, bypass shims, electronic keypads, safe dials, and reinforced vault doors.",
  "stat_recommendations": {
    "DEX": 3,
    "INT": 2,
    "WIS": 1,
    "STR": 0,
    "CON": 0,
    "CHA": 0
  },
  "skills": {
    "Tumbler Decryption": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Picking mechanical lock tumblers and bypassing runic keyholes.",
      "milestones_unlocked": [
        50
      ]
    },
    "Perimeter Intrusion": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Detecting hidden floor pressure plates, tripwires, and intrusion wards.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Skeleton Key Insight (Passive): Lockpicks and bypass probes never break upon a failed check."
}
```

### Chemist / Industrial Pharmacist (`chemist_pharmacist`)
```json
{
  "title": "Chemist / Industrial Pharmacist",
  "description": "Handled reagent purity, exothermic titrations, compound crystallization, and pharmacology.",
  "stat_recommendations": {
    "INT": 4,
    "WIS": 2,
    "STR": 0,
    "DEX": 0,
    "CON": 0,
    "CHA": 0
  },
  "skills": {
    "Chemical Distillation": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Refining raw aetheric minerals and solvent extractions into stable reagents.",
      "milestones_unlocked": [
        50
      ]
    },
    "Toxicological Neutralization": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Synthesizing antivenoms and neutralizing environmental toxins and vapors.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Catalytic Reaction (Passive): Crafted potions, poisons, and solvent bombs have +20% potency or duration."
}
```

### Librarian / Antiquarian Archivist (`librarian_archivist`)
```json
{
  "title": "Librarian / Antiquarian Archivist",
  "description": "Curated ancient manuscripts, cross-referenced forgotten histories, and translated dead languages.",
  "stat_recommendations": {
    "INT": 3,
    "WIS": 3,
    "STR": 0,
    "DEX": 0,
    "CON": 0,
    "CHA": 0
  },
  "skills": {
    "Ancient Glyph Deciphering": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Translating forgotten pre-collapse scripts and magical rune matrices.",
      "milestones_unlocked": [
        50
      ]
    },
    "Lore Cataloging": {
      "mastery": 45,
      "tier": "Novice",
      "description": "Cross-referencing monster codices to reveal enemy resistances and loot tables.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Eidetic Index (Passive): Instantly identify the tier, origin, and hidden curse of any discovered magical grimoire or parchment."
}
```

### Long-Haul Trucker / Logistics Hauler (`trucker_highwayman`)
```json
{
  "title": "Long-Haul Trucker / Logistics Hauler",
  "description": "Mastered interstate convoy logistics, diesel mechanics, and sleepless cross-country hauls.",
  "stat_recommendations": {
    "CON": 3,
    "STR": 2,
    "WIS": 1,
    "DEX": 0,
    "INT": 0,
    "CHA": 0
  },
  "skills": {
    "Heavy Vehicle Rigging": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Operating, maintaining, and hot-wiring motorized carts and heavy salvage crawlers.",
      "milestones_unlocked": [
        50
      ]
    },
    "Interstate Navigation": {
      "mastery": 45,
      "tier": "Novice",
      "description": "Plotting the most efficient transit routes and chokepoints between distant sectors.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Highballing (Passive): Overland convoy and travel speeds are increased by 20%; driver travel fatigue is halved."
}
```

### Architect / Structural Engineer (`architect_planner`)
```json
{
  "title": "Architect / Structural Engineer",
  "description": "Designed high-rise foundations, cantilever trusses, blueprint schematics, and load limits.",
  "stat_recommendations": {
    "INT": 3,
    "WIS": 2,
    "STR": 1,
    "DEX": 0,
    "CON": 0,
    "CHA": 0
  },
  "skills": {
    "Structural Assessment": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Identifying foundational stress points, collapse hazards, and bunker layouts.",
      "milestones_unlocked": [
        50
      ]
    },
    "Homestead Engineering": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Designing reinforced fortifications, automated defenses, and vault expansions.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Blueprinter (Passive): Homestead room construction costs are reduced by 15%, and base bunker durability is increased by 25%."
}
```

### Detective / Forensic Investigator (`detective_forensics`)
```json
{
  "title": "Detective / Forensic Investigator",
  "description": "Reconstructed ballistic trajectories, analyzed blood spatter, and cracked criminal conspiracies.",
  "stat_recommendations": {
    "WIS": 3,
    "INT": 3,
    "STR": 0,
    "DEX": 0,
    "CON": 0,
    "CHA": 0
  },
  "skills": {
    "Crime Scene Reconstruction": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Deducing what occurred in a ruined room from blood patterns and footprints.",
      "milestones_unlocked": [
        50
      ]
    },
    "Ballistic Telemetry": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Calculating sniper lines of fire and anticipating enemy ranged trajectories.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Forensic Eye (Passive): Clues, tracks, and concealed cache markers glow with faint residual phosphor under examination."
}
```

### Botanist / Hydroponics Cultivator (`botanist_horticulturist`)
```json
{
  "title": "Botanist / Hydroponics Cultivator",
  "description": "Mastered soil chemistry, cross-pollination, mycorrhizal networks, and greenhouse pruning.",
  "stat_recommendations": {
    "WIS": 3,
    "INT": 2,
    "CON": 1,
    "STR": 0,
    "DEX": 0,
    "CHA": 0
  },
  "skills": {
    "Flora Harvesting": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Harvesting delicate medicinal plants and toxic spores without damaging yields.",
      "milestones_unlocked": [
        50
      ]
    },
    "Mycelial Grafting": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Cultivating bioluminescent mushrooms and graftable fungal symbiotes.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Green Thumb (Passive): Greenhouse harvest yields in the Homestead are doubled, with a 25% chance for mutant rare strains."
}
```

### Firefighter / Smokejumper (`firefighter_smokejumper`)
```json
{
  "title": "Firefighter / Smokejumper",
  "description": "Ran into burning buildings, wielded Halligan breach bars, and survived suffocating thermal storms.",
  "stat_recommendations": {
    "STR": 3,
    "CON": 3,
    "DEX": 1,
    "INT": 0,
    "WIS": 0,
    "CHA": 0
  },
  "skills": {
    "Hazard Breaching": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Forcing open warped steel blast doors and chopping through burning debris.",
      "milestones_unlocked": [
        50
      ]
    },
    "Pyric Suppression": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Extinguishing arcane flame hazards and handling pressurized hose lines.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Thermal Resistance (Passive): Take 20% reduced fire damage and ignore smoke inhalation and choking penalties."
}
```

### Commercial Pilot / Avionics Technician (`pilot_avionics`)
```json
{
  "title": "Commercial Pilot / Avionics Technician",
  "description": "Mastered instrument flight ratings, three-axis aerodynamics, gyroscopic navigation, and engine diagnostics.",
  "stat_recommendations": {
    "DEX": 3,
    "INT": 2,
    "WIS": 1,
    "STR": 0,
    "CON": 0,
    "CHA": 0
  },
  "skills": {
    "Aerodynamic Navigation": {
      "mastery": 50,
      "tier": "Apprentice",
      "description": "Glider steering, calculating wind shear, and high-altitude drift control.",
      "milestones_unlocked": [
        50
      ]
    },
    "Gyroscopic Balance": {
      "mastery": 45,
      "tier": "Novice",
      "description": "Maintaining spatial orientation during falls, zero-G, or disorienting spins.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Horizon Lock (Passive): Immune to vertigo and disorientation; fall damage is reduced by 25%."
}
```

### Master Tailor / Leathercrafter (`tailor_leathercrafter`)
```json
{
  "title": "Master Tailor / Leathercrafter",
  "description": "Stitched heavy hide armors, handled delicate silk weaves, and reinforced load-bearing seams.",
  "stat_recommendations": {
    "DEX": 3,
    "WIS": 2,
    "CHA": 1,
    "STR": 0,
    "CON": 0,
    "INT": 0
  },
  "skills": {
    "Weave Reinforcement": {
      "mastery": 55,
      "tier": "Apprentice",
      "description": "Stitching protective aether-threading and Kevlar backing into light armors.",
      "milestones_unlocked": [
        50
      ]
    },
    "Hide Tanning & Curing": {
      "mastery": 40,
      "tier": "Novice",
      "description": "Processing beast pelts, chitin plates, and sinew cords into wearable gear.",
      "milestones_unlocked": []
    }
  },
  "innate_perk": "Seamless Stitch (Passive): Fabric and leather armor repaired by you gains +10% bonus durability over maximum."
}
```

## `PRESET_LIFESTYLES` (18 entries)

### 🛋️ Desk Bound / Sedentary (+Mental) (`desk_bound`)
```json
{
  "title": "🛋️ Desk Bound / Sedentary (+Mental)",
  "desc": "Long hours at keyboards, low physical strain, high cognitive and analytical conditioning.",
  "points": {
    "STR": 1,
    "DEX": 1,
    "CON": 2,
    "INT": 6,
    "WIS": 6,
    "CHA": 4
  }
}
```

### 🏃 Athletic / Field Sports (+Agility) (`athletic`)
```json
{
  "title": "🏃 Athletic / Field Sports (+Agility)",
  "desc": "High cardiovascular fitness, agile footwork, kinetic discipline, and team communication.",
  "points": {
    "STR": 5,
    "DEX": 6,
    "CON": 4,
    "INT": 1,
    "WIS": 2,
    "CHA": 2
  }
}
```

### 🔨 Heavy Labor / Trades (+STR/CON) (`heavy_labor`)
```json
{
  "title": "🔨 Heavy Labor / Trades (+STR/CON)",
  "desc": "Repetitive heavy lifting, calloused endurance, mechanical resistance, and tool wielding.",
  "points": {
    "STR": 7,
    "DEX": 3,
    "CON": 6,
    "INT": 1,
    "WIS": 2,
    "CHA": 1
  }
}
```

### 🎖️ First Responder / Combat (+Combat) (`first_responder`)
```json
{
  "title": "🎖️ First Responder / Combat (+Combat)",
  "desc": "Crisis tactical response, rapid triage decision-making, and high adrenaline composure.",
  "points": {
    "STR": 5,
    "DEX": 5,
    "CON": 4,
    "INT": 2,
    "WIS": 3,
    "CHA": 1
  }
}
```

### 📚 Academic Scholar / Researcher (+INT/WIS) (`academic_scholar`)
```json
{
  "title": "📚 Academic Scholar / Researcher (+INT/WIS)",
  "desc": "Archival synthesis, methodological logic, rigorous deductive reasoning, and deep theory.",
  "points": {
    "STR": 0,
    "DEX": 1,
    "CON": 1,
    "INT": 8,
    "WIS": 7,
    "CHA": 3
  }
}
```

### 🔦 Night Shift Security / Sentry (+WIS/CON) (`night_security`)
```json
{
  "title": "🔦 Night Shift Security / Sentry (+WIS/CON)",
  "desc": "Perimeter vigilance, sleep deprivation resistance, darkness adaptation, and acute hearing.",
  "points": {
    "STR": 3,
    "DEX": 4,
    "CON": 5,
    "INT": 1,
    "WIS": 6,
    "CHA": 1
  }
}
```

### 🌲 Off-Grid Homesteader / Survivalist (+CON/WIS) (`offgrid_homesteader`)
```json
{
  "title": "🌲 Off-Grid Homesteader / Survivalist (+CON/WIS)",
  "desc": "Timber felling, well digging, food preservation, weather reading, and stubborn endurance.",
  "points": {
    "STR": 4,
    "DEX": 3,
    "CON": 6,
    "INT": 1,
    "WIS": 5,
    "CHA": 1
  }
}
```

### 🧘 Yoga Instructor / Contortionist (+DEX/WIS) (`yoga_contortionist`)
```json
{
  "title": "🧘 Yoga Instructor / Contortionist (+DEX/WIS)",
  "desc": "Supreme core balance, ligament elasticity, breath regulation, and joint freedom.",
  "points": {
    "STR": 1,
    "DEX": 8,
    "CON": 4,
    "INT": 1,
    "WIS": 4,
    "CHA": 2
  }
}
```

### 🎮 Esports Athlete / Speedrunner (+DEX/INT) (`esports_gamer`)
```json
{
  "title": "🎮 Esports Athlete / Speedrunner (+DEX/INT)",
  "desc": "Micro-second twitch reactions, spatial routing, predictive framing, and APM dexterity.",
  "points": {
    "STR": 0,
    "DEX": 7,
    "CON": 1,
    "INT": 7,
    "WIS": 3,
    "CHA": 2
  }
}
```

### 🎭 Performing Musician / Stage Actor (+CHA/DEX) (`stage_performer`)
```json
{
  "title": "🎭 Performing Musician / Stage Actor (+CHA/DEX)",
  "desc": "Magnetic crowd presence, acoustic projection, physical choreography, and empathetic resonance.",
  "points": {
    "STR": 1,
    "DEX": 4,
    "CON": 2,
    "INT": 2,
    "WIS": 3,
    "CHA": 8
  }
}
```

### 🚛 Long-Haul Trucker / Highway Specialist (+CON/WIS) (`longhaul_trucker`)
```json
{
  "title": "🚛 Long-Haul Trucker / Highway Specialist (+CON/WIS)",
  "desc": "Iron highway stamina, solitary mental resilience, situational radar, and route planning.",
  "points": {
    "STR": 3,
    "DEX": 2,
    "CON": 7,
    "INT": 1,
    "WIS": 5,
    "CHA": 2
  }
}
```

### 🏂 Extreme Sports / Adrenaline Junkie (+DEX/STR) (`extreme_sports`)
```json
{
  "title": "🏂 Extreme Sports / Adrenaline Junkie (+DEX/STR)",
  "desc": "High-velocity downhill balance, rapid kinetic recovery, and zero fear of terminal velocity.",
  "points": {
    "STR": 5,
    "DEX": 7,
    "CON": 5,
    "INT": 1,
    "WIS": 1,
    "CHA": 1
  }
}
```

### 🤿 Commercial Diver / Hyperbaric Welder (+CON/STR) (`commercial_diver`)
```json
{
  "title": "🤿 Commercial Diver / Hyperbaric Welder (+CON/STR)",
  "desc": "Hyperbaric lung fortitude, freezing water tolerance, deep darkness composure, and torch work.",
  "points": {
    "STR": 5,
    "DEX": 2,
    "CON": 8,
    "INT": 1,
    "WIS": 3,
    "CHA": 1
  }
}
```

### 🍳 Line Cook / Kitchen Warrior (+DEX/CON) (`line_cook`)
```json
{
  "title": "🍳 Line Cook / Kitchen Warrior (+DEX/CON)",
  "desc": "Blistering stove endurance, multi-pan micro-timing, knife agility, and battle-cry tempo.",
  "points": {
    "STR": 2,
    "DEX": 6,
    "CON": 6,
    "INT": 1,
    "WIS": 3,
    "CHA": 2
  }
}
```

### 👨‍🏫 High School Educator / Counselor (+CHA/INT/WIS) (`highschool_educator`)
```json
{
  "title": "👨‍🏫 High School Educator / Counselor (+CHA/INT/WIS)",
  "desc": "Infinite crisis patience, behavioral de-escalation, group discipline, and clear instruction.",
  "points": {
    "STR": 1,
    "DEX": 1,
    "CON": 2,
    "INT": 5,
    "WIS": 5,
    "CHA": 6
  }
}
```

### 🧭 Park Ranger / Forestry Tracker (+WIS/DEX) (`park_ranger`)
```json
{
  "title": "🧭 Park Ranger / Forestry Tracker (+WIS/DEX)",
  "desc": "Topographical wilderness mastery, predator track reading, brush navigation, and fire watching.",
  "points": {
    "STR": 3,
    "DEX": 5,
    "CON": 4,
    "INT": 1,
    "WIS": 6,
    "CHA": 1
  }
}
```

### ⚒️ Blacksmith / Metal Sculptor (+STR/CON) (`blacksmith_sculptor`)
```json
{
  "title": "⚒️ Blacksmith / Metal Sculptor (+STR/CON)",
  "desc": "Ten-pound hammer swinging, radiant heat endurance, steel quenching, and structural vision.",
  "points": {
    "STR": 7,
    "DEX": 2,
    "CON": 6,
    "INT": 2,
    "WIS": 2,
    "CHA": 1
  }
}
```

### 🥊 Combat Sports Fighter / MMA Striker (+STR/DEX) (`mma_fighter`)
```json
{
  "title": "🥊 Combat Sports Fighter / MMA Striker (+STR/DEX)",
  "desc": "Explosive hip drive, choke defense, pain suppression, and bone-crushing striking accuracy.",
  "points": {
    "STR": 6,
    "DEX": 6,
    "CON": 5,
    "INT": 1,
    "WIS": 1,
    "CHA": 1
  }
}
```

## `RACIAL_LINEAGES` (20 entries)

### Pure Human (`pure_human`)
```json
{
  "name": "Pure Human",
  "genre": "Universal",
  "desc": "Resisted genetic mutation during the Aetheric Rift collapse. Highly adaptable, tenacious, and versatile.",
  "stat_mods": {
    "STR": 1,
    "DEX": 1,
    "CON": 1,
    "INT": 1,
    "WIS": 1,
    "CHA": 1
  },
  "racial_abilities": [
    "Tenacious Will: +10% bonus experience gain from all combat and discovery actions.",
    "Versatile Conditioning: +1 additional starting Feat slot."
  ]
}
```

### Phrenic Human (`phrenic_human`)
```json
{
  "name": "Phrenic Human",
  "genre": "Psionic / Sci-Fi",
  "desc": "Awakened latent psionic neural pathways when flooded by atmospheric mana. Projects telekinetic forces.",
  "stat_mods": {
    "INT": 2,
    "WIS": 2,
    "DEX": 1,
    "STR": 0,
    "CON": 0,
    "CHA": 0
  },
  "racial_abilities": [
    "Aether-Telepathy: Communicate silently with party members within 60ft.",
    "Telekinetic Grip: Manipulate lightweight objects remotely and recall thrown weapons to your hand.",
    "Psionic Shielding: Project a minor kinetic barrier to absorb incoming impacts.",
    "Flaw - Sensory Overload: Vulnerable to high-frequency sonic or psychic distortion."
  ]
}
```

### Deepforged Dwarf (`deepforged_dwarf`)
```json
{
  "name": "Deepforged Dwarf",
  "genre": "Fantasy",
  "desc": "Underground heritage fused with aether-furnaces. Unmatched physical fortitude and geological intuition.",
  "stat_mods": {
    "CON": 3,
    "STR": 2,
    "WIS": 1,
    "DEX": -1,
    "INT": 0,
    "CHA": -1
  },
  "racial_abilities": [
    "Stone-Sense: Instantly detect structural hollows, secret vaults, and ore seams in subterranean sectors.",
    "Toxic Hardening: Advantage on saving throws against atmospheric poisons, radiation, and spores."
  ]
}
```

### Scrapper Goblinoid (`scrapper_goblinoid`)
```json
{
  "name": "Scrapper Goblinoid",
  "genre": "Fantasy / Steampunk",
  "desc": "Warped into an agile, sharp-eyed industrial scavenger. Masters of salvage, stealth, and evasion.",
  "stat_mods": {
    "DEX": 3,
    "INT": 2,
    "STR": -1,
    "CON": 0,
    "WIS": 0,
    "CHA": 0
  },
  "racial_abilities": [
    "Junk-Engine Intuition: Assemble and repair crude weapons/tools using 50% fewer materials.",
    "Scurry: Disengage from melee combat without drawing free hostile attacks."
  ]
}
```

### Aether-Touched Elf (`aether_elf`)
```json
{
  "name": "Aether-Touched Elf",
  "genre": "Fantasy",
  "desc": "Infused with raw ambient leyline energy. Graceful, sharp-eyed, and inherently sensitive to magic.",
  "stat_mods": {
    "DEX": 2,
    "INT": 2,
    "CHA": 1,
    "STR": -1,
    "CON": 0,
    "WIS": 0
  },
  "racial_abilities": [
    "Mana Resonance: Low-light vision and natural passive detection of magical wardings.",
    "Quickstep: Base overland travel speed increased by +15%."
  ]
}
```

### Golem Reborn (`golem_reborn`)
```json
{
  "name": "Golem Reborn",
  "genre": "MageTech / Construct",
  "desc": "Organic consciousness salvaged into a heavy mechanized construct of blackened steel and runic stone.",
  "stat_mods": {
    "CON": 4,
    "STR": 2,
    "DEX": -2,
    "CHA": -2,
    "INT": 0,
    "WIS": 0
  },
  "racial_abilities": [
    "Living Construct: Immune to biological diseases, starvation, and natural sleep exhaustion.",
    "Reinforced Chassis: Natural Armor Class increased by +2.",
    "Flaw - Machine Maintenance: Biological healing items are only 50% effective; requires tool repairs."
  ]
}
```

### Hellforged Fiendblood (Tiefling) (`hellforged_tiefling`)
```json
{
  "name": "Hellforged Fiendblood (Tiefling)",
  "genre": "Fantasy",
  "desc": "Infernal heritage manifested when the rift tore into planar fire-realms. Curled obsidian horns, sulfurous blood, and fiery resilience.",
  "stat_mods": {
    "CHA": 2,
    "INT": 2,
    "DEX": 1,
    "STR": 0,
    "CON": 0,
    "WIS": -1
  },
  "racial_abilities": [
    "Hellfire Flare: Can ignite melee weapon strikes with +1d4 infernal fire damage once per encounter.",
    "Infernal Resistance: Gain 25% passive damage reduction against fire and heat hazards.",
    "Darkvision: See clearly in non-magical darkness up to 60ft."
  ]
}
```

### Celestial Radiant (Aasimar) (`celestial_aasimar`)
```json
{
  "name": "Celestial Radiant (Aasimar)",
  "genre": "Fantasy",
  "desc": "Blessed with ambient astral light from uncorrupted celestial planes. Faint golden luminescence, halo-reflections, and purifying grace.",
  "stat_mods": {
    "WIS": 2,
    "CHA": 3,
    "CON": 1,
    "STR": 0,
    "DEX": 0,
    "INT": -1
  },
  "racial_abilities": [
    "Luminescent Touch: Release a burst of healing light restoring 15 HP to an ally (once per rest).",
    "Radiant Resistance: Passive 25% damage reduction against necrotic and void corruption.",
    "Celestial Visage: +2 on diplomacy and leadership checks."
  ]
}
```

### Draconic Scion (Dragonborn) (`draconic_scion`)
```json
{
  "name": "Draconic Scion (Dragonborn)",
  "genre": "Fantasy",
  "desc": "Dormant primeval reptile genomes mutated into thick iridescent dragon scales, slit pupils, and an elemental breath organ.",
  "stat_mods": {
    "STR": 3,
    "CHA": 2,
    "CON": 1,
    "DEX": -1,
    "INT": 0,
    "WIS": 0
  },
  "racial_abilities": [
    "Draconic Breath: Exhale a 15ft cone of elemental energy dealing 2d6 damage (once per rest).",
    "Dragon-Scale Armor: Natural AC increased by +1; resistant to elemental blasts.",
    "Intimidating Roar: Advantage on Intimidation checks against beasts and humanoids."
  ]
}
```

### Changeling / Faceless Mimic (`changeling_mimic`)
```json
{
  "name": "Changeling / Faceless Mimic",
  "genre": "Fantasy / Sci-Fi",
  "desc": "Unstable cellular matrix allowing rapid restructuring of facial features, voice chords, skin pigmentation, and body height.",
  "stat_mods": {
    "CHA": 3,
    "DEX": 2,
    "INT": 1,
    "STR": -1,
    "CON": 0,
    "WIS": 0
  },
  "racial_abilities": [
    "Cellular Shift: Magically alter facial appearance, voice, and build to impersonate any humanoid.",
    "Slippery Identity: +4 bonus to Deception and Stealth checks when undercover.",
    "Flaw - Identity Dissonance: Takes double psychic strain from mental probes."
  ]
}
```

### MageTech Cyborg (Crucible Conscript) (`neuromancer_cyborg`)
```json
{
  "name": "MageTech Cyborg (Crucible Conscript)",
  "genre": "MageTech / Biomechanical",
  "desc": "Survivors whose catastrophic trauma or pre-collapse medical implants were seized during Initialization and forcibly welded to high-torque pneumatic servos, runic copper conduits, and an aether-ocular reticle by the Cardinal System's auto-forges. Rebuilt as frontline biomechanical conscripts of the Crucible.",
  "stat_mods": {
    "STR": 2,
    "CON": 2,
    "INT": 1,
    "DEX": 1,
    "WIS": -1,
    "CHA": -1
  },
  "racial_abilities": [
    "Cardinal Telemetry Ocular: Retinal HUD crosshair scans enemy armor seams and weakpoints, granting +1 to hit against analyzed targets and displaying exact enemy HP percentages.",
    "Pneumatic Endoskeleton: Heavy titanium-composite bone reinforcement grants +1 Natural Armor Class, adds +25 lbs carrying capacity before encumbrance penalties, and grants +2 on Strength checks to break barriers or resist grappling.",
    "Innate Graft-Tolerance: Biomechanical conditioning increases baseline Golem-Graft Strain threshold by +15, allowing the character to install advanced cybernetic and monster grafts without neuro-vascular rejection.",
    "Flaw - Arc & EMP Conductivity: Lightning damage, electric arc spells, and electromagnetic pulse hazards deal +20% bonus damage and cause motor-servo jitter (-1 DEX penalty for 1 round following electrical damage)."
  ]
}
```

### Mantid Insectoid (Chittering Carapace) (`mantid_insectoid`)
```json
{
  "name": "Mantid Insectoid (Chittering Carapace)",
  "genre": "Sci-Fi / Alien",
  "desc": "Radical insectoid metamorphosis featuring chitinous armor plates, compound eyes, compound antennae, and barbed forearms.",
  "stat_mods": {
    "DEX": 3,
    "CON": 2,
    "STR": 1,
    "INT": 0,
    "WIS": 0,
    "CHA": -2
  },
  "racial_abilities": [
    "Chitinous Exoskeleton: Natural +2 AC against slashing and piercing attacks.",
    "Wall-Climber: Climb vertical surfaces and ceilings without movement speed penalties.",
    "Compound Vision: Cannot be flanked or caught flat-footed from behind."
  ]
}
```

### Shade-Touched (Shadowstalker) (`shade_touched`)
```json
{
  "name": "Shade-Touched (Shadowstalker)",
  "genre": "Fantasy / Umbral",
  "desc": "Soul fused with umbral rift energies. Casts no natural shadow; skin has a faint dusky hue that absorbs direct light.",
  "stat_mods": {
    "DEX": 3,
    "WIS": 2,
    "INT": 1,
    "STR": -1,
    "CON": 0,
    "CHA": 0
  },
  "racial_abilities": [
    "Shadowstep: Teleport up to 30ft between two areas of dim light or darkness (once per encounter).",
    "Umbral Camouflage: Advantage on Stealth checks in dark or subterranean environments.",
    "Flaw - Photosensitivity: -1 to attack rolls in direct blinding sunlight without eye protection."
  ]
}
```

### Iron-Jaw Orc / Savage Born (`ironjaw_orc`)
```json
{
  "name": "Iron-Jaw Orc / Savage Born",
  "genre": "Fantasy",
  "desc": "Hulking muscular frame, prominent lower tusk canines, and a volcanic battle fury that shrugs off mortal wounds.",
  "stat_mods": {
    "STR": 4,
    "CON": 3,
    "WIS": 0,
    "DEX": -1,
    "INT": -1,
    "CHA": -1
  },
  "racial_abilities": [
    "Relentless Endurance: When reduced to 0 HP, drop to 1 HP instead (once per long rest).",
    "Savage Critical: Melee weapon critical hits roll an extra weapon damage die.",
    "Menacing Presence: +2 to Intimidation and morale break checks."
  ]
}
```

### Nanite Swarm Symbiote (`nanite_host`)
```json
{
  "name": "Nanite Swarm Symbiote",
  "genre": "Sci-Fi",
  "desc": "Ingested military nanite colonies in pre-integration research, now sustained by ambient aether and living tissue.",
  "stat_mods": {
    "CON": 3,
    "INT": 2,
    "DEX": 1,
    "STR": 0,
    "WIS": 0,
    "CHA": -1
  },
  "racial_abilities": [
    "Cellular Regeneration: Passively regenerates 2 HP per minute when out of active combat.",
    "Micro-Tool Extrusion: Extrude lockpicks, scalpel blades, or soldering tips directly from fingertips.",
    "Flaw - High Caloric Drain: Starvation and dehydration accumulate at double the normal rate."
  ]
}
```

### Sylph (Zephyr-Born) (`sylph_windstrider`)
```json
{
  "name": "Sylph (Zephyr-Born)",
  "genre": "Fantasy",
  "desc": "Airy, buoyant biology infused with elemental aer-spirits. Unusually light on their feet, with hair that drifts as if caught in a breeze.",
  "stat_mods": {
    "DEX": 3,
    "WIS": 2,
    "CHA": 1,
    "STR": -2,
    "CON": 0,
    "INT": 0
  },
  "racial_abilities": [
    "Feather Fall: Naturally glide down from any height, immune to standard falling damage.",
    "Zephyr Burst: Increase movement speed by +50% for 2 rounds (once per encounter).",
    "Wind Guidance: Ranged arrow and spell accuracy penalty from heavy winds is ignored."
  ]
}
```

### Sylvan Thornborn (Fey-Touched) (`sylvan_dryad`)
```json
{
  "name": "Sylvan Thornborn (Fey-Touched)",
  "genre": "Fantasy",
  "desc": "Flesh intertwined with living chlorophytic vines, bark-like knuckles, and deep connection to wild flora and leyline root-networks.",
  "stat_mods": {
    "WIS": 3,
    "CON": 2,
    "CHA": 1,
    "STR": 0,
    "DEX": 0,
    "INT": -1
  },
  "racial_abilities": [
    "Root-Mend: Heal 10 HP when resting directly on fertile earth or natural soil.",
    "Thorn Bramble Skin: Melee attackers that strike you without reach suffer 1d4 piercing recoil damage.",
    "Flora Rapport: Communicate basic concepts with natural plants and trees."
  ]
}
```

### Void-Walker (Singularity Drifter) (`void_walker`)
```json
{
  "name": "Void-Walker (Singularity Drifter)",
  "genre": "Sci-Fi / Cosmic",
  "desc": "Exposed directly to a zero-point spatial rift. Reality slightly bends around their periphery with faint distortion ripples.",
  "stat_mods": {
    "WIS": 3,
    "INT": 2,
    "DEX": 1,
    "STR": 0,
    "CON": -1,
    "CHA": 0
  },
  "racial_abilities": [
    "Phase Shift: Become incorporeal for 1 turn, avoiding all non-magical physical damage (once per combat).",
    "Spatial Anchor: Immune to being forcibly pushed, pulled, or banished through rifts.",
    "Flaw - Gravity Drift: Takes +25% increased fall damage if phase shift is on cooldown."
  ]
}
```

### Saurian Dredge (Lizardfolk) (`amphibian_lizardfolk`)
```json
{
  "name": "Saurian Dredge (Lizardfolk)",
  "genre": "Fantasy",
  "desc": "Cold-blooded scaled hunter adapted to marshlands, sewers, and flooded subway tunnels. Serrated claws and swimming tail.",
  "stat_mods": {
    "CON": 3,
    "STR": 2,
    "WIS": 1,
    "DEX": 0,
    "INT": -1,
    "CHA": -1
  },
  "racial_abilities": [
    "Amphibious Vigor: Hold breath for up to 30 minutes underwater; swim speed matches land speed.",
    "Natural Jaws: Secondary bite attack in melee dealing 1d6 piercing damage.",
    "Scavenger Guts: Immune to food poisoning and diseases from stale or raw meat."
  ]
}
```

### Synthetic Android (Printed Soul-Vessel) (`synthetic_android`)
```json
{
  "name": "Synthetic Android (Printed Soul-Vessel)",
  "genre": "Pathfinder / Bio-Synthetic",
  "desc": "Derived from Pathfinder's Numerian synthetic humanoids and the Cardinal System's automated bio-foundries. Fabricated in deep subterranean print-vats from living carbon polymers, nanite circulatory fluid, and cold-forged porcelain/composite dermal plating. Created as disposable automated conscripts for the death-game, the planetary mana rupture unexpectedly seeded emergent souls and mortal consciousness into their logic cores.",
  "stat_mods": {
    "INT": 3,
    "DEX": 2,
    "CON": 1,
    "STR": 0,
    "WIS": 0,
    "CHA": -2
  },
  "racial_abilities": [
    "Synthetic Biology (Dual Nature): Counts as both Humanoid and Construct. Fully immune to biological diseases, atmospheric spores, and magical sleep effects. Biological healing and nanite repair items both function at full efficiency.",
    "Nanite Surge: Once per combat encounter or short rest, can trigger an internal nanite circulatory burst as a free action, adding a +4 bonus to any single attack roll, saving throw, or skill check, or immediately self-stabilizing at 1 HP upon falling unconscious.",
    "Logic-Core Discipline: Emotional suppression grants complete immunity to fear, intimidation, and charm/confusion spells. Grants +2 on tactical deduction, cryptography, and complex system query checks.",
    "Flaw - Empathy Void & Core Flush: Suffers a -2 penalty on Charisma (Persuasion, Animal Handling, and Empathy) checks with organic survivors. Requires a 4-hour stationary diagnostic stasis during long rests to cycle internal coolant and vent memory buffers."
  ]
}
```

## `STARTER_WEAPON_OPTIONS` (14 entries)

```json
[
  "Rusted Iron Sword",
  "Heavy Scavenged Mace",
  "Scrap-Plate Shield",
  "Arcane Stun-Pistol",
  "Tanto Combat Knife",
  "Aetheric Focusing Wand",
  "Recurve Hunting Bow",
  "Chipped Wood-Axe",
  "Sanctified Flail",
  "Concealed Trench Daggers",
  "Kinetic Shock-Staff",
  "Reinforced Spear",
  "Twin Scavenger Daggers",
  "None"
]
```
