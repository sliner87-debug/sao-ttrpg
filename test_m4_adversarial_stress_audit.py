"""
test_m4_adversarial_stress_audit.py
===================================
Forensic Adversarial Stress Test Suite for Milestone 4 (R4):
Classic 10 Base Classes, Gating, Evolution Synthesis, and Persistence.
"""

import copy
import os
import shutil
import tempfile
import unittest

import backend.character_generator as cg
import backend.database as db
import backend.mechanics as mechanics
from backend.database.engine import create_sao_engine, db_transaction, init_db
from backend.database.repositories import CharacterRepository


class TestM4AdversarialForensics(unittest.TestCase):
    CLASSIC_10 = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "druid", "bard", "barbarian", "monk"
    ]

    # --- 1. Adversarial Class Normalization ---
    def test_adversarial_normalize_class_key(self):
        """Stress-test normalize_class_key with edge cases, corrupt inputs, and casing."""
        self.assertEqual(mechanics.normalize_class_key(None), "pathless")
        self.assertEqual(mechanics.normalize_class_key(""), "pathless")
        self.assertEqual(mechanics.normalize_class_key("   "), "pathless")
        self.assertEqual(mechanics.normalize_class_key(12345), "pathless")
        self.assertEqual(mechanics.normalize_class_key([]), "pathless")
        self.assertEqual(mechanics.normalize_class_key({}), "pathless")

        # Mixed casing and extra spaces
        self.assertEqual(mechanics.normalize_class_key("  FiGhTeR  "), "fighter")
        self.assertEqual(mechanics.normalize_class_key("\tWIZARD\n"), "wizard")
        self.assertEqual(mechanics.normalize_class_key("RoGuE"), "rogue")
        self.assertEqual(mechanics.normalize_class_key("CLERIC"), "cleric")
        self.assertEqual(mechanics.normalize_class_key("rAnGeR"), "ranger")
        self.assertEqual(mechanics.normalize_class_key("PALADIN"), "paladin")
        self.assertEqual(mechanics.normalize_class_key("druid"), "druid")
        self.assertEqual(mechanics.normalize_class_key("BaRd"), "bard")
        self.assertEqual(mechanics.normalize_class_key("BARBARIAN"), "barbarian")
        self.assertEqual(mechanics.normalize_class_key("mOnK"), "monk")

        # Substring / descriptive titles
        self.assertEqual(mechanics.normalize_class_key("Grand High Paladin of Dawn"), "paladin")
        self.assertEqual(mechanics.normalize_class_key("Primal Shifter of the Bramble"), "druid")
        self.assertEqual(mechanics.normalize_class_key("Spire Templar Inquisitor"), "cleric")
        self.assertEqual(mechanics.normalize_class_key("Shadow Infiltrator Operative"), "rogue")
        self.assertEqual(mechanics.normalize_class_key("Wilderness Scout Marksman"), "ranger")
        self.assertEqual(mechanics.normalize_class_key("Aetheric Mana Arcanist"), "wizard")
        self.assertEqual(mechanics.normalize_class_key("Colossus Berserker Juggernaut"), "barbarian")
        self.assertEqual(mechanics.normalize_class_key("Ki Flow Ascetic Master"), "monk")

    # --- 2. Integrity of All 10 Base Classes in CLASS_PATHS ---
    def test_all_10_classes_schema_integrity(self):
        """Verify each of the 10 classes has non-trivial, authentic attributes and starting feats."""
        class_paths = getattr(cg, "CLASS_PATHS", {})
        for c_key in self.CLASSIC_10:
            self.assertIn(c_key, class_paths, f"Missing class '{c_key}' in CLASS_PATHS")
            c = class_paths[c_key]
            self.assertTrue(len(c["title"]) > 5, f"Class {c_key} title too short")
            self.assertTrue(len(c["description"]) > 20, f"Class {c_key} description too short")
            self.assertGreaterEqual(c["base_hp"], 70, f"Class {c_key} base_hp unreasonably low")
            self.assertLessEqual(c["base_hp"], 150, f"Class {c_key} base_hp unreasonably high")
            self.assertGreaterEqual(c["hp_per_lvl"], 15, f"Class {c_key} hp_per_lvl too low")
            self.assertGreaterEqual(len(c["favored_skills"]), 2, f"Class {c_key} favored_skills too few")
            self.assertEqual(len(c["starting_feats"]), 2, f"Class {c_key} must have exactly 2 starting feats")

            # Check combat resource
            r = c["combat_resource"]
            self.assertTrue(isinstance(r, dict))
            self.assertIn("name", r)
            self.assertIn("type", r)
            self.assertGreater(r["max"], 0)
            self.assertGreaterEqual(r["current"], 0)

            # Check presence in ARCHETYPE_HP_GROWTH
            growth = mechanics.ARCHETYPE_HP_GROWTH.get(c_key)
            self.assertIsNotNone(growth, f"Class {c_key} missing from ARCHETYPE_HP_GROWTH")
            self.assertGreaterEqual(growth, 20)

    # --- 3. Full Level 1-30 Progression & HP Scaling ---
    def test_level_1_to_30_progression_all_classes(self):
        """Stress-test level up progression from level 1 to 30 across all 10 classes."""
        for c_key in self.CLASSIC_10:
            char = cg.generate_starting_character(name=f"LvHero_{c_key}", class_key=c_key, start_tutorial=False)
            p = char.get("player", char)
            initial_hp = p["max_hp"]

            for lvl in range(2, 31):
                prev_hp = p["max_hp"]
                res = mechanics.apply_level_up(p)
                self.assertEqual(p["level"], lvl)
                self.assertGreater(p["max_hp"], prev_hp)
                self.assertEqual(res["new_level"], lvl)
                self.assertEqual(res["max_hp"], p["max_hp"])

            self.assertEqual(p["level"], 30)
            self.assertGreater(p["max_hp"], initial_hp + 500)

    # --- 4. Adversarial Gating Checks ---
    def test_adversarial_evolution_gating(self):
        """Adversarially probe check_evolution_eligibility with malformed and boundary inputs."""
        p = {"level": 10, "class_tier": 1, "skills": {}, "bosses_defeated": []}

        # Level 10, no boss, no skills -> Ineligible
        res = mechanics.check_evolution_eligibility(p)
        self.assertFalse(res["eligible"])
        self.assertEqual(res["target_tier"], 2)
        self.assertEqual(len(res["unmet_conditions"]), 2)  # boss unmet + mastery unmet

        # Add boss as string instead of list
        p["bosses_defeated"] = "The Gilded Spire Overlord (Sector 1)"
        res = mechanics.check_evolution_eligibility(p)
        self.assertFalse(res["eligible"])  # still missing mastery

        # Add skill mastery via dictionary format
        p["skills"] = {"Swords": {"mastery": 120}}
        res = mechanics.check_evolution_eligibility(p)
        self.assertTrue(res["eligible"])
        self.assertEqual(len(res["unmet_conditions"]), 0)

        # Add skill mastery via integer format
        p["skills"] = {"Swords": 150}
        res = mechanics.check_evolution_eligibility(p)
        self.assertTrue(res["eligible"])

        # Add skill mastery via list of dicts format
        p["skills"] = [{"name": "Swords", "mastery": 200}]
        res = mechanics.check_evolution_eligibility(p)
        self.assertTrue(res["eligible"])

        # Boundary check: Level 9 with boss and 200 mastery -> Ineligible
        p["level"] = 9
        res = mechanics.check_evolution_eligibility(p)
        self.assertFalse(res["eligible"])

    # --- 5. Evolution Synthesis Cold-Start & Telemetry Stress ---
    def test_evolution_synthesis_all_10_classes_cold_start(self):
        """Verify generate_curated_evolutions operates cleanly with zero/corrupt telemetry."""
        for c_key in self.CLASSIC_10:
            p = {
                "class": c_key,
                "level": 10,
                "class_tier": 1,
                "telemetry": None,  # Cold start / None
                "skills": {},
                "inventory": [],
                "equipped": {}
            }
            evos = mechanics.generate_curated_evolutions(p)
            self.assertEqual(len(evos), 3, f"Class {c_key} must yield exactly 3 choices on cold start")
            for e in evos:
                self.assertIn("title", e)
                self.assertIn("category", e)
                self.assertIn("desc", e)
                self.assertEqual(e["tier"], 2)

    # --- 6. Monstrous Lineages Evolution Anchors ---
    def test_monstrous_lineage_evolution_anchors(self):
        """Verify all monstrous/fey playable races receive their specific racial anchor choice."""
        races_to_expected = {
            "minotaur_labyrinth_breaker": ["minotaur", "bull", "labyrinth"],
            "pixie_fey_sprite": ["pixie", "trickster"],
            "satyr_fey_reveler": ["satyr", "skald"],
            "meadow_nymph_fey": ["nymph", "grace"],
            "gargoyle_lithic_sentinel": ["gargoyle", "stone"],
            "centaur_plains_vanguard": ["centaur", "dragoon"],
            "troll_kreen_chimera": ["troll", "regenerator"],
            "medusa_gorgon_scion": ["medusa", "gorgon", "stone"],
            "ogre_titan_brute": ["ogre", "crusher"],
            "kobold_dragon_herald": ["dragon", "wyrm", "kobold"],
            "gnoll_hyena_ravager": ["hyena", "pack", "gnoll"],
        }

        for r_key, keywords in races_to_expected.items():
            char = cg.generate_starting_character(name=f"R_{r_key[:8]}", race_key=r_key, class_key="barbarian", start_tutorial=False)
            p = char.get("player", char)
            p["level"] = 10
            p["class_tier"] = 1
            evos = mechanics.generate_curated_evolutions(p)
            self.assertEqual(len(evos), 3)
            c3 = evos[2]
            c3_text = f"{c3['title']} {c3.get('desc', '')}".lower()
            matched = any(kw in c3_text for kw in keywords)
            self.assertTrue(
                matched,
                f"Race {r_key} expected anchor keywords {keywords}, got title '{c3['title']}' desc '{c3.get('desc')}'"
            )

    # --- 7. Full Tier 1 -> Tier 4 Evolution Progression & Math ---
    def test_full_tier_1_to_4_evolution_cycle(self):
        """Simulate a character progressing from Tier 1 -> Tier 2 -> Tier 3 -> Tier 4 with authentic math."""
        char = cg.generate_starting_character(name="PaladinHero", class_key="paladin", start_tutorial=False)
        p = char.get("player", char)
        initial_res_max = p["combat_resource"]["max"]  # 100 for paladin
        # 1. Reach Level 10 and evolve to Tier 2
        p["level"] = 10
        p["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]
        p["skills"]["Heavy Swords"] = 150
        elig2 = mechanics.check_evolution_eligibility(p)
        self.assertTrue(elig2["eligible"])

        evos2 = mechanics.generate_curated_evolutions(p)
        choice2 = evos2[0]  # Pick Choice 1
        res2 = mechanics.apply_class_evolution(p, choice2)
        self.assertEqual(p["class_tier"], 2)
        self.assertEqual(p["combat_resource"]["max"], int(initial_res_max * 1.25))

        # 2. Reach Level 20 and evolve to Tier 3
        p["level"] = 20
        p["bosses_defeated"].append("Regional Apex Behemoth (Sector 5)")
        p["skills"]["Heavy Swords"] = 400
        elig3 = mechanics.check_evolution_eligibility(p)
        self.assertTrue(elig3["eligible"])

        evos3 = mechanics.generate_curated_evolutions(p)
        choice3 = evos3[0]
        res3 = mechanics.apply_class_evolution(p, choice3)
        self.assertEqual(p["class_tier"], 3)
        self.assertEqual(p["combat_resource"]["max"], int(int(initial_res_max * 1.25) * 1.50))

        # 3. Reach Level 30 and evolve to Tier 4
        p["level"] = 30
        p["bosses_defeated"].append("Planetary World-Eater Core")
        p["skills"]["Heavy Swords"] = 800
        elig4 = mechanics.check_evolution_eligibility(p)
        self.assertTrue(elig4["eligible"])

        evos4 = mechanics.generate_curated_evolutions(p)
        choice4 = evos4[0]
        res4 = mechanics.apply_class_evolution(p, choice4)
        self.assertEqual(p["class_tier"], 4)
        expected_t4 = int(int(int(initial_res_max * 1.25) * 1.50) * 2.00)
        self.assertEqual(p["combat_resource"]["max"], expected_t4)

    # --- 8. Database Persistence Round-Trip for Classic 10 Classes ---
    def test_database_persistence_classic_10_classes(self):
        """Verify all 10 classic classes save and hydrate faithfully through SQLAlchemy SQLite repository."""
        temp_dir = tempfile.mkdtemp(prefix="sao_m4_audit_db_")
        db_path = os.path.join(temp_dir, "sao_audit.db")
        db_url = f"sqlite:///{db_path}"

        try:
            engine = create_sao_engine(db_url)
            init_db(engine)

            for c_key in self.CLASSIC_10:
                char = cg.generate_starting_character(name=f"Persist_{c_key}", class_key=c_key, start_tutorial=False)
                p = char.get("player", char)
                p["level"] = 10
                p["class_tier"] = 2
                p["class"] = f"Evolved {c_key.title()}"
                p["combat_resource"]["max"] = 125
                p["combat_resource"]["current"] = 125

                session_id = f"sess_{c_key}"
                with db_transaction(engine) as db_sess:
                    rec = CharacterRepository.save_character(db_sess, p, session_id=session_id)
                    self.assertIsNotNone(rec.id)

                with db_transaction(engine) as db_sess:
                    hydrated = CharacterRepository.load_character(db_sess, p["name"], session_id=session_id)
                    self.assertIsNotNone(hydrated, f"Failed to hydrate character for class {c_key}")
                    self.assertEqual(hydrated["level"], 10)
                    self.assertEqual(hydrated["class"], f"Evolved {c_key.title()}")
                    self.assertEqual(hydrated["combat_resource"]["max"], 125)
                    self.assertEqual(hydrated["combat_resource"]["type"], p["combat_resource"]["type"])

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
