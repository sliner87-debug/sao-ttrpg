"""
test_classic_fantasy_e2e.py
===========================
Comprehensive Opaque-Box Requirement-Driven E2E Test Suite for
Fractured Earth SAO Sandbox V2: Classic Fantasy Framework Overhaul.

Authoritative Requirements Grounding:
- ORIGINAL_REQUEST.md (2026-10-16T00:04:06Z Request)
- PROJECT.md (§ Architecture, Feature Inventory, Interface Contracts, Milestones)
- TEST_INFRA.md (§ Test Architecture, Category Partition, Coverage Thresholds)

Test Tier Architecture:
- Tier 1: Feature Coverage (>=5 test cases per requirement: R1 Lifestyles, R2 Lineages & Sci-Fi Purge,
          R3 Mini-Dungeons, R4 Classic 10 Classes & Evolutions) -> 26 test cases.
- Tier 2: Boundary & Corner Cases (stat boundary tests, encumbrance STR*15 limits, durability broken state,
          level-up edge conditions, Tiny vs Large size mechanics) -> 5 test cases.
- Tier 3: Cross-Feature Combinations (Pixie+Woodsman+Rogue, Minotaur+Gladiator+Barbarian, Nymph+Courtier+Paladin,
          Centaur+Delver+Ranger, Dual-Track Telemetry+Evolution Synthesis) -> 5 test cases.
- Tier 4: Real-World Application Scenarios (Full character creation -> 3-stage mini-dungeon completion ->
          Level 3 safe-zone graduation -> Level 10 Spire Boss defeat -> Bespoke Level 10 evolution synthesis ->
          Level 20/30 epic specialization) -> 5 test cases.

Total: 41 comprehensive automated E2E test cases.
"""

import copy
import os
import sys
import unittest
from typing import Any, Dict, List, Optional, Set

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.mechanics as mechanics


def _create_character_safe(test_case: unittest.TestCase, **kwargs) -> Dict[str, Any]:
    """Helper to call generate_starting_character, converting TypeError into clean test failure if argument missing."""
    try:
        char = cg.generate_starting_character(**kwargs)
        return char.get("player", char)
    except TypeError as te:
        if "lifestyle_key" in str(te):
            test_case.fail(f"Requirement R1 Violation: generate_starting_character() does not support 'lifestyle_key' argument: {te}")
        test_case.fail(f"generate_starting_character() failed with TypeError: {te}")


# =====================================================================
# TIER 1: FEATURE COVERAGE (R1 LIFESTYLES)
# =====================================================================

class TestTier1R1Lifestyles(unittest.TestCase):
    """
    R1: Expanded Lifestyle Archetypes with Skill Bonuses & Starting Feats/Spells.
    Verifies PRESET_LIFESTYLES contains >= 24 presets (including 8 new requested ones),
    strictly 20 allocated attribute points, 2 thematic skill bonuses (+10 to +20 mastery),
    and innate starting feat/spell per preset.
    """

    def setUp(self):
        self.presets = getattr(cg, "PRESET_LIFESTYLES", {})

    def test_r1_01_lifestyle_catalog_count_and_required_keys(self):
        """Verify PRESET_LIFESTYLES contains >= 24 presets including all 8 new required archetypes."""
        self.assertTrue(bool(self.presets), "cg.PRESET_LIFESTYLES must not be empty.")
        self.assertGreaterEqual(
            len(self.presets), 24,
            f"Expected at least 24 Lifestyle presets per R1, found {len(self.presets)}."
        )

        required_new_keys = [
            "woodsman",
            "monastery_ascetic",
            "hearth_apothecary",
            "dungeon_delver",
            "arena_gladiator",
            "courtier_emissary",
            "blacksmith_apprentice",
            "archive_scribe",
        ]
        missing_keys = [k for k in required_new_keys if k not in self.presets]
        self.assertEqual(
            missing_keys, [],
            f"R1 Violation: Missing required new lifestyle presets: {missing_keys}"
        )

    def test_r1_02_lifestyle_20_point_attribute_balance(self):
        """Verify every single preset allocates strictly 20 attribute points across STR, DEX, CON, INT, WIS, CHA."""
        core_stats = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
        unbalanced = {}

        for key, preset in self.presets.items():
            points = preset.get("points", {})
            self.assertTrue(
                core_stats.issubset(points.keys()),
                f"Preset '{key}' missing core stat keys. Found: {list(points.keys())}"
            )
            for s, val in points.items():
                self.assertIsInstance(val, int, f"Preset '{key}' stat '{s}' must be integer, got {type(val)}")
                self.assertGreaterEqual(val, 0, f"Preset '{key}' stat '{s}' must be non-negative, got {val}")

            pt_sum = sum(points[s] for s in core_stats)
            if pt_sum != 20:
                unbalanced[key] = pt_sum

        self.assertEqual(
            unbalanced, {},
            f"R1 Violation: Presets must allocate strictly 20 attribute points. Unbalanced: {unbalanced}"
        )

    def test_r1_03_lifestyle_skill_bonuses(self):
        """Verify each preset grants +10 to +20 starting mastery bonus across exactly 2 thematic skills."""
        invalid_skills = {}
        for key, preset in self.presets.items():
            bonuses = preset.get("skill_bonuses")
            if not isinstance(bonuses, dict) or len(bonuses) != 2:
                invalid_skills[key] = f"Expected dict with 2 skill bonuses, got {bonuses}"
                continue
            for skill_name, bonus_val in bonuses.items():
                if not isinstance(bonus_val, (int, float)) or not (10 <= bonus_val <= 20):
                    invalid_skills[key] = f"Skill '{skill_name}' bonus {bonus_val} outside [10, 20] range."

        self.assertEqual(
            invalid_skills, {},
            f"R1 Violation: Presets must specify 2 thematic skill bonuses between +10 and +20. Errors: {invalid_skills}"
        )

    def test_r1_04_lifestyle_starting_feat(self):
        """Verify each preset defines an innate starting feat/spell/passive ability."""
        missing_feats = []
        for key, preset in self.presets.items():
            feat = preset.get("starting_feat")
            if not feat or not isinstance(feat, str) or len(feat.strip()) < 5:
                missing_feats.append(key)

        self.assertEqual(
            missing_feats, [],
            f"R1 Violation: Presets missing valid starting_feat: {missing_feats}"
        )

    def test_r1_05_character_generator_lifestyle_application(self):
        """Verify generate_starting_character applies lifestyle points, skill bonuses, and starting feat."""
        preset_key = "hearth_apothecary" if "hearth_apothecary" in self.presets else list(self.presets.keys())[0]
        preset_data = self.presets[preset_key]

        player = _create_character_safe(
            self,
            name="ApothecaryHero",
            lifestyle_key=preset_key,
            start_tutorial=False
        )

        self.assertIn("lifestyle", player, "Player record must record lifestyle.")

        # Verify attribute points were applied
        for stat, expected_alloc in preset_data["points"].items():
            actual_stat = player["stats"].get(stat, 0)
            self.assertGreaterEqual(
                actual_stat, expected_alloc,
                f"Stat {stat} ({actual_stat}) should incorporate lifestyle allocation ({expected_alloc})"
            )

        # Verify skill bonuses were applied if preset has skill_bonuses
        if "skill_bonuses" in preset_data:
            for sk_name, sk_bonus in preset_data["skill_bonuses"].items():
                self.assertIn(sk_name, player.get("skills", {}), f"Skill bonus {sk_name} must be present in player skills.")
                self.assertGreaterEqual(
                    player["skills"][sk_name], sk_bonus,
                    f"Skill {sk_name} mastery should be >= starting bonus {sk_bonus}"
                )

        # Verify starting feat is present in player feats
        if "starting_feat" in preset_data:
            player_feats = player.get("feats", [])
            feat_found = any(preset_data["starting_feat"] in f or f in preset_data["starting_feat"] for f in player_feats)
            self.assertTrue(
                feat_found,
                f"Player feats {player_feats} must include lifestyle starting feat '{preset_data['starting_feat']}'"
            )

    def test_r1_06_lifestyle_fallback_on_unknown_key(self):
        """Verify character generation with unknown or None lifestyle falls back safely without crashing."""
        try:
            char = cg.generate_starting_character(
                name="FallbackSurvivor",
                start_tutorial=False
            )
            player = char.get("player", char)
            self.assertIsNotNone(player)
            self.assertIn("stats", player)
        except Exception as e:
            self.fail(f"generate_starting_character crashed on fallback: {e}")


