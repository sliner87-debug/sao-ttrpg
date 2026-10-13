# G75VW Phase 1–9 Engine Mechanics, Mastery Perks, Grafts & Geopolitical Factions

Canonical mechanical architecture from `backend/mechanics.py` and `PROJECT.md` on `ROG_G75VW`.

## 1. 1–1000 Skill Mastery Tiers & Thresholds
- **Novice**: 1–49
- **Apprentice**: 50–99
- **Journeyman**: 100–249
- **Adept**: 250–499
- **Master**: 500–749
- **Grandmaster**: 750–999
- **Transcendence**: 1000

## 2. Canonical Skill Milestones

### One-Handed Axes
- **Tier 50 (Hewing Edge)**: Your strikes find structural seams in armor and hide with ruthless economy of motion.
- **Tier 100 (Gale Cleave)**: A 2-hit horizontal centrifugal spin that tears through enemy hitboxes with accelerated momentum.
- **Tier 250 (Bearded Hook)**: Utilize the recessed beard of your axe blade to catch enemy shields, parry weapons, and manipulate hitboxes.
- **Tier 500 (Executioner's Descent)**: A devastating overhead vertical leap-cleave focused entirely on the target's primary structural core or neck joint.
- **Tier 750 (Einherjar's Blood-Frenzy)**: The spirit of the fallen Nordic vanguard infuses your neural interface; physical pain accelerates attack rate.
- **Tier 1000 (Fenrir's Howling Ruin)**: A reality-fracturing 5-hit phantom axe combo that shears directly into Cardinal's collision geometry, leaving spatial vacuum tears.

### Trench Hammers
- **Tier 50 (Concussive Impact)**: Heavy blunt force vibrates through solid protection, transferring trauma directly to interior organs and chassis.
- **Tier 100 (Pneumatic Back-Pick)**: Reversing swing direction, drive the diamond-hard armor-piercing raven-bill or pick into a pressurized joint.
- **Tier 250 (Kinetic Rebound)**: Channel massive recoil vibration of dense alloy strikes back into posture and subsequent swings.
- **Tier 500 (Seismic Fracture)**: Slam the weighted head of the hammer into bedrock or pavement, propagating a directional piezoelectric seismic shockwave.
- **Tier 750 (Colossus Breaker)**: Heavy blunt impacts deform high-density exo-chassis, boss-grade carapace, and golem-grafts on a molecular level.
- **Tier 1000 (Mjölnir-Null Singularity)**: Overcharging the depleted-uranium core, bring the hammer down with the crushing gravitational weight of a collapsing star.

### Field Trapping
- **Tier 50 (Hair-Trigger Rigging)**: Rapid deployment techniques allow setting mechanical snares, anchors, and tripwires in seconds.
- **Tier 100 (Serrated Deadfall Snare)**: Rig a spring-loaded carbon-line snare armed with micro-serrated barbs and weighted tension pins across a transit path.
- **Tier 250 (Pheromone Baiting & Marrow-Grafting)**: Imbue trap triggers with synthesized marrow mash and biological attractants to manipulate monster aggro scripts.
- **Tier 500 (Micro-Capacitor Overload Trap)**: Splice a corroded micro-capacitor and copper wiring into a tension net, discharging high-voltage EMP lightning when tripped.
- **Tier 750 (Tactical Ambush Mastery)**: Seamlessly integrate multiple trap lines into overlapping crossfire kill-boxes.
- **Tier 1000 (Cardinal Net: Spatial Quarantine)**: Project a hard-light spatial quarantine grid anchored by anchor pins, sealing an entire battlefield node from the Cardinal network.

### Cartography
- **Tier 50 (Topographic Awareness)**: Your eye parses elevation gradients, contour lines, and natural choke points with effortless clarity.
- **Tier 100 (Sub-Level Nav-Mesh Bypass)**: Analyze glitching geometry to identify decommissioned maintenance ducts, old subway shafts, and unindexed paths.
- **Tier 250 (Geodetic Triangulation)**: Cross-reference satellite telemetry, radio pings, and ancient colonial survey markers to locate valuable anomalies.
- **Tier 500 (Chorographer's Sight: Ley-Line Mapping)**: Project an arcane aetheric compass overlay that traces subterranean mana-currents and firewall boundaries.
- **Tier 750 (Macro-Territory Cartogram)**: Read macro-geopolitical faction shifts, troop movements, and global glitch-horde migrations before they strike.
- **Tier 1000 (Architect's Omniscient Overlay)**: Interface directly with Cardinal's root coordinate engine, rendering the entire world map in transparent wireframe.

## 3. Dual-Tech Party Combos

- **Runic Axe Storm** (`runic_axe_storm`): {"id": "runic_axe_storm", "name": "Runic Axe Storm", "partners": ["Banki", "Ren"], "req_affinity": 50, "desc": "Banki executes a furious whirlwind cleave while Ren fires lightning runes directly into the axe head, unleashing a 360\u00b0 chain-lightning cyclone.", "damage": "4d10+8 Slashing + 2d8 Lightning AOE", "effect": "Hits all surrounding enemies, deals 4d10+8 Slashing + 2d8 Lightning DMG and inflicts Stagger on secondary targets.", "log_tag": "[DUAL-TECH: BANKI + REN -> RUNIC AXE STORM]"}
- **Titan's Anvil Shockwave** (`titans_anvil_shockwave`): {"id": "titans_anvil_shockwave", "name": "Titan's Anvil Shockwave", "partners": ["Banki", "Torvald"], "req_affinity": 50, "desc": "Torvald plants his adamant tower shield while Banki strikes the shield's runic center with his Trench Hammer, detonating a sonic kinetic shockwave.", "damage": "3d12+10 Force DMG", "effect": "Inflicts 3d12+10 Force DMG and shatters 60 Break Gauge points (guaranteed boss STAGGER).", "log_tag": "[DUAL-TECH: BANKI + TORVALD -> TITAN'S ANVIL SHOCKWAVE]"}
- **Spellblade Vortex** (`spellblade_vortex`): {"id": "spellblade_vortex", "name": "Spellblade Vortex", "partners": ["Banki", "Elora"], "req_affinity": 50, "desc": "Banki hurls his bearded axe into Elora's dimensional spatial rift; the blade ricochets between 3 targets enveloped in cold aether-flames.", "damage": "3d8 Slashing + 3d8 Frost-Burn to 3 targets", "effect": "Cleaves through 3 enemies bypassing 50% Armor Class.", "log_tag": "[DUAL-TECH: BANKI + ELORA -> SPELLBLADE VORTEX]"}
- **Shadow-Flank Execution** (`shadow_flank_execution`): {"id": "shadow_flank_execution", "name": "Shadow-Flank Execution", "partners": ["Banki", "Kibs"], "req_affinity": 50, "desc": "Kibs throws an aetheric flash-smoke bomb blinding the primary foe while Banki steps through the blind spot for a guaranteed decapitation strike.", "damage": "5d10+12 Critical Slashing DMG", "effect": "Guaranteed critical hit dealing 5d10+12 Slashing DMG and severe Bleed (10 DMG/turn).", "log_tag": "[DUAL-TECH: BANKI + KIBS -> SHADOW-FLANK EXECUTION]"}
- **Valkyrie's Sky-Cleave** (`valkyries_wrath`): {"id": "valkyries_wrath", "name": "Valkyrie's Sky-Cleave", "partners": ["Banki", "Valeria"], "req_affinity": 50, "desc": "Valeria lifts Banki into an aerial trajectory before hurling him downward in a terminal-velocity dive-bomb while unleashing radiant spear salvos.", "damage": "4d10+10 Radiant Slashing + 2d8 Piercing AOE", "effect": "Inflicts 4d10+10 Radiant Slashing DMG to primary target and 2d8 Piercing to surrounding foes with guaranteed Knockdown.", "log_tag": "[DUAL-TECH: BANKI + VALERIA -> VALKYRIE'S SKY-CLEAVE]"}
- **Grave-Lord Soul Reaver** (`grave_lord_cleave`): {"id": "grave_lord_cleave", "name": "Grave-Lord Soul Reaver", "partners": ["Banki", "Morrigan"], "req_affinity": 50, "desc": "Morrigan binds the enemy's life-force in necrotic soul-chains as Banki cleaves through the tether, detonating a necrotic siphon that leeches vital essence.", "damage": "4d10+8 Slashing + 3d8 Necrotic DMG", "effect": "Deals 4d10+8 Slashing + 3d8 Necrotic DMG; heals Banki and Morrigan for 50% of necrotic damage dealt.", "log_tag": "[DUAL-TECH: BANKI + MORRIGAN -> GRAVE-LORD SOUL REAVER]"}
- **Seismic Cataclysm** (`seismic_cataclysm`): {"id": "seismic_cataclysm", "name": "Seismic Cataclysm", "partners": ["Banki", "Garrick"], "req_affinity": 50, "desc": "Garrick channels ki into a seismic earth-breaker slam while Banki drives his Trench Hammer into the fractured faultline, launching explosive tectonic debris.", "damage": "5d10+12 Bludgeoning Force DMG", "effect": "Shatters 75 Break Gauge points (guaranteed boss STUN), dealing 5d10+12 Bludgeoning Force DMG in a 20ft radius.", "log_tag": "[DUAL-TECH: BANKI + GARRICK -> SEISMIC CATACLYSM]"}
- **Cyclone Arrow Tempest** (`cyclone_arrow_storm`): {"id": "cyclone_arrow_storm", "name": "Cyclone Arrow Tempest", "partners": ["Banki", "Sariel"], "req_affinity": 50, "desc": "Sariel fires a spiral gale-force volley pinning the targets to the earth while Banki charges through the vortex with twin-axe whirlwind cleaves.", "damage": "3d10+6 Slashing + 4d6 Wind-Piercing DMG", "effect": "Pins targets for 1 turn (Immobilized) and deals 3d10+6 Slashing + 4d6 Piercing DMG across the line.", "log_tag": "[DUAL-TECH: BANKI + SARIEL -> CYCLONE ARROW TEMPEST]"}
- **Dawn-Breaker Radiant Smite** (`dawn_breaker_smite`): {"id": "dawn_breaker_smite", "name": "Dawn-Breaker Radiant Smite", "partners": ["Banki", "Kaelen"], "req_affinity": 50, "desc": "Brother Kaelen invokes the Sol-Altar's zenith light, wrapping Banki's weapons in blinding solar fire as Banki delivers an overhead solar execution strike.", "damage": "4d10+10 Radiant/Fire DMG", "effect": "Deals 4d10+10 Radiant DMG (+4d10 bonus vs Undead/Corrupted), Blinds targets for 2 turns, and restores 25 HP to all allies.", "log_tag": "[DUAL-TECH: BANKI + KAELEN -> DAWN-BREAKER RADIANT SMITE]"}
- **Volt-Tempest Plasma Detonation** (`volt_tempest_detonation`): {"id": "volt_tempest_detonation", "name": "Volt-Tempest Plasma Detonation", "partners": ["Banki", "Zedd"], "req_affinity": 50, "desc": "Zedd hurls a high-voltage plasma sphere into the target's center-mass, which Banki violently detonates with a thunderous kinetic hammer impact.", "damage": "3d10+8 Bludgeoning + 4d8 Chain-Lightning DMG", "effect": "Detonates in a chain-lightning shockwave leaping to up to 4 nearby hostiles, inflicting Stunned on a failed DC 15 CON save.", "log_tag": "[DUAL-TECH: BANKI + ZEDD -> VOLT-TEMPEST PLASMA DETONATION]"}
- **Valkyrie Battle Anthem** (`valkyrie_war_chorus`): {"id": "valkyrie_war_chorus", "name": "Valkyrie Battle Anthem", "partners": ["Banki", "Daphne"], "req_affinity": 50, "desc": "Daphne weaves a resounding skaldic war-chant that synchronizes heartbeats and multiplies adrenaline, propelling Banki into a hyper-accelerated strike frenzy.", "damage": "6d8+12 Sonic-Empowered Slashing DMG", "effect": "Grants Banki +2 extra attacks this turn, deals 6d8+12 Sonic Slashing DMG, and grants all party members +4 Attack and +15 Temp HP for 3 turns.", "log_tag": "[DUAL-TECH: BANKI + DAPHNE -> VALKYRIE BATTLE ANTHEM]"}
- **Blood-Twin Berserker Cleave** (`blood_twin_cleave`): {"id": "blood_twin_cleave", "name": "Blood-Twin Berserker Cleave", "partners": ["Banki", "Rok"], "req_affinity": 50, "desc": "Banki and Rok roar in feral unison, executing synchronised spinning greataxe and broadaxe cleaves that tear through armor like parchment.", "damage": "6d12+16 Brutal Slashing DMG", "effect": "Bypasses 100% of enemy Damage Reduction, inflicts 6d12+16 Slashing DMG and severe Arterial Bleed (15 DMG/turn for 3 turns).", "log_tag": "[DUAL-TECH: BANKI + ROK -> BLOOD-TWIN BERSERKER CLEAVE]"}
- **Temporal Stasis Shatter** (`temporal_shatter_strike`): {"id": "temporal_shatter_strike", "name": "Temporal Stasis Shatter", "partners": ["Banki", "Lyra"], "req_affinity": 50, "desc": "Lyra locks the enemy within a 3-second localized time-stop capsule; Banki unleashes four devastating attacks that detonate simultaneously the instant time resumes.", "damage": "8d8+16 Chrono-Kinetic Force DMG", "effect": "Enemy is helpless during setup; deals 8d8+16 Force DMG and resets enemy initiative/turn order to the very bottom.", "log_tag": "[DUAL-TECH: BANKI + LYRA -> TEMPORAL STASIS SHATTER]"}
- **Foundry Hydraulic Overdrive** (`foundry_forge_smash`): {"id": "foundry_forge_smash", "name": "Foundry Hydraulic Overdrive", "partners": ["Banki", "Titus"], "req_affinity": 50, "desc": "Titus locks the target in steam-powered pneumatic vise-clamps while Banki strikes Titus's chest-anvil, driving a superheated hydraulic piston through the target.", "damage": "5d10+14 Fire & Bludgeoning DMG", "effect": "Deals 5d10+14 Fire/Bludgeoning DMG, permanently shreds target Armor Class by -4, and leaves the foe Prone.", "log_tag": "[DUAL-TECH: BANKI + TITUS -> FOUNDRY HYDRAULIC OVERDRIVE]"}
- **Apex Pack-Hunt Ambush** (`pack_hunt_ambush`): {"id": "pack_hunt_ambush", "name": "Apex Pack-Hunt Ambush", "partners": ["Banki", "Nyssa"], "req_affinity": 50, "desc": "Nyssa takes Dire-Wolf aspect to drag the target down by the throat while Banki closes the pincer from the blindside with a merciless downward execution stroke.", "damage": "4d10+10 Slashing + 3d8 Beast-Tear Piercing DMG", "effect": "Knocks target Prone, inflicts Crippled status (-50% movement speed), and deals 4d10+10 Slashing + 3d8 Piercing DMG.", "log_tag": "[DUAL-TECH: BANKI + NYSSA -> APEX PACK-HUNT AMBUSH]"}
- **Void-Singularity Cleave** (`void_abyss_cleave`): {"id": "void_abyss_cleave", "name": "Void-Singularity Cleave", "partners": ["Banki", "Malakor"], "req_affinity": 50, "desc": "Malakor rips open an eldritch void anomaly that collapses space and draws all surrounding foes into a singular vortex, right into Banki's full-force whirlwind sweep.", "damage": "5d8 Slashing + 4d8 Void-Cold DMG (AOE)", "effect": "Pulls all enemies in 30ft into melee range, deals 5d8 Slashing + 4d8 Void DMG, and inflicts -3 to all enemy attack rolls for 2 turns.", "log_tag": "[DUAL-TECH: BANKI + MALAKOR -> VOID-SINGULARITY CLEAVE]"}
- **Corrosive Slag Shatter** (`corrosive_shatter_bomb`): {"id": "corrosive_shatter_bomb", "name": "Corrosive Slag Shatter", "partners": ["Banki", "Thorne"], "req_affinity": 50, "desc": "Dr. Thorne hurls a concentrated vial of alchemical vitriol onto the enemy's armor plate, followed instantly by Banki's concussive hammer strike that shatters the brittle slag.", "damage": "3d10+8 Bludgeoning + 4d6 Acid DMG", "effect": "Completely dissolves enemy Damage Reduction (DR reduced to 0), deals 3d10+8 Bludgeoning + 4d6 Acid DMG, and leaves a lingering acid pool.", "log_tag": "[DUAL-TECH: BANKI + THORNE -> CORROSIVE SLAG SHATTER]"}
- **Grand Inquisitor's Execution** (`inquisition_execution`): {"id": "inquisition_execution", "name": "Grand Inquisitor's Execution", "partners": ["Banki", "Teresa"], "req_affinity": 50, "desc": "Sister Teresa pins the condemned hostile to the earth with a consecrated heavy silver stake and recites the final rite while Banki delivers a thunderous decapitation blow.", "damage": "6d10+15 Holy Slashing DMG", "effect": "Instant execution threshold against foes below 25% HP; otherwise deals 6d10+15 Holy Slashing DMG and permanently prevents resurrection or undead reanimation.", "log_tag": "[DUAL-TECH: BANKI + TERESA -> GRAND INQUISITOR'S EXECUTION]"}

## 4. Regional Geopolitical Factions

### vanguard_coalition
```json
{
  "id": "vanguard_coalition",
  "name": "The Vanguard Coalition",
  "leader": "Commander Kaelen Vance",
  "headquarters": "Washington Fortress Bastion",
  "icon": "\u2694\ufe0f",
  "description": "Dedicated frontline raid coalition committed to breaking the regional labyrinth bosses and ascending the regional spires.",
  "perks": {
    "25": "+10% bonus damage against Dungeon and Sector Bosses; Coalition Quartermaster access.",
    "50": "+15% Maximum HP and military requisition grade armor."
  }
}
```

### iron_syndicate
```json
{
  "id": "iron_syndicate",
  "name": "The Iron Syndicate",
  "leader": "Guildmaster Silas Bron",
  "headquarters": "Oxford Forge & Smelting Vaults",
  "icon": "\u2692\ufe0f",
  "description": "Mercantile crafting cartel that monopolizes regional raw materials, forge leylines, and trade routes across Warren County.",
  "perks": {
    "25": "15% wholesale discount on all store purchases and repair services.",
    "50": "Masterwork forging blueprints and priority auction trade access."
  }
}
```

### blood_shroud
```json
{
  "id": "blood_shroud",
  "name": "The Blood Shroud",
  "leader": "The Pale Whisper",
  "headquarters": "Scotts Mountain Glitch-Vaults",
  "icon": "\ud83e\ude78",
  "description": "Secretive outlaw guild operating in dark sectors (Laughing Coffin analog); orchestrates ambushes and black market trade.",
  "perks": {
    "25": "Immunity to wilderness outlaw ambushes; access to illicit poison blueprints.",
    "50": "Black-market teleporters and outlaw contract bounties."
  }
}
```
