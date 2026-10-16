"""
test_warlock_35_and_supplements.py
==================================
Comprehensive test suite verifying the complete D&D 3.5 Warlock implementation
and all supplement coverage across Complete Arcane, Complete Mage, Fiendish Codex I & II,
and Dragon #358 in Fractured Earth SAO Sandbox V2.
"""

import unittest
import copy
import tempfile
import os
import shutil

import backend.character_generator as cg
import backend.mechanics as mechanics
from backend.database.engine import create_sao_engine, init_db, db_transaction
from backend.database.repositories import CharacterRepository


class TestWarlockBaseAndSupplements(unittest.TestCase):

    def setUp(self):
        self.warlock_char = cg.generate_starting_character(
            name="Morvath",
            class_key="warlock",
            race_key="human",
            lifestyle_key="archive_scribe",
            start_tutorial=False
        )
        self.player = self.warlock_char.get("player", self.warlock_char)

    # -------------------------------------------------------------------------
    # 1. CHARACTER CREATION & INITIAL LOADOUT
    # -------------------------------------------------------------------------
    def test_warlock_class_paths_registration(self):
        """Verify warlock exists in CLASS_PATHS with accurate D&D 3.5 mechanical metadata."""
        self.assertIn("warlock", cg.CLASS_PATHS)
        w_def = cg.CLASS_PATHS["warlock"]
        self.assertEqual(w_def["base_hp"], 85)
        self.assertEqual(w_def["hp_per_lvl"], 22)
        self.assertIn("Light", w_def["native_armor"])
        self.assertIn("Cloth", w_def["native_armor"])
        self.assertEqual(w_def["combat_resource"]["type"], "eldritch")
        self.assertIn("Eldritch Blast", w_def["starting_feats"])
        self.assertIn("Dark One's Own Luck", w_def["starting_feats"])

    def test_warlock_starting_spells_and_invocations(self):
        """Verify warlock generates with Complete Arcane & Complete Mage starting invocations."""
        spells = self.player.get("spells", [])
        expected_invocations = [
            "Eldritch Blast (At Will)",
            "Eldritch Glaive (At Will)",
            "Dark One's Own Luck (At Will)",
            "Devil's Sight (At Will)",
            "See the Unseen (At Will)",
            "Brimstone Blast (At Will)"
        ]
        for inv in expected_invocations:
            self.assertIn(inv, spells, f"Missing expected starting invocation: {inv}")

    def test_warlock_weapons_loadout(self):
        """Verify warlock starts equipped with Eldritch Focus Rod and Tome of the Forbidden Pact."""
        self.assertEqual(self.player["equipped"]["main_hand"], "Eldritch Focus Rod")
        self.assertEqual(self.player["equipped"]["off_hand"], "Tome of the Forbidden Pact")

        # Verify item entries exist in inventory and canonical catalog
        inv_names = [it["name"] if isinstance(it, dict) else str(it) for it in self.player["inventory"]]
        self.assertIn("Eldritch Focus Rod", inv_names)
        self.assertIn("Tome of the Forbidden Pact", inv_names)

        rod_details = mechanics.get_item_details("Eldritch Focus Rod")
        self.assertEqual(rod_details["slot"], "main_hand")
        self.assertEqual(rod_details["rarity"], "Uncommon")
        self.assertIn("cold-iron", rod_details["desc"].lower())

    def test_warlock_class_normalization_and_aliases(self):
        """Verify normalize_class_key correctly maps all warlock aliases."""
        aliases = ["warlock", "invocator", "hellfire", "hellfire_warlock", "eldritch", "eldritch_theurge"]
        for a in aliases:
            norm = mechanics.normalize_class_key(a)
            self.assertEqual(norm, "warlock", f"Alias {a} did not normalize to warlock")

    # -------------------------------------------------------------------------
    # 2. ELDRITCH BLAST DAMAGE SCALING (D&D 3.5 RULES)
    # -------------------------------------------------------------------------
    def test_eldritch_blast_dice_scaling(self):
        """Verify Eldritch Blast damage dice scales 1d6 up to 9d6+ across levels 1-20."""
        p = copy.deepcopy(self.player)
        level_scaling_table = {
            1: 1, 2: 1,
            3: 2, 4: 2,
            5: 3, 6: 3,
            7: 4, 8: 4,
            9: 5, 10: 5,
            11: 6, 12: 6,
            13: 7, 14: 7,
            15: 8, 16: 8,
            17: 9, 18: 9,
            19: 10, 20: 10,
            21: 11
        }
        for lvl, expected_dice in level_scaling_table.items():
            p["level"] = lvl
            actual_dice = mechanics.calculate_eldritch_blast_dice(p)
            self.assertEqual(
                actual_dice, expected_dice,
                f"Level {lvl} expected {expected_dice}d6 blast dice, got {actual_dice}d6"
            )

    # -------------------------------------------------------------------------
    # 3. BLAST SHAPES & ESSENCES MODULATION ENGINE
    # -------------------------------------------------------------------------
    def test_execute_eldritch_blast_default_ray(self):
        """Verify standard ray blast resolves as a 60ft ranged touch attack dealing 1d6 force damage."""
        res = mechanics.execute_eldritch_blast(self.player, shape="ray", essence="raw")
        self.assertTrue(res["success"])
        self.assertEqual(res["damage_dice"], "1d6")
        self.assertEqual(res["range_ft"], 60)
        self.assertEqual(res["damage_type"], "magical force / untyped")
        self.assertTrue(res["touch_attack"])
        self.assertEqual(res["con_cost"], 0)

    def test_blast_shapes_coverage(self):
        """Verify all canonical blast shapes from Complete Arcane, Complete Mage, and Dragon #358."""
        shapes_to_test = {
            "glaive": (10, "Melee Touch Full Attack (10ft Reach)"),
            "spear": (250, "Extreme-Range Ranged Touch Attack"),
            "chain": (60, "Arcing Multi-Target Attack"),
            "cone": (30, "30-ft Cone Area Burst (Reflex Half)"),
            "doom": (20, "20-ft Radius Point-Blank Nova (Reflex Half)"),
            "hideous_blow": (5, "Melee Weapon Channel"),
            "claws": (5, "Natural Claws Touch")
        }
        for shape_key, (exp_range, exp_type) in shapes_to_test.items():
            res = mechanics.execute_eldritch_blast(self.player, shape=shape_key, essence="raw")
            self.assertTrue(res["success"], f"Failed for shape {shape_key}")
            self.assertEqual(res["range_ft"], exp_range)
            self.assertEqual(res["attack_mode"], exp_type)

    def test_blast_essences_coverage(self):
        """Verify all canonical essences from Complete Arcane, Complete Mage, and Fiendish Codex."""
        p = copy.deepcopy(self.player)
        p["level"] = 11  # 6d6 blast dice

        essences_to_test = {
            "brimstone": "fire",
            "hellrime": "cold",
            "vitriolic": "acid",
            "utterdark": "negative energy",
            "frightful": "force",
            "sickening": "force",
            "beshadowed": "force",
            "bewitching": "force",
            "repelling": "force",
            "hindering": "force",
            "binding": "force"
        }
        for ess_key, exp_dmg_type in essences_to_test.items():
            res = mechanics.execute_eldritch_blast(p, shape="ray", essence=ess_key)
            self.assertTrue(res["success"])
            self.assertEqual(res["damage_type"], exp_dmg_type)
            self.assertEqual(res["damage_dice"], "6d6")

        # Test Vitriolic bypasses SR
        vit_res = mechanics.execute_eldritch_blast(p, shape="ray", essence="vitriolic")
        self.assertTrue(vit_res["bypasses_sr"])

        # Test Hellfire (Fiendish Codex II): adds +4d6 (total 10d6) and costs 1 CON
        hf_res = mechanics.execute_eldritch_blast(p, shape="ray", essence="hellfire")
        self.assertEqual(hf_res["damage_dice"], "10d6")
        self.assertEqual(hf_res["damage_type"], "hellfire (unresistable)")
        self.assertEqual(hf_res["con_cost"], 1)

    # -------------------------------------------------------------------------
    # 4. DAMAGE REDUCTION / COLD IRON SCALING
    # -------------------------------------------------------------------------
    def test_warlock_cold_iron_dr_scaling(self):
        """Verify D&D 3.5 Cold Iron Damage Reduction scales: DR 1 at 3, DR 2 at 7, DR 3 at 11, DR 4 at 15, DR 5 at 19."""
        p = copy.deepcopy(self.player)
        p["class"] = "warlock"

        # Level 1: No DR
        p["level"] = 1
        dmg_l1 = mechanics.resolve_damage_reduction(p, 10, damage_type="physical", weapon_properties=[])
        self.assertEqual(dmg_l1, 10)

        # Level 3: DR 1/cold iron
        p["level"] = 3
        dmg_l3 = mechanics.resolve_damage_reduction(p, 10, damage_type="physical", weapon_properties=[])
        self.assertEqual(dmg_l3, 9)

        # Level 7: DR 2/cold iron
        p["level"] = 7
        dmg_l7 = mechanics.resolve_damage_reduction(p, 10, damage_type="physical", weapon_properties=[])
        self.assertEqual(dmg_l7, 8)

        # Level 11: DR 3/cold iron
        p["level"] = 11
        dmg_l11 = mechanics.resolve_damage_reduction(p, 10, damage_type="physical", weapon_properties=[])
        self.assertEqual(dmg_l11, 7)

        # Level 15: DR 4/cold iron
        p["level"] = 15
        dmg_l15 = mechanics.resolve_damage_reduction(p, 10, damage_type="physical", weapon_properties=[])
        self.assertEqual(dmg_l15, 6)

        # Level 19: DR 5/cold iron
        p["level"] = 19
        dmg_l19 = mechanics.resolve_damage_reduction(p, 10, damage_type="physical", weapon_properties=[])
        self.assertEqual(dmg_l19, 5)

        # Cold Iron weapon bypasses DR completely
        dmg_ci = mechanics.resolve_damage_reduction(p, 10, damage_type="physical", weapon_properties=["cold iron dagger"])
        self.assertEqual(dmg_ci, 10)

    # -------------------------------------------------------------------------
    # 5. MULTI-TIER CLASS EVOLUTIONS (LEVEL 10 & LEVEL 20)
    # -------------------------------------------------------------------------
    def test_warlock_level_10_tier_2_evolutions(self):
        """Verify Level 10 Warlock evolution options generate 3 distinct thematic paths."""
        p = copy.deepcopy(self.player)
        p["level"] = 10
        p["bosses_defeated"] = ["Crucible Warden", "Sector 1 Spire Boss"]

        evos = mechanics.generate_curated_evolutions(p)
        self.assertEqual(len(evos), 3, "Must generate exactly 3 evolution choices for Level 10 Warlock.")

        evo_titles = [e["title"] for e in evos]
        # At least one recognized Warlock specialization should be present
        known_warlock_t2 = [
            "Glaive-Master",
            "Sniper",
            "Theurge",
            "Enlightened Spirit",
            "Hellfire Warlock",
            "Fey-Pact Deceiver"
        ]
        matches = [t for t in evo_titles if any(k.lower() in t.lower() for k in known_warlock_t2)]
        self.assertGreaterEqual(len(matches), 1, f"Expected known Warlock T2 evolution, got: {evo_titles}")

        # Apply choice 1
        res = mechanics.apply_class_evolution(p, evos[0])
        self.assertTrue(res["success"])
        self.assertEqual(p["class_tier"], 2)

    def test_warlock_level_20_tier_3_evolutions(self):
        """Verify Level 20 Warlock evolution options generate 3 advanced specialization branches."""
        p = copy.deepcopy(self.player)
        p["level"] = 20
        p["class_tier"] = 2
        p["bosses_defeated"] = ["Crucible Warden", "Sector 1 Spire Boss", "Regional Apex Behemoth (Sector 5)"]

        evos = mechanics.generate_curated_evolutions(p)
        self.assertEqual(len(evos), 3, "Must generate exactly 3 evolution choices for Level 20 Warlock.")

        known_warlock_t3 = [
            "Hellfire Archon Sovereign",
            "Eldritch Theurge Ascendant",
            "Void-Born Invocator Prime"
        ]
        evo_titles = [e["title"] for e in evos]
        matches = [t for t in evo_titles if any(k in t for k in known_warlock_t3)]
        self.assertGreaterEqual(len(matches), 1, f"Expected known Warlock T3 evolution, got: {evo_titles}")

        res = mechanics.apply_class_evolution(p, evos[0])
        self.assertTrue(res["success"])
        self.assertEqual(p["class_tier"], 3)

    # -------------------------------------------------------------------------
    # 6. CANONICAL POWERS & INVOCATIONS ENRICHMENT
    # -------------------------------------------------------------------------
    def test_canonical_invocations_and_powers_catalog(self):
        """Verify Complete Arcane and Complete Mage invocations are registered in CANONICAL_SPELLS_AND_POWERS."""
        check_list = [
            "eldritch blast",
            "eldritch glaive",
            "chilling tentacles",
            "wall of perilous flame",
            "retributive invisibility",
            "fiendish resilience",
            "deceive item",
            "imbue item",
            "dark foresight",
            "word of changing",
            "devour magic",
            "caustic mire"
        ]
        for power_name in check_list:
            det = mechanics.get_spell_or_power_details(power_name)
            self.assertIn("category", det)
            self.assertNotEqual(det["category"], "Generic Ability", f"Power '{power_name}' fell back to generic!")
            self.assertIn("mechanics", det)

    # -------------------------------------------------------------------------
    # 7. SQLALCHEMY DATABASE PERSISTENCE ROUND-TRIP
    # -------------------------------------------------------------------------
    def test_warlock_database_persistence_roundtrip(self):
        """Verify Warlock character state persists to SQLite database and rehydrates with fidelity."""
        temp_dir = tempfile.mkdtemp(prefix="sao_warlock_test_db_")
        db_path = os.path.join(temp_dir, "warlock_test.db")
        db_url = f"sqlite:///{db_path}"

        try:
            engine = create_sao_engine(db_url)
            init_db(engine)

            p = copy.deepcopy(self.player)
            p["level"] = 10
            p["class_tier"] = 2
            p["combat_resource"]["current"] = 75

            session_id = "test_warlock_session_1"
            with db_transaction(engine) as db_sess:
                saved_rec = CharacterRepository.save_character(db_sess, p, session_id=session_id)
                self.assertIsNotNone(saved_rec.id)

            with db_transaction(engine) as db_sess:
                hydrated = CharacterRepository.load_character(db_sess, p["name"], session_id=session_id)
                self.assertIsNotNone(hydrated)
                self.assertEqual(hydrated["name"], "Morvath")
                self.assertEqual(hydrated["combat_resource"]["type"], "eldritch")
                self.assertEqual(hydrated["combat_resource"]["current"], 75)
                self.assertIn("Eldritch Blast (At Will)", hydrated["spells"])
                self.assertIn("Eldritch Glaive (At Will)", hydrated["spells"])
                self.assertEqual(hydrated["equipped"]["main_hand"], "Eldritch Focus Rod")
                self.assertEqual(hydrated["equipped"]["off_hand"], "Tome of the Forbidden Pact")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