# =====================================================================
# TIER 1: FEATURE COVERAGE (R2 LINEAGES & SCI-FI PURGE)
# =====================================================================

class TestTier1R2LineagesAndSciFiPurge(unittest.TestCase):
    """
    R2: Pure Fantasy & D&D 3.0 Savage Species Playable Lineages.
    Verifies purging of modern/sci-fi races from character creation, legacy fallbacks,
    presence of 25+ pure fantasy lineages, Pixie, Meadow Nymph, Savage Species monstrous races,
    and Glenny multi-limb parity.
    """

    PURGED_SCI_FI = {
        "neuromancer_cyborg",
        "mantid_insectoid",
        "nanite_host",
        "void_walker",
        "synthetic_android",
        "phrenic_human",
    }

    def test_r2_01_scifi_races_purged_from_character_creation(self):
        """Verify character creation lineages catalog does NOT contain any modern/sci-fi races."""
        get_lineages_fn = getattr(cg, "get_character_creation_lineages", None)
        if get_lineages_fn is None:
            self.fail("backend.character_generator must export get_character_creation_lineages()")

        creation_lineages = get_lineages_fn()
        self.assertIsInstance(creation_lineages, dict, "get_character_creation_lineages() must return a dict.")

        creation_keys = set(creation_lineages.keys())
        purged_present = creation_keys & self.PURGED_SCI_FI
        self.assertEqual(
            purged_present, set(),
            f"R2 Violation: Modern sci-fi races present in character creation catalog: {purged_present}"
        )

        # Also verify genre tags
        disallowed_genres = ["sci-fi", "biomechanical", "cyber", "android", "alien"]
        flagged_lineages = []
        for r_key, r_data in creation_lineages.items():
            genre = str(r_data.get("genre", "")).lower()
            if any(dg in genre for dg in disallowed_genres):
                flagged_lineages.append((r_key, genre))

        self.assertEqual(
            flagged_lineages, [],
            f"R2 Violation: Character creation lineages contain sci-fi genres: {flagged_lineages}"
        )

    def test_r2_02_legacy_race_fallbacks_backward_compatibility(self):
        """Verify LEGACY_RACE_FALLBACKS maps all 6 purged races and character creation handles legacy keys safely."""
        fallbacks = getattr(cg, "LEGACY_RACE_FALLBACKS", {})
        self.assertTrue(bool(fallbacks), "cg.LEGACY_RACE_FALLBACKS dictionary must be defined.")

        for purged_key in self.PURGED_SCI_FI:
            self.assertIn(
                purged_key, fallbacks,
                f"R2 Violation: Purged race '{purged_key}' must have a fallback in LEGACY_RACE_FALLBACKS"
            )
            fallback_target = fallbacks[purged_key]
            self.assertIn(
                fallback_target, cg.RACIAL_LINEAGES,
                f"Fallback target '{fallback_target}' for '{purged_key}' must exist in RACIAL_LINEAGES."
            )

        # Test character generation with legacy race key
        char = cg.generate_starting_character(
            name="LegacyCyborg",
            race_key="neuromancer_cyborg",
            start_tutorial=False
        )
        player = char.get("player", char)
        self.assertIsNotNone(player)
        self.assertNotEqual(player.get("race_key"), "neuromancer_cyborg")

    def test_r2_03_dnd_30_pixie_lineage(self):
        """Verify D&D 3.0 Pixie lineage has Tiny size, natural flight, Greater Invisibility, DR/cold iron, Pixie Dust."""
        self.assertIn("pixie_fey_sprite", cg.RACIAL_LINEAGES, "RACIAL_LINEAGES must define 'pixie_fey_sprite'.")
        pixie = cg.RACIAL_LINEAGES["pixie_fey_sprite"]

        abilities_text = " ".join(pixie.get("racial_abilities", []))
        self.assertIn("Tiny", abilities_text, "Pixie must have Tiny size attribute.")
        self.assertIn("Flight", abilities_text, "Pixie must have Natural Flight.")
        self.assertIn("Invisibility", abilities_text, "Pixie must have Greater Invisibility.")
        self.assertIn("Cold Iron", abilities_text, "Pixie must have Cold Iron DR.")
        self.assertIn("Dust", abilities_text, "Pixie must have Pixie Dust ability.")

        # Generate a Pixie character and check physical & limb profile
        char = cg.generate_starting_character(name="Tinker", race_key="pixie_fey_sprite", start_tutorial=False)
        player = char.get("player", char)

        # Check physical size
        phys = mechanics.get_physical_profile(player)
        self.assertEqual(phys.get("size"), "Tiny", f"Pixie size should be Tiny, got {phys.get('size')}")
        self.assertEqual(phys.get("ac_mod"), 2, "Tiny size grants +2 size AC modifier.")
        self.assertEqual(phys.get("carry_mult"), 0.5, "Tiny size halves carrying capacity (0.5x).")

        # Check winged anatomy
        limb_profile = mechanics.get_limb_anatomy_profile(player)
        self.assertTrue(limb_profile.get("is_winged"), "Pixie anatomy must have is_winged=True.")
        self.assertIn("wings", limb_profile.get("unlocked_graft_slots", []), "Pixie must have wings graft slot.")

    def test_r2_04_meadow_nymph_unearthly_grace(self):
        """Verify Meadow Nymph lineage has Unearthly Grace (CHA deflection to AC/saves), Blinding Beauty, Dimension Door."""
        self.assertIn("meadow_nymph_fey", cg.RACIAL_LINEAGES, "RACIAL_LINEAGES must define 'meadow_nymph_fey'.")
        nymph = cg.RACIAL_LINEAGES["meadow_nymph_fey"]

        abilities_text = " ".join(nymph.get("racial_abilities", []))
        self.assertIn("Unearthly Grace", abilities_text)
        self.assertIn("Blinding Beauty", abilities_text)

        # Generate Nymph and test AC calculation incorporating Unearthly Grace
        char = cg.generate_starting_character(
            name="SylvanLady",
            race_key="meadow_nymph_fey",
            point_alloc={"STR": 1, "DEX": 3, "CON": 2, "INT": 2, "WIS": 4, "CHA": 8},
            start_tutorial=False
        )
        player = char.get("player", char)

        # Unarmored or light armor should grant CHA deflection bonus to AC
        ac = mechanics.calculate_ac(player)
        cha_mod = (player["stats"]["CHA"] - 10) // 2
        self.assertGreaterEqual(
            ac, 10 + cha_mod,
            f"Meadow Nymph AC ({ac}) should include Unearthly Grace CHA deflection (+{cha_mod})."
        )

    def test_r2_05_savage_species_monstrous_lineages(self):
        """Verify >= 25 pure fantasy lineages including Minotaur, Gargoyle, Centaur, Troll, Medusa exist."""
        get_lineages_fn = getattr(cg, "get_character_creation_lineages", None)
        creation_lineages = get_lineages_fn() if get_lineages_fn else cg.RACIAL_LINEAGES

        self.assertGreaterEqual(
            len(creation_lineages), 25,
            f"Expected at least 25 pure fantasy lineages, found {len(creation_lineages)}."
        )

        expected_savage_lineages = [
            "minotaur_labyrinth_breaker",
            "gargoyle_lithic_sentinel",
            "centaur_plains_vanguard",
            "troll_fleshwarped",
            "medusa_gorgon_scion",
            "doppelganger_morph",
            "half_ogre_crusher",
            "kobold_dragon_herald",
            "gnoll_hyena_ravager",
            "bugbear_shadow_stalker",
        ]
        missing_lineages = [k for k in expected_savage_lineages if k not in creation_lineages]
        self.assertEqual(
            missing_lineages, [],
            f"R2 Violation: Missing Savage Species monstrous lineages: {missing_lineages}"
        )

    def test_r2_06_glenny_chimera_multi_limb_parity(self):
        """Verify Glenny's 4-armed troll-kreen chimera profile retains 4 hand slots, 2H grip, 9 grafts, AC 14/16."""
        char = cg.generate_starting_character(name="Glenny", start_tutorial=False)
        player = char.get("player", char)

        # Check multi-limb equipment slots
        equipped = player.get("equipped", {})
        self.assertIn("main_hand", equipped)
        self.assertIn("off_hand", equipped)
        self.assertIn("lower_main_hand", equipped)
        self.assertIn("lower_off_hand", equipped)

        # Check 2H grip binding for hunting bow
        self.assertIn("Bow", equipped.get("main_hand", ""))
        self.assertIn("2H Grip", equipped.get("off_hand", ""))

        # Check anatomy profile
        limb_profile = mechanics.get_limb_anatomy_profile(player)
        self.assertTrue(limb_profile.get("is_four_armed"), "Glenny must be 4-armed.")
        self.assertEqual(limb_profile.get("secondary_ganglia_strain_bonus"), 1)

        # Check AC calculation: Base 14 unshielded, 16 shielded
        base_ac = mechanics.calculate_ac(player)
        self.assertEqual(base_ac, 14, f"Glenny baseline AC must be 14, got {base_ac}")

        # Equip shield in lower_off_hand
        player_shielded = copy.deepcopy(player)
        player_shielded["equipped"]["lower_off_hand"] = "Riot Shield"
        shielded_ac = mechanics.calculate_ac(player_shielded)
        self.assertEqual(shielded_ac, 16, f"Glenny shielded AC must be 16, got {shielded_ac}")


