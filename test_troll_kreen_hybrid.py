import itertools
import os
import shutil
import unittest

from backend import character_generator as cg, mechanics

STATS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
ZERO_ALLOC = {s: 0 for s in STATS}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestTrollKreenHybrids(unittest.TestCase):
    created = []

    @classmethod
    def tearDownClass(cls):
        for name in cls.created:
            d = cg.get_character_save_dir(BASE_DIR, name)
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)

    def _make(self, name, race_key, choices=None):
        self.created.append(name)
        return cg.generate_starting_character(name, ZERO_ALLOC, "software_engineer", race_key,
                                              "warrior", "smartphone", chimera_choices=choices)

    def test_three_variants_registered(self):
        for k in ("troll_kreen_juggernaut", "thri_troll_stalker", cg.CHIMERA_RACE_KEY):
            self.assertIn(k, cg.RACIAL_LINEAGES)

    def test_variant_1_troll_dominant_stats(self):
        r = cg.RACIAL_LINEAGES["troll_kreen_juggernaut"]
        self.assertEqual(r["stat_mods"], {"STR": 4, "DEX": 1, "CON": 4, "INT": -2, "WIS": 0, "CHA": -3})
        self.assertTrue(any(a.startswith("Flaw") for a in r["racial_abilities"]))

    def test_variant_2_user_chosen_net_plus_5(self):
        r = cg.RACIAL_LINEAGES["thri_troll_stalker"]
        self.assertEqual(r["stat_mods"], {"STR": 1, "DEX": 4, "CON": 1, "INT": -1, "WIS": 2, "CHA": -2})
        self.assertEqual(sum(r["stat_mods"].values()), 5)

    def test_chimera_has_5_slots_and_3_bloodline_categories(self):
        self.assertEqual(len(cg.CHIMERA_PHYSICAL_SLOTS), 5)
        self.assertEqual(set(cg.CHIMERA_BLOODLINE_OPTIONS), {"defense", "offense", "instinct"})
        self.assertEqual(len(cg.CHIMERA_BLOODLINE_OPTIONS["defense"]["options"]), 3)
        self.assertEqual(len(cg.CHIMERA_BLOODLINE_OPTIONS["offense"]["options"]), 3)
        self.assertEqual(len(cg.CHIMERA_BLOODLINE_OPTIONS["instinct"]["options"]), 2)

    def test_every_chimera_combination_is_valid(self):
        slots = list(cg.CHIMERA_PHYSICAL_SLOTS)
        cats = list(cg.CHIMERA_BLOODLINE_OPTIONS)
        count = 0
        for phys in itertools.product(["troll", "kreen"], repeat=len(slots)):
            for blood in itertools.product(*[list(cg.CHIMERA_BLOODLINE_OPTIONS[c]["options"]) for c in cats]):
                ch = dict(zip(slots, phys)) | dict(zip(cats, blood))
                lin = cg.build_chimera_lineage(ch)
                self.assertEqual(len(lin["racial_abilities"]), 9)  # 5 physical + 3 bloodline + 1 flaw
                self.assertEqual(lin["stat_mods"]["INT"], -1)
                self.assertEqual(lin["stat_mods"]["CHA"], -2)
                self.assertEqual(lin["max_hp_bonus"], 10 if ch["hide"] == "troll" else 0)
                count += 1
        self.assertEqual(count, 32 * 18)

    def test_frame_slot_drives_stats(self):
        troll = cg.build_chimera_lineage({"frame": "troll"})["stat_mods"]
        kreen = cg.build_chimera_lineage({"frame": "kreen"})["stat_mods"]
        self.assertEqual((troll["STR"], troll["CON"], troll["DEX"]), (3, 2, 0))
        self.assertEqual((kreen["DEX"], kreen["WIS"], kreen["CON"], kreen["STR"]), (3, 1, 1, 0))

    def test_invalid_choices_fall_back_to_defaults(self):
        ch = cg.normalize_chimera_choices({"frame": "goblin", "defense": "nope", "arms": "kreen"})
        self.assertEqual(ch["frame"], cg.DEFAULT_CHIMERA_CHOICES["frame"])
        self.assertEqual(ch["defense"], cg.DEFAULT_CHIMERA_CHOICES["defense"])
        self.assertEqual(ch["arms"], "kreen")

    def test_generate_chimera_character_applies_choices(self):
        ch = {"frame": "kreen", "arms": "kreen", "hide": "troll", "senses": "kreen", "legs": "kreen",
              "defense": "shell_molt", "offense": "caustic_bile_spit", "instinct": "phantom_reflex"}
        p = self._make("Test_Hybrid_Chimera", cg.CHIMERA_RACE_KEY, ch)
        self.assertEqual(p["stats"]["DEX"], 13)
        self.assertEqual(p["stats"]["CHA"], 8)
        self.assertIn("1 Troll / 4 Kreen", p["race"])
        self.assertEqual({k: p["racial_variant_config"]["choices"][k] for k in ch}, ch)
        self.assertTrue(any(a.startswith("Reactive Chitin Shell-Molt") for a in p["racial_abilities"]))
        base = self._make("Test_Hybrid_Chimera_NoHide", cg.CHIMERA_RACE_KEY, dict(ch, hide="kreen"))
        self.assertEqual(p["max_hp"] - base["max_hp"], 10)

    def test_fixed_variants_generate(self):
        p1 = self._make("Test_Hybrid_Juggernaut", "troll_kreen_juggernaut")
        p2 = self._make("Test_Hybrid_Stalker", "thri_troll_stalker")
        self.assertEqual(p1["stats"]["STR"], 14)
        self.assertEqual(p2["stats"]["DEX"], 14)
        self.assertIsNone(p1.get("racial_variant_config"))

    def test_ability_details_resolve_to_own_lineage(self):
        abilities = list(cg.CHIMERA_ABILITY_CATALOG)
        for k in ("troll_kreen_juggernaut", "thri_troll_stalker"):
            abilities += cg.RACIAL_LINEAGES[k]["racial_abilities"]
        for ab in abilities:
            det = mechanics.get_spell_or_power_details(ab)
            self.assertEqual(det["name"], ab.split(":", 1)[0].strip())
            self.assertIn(ab.split(":", 1)[1].strip(), det["mechanics"])
            self.assertIn("Hybrid", det["category"])

    def test_troll_regen_no_longer_shows_nanite_text(self):
        troll_regen = next(a for a in cg.RACIAL_LINEAGES["troll_fleshwarped"]["racial_abilities"] if "Regeneration" in a)
        det = mechanics.get_spell_or_power_details(troll_regen)
        self.assertIn("Troll", det["category"])
        self.assertIn("5 HP", det["mechanics"])

    def test_seven_flaws_all_available_to_every_build(self):
        self.assertEqual(len(cg.CHIMERA_FLAWS), 7)
        for build in ({"frame": "troll", "arms": "troll", "hide": "troll", "senses": "troll", "legs": "troll"},
                      {"frame": "kreen", "arms": "kreen", "hide": "kreen", "senses": "kreen", "legs": "kreen"}):
            for fk, fd in cg.CHIMERA_FLAWS.items():
                lin = cg.build_chimera_lineage(dict(build, flaw=fk))
                self.assertIn(fd["ability"], lin["racial_abilities"])

    def test_second_flaw_stat_reward(self):
        lin = cg.build_chimera_lineage({"frame": "troll", "flaw": "thermal_flesh", "flaw_2": "molting_cycle",
                                        "flaw_2_reward": "stats", "reward_stats": ["DEX", "WIS", "CHA", "INT"]})
        m = lin["stat_mods"]
        self.assertEqual((m["DEX"], m["WIS"], m["CHA"], m["INT"]), (1, 1, -1, -1))  # capped at 3 stats
        self.assertEqual(sum(1 for a in lin["racial_abilities"] if a.startswith("Flaw")), 2)

    def test_second_flaw_stat_reward_ignores_duplicates_and_same_flaw(self):
        ch = cg.normalize_chimera_choices({"flaw": "blood_frenzy", "flaw_2": "blood_frenzy"})
        self.assertIsNone(ch["flaw_2"])
        ch = cg.normalize_chimera_choices({"flaw_2": "molting_cycle", "reward_stats": ["STR", "STR", "BOGUS"]})
        self.assertEqual(ch["reward_stats"], ["STR"])

    def test_second_flaw_feat_reward(self):
        lin = cg.build_chimera_lineage({"defense": "hyper_regeneration", "offense": "savage_quad_rend",
                                        "flaw_2": "uncanny_abomination", "flaw_2_reward": "feat",
                                        "reward_feat": "offense:caustic_bile_spit"})
        self.assertTrue(any(a.startswith("Caustic Bile-Spit") for a in lin["racial_abilities"]))
        self.assertTrue(any(a.startswith("Savage Quad-Rend") for a in lin["racial_abilities"]))
        self.assertNotIn(cg.CHIMERA_REGEN_CAP_RULE, lin["racial_abilities"])

    def test_feat_reward_cannot_duplicate_and_defense_adds_regen_cap(self):
        ch = cg.normalize_chimera_choices({"defense": "shell_molt", "flaw_2": "molting_cycle",
                                           "flaw_2_reward": "feat", "reward_feat": "defense:shell_molt"})
        self.assertNotEqual(ch["reward_feat"], "defense:shell_molt")
        lin = cg.build_chimera_lineage({"defense": "shell_molt", "flaw_2": "molting_cycle",
                                        "flaw_2_reward": "feat", "reward_feat": "defense:bio_carapace_ward"})
        self.assertIn(cg.CHIMERA_REGEN_CAP_RULE, lin["racial_abilities"])

    def test_concept_art_files_exist(self):
        for paths in cg.HYBRID_CONCEPT_ART.values():
            for p in paths:
                self.assertTrue(os.path.exists(os.path.join(BASE_DIR, p)), p)


if __name__ == "__main__":
    unittest.main()