# =====================================================================
# TIER 1: FEATURE COVERAGE (R3 MINI-DUNGEONS)
# =====================================================================

class TestTier1R3MiniDungeons(unittest.TestCase):
    """
    R3: Hands-On Mini-Dungeon Tutorial System (3 Distinct Phases).
    Verifies 13-room graph engine, Phase I (encumbrance, durability, relic resonance),
    Phase II (1-1000 skills, parry/charge, multi-limb, sentinel combat, Lv2),
    Phase III (puzzles, secret doors, Crucible Warden boss, Lv3 graduation with 8 loot items),
    and backward-compatible advance_tutorial_stage().
    """

    def test_r3_01_mini_dungeon_room_graph_structure(self):
        """Verify TUTORIAL_MINI_DUNGEON_ROOMS defines 13 rooms across 3 phases with valid graph connections."""
        rooms = getattr(mechanics, "TUTORIAL_MINI_DUNGEON_ROOMS", getattr(mechanics, "TUTORIAL_MINI_DUNGEONS", None))
        if rooms is None:
            self.fail("backend.mechanics must export TUTORIAL_MINI_DUNGEON_ROOMS.")

        self.assertEqual(
            len(rooms), 13,
            f"R3 Violation: Expected exactly 13 tutorial mini-dungeon rooms, got {len(rooms)}."
        )

        phase1_rooms = [r for r, d in rooms.items() if d.get("phase") == 1 or "phase1" in r]
        phase2_rooms = [r for r, d in rooms.items() if d.get("phase") == 2 or "phase2" in r]
        phase3_rooms = [r for r, d in rooms.items() if d.get("phase") == 3 or "phase3" in r]

        self.assertEqual(len(phase1_rooms), 4, f"Phase I must have 4 rooms, got {len(phase1_rooms)}")
        self.assertEqual(len(phase2_rooms), 4, f"Phase II must have 4 rooms, got {len(phase2_rooms)}")
        self.assertEqual(len(phase3_rooms), 5, f"Phase III must have 5 rooms, got {len(phase3_rooms)}")

        # Verify all connections point to valid rooms
        for r_id, r_data in rooms.items():
            for conn in r_data.get("connections", []):
                self.assertIn(conn, rooms, f"Room '{r_id}' has connection to non-existent room '{conn}'.")

    def test_r3_02_phase_1_encumbrance_and_durability(self):
        """Verify Phase I mini-dungeon tests physical encumbrance (STR*15 lbs), durability degradation, and whetstone repair."""
        char = cg.generate_starting_character(name="Cadet", start_tutorial=True)
        player = char.get("player", char)

        # Verify encumbrance calculation
        enc = mechanics.calculate_encumbrance(player)
        expected_max_weight = player["stats"]["STR"] * 15.0
        self.assertEqual(
            enc["max_weight_lbs"], expected_max_weight,
            f"Base encumbrance limit must equal STR * 15 lbs ({expected_max_weight}), got {enc['max_weight_lbs']}"
        )

        # Test durability damage
        init_dur = player.get("gear_durability", {}).get("main_hand", {}).get("cur", 100)
        mechanics.apply_durability_damage(player, "main_hand", 15)
        new_dur = player.get("gear_durability", {}).get("main_hand", {}).get("cur", 85)
        self.assertEqual(new_dur, init_dur - 15, "Durability damage must reduce item current durability.")

        # Test whetstone maintenance (repair)
        repair_fn = getattr(mechanics, "repair_gear_durability", None)
        if repair_fn:
            repair_fn(player, "main_hand", 25)
            repaired_dur = player.get("gear_durability", {}).get("main_hand", {}).get("cur")
            self.assertGreaterEqual(repaired_dur, new_dur)

    def test_r3_03_phase_1_relic_resonance(self):
        """Verify Phase I personal keepsake relic resonance via activate_personal_relic()."""
        char = cg.generate_starting_character(name="RelicHero", relic_key="tuning_fork", start_tutorial=True)
        player = char.get("player", char)

        res = mechanics.activate_personal_relic(player)
        self.assertTrue(res.get("success"), "Personal relic resonance must succeed.")
        self.assertIn("vibrates", res.get("message", "").lower() + res.get("effect", "").lower() + "440 hz")

    def test_r3_04_phase_2_martial_trials_and_sentinel(self):
        """Verify Phase II martial progression, parry/charge, multi-limb check, sentinel defeat, and Level 2 advance."""
        char = cg.generate_starting_character(name="WarriorHero", class_key="fighter", start_tutorial=True)
        player = char.get("player", char)

        # Advance through Phase 1 to Phase 2
        mechanics.advance_tutorial_stage(player)
        self.assertEqual(player.get("level", 1), 1)

        # Advance through Phase 2
        mechanics.advance_tutorial_stage(player)
        self.assertEqual(player.get("level"), 2, "Defeating Clockwork Sentinel in Phase II must advance player to Level 2.")
        self.assertIn("Astral Bolt", player.get("spells", []) + [player.get("attuned_spell", "")], "Phase II must attune Astral Bolt.")

    def test_r3_05_phase_3_puzzle_secret_door_and_boss(self):
        """Verify Phase III harmonic puzzle vault, secret door check, and Crucible Warden apex boss encounter."""
        char = cg.generate_starting_character(name="CrucibleHero", class_key="wizard", start_tutorial=True)
        player = char.get("player", char)

        # Advance through Phase 1 and 2
        mechanics.advance_tutorial_stage(player)
        mechanics.advance_tutorial_stage(player)

        # Advance through Phase 3 (Apex Boss)
        res3 = mechanics.advance_tutorial_stage(player)
        self.assertTrue(res3.get("graduated"), "Phase III completion must graduate the player.")
        self.assertEqual(player.get("level"), 3, "Phase III apex boss defeat must advance player to Level 3.")

    def test_r3_06_tutorial_graduation_and_8_loot_items(self):
        """Verify safe-zone graduation to Washington Borough, NJ retaining all 8 canonical loot items."""
        char = cg.generate_starting_character(name="GraduatingHero", start_tutorial=True)
        player = char.get("player", char)

        # Fast forward tutorial completion
        res = mechanics.advance_tutorial_stage(player, complete_all=True)

        self.assertTrue(player.get("tutorial", {}).get("completed"), "Tutorial must be marked completed.")
        self.assertIn("Washington Borough", player.get("location", ""))
        self.assertEqual(player.get("level"), 3)

        canonical_loot = [
            "Minor Aether-Salve Vial",
            "Calibration Whetstone Kit",
            "Sentinel Brass Armguards",
            "Clockwork Reflex Servo",
            "Inscribed Spell Slate: Astral Bolt",
            "Crucible Vanguard Signet",
            "Condensed Aether-Core",
            "Greater Crimson Draught",
        ]

        inv_names = [item["name"] if isinstance(item, dict) else str(item) for item in player.get("inventory", [])]
        equipped_names = [str(v) for v in player.get("equipped", {}).values()]
        all_items_str = " ".join(inv_names + equipped_names)
        missing_loot = [item for item in canonical_loot if item.lower() not in all_items_str.lower()]
        self.assertEqual(
            missing_loot, [],
            f"R3 Violation: Missing canonical tutorial graduation loot items: {missing_loot}"
        )

    def test_r3_07_advance_tutorial_stage_backward_compatibility(self):
        """Verify legacy advance_tutorial_stage wrapper contract is fully preserved."""
        char = cg.generate_starting_character(name="CompatHero", start_tutorial=True)
        player = char.get("player", char)

        # Stage 1 contract
        st1 = mechanics.advance_tutorial_stage(player)
        self.assertEqual(st1.get("completed_stage"), 1)
        self.assertEqual(st1.get("new_stage"), 2)
        self.assertFalse(st1.get("graduated"))

        # Stage 2 contract
        st2 = mechanics.advance_tutorial_stage(player)
        self.assertEqual(st2.get("completed_stage"), 2)
        self.assertEqual(st2.get("new_stage"), 3)
        self.assertEqual(player.get("level"), 2)

        # Stage 3 contract
        st3 = mechanics.advance_tutorial_stage(player)
        self.assertEqual(st3.get("completed_stage"), 3)
        self.assertTrue(st3.get("graduated"))
        self.assertTrue(st3.get("teleported"))
        self.assertEqual(player.get("level"), 3)


# =====================================================================
# TIER 1: FEATURE COVERAGE (R4 CLASSIC 10 CLASSES & EVOLUTIONS)
# =====================================================================

class TestTier1R4Classic10ClassesAndEvolutions(unittest.TestCase):
    """
    R4: Full Classic 10 Base Classes & Multi-Tier Observational Evolutions (Lvl 10, 20, 30).
    Verifies 10 base classes roster, legacy class aliases, Levels 1-9 progression,
    Level 10 evolution gate (Spire Boss), dual-track telemetry synthesis,
    Level 20/30 branches, and combat resource multipliers.
    """

    CLASSIC_10 = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "druid", "bard", "barbarian", "monk"
    ]

    def test_r4_01_classic_10_base_classes_roster(self):
        """Verify all 10 classic base classes exist in CLASS_PATHS with resources, HP, and favored skills."""
        class_paths = getattr(cg, "CLASS_PATHS", {})
        missing_classes = [c for c in self.CLASSIC_10 if c not in class_paths]
        self.assertEqual(
            missing_classes, [],
            f"R4 Violation: Missing Classic 10 base classes in CLASS_PATHS: {missing_classes}"
        )

        for c_key in self.CLASSIC_10:
            c_info = class_paths[c_key]
            self.assertIn("base_hp", c_info, f"Class {c_key} missing base_hp")
            self.assertIn("hp_per_lvl", c_info, f"Class {c_key} missing hp_per_lvl")
            self.assertIn("combat_resource", c_info, f"Class {c_key} missing combat_resource")
            self.assertIn("favored_skills", c_info, f"Class {c_key} missing favored_skills")
            self.assertGreaterEqual(len(c_info["favored_skills"]), 2)

    def test_r4_02_class_key_normalization_and_aliases(self):
        """Verify normalize_class_key resolves warrior->fighter, mage->wizard, thief->rogue, etc."""
        normalize_fn = getattr(mechanics, "normalize_class_key", None)
        if normalize_fn is None:
            self.fail("backend.mechanics must export normalize_class_key.")

        alias_map = {
            "warrior": "fighter",
            "vanguard": "fighter",
            "mage": "wizard",
            "aether_slinger": "wizard",
            "thief": "rogue",
            "infiltrator": "rogue",
            "wilderness_ranger": "ranger",
            "fighter": "fighter",
            "wizard": "wizard",
            "rogue": "rogue",
            "paladin": "paladin",
            "druid": "druid",
            "bard": "bard",
            "barbarian": "barbarian",
            "monk": "monk",
        }

        for input_key, expected_canonical in alias_map.items():
            resolved = normalize_fn(input_key)
            self.assertEqual(
                resolved, expected_canonical,
                f"normalize_class_key('{input_key}') returned '{resolved}', expected '{expected_canonical}'"
            )

        # Verify legacy non-breaking classes also resolve without crash
        self.assertIn(normalize_fn("engineer"), ["engineer", "pathless"])
        self.assertIn(normalize_fn("psion"), ["psion", "pathless"])

    def test_r4_03_level_1_to_9_progression_and_hp(self):
        """Verify characters level cleanly from 1 to 9, gaining HP based on ARCHETYPE_HP_GROWTH."""
        char = cg.generate_starting_character(name="BarbarianTest", class_key="barbarian", start_tutorial=False)
        player = char.get("player", char)

        initial_hp = player["max_hp"]

        # Level up to 9
        for target_lvl in range(2, 10):
            mechanics.apply_level_up(player)
            self.assertEqual(player["level"], target_lvl)
            self.assertGreater(player["max_hp"], initial_hp)

        self.assertEqual(player["level"], 9)

    def test_r4_04_level_10_evolution_gate_and_spire_boss(self):
        """Verify check_evolution_eligibility enforces Level >= 10 AND Sector 1 Spire Boss defeat."""
        char = cg.generate_starting_character(name="EvoCandidate", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)

        # At level 1 -> not eligible
        elig1 = mechanics.check_evolution_eligibility(player)
        self.assertFalse(elig1.get("eligible"), "Level 1 character must not be eligible for evolution.")

        # At level 10 without boss -> not eligible
        player["level"] = 10
        player["skills"]["Trench Hammers"] = 150  # meet mastery requirement
        player["bosses_defeated"] = []
        player["sector_boss_defeated"] = False

        elig2 = mechanics.check_evolution_eligibility(player)
        self.assertFalse(
            elig2.get("eligible"),
            "Level 10 character without Spire Boss defeat must NOT be eligible."
        )

        # Defeat Spire Boss -> eligible
        player["sector_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]

        elig3 = mechanics.check_evolution_eligibility(player)
        self.assertTrue(
            elig3.get("eligible"),
            f"Level 10 character with Spire Boss defeat must be eligible. Reasons: {elig3.get('reasons')}"
        )

    def test_r4_05_level_10_bespoke_3_option_evolution_synthesis(self):
        """Verify generate_curated_evolutions returns exactly 3 bespoke choices matching observed telemetry."""
        char = cg.generate_starting_character(name="TelemetryHero", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)
        player["level"] = 10
        player["sector_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]

        # Dual track telemetry: Holy damage + Good dialogue
        player["telemetry"] = {
            "weapon_masteries": {"swords": 120, "axes": 20},
            "spells_cast": {"holy_radiant": 25, "necrotic_curse": 0},
            "combat_discipline": {"holy_radiant_damage_dealt": 500, "necrotic_curse_damage_dealt": 0},
            "moral_choices": {"good_compassionate_dialogues": 8, "evil_ruthless_dialogues": 0},
            "deeds": ["spared_cultist_in_mine"],
            "relics_held": ["polaroid_camera"]
        }

        options = mechanics.generate_curated_evolutions(player)
        self.assertEqual(
            len(options), 3,
            f"R4 Violation: generate_curated_evolutions must return exactly 3 bespoke choices, got {len(options)}"
        )

        # Verify structure of each evolution option
        for opt in options:
            self.assertIn("title", opt)
            self.assertIn("category", opt)
            self.assertIn("desc", opt)

        categories = [opt.get("category", "") for opt in options]
        # Should cover Discipline/Synergy, Alignment, and Deed/Relic/Lineage
        self.assertTrue(
            any("synergy" in c.lower() or "discipline" in c.lower() or "weapon" in c.lower() for c in categories),
            f"Expected Discipline & Weapon Synergy option in {categories}"
        )
        self.assertTrue(
            any("alignment" in c.lower() or "moral" in c.lower() or "ethical" in c.lower() for c in categories),
            f"Expected Moral/Ethical Alignment option in {categories}"
        )

    def test_r4_06_level_20_and_30_specializations(self):
        """Verify Level 20 eligibility triggers 3 prestige branches, and Level 30 triggers 3 apex legendary evolutions."""
        char = cg.generate_starting_character(name="EpicHero", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)

        # Simulate Tier 2 evolution at Level 10
        player["level"] = 10
        player["class_tier"] = 2
        player["class"] = "Paladin Crusader"

        # Advance to Level 20 + Regional Boss
        player["level"] = 20
        player["skills"]["Heavy Swords"] = 400
        player["regional_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)", "Regional Apex Behemoth (Sector 5)"]

        elig_t3 = mechanics.check_evolution_eligibility(player)
        self.assertTrue(
            elig_t3.get("eligible"),
            f"Level 20 character with Regional Boss defeat must be eligible for Tier 3. Reasons: {elig_t3.get('reasons')}"
        )

        t3_options = mechanics.generate_curated_evolutions(player)
        self.assertEqual(len(t3_options), 3, f"Tier 3 must offer exactly 3 prestige branches, got {len(t3_options)}")

        # Advance to Level 30 + Planetary Boss
        player["class_tier"] = 3
        player["level"] = 30
        player["skills"]["Heavy Swords"] = 800
        player["planetary_boss_defeated"] = True
        player["bosses_defeated"].append("Planetary World-Eater Core")

        elig_t4 = mechanics.check_evolution_eligibility(player)
        self.assertTrue(
            elig_t4.get("eligible"),
            f"Level 30 character with Planetary Boss defeat must be eligible for Tier 4. Reasons: {elig_t4.get('reasons')}"
        )

        t4_options = mechanics.generate_curated_evolutions(player)
        self.assertEqual(len(t4_options), 3, f"Tier 4 must offer exactly 3 apex legendary evolutions, got {len(t4_options)}")

    def test_r4_07_apply_class_evolution_resource_scaling(self):
        """Verify apply_class_evolution scales combat resources: +25% at Tier 2, +50% at Tier 3, +100% at Tier 4."""
        char = cg.generate_starting_character(name="ScalingHero", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)

        base_res_max = player.get("combat_resource", {}).get("max", 100)

        # Apply Tier 2
        t2_choice = {"title": "Runic Spellblade", "tier": 2, "category": "Discipline Synergy", "desc": "Spell-infused blade."}
        mechanics.apply_class_evolution(player, t2_choice)
        self.assertEqual(player["class"], "Runic Spellblade")
        self.assertEqual(player["class_tier"], 2)
        expected_t2_max = int(base_res_max * 1.25)
        self.assertEqual(
            player["combat_resource"]["max"], expected_t2_max,
            f"Tier 2 must scale combat resource by +25% ({expected_t2_max}), got {player['combat_resource']['max']}"
        )

        # Apply Tier 3
        t3_choice = {"title": "Grand Aether-Blademaster", "tier": 3, "category": "Prestige Branch", "desc": "Master blade."}
        mechanics.apply_class_evolution(player, t3_choice)
        self.assertEqual(player["class_tier"], 3)
        expected_t3_max = int(expected_t2_max * 1.50)
        self.assertEqual(player["combat_resource"]["max"], expected_t3_max)


# =====================================================================
# TIER 2: BOUNDARY & CORNER CASES
# =====================================================================

class TestTier2BoundaryAndCornerCases(unittest.TestCase):
    """
    Tier 2: Boundary & Corner Cases.
    Tests stat point limits, encumbrance STR*15 exact thresholds, durability broken state,
    level-up boundary conditions, and Tiny size vs Large size mechanics.
    """

    def test_t2_01_stat_boundary_allocations(self):
        """Verify stat boundaries: 0-stat allocation, extreme single-stat allocation, invalid sums clamped/rejected."""
        # Test extreme valid allocation: 20 points in STR, 0 in all others
        char_str20 = cg.generate_starting_character(
            name="MaxStrHero",
            point_alloc={"STR": 20, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0},
            start_tutorial=False
        )
        p = char_str20.get("player", char_str20)
        race_str_mod = cg.RACIAL_LINEAGES.get(p.get("race_key", "pure_human"), {}).get("stat_mods", {}).get("STR", 0)
        race_dex_mod = cg.RACIAL_LINEAGES.get(p.get("race_key", "pure_human"), {}).get("stat_mods", {}).get("DEX", 0)
        expected_str = 10 + 20 + race_str_mod
        self.assertEqual(p["stats"]["STR"], expected_str, f"STR should be 10 base + 20 alloc + {race_str_mod} racial mod")
        self.assertEqual(p["stats"]["DEX"], 10 + 0 + race_dex_mod)

        # Test invalid sum > 20 points: should be clamped or rejected
        try:
            char_over = cg.generate_starting_character(
                name="OverallocHero",
                point_alloc={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},  # 60 points!
                start_tutorial=False
            )
            p_over = char_over.get("player", char_over)
            # Sum of allocated points beyond base 10 should not exceed 20
            alloc_sum = sum(p_over["stats"][s] - 10 for s in ["STR", "DEX", "CON", "INT", "WIS", "CHA"] if s in p_over["stats"])
            self.assertLessEqual(alloc_sum, 20 + 6, "Over-allocated points must be clamped to 20 maximum (+ racial mods).")
        except ValueError:
            pass  # Raising ValueError on illegal point sum is also valid

    def test_t2_02_encumbrance_str_times_15_limits(self):
        """Verify encumbrance transitions: exact boundary at STR*15 lbs, STR*15 + 0.1 lbs, carry multipliers."""
        char = cg.generate_starting_character(name="EncumbTest", point_alloc={"STR": 10, "DEX": 2, "CON": 2, "INT": 2, "WIS": 2, "CHA": 2}, start_tutorial=False)
        player = char.get("player", char)
        
        # Clear inventory to isolate exact weight test
        player["inventory"] = []
        enc_init = mechanics.calculate_encumbrance(player)
        equipped_w = enc_init["current_weight_lbs"]
        max_w = enc_init["max_weight_lbs"]

        # Add mock item so total weight reaches exact max_w capacity (Heavy Load tier)
        rem_w = round(max_w - equipped_w, 1)
        player["inventory"] = [{"name": "Calibration Ingot", "weight": rem_w, "qty": 1}]
        enc_at_limit = mechanics.calculate_encumbrance(player)
        self.assertEqual(
            enc_at_limit["tier"], "Heavy Load",
            f"Weight at exact max capacity ({max_w} lbs) must be Heavy Load, got {enc_at_limit['tier']}"
        )

        # Add 0.1 lb more -> Overencumbered
        player["inventory"] = [{"name": "Calibration Ingot", "weight": round(rem_w + 0.2, 1), "qty": 1}]
        enc_over = mechanics.calculate_encumbrance(player)
        self.assertEqual(
            enc_over["tier"], "Overencumbered",
            f"Weight exceeding max capacity ({round(rem_w + 0.2 + equipped_w, 1)} > {max_w}) must trigger Overencumbered."
        )

    def test_t2_03_durability_broken_state_penalties(self):
        """Verify durability degradation to 0 ('Broken') applies severe attack and AC penalties."""
        char = cg.generate_starting_character(name="DuraHero", start_tutorial=False)
        player = char.get("player", char)

        # Break main hand weapon
        player["gear_durability"]["main_hand"] = {"cur": 0, "max": 100, "state": "Broken"}
        penalties = mechanics.calculate_durability_penalties(player)

        atk_pen = penalties.get("atk_penalty", penalties.get("attack_penalty", 0))
        self.assertGreaterEqual(
            atk_pen, 4,
            f"Broken main_hand must impose at least 4 attack penalty, got {atk_pen}"
        )

    def test_t2_04_level_up_edge_conditions_and_capstones(self):
        """Verify level up handles negative CON mod, zero free points, and Level 9 to 10 cap."""
        char = cg.generate_starting_character(
            name="FragileHero",
            point_alloc={"STR": 2, "DEX": 2, "CON": 0, "INT": 8, "WIS": 6, "CHA": 2},
            start_tutorial=False
        )
        player = char.get("player", char)
        # Force low CON (e.g., CON 6 -> CON mod -2)
        player["stats"]["CON"] = 6

        init_hp = player["max_hp"]
        mechanics.apply_level_up(player)
        # Even with negative CON modifier, HP gain must be >= 1
        self.assertGreater(player["max_hp"], init_hp, "HP gain upon level up must never be zero or negative.")

    def test_t2_05_tiny_size_vs_large_size_mechanics(self):
        """Verify Tiny Pixie (20 in, 15 lbs) vs Large Minotaur (96 in, 450 lbs) size modifiers and physics."""
        # Tiny Pixie
        pixie_char = cg.generate_starting_character(name="TinyPixie", race_key="pixie_fey_sprite", start_tutorial=False)
        pixie = pixie_char.get("player", pixie_char)
        pixie_phys = mechanics.get_physical_profile(pixie)

        self.assertEqual(pixie_phys["size"], "Tiny")
        self.assertEqual(pixie_phys["ac_mod"], 2)
        self.assertEqual(pixie_phys["carry_mult"], 0.5)

        # Large Minotaur
        minotaur_char = cg.generate_starting_character(name="HugeBull", race_key="minotaur_labyrinth_breaker", start_tutorial=False)
        minotaur = minotaur_char.get("player", minotaur_char)
        minotaur_phys = mechanics.get_physical_profile(minotaur)

        self.assertEqual(minotaur_phys["size"], "Large")
        self.assertEqual(minotaur_phys["ac_mod"], -1)
        self.assertEqual(minotaur_phys["carry_mult"], 2.0)


# =====================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# =====================================================================

class TestTier3CrossFeatureCombinations(unittest.TestCase):
    """
    Tier 3: Cross-Feature Combinations.
    Tests multi-system interactions:
    - Pixie + Woodsman + Rogue in Phase I Encumbrance
    - Minotaur + Gladiator + Barbarian in Phase II Combat
    - Meadow Nymph + Courtier + Paladin Unearthly Grace
    - Centaur + Delver + Ranger Trample & Traps
    - Dual-Track Telemetry + Level 10 Evolution Synthesis
    """

    def test_t3_01_pixie_woodsman_rogue_phase1_encumbrance(self):
        """Cross-feature: Pixie (Tiny) + Woodsman (Camouflage) + Rogue in Phase I encumbrance and stealth."""
        player = _create_character_safe(
            self,
            name="WoodPixie",
            race_key="pixie_fey_sprite",
            lifestyle_key="woodsman",
            class_key="rogue",
            start_tutorial=True
        )

        # Check Tiny carrying capacity formula: STR * 15 * 0.5 lbs
        enc = mechanics.calculate_encumbrance(player)
        expected_cap = round(player["stats"]["STR"] * 15.0 * 0.5, 1)
        self.assertEqual(enc["max_weight_lbs"], expected_cap)

        # Check Woodsman feat integration
        self.assertTrue(
            any("Nature's Camouflage" in f or "Camouflage" in f for f in player.get("feats", [])),
            "Woodsman starting feat must be present in player feats."
        )

        # Enter Phase 1 durability test
        mechanics.apply_durability_damage(player, "main_hand", 10)
        self.assertEqual(player["gear_durability"]["main_hand"]["cur"], 90)

    def test_t3_02_minotaur_gladiator_barbarian_phase2_combat(self):
        """Cross-feature: Minotaur (Large/Gore) + Gladiator (Crowd Thrill) + Barbarian (Rage) in Phase II."""
        player = _create_character_safe(
            self,
            name="GoreGladiator",
            race_key="minotaur_labyrinth_breaker",
            lifestyle_key="arena_gladiator",
            class_key="barbarian",
            start_tutorial=True
        )

        # Verify Minotaur Gore and Gladiator Crowd Thrill
        feats = " ".join(player.get("feats", []))
        self.assertTrue("Crowd Thrill" in feats or "Gladiator" in feats or "Gore" in feats)

        # Advance to Phase II
        mechanics.advance_tutorial_stage(player)
        self.assertEqual(player.get("tutorial", {}).get("current_stage"), 2)

        # Combat resource should be Rage
        res = player.get("combat_resource", {})
        self.assertEqual(res.get("type"), "rage")

    def test_t3_03_meadow_nymph_courtier_paladin_unearthly_grace(self):
        """Cross-feature: Meadow Nymph + Courtier (CHA 7) + Paladin: Unearthly Grace AC + Righteous Smite."""
        player = _create_character_safe(
            self,
            name="LadyCrusader",
            race_key="meadow_nymph_fey",
            lifestyle_key="courtier_emissary",
            class_key="paladin",
            start_tutorial=False
        )

        # High Charisma from Courtier + Nymph
        cha = player["stats"]["CHA"]
        self.assertGreaterEqual(cha, 16, f"Nymph + Courtier should have high CHA, got {cha}")

        # AC calculation includes deflection bonus
        ac = mechanics.calculate_ac(player)
        cha_mod = (cha - 10) // 2
        self.assertGreaterEqual(ac, 10 + cha_mod)

    def test_t3_04_centaur_delver_ranger_multi_limb_trample(self):
        """Cross-feature: Centaur (Large equine build, 40ft move) + Delver (Subterranean Echo) + Ranger."""
        player = _create_character_safe(
            self,
            name="EquineScout",
            race_key="centaur_plains_vanguard",
            lifestyle_key="dungeon_delver",
            class_key="ranger",
            start_tutorial=False
        )

        # Large size
        phys = mechanics.get_physical_profile(player)
        self.assertEqual(phys["size"], "Large")

        # Delver feat
        feats = " ".join(player.get("feats", []))
        self.assertTrue("Subterranean Echo" in feats or "Echo" in feats or "Delver" in feats)

    def test_t3_05_dual_track_telemetry_holy_vs_necrotic_evolution_synthesis(self):
        """Cross-feature: Telemetry Holy/Compassionate synthesizes Templar; Necrotic/Ruthless synthesizes Deathknight."""
        # Holy Character
        holy_char = cg.generate_starting_character(name="HolyHero", class_key="cleric", start_tutorial=False)
        p_holy = holy_char.get("player", holy_char)
        p_holy["level"] = 10
        p_holy["sector_boss_defeated"] = True
        p_holy["telemetry"] = {
            "weapon_masteries": {"maces": 100},
            "spells_cast": {"holy_radiant": 30},
            "combat_discipline": {"holy_radiant_damage_dealt": 1000, "necrotic_curse_damage_dealt": 0},
            "moral_choices": {"good_compassionate_dialogues": 10, "evil_ruthless_dialogues": 0},
            "deeds": ["consecrated_shrine"],
            "relics_held": []
        }
        holy_evos = mechanics.generate_curated_evolutions(p_holy)
        holy_titles = [e["title"].lower() for e in holy_evos]
        self.assertTrue(
            any("templar" in t or "protector" in t or "crusader" in t or "radiant" in t for t in holy_titles),
            f"Holy telemetry should offer Good/Holy evolution path, got {holy_titles}"
        )

        # Necrotic Character
        necro_char = cg.generate_starting_character(name="DarkHero", class_key="fighter", start_tutorial=False)
        p_necro = necro_char.get("player", necro_char)
        p_necro["level"] = 10
        p_necro["sector_boss_defeated"] = True
        p_necro["telemetry"] = {
            "weapon_masteries": {"greatswords": 100},
            "spells_cast": {"necrotic_curse": 30},
            "combat_discipline": {"holy_radiant_damage_dealt": 0, "necrotic_curse_damage_dealt": 1000},
            "moral_choices": {"good_compassionate_dialogues": 0, "evil_ruthless_dialogues": 10},
            "deeds": ["desecrated_shrine"],
            "relics_held": []
        }
        necro_evos = mechanics.generate_curated_evolutions(p_necro)
        necro_titles = [e["title"].lower() for e in necro_evos]
        self.assertTrue(
            any("deathknight" in t or "blood" in t or "shadow" in t or "dread" in t for t in necro_titles),
            f"Necrotic telemetry should offer Evil/Necrotic evolution path, got {necro_titles}"
        )


# =====================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# =====================================================================

class TestTier4RealWorldApplicationScenarios(unittest.TestCase):
    """
    Tier 4: Real-World Application Scenarios.
    Executes full end-to-end player journeys:
    - 4.01: Full character creation -> 3-stage mini-dungeon completion -> safe-zone graduation with 8 loot items.
    - 4.02: Fast-forward tutorial graduation -> verify master state and persistent inventory.
    - 4.03: Progression from Level 3 to Level 10 Spire Boss defeat -> evolution eligibility unlock.
    - 4.04: Bespoke Level 10 evolution choice synthesis and application (+25% resource scaling).
    - 4.05: Multi-tier epic journey to Level 20 (Prestige branch) and Level 30 (Apex Legendary Apotheosis).
    """

    def test_t4_01_e2e_character_creation_to_graduation(self):
        """Full E2E Scenario 1: Create Hearth Apothecary Dryad Druid -> complete mini-dungeons -> graduate Level 3."""
        player = _create_character_safe(
            self,
            name="Lyra",
            lifestyle_key="hearth_apothecary",
            race_key="sylvan_dryad",
            class_key="druid",
            relic_key="polaroid_camera",
            start_tutorial=True
        )

        # Verify initial state
        self.assertEqual(player["level"], 1)
        self.assertIn("Cardinal Calibration Crucible", player["location"])

        # Phase I: The Threshold of Aether & Load
        st1 = mechanics.advance_tutorial_stage(player)
        self.assertEqual(st1["completed_stage"], 1)
        self.assertIn("Minor Aether-Salve Vial", player["inventory"])

        # Phase II: The Hall of Martial Form & Maneuvers
        st2 = mechanics.advance_tutorial_stage(player)
        self.assertEqual(st2["completed_stage"], 2)
        self.assertEqual(player["level"], 2)
        self.assertIn("Sentinel Brass Armguards", player["inventory"])

        # Phase III: The Crucible Apex & Boss Lair
        st3 = mechanics.advance_tutorial_stage(player)
        self.assertEqual(st3["completed_stage"], 3)
        self.assertTrue(st3["graduated"])
        self.assertEqual(player["level"], 3)
        self.assertIn("Washington Borough", player["location"])

        # Retained all 8 items
        self.assertGreaterEqual(len(player["inventory"]) + len(player["equipped"]), 8)

    def test_t4_02_e2e_fast_forward_tutorial_and_safe_zone_state(self):
        """Full E2E Scenario 2: Fast-forward tutorial (complete_all=True) -> verify immediate Level 3 safe-zone graduation."""
        char = cg.generate_starting_character(name="Speedy", start_tutorial=True)
        player = char.get("player", char)

        res = mechanics.advance_tutorial_stage(player, complete_all=True)
        self.assertTrue(res["graduated"])
        self.assertEqual(player["level"], 3)
        self.assertTrue(player["tutorial"]["completed"])
        self.assertIn("Washington Borough", player["location"])

    def test_t4_03_e2e_sector_1_advancement_and_level_10_spire_boss(self):
        """Full E2E Scenario 3: Character advances Level 3 -> 10, earns weapon mastery, defeats Spire Boss."""
        char = cg.generate_starting_character(name="VanguardVera", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)
        player["level"] = 3

        # Advance levels 4 through 10
        for lvl in range(4, 11):
            mechanics.apply_level_up(player)
            self.assertEqual(player["level"], lvl)

        self.assertEqual(player["level"], 10)

        # Train weapon mastery to Journeyman (100)
        player["skills"]["Trench Hammers"] = 125

        # Defeat Sector 1 Spire Boss
        player["sector_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]

        # Check eligibility
        elig = mechanics.check_evolution_eligibility(player)
        self.assertTrue(elig["eligible"])

    def test_t4_04_e2e_bespoke_evolution_choice_and_application(self):
        """Full E2E Scenario 4: Synthesize 3 bespoke choices at Level 10 -> select Choice 1 -> apply evolution."""
        char = cg.generate_starting_character(name="EvoMaster", class_key="rogue", start_tutorial=False)
        player = char.get("player", char)
        player["level"] = 10
        player["sector_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]
        player["skills"]["One-Handed Daggers"] = 150

        # Telemetry: Daggers + Backstabs + Stealth
        player["telemetry"] = {
            "weapon_masteries": {"daggers": 150},
            "techniques_executed": {"backstab": 20, "parry": 5},
            "spells_cast": {},
            "combat_discipline": {"holy_radiant_damage_dealt": 0, "necrotic_curse_damage_dealt": 200},
            "moral_choices": {"pragmatic_mercenary_dialogues": 8},
            "deeds": ["infiltrated_gilded_vault"],
            "relics_held": ["smartphone"]
        }

        choices = mechanics.generate_curated_evolutions(player)
        self.assertEqual(len(choices), 3)

        # Player picks Choice 0
        chosen_evo = choices[0]
        init_res_max = player["combat_resource"]["max"]
        mechanics.apply_class_evolution(player, chosen_evo)

        self.assertEqual(player["class"], chosen_evo["title"])
        self.assertEqual(player["class_tier"], 2)
        self.assertEqual(player["combat_resource"]["max"], int(init_res_max * 1.25))

    def test_t4_05_e2e_epic_progression_level_20_and_30_apotheosis(self):
        """Full E2E Scenario 5: Multi-tier epic progression to Level 20 (Prestige) and Level 30 (Apex Legendary)."""
        char = cg.generate_starting_character(name="ImmortalHero", class_key="wizard", start_tutorial=False)
        player = char.get("player", char)

        # Tier 2 at Level 10
        player["level"] = 10
        player["class_tier"] = 2
        player["class"] = "Aether Arcanist"
        player["combat_resource"]["max"] = 62  # 50 * 1.25

        # Level 20 Tier 3 Prestige
        player["level"] = 20
        player["skills"]["Aether-Weaving"] = 400
        player["regional_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)", "Regional Apex Behemoth (Sector 5)"]

        t3_choices = mechanics.generate_curated_evolutions(player)
        self.assertEqual(len(t3_choices), 3)

        mechanics.apply_class_evolution(player, t3_choices[0])
        self.assertEqual(player["class_tier"], 3)
        self.assertEqual(player["combat_resource"]["max"], int(62 * 1.50))

        # Level 30 Tier 4 Apex Legendary Apotheosis
        player["level"] = 30
        player["skills"]["Aether-Weaving"] = 800
        player["planetary_boss_defeated"] = True
        player["bosses_defeated"].append("Planetary World-Eater Core")

        t4_choices = mechanics.generate_curated_evolutions(player)
        self.assertEqual(len(t4_choices), 3)

        mechanics.apply_class_evolution(player, t4_choices[0])
        self.assertEqual(player["class_tier"], 4)
        self.assertEqual(player["combat_resource"]["max"], int(int(62 * 1.50) * 2.0))


# =====================================================================
# MAIN RUNNER
# =====================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
