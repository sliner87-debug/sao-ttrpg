"""
test_m2_adversarial_challenge.py
================================
Adversarial Challenge Test Suite for Milestone 2:
Requirement R2: Pure Fantasy & D&D 3.0 Savage Species Playable Lineages.

Covers:
1. Pure fantasy lineages in get_character_creation_lineages(): sci-fi blacklist strictness,
   schema invariants, physical defaults, and generative fuzzing.
2. D&D 3.0 Pixie: Tiny size mechanics (+2 AC/attack, -8 grapple, 0.5x carry, +8 stealth),
   permanent Greater Invisibility, DR 5/cold iron, Pixie Dust sleep/confusion saves and immunities.
3. Meadow Nymph: Unearthly Grace CHA deflection AC across CHA range 8 to 24, heavy armor
   deflection exclusion, Blinding Beauty aura.
4. Savage Species Monstrous Lineages: Minotaur, Gargoyle, Centaur, Half-Ogre, Ogre Titan-Brute,
   Feral Troll, and Medusa traits, natural armor, flight, barding slots, and size mechanics.
5. Legacy backward compatibility and Glenny 4-armed chimera multi-limb parity.
"""

import math
import random
import unittest
import backend.character_generator as cg
import backend.mechanics as mechanics


class TestLineagePurgeAndCatalogFuzzing(unittest.TestCase):
    """
    Adversarial property-based testing and fuzzing on character creation lineages catalog.
    Ensures 0% leakage of sci-fi/biomechanical/cyberpunk concepts into character creation menus.
    """

    BANNED_SCI_FI_TOKENS = (
        "sci-fi",
        "biomechanical",
        "cyber",
        "android",
        "alien",
        "cyborg",
        "nanite",
        "neuromancer",
        "synthetic",
    )

    def test_lineages_count_and_sci_fi_exclusion(self):
        """Property: Creation lineages catalog has >= 25 lineages and strictly 0 sci-fi races."""
        lineages = cg.get_character_creation_lineages()
        self.assertIsInstance(lineages, dict)
        self.assertGreaterEqual(
            len(lineages), 25,
            f"Expected at least 25 pure fantasy lineages, found {len(lineages)}"
        )

        # Ensure none of the purged sci-fi race keys exist in creation catalog
        purged_keys = set(cg.PURGED_SCI_FI_RACES)
        found_purged = set(lineages.keys()) & purged_keys
        self.assertEqual(
            found_purged, set(),
            f"Purged sci-fi race keys found in character creation catalog: {found_purged}"
        )

        # Fuzz genre metadata against banned tokens
        flagged_genres = {}
        for r_key, r_data in lineages.items():
            genre_str = str(r_data.get("genre", "")).lower()
            for token in self.BANNED_SCI_FI_TOKENS:
                # Disallow exact matches or sub-token occurrences in genre
                if token in genre_str:
                    flagged_genres[r_key] = (token, genre_str)

        self.assertEqual(
            flagged_genres, {},
            f"Lineages contain banned sci-fi tokens in genre metadata: {flagged_genres}"
        )

    def test_all_creation_lineages_schema_invariants(self):
        """Property: Every single lineage in creation catalog adheres strictly to schema invariants."""
        lineages = cg.get_character_creation_lineages()
        core_stats = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}

        for r_key, r_data in lineages.items():
            # 1. Name is non-empty string
            self.assertIn("name", r_data, f"Lineage {r_key} missing 'name'")
            self.assertIsInstance(r_data["name"], str)
            self.assertGreater(len(r_data["name"].strip()), 3)

            # 2. Genre is non-empty string
            self.assertIn("genre", r_data, f"Lineage {r_key} missing 'genre'")
            self.assertIsInstance(r_data["genre"], str)

            # 3. Stat mods has all 6 core attributes as integers
            self.assertIn("stat_mods", r_data, f"Lineage {r_key} missing 'stat_mods'")
            mods = r_data["stat_mods"]
            self.assertIsInstance(mods, dict)
            self.assertTrue(core_stats.issubset(mods.keys()), f"Lineage {r_key} missing core stats in {mods}")
            for stat in core_stats:
                val = mods[stat]
                self.assertIsInstance(val, int, f"Stat {stat} for {r_key} must be int, got {type(val)}")
                # Bounded sanity check: racial mod must be between -8 and +10
                self.assertGreaterEqual(val, -8, f"Stat mod {stat} for {r_key} unreasonably low: {val}")
                self.assertLessEqual(val, 10, f"Stat mod {stat} for {r_key} unreasonably high: {val}")

            # 4. Racial abilities is a list with at least 2 entries
            self.assertIn("racial_abilities", r_data, f"Lineage {r_key} missing 'racial_abilities'")
            abilities = r_data["racial_abilities"]
            self.assertIsInstance(abilities, list)
            self.assertGreaterEqual(len(abilities), 2, f"Lineage {r_key} must have >= 2 racial abilities, got {len(abilities)}")
            for ab in abilities:
                self.assertIsInstance(ab, str)
                self.assertGreater(len(ab.strip()), 5)

    def test_generative_fuzzing_character_creation_all_lineages(self):
        """Generative property test: generate_starting_character succeeds for every creation lineage."""
        lineages = cg.get_character_creation_lineages()
        for r_key in lineages.keys():
            char = cg.generate_starting_character(
                name=f"Hero_{r_key}",
                race_key=r_key,
                start_tutorial=False
            )
            player = char.get("player", char)
            self.assertIsNotNone(player)
            self.assertEqual(player.get("race_key"), r_key)

            # Check stats
            stats = player.get("stats", {})
            for s in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
                self.assertIn(s, stats)
                self.assertGreaterEqual(stats[s], 1)

            # Check max HP
            self.assertGreater(player.get("max_hp", 0), 0)

            # Check physical profile
            phys = mechanics.get_physical_profile(player)
            self.assertIn(phys.get("size"), ("Tiny", "Small", "Medium", "Large"))
            self.assertIsInstance(phys.get("ac_mod"), int)
            self.assertIsInstance(phys.get("carry_mult"), (int, float))
            self.assertGreater(phys.get("carry_mult"), 0)

    def test_legacy_race_fallbacks_strict_safety(self):
        """Property: All purged sci-fi races map to existing fantasy lineages and generate cleanly."""
        fallbacks = getattr(cg, "LEGACY_RACE_FALLBACKS", {})
        self.assertTrue(bool(fallbacks))

        for purged_key in cg.PURGED_SCI_FI_RACES:
            self.assertIn(purged_key, fallbacks, f"Purged race {purged_key} missing from LEGACY_RACE_FALLBACKS")
            target = fallbacks[purged_key]
            self.assertIn(target, cg.RACIAL_LINEAGES, f"Fallback target {target} does not exist in RACIAL_LINEAGES")
            # Target must NOT be in purged list
            self.assertNotIn(target, cg.PURGED_SCI_FI_RACES)

            # Generate character with legacy key
            char = cg.generate_starting_character(name="OldSaveHero", race_key=purged_key, start_tutorial=False)
            player = char.get("player", char)
            self.assertIsNotNone(player)
            # Must resolve to fallback key, not the purged key
            self.assertEqual(player.get("race_key"), target)


class TestDnd30PixieMechanicsStress(unittest.TestCase):
    """
    Adversarial property-based stress tests on D&D 3.0 Pixie:
    - Tiny size mechanics (+2 AC/attack, -8 grapple, 0.5x carry, +8 stealth)
    - Permanent Greater Invisibility (passive 50% miss, flickering 20% on attack, deny DEX)
    - DR 5/cold iron against physical, cold iron, and elemental damage
    - Pixie Dust Sleep/Confusion saves, DC derivation, and immunities
    """

    def setUp(self):
        self.pixie = cg.generate_starting_character(name="Gossamer", race_key="pixie_fey_sprite", start_tutorial=False)

    def test_tiny_size_modifiers_invariants(self):
        """Property: Pixie size is Tiny and all Tiny modifiers match D&D 3.0 rules."""
        phys = mechanics.get_physical_profile(self.pixie)
        self.assertEqual(phys["size"], "Tiny")

        # Check root level and nested modifiers
        self.assertEqual(phys["ac_mod"], 2)
        self.assertEqual(phys["modifiers"]["ac_mod"], 2)
        self.assertEqual(phys["attack_mod"], 2)
        self.assertEqual(phys["modifiers"]["attack_mod"], 2)
        self.assertEqual(phys["grapple_mod"], -8)
        self.assertEqual(phys["modifiers"]["grapple_mod"], -8)
        self.assertEqual(phys["carry_mult"], 0.5)
        self.assertEqual(phys["modifiers"]["carry_mult"], 0.5)
        self.assertEqual(phys["stealth_bonus"], 8)
        self.assertEqual(phys["modifiers"]["stealth_bonus"], 8)

    def test_pixie_encumbrance_scaling_property(self):
        """Property: Pixie max carry weight is exactly half that of a medium humanoid with identical STR."""
        for test_str in range(1, 25):
            pixie_state = {
                "stats": {"STR": test_str},
                "race": self.pixie["race"],
                "feats": [],
                "equipped": {},
                "inventory": [],
                "physical": {"height_in": 20.0, "weight_lbs": 15.0, "age": 60}
            }
            human_state = {
                "stats": {"STR": test_str},
                "race": "Pure Human",
                "feats": [],
                "equipped": {},
                "inventory": [],
                "physical": {"height_in": 70.0, "weight_lbs": 170.0, "age": 25}
            }

            pixie_enc = mechanics.calculate_encumbrance(pixie_state)
            human_enc = mechanics.calculate_encumbrance(human_state)

            expected_pixie_max = round((test_str * 15.0) * 0.5, 1)
            expected_human_max = round(test_str * 15.0, 1)

            self.assertEqual(pixie_enc["max_weight_lbs"], expected_pixie_max)
            self.assertEqual(human_enc["max_weight_lbs"], expected_human_max)
            self.assertAlmostEqual(pixie_enc["max_weight_lbs"] * 2, human_enc["max_weight_lbs"], places=1)

    def test_permanent_greater_invisibility_state_machine(self):
        """Property: Permanent Greater Invisibility provides passive 50% miss chance and 20% flickering on attack."""
        # Case 1: Passive / not just attacked
        invis_passive = mechanics.evaluate_stealth_and_invisibility(self.pixie, in_combat=True, just_attacked=False)
        self.assertTrue(invis_passive["is_invisible"])
        self.assertFalse(invis_passive["flickering"])
        self.assertTrue(invis_passive["advantage_on_attack"])
        self.assertTrue(invis_passive["deny_target_dex_ac"])
        self.assertEqual(invis_passive["stealth_bonus"], 8)
        self.assertEqual(invis_passive["miss_chance_vs_actor"], 0.50)

        # Case 2: Just attacked (flickering for 1 turn)
        invis_attacked = mechanics.evaluate_stealth_and_invisibility(self.pixie, in_combat=True, just_attacked=True)
        self.assertTrue(invis_attacked["is_invisible"])
        self.assertTrue(invis_attacked["flickering"])
        self.assertTrue(invis_attacked["advantage_on_attack"])
        self.assertTrue(invis_attacked["deny_target_dex_ac"])
        self.assertEqual(invis_attacked["stealth_bonus"], 8)
        self.assertEqual(invis_attacked["miss_chance_vs_actor"], 0.20)

        # Case 3: Standard human (no invisibility)
        human = cg.generate_starting_character(name="Mundane", race_key="pure_human", start_tutorial=False)
        invis_human = mechanics.evaluate_stealth_and_invisibility(human, in_combat=True, just_attacked=False)
        self.assertFalse(invis_human["is_invisible"])
        self.assertFalse(invis_human["advantage_on_attack"])
        self.assertEqual(invis_human["miss_chance_vs_actor"], 0.0)

    def test_pixie_dr_5_cold_iron_fuzzing(self):
        """Property: DR 5/cold iron reduces physical damage by 5 (min 1), bypassed by cold iron or energy."""
        random.seed(42)
        for _ in range(50):
            dmg = random.randint(1, 100)

            # Mundane physical damage
            reduced = mechanics.resolve_damage_reduction(self.pixie, dmg, damage_type="physical", weapon_properties=[])
            expected_reduced = max(1, dmg - 5)
            self.assertEqual(
                reduced, expected_reduced,
                f"DR 5 failed on damage {dmg}: expected {expected_reduced}, got {reduced}"
            )

            # Cold iron weapon bypasses DR
            bypassed_ci = mechanics.resolve_damage_reduction(
                self.pixie, dmg, damage_type="physical", weapon_properties=["Cold Iron Shortsword"]
            )
            self.assertEqual(
                bypassed_ci, dmg,
                f"Cold iron failed to bypass DR on damage {dmg}: expected {dmg}, got {bypassed_ci}"
            )

            # Elemental / energy damage bypasses DR
            bypassed_elem = mechanics.resolve_damage_reduction(
                self.pixie, dmg, damage_type="fire", weapon_properties=[]
            )
            self.assertEqual(
                bypassed_elem, dmg,
                f"Fire damage improperly reduced by physical DR: expected {dmg}, got {bypassed_elem}"
            )

        # Boundary checks: zero or negative damage
        self.assertEqual(mechanics.resolve_damage_reduction(self.pixie, 0, "physical"), 0)
        self.assertEqual(mechanics.resolve_damage_reduction(self.pixie, -10, "physical"), 0)

    def test_pixie_dust_effects_and_immunities(self):
        """Property: Pixie Dust applies sleep/confusion with WIS saves and respects racial immunities."""
        # 1. Sleep effect on standard humanoid
        target = {"stats": {"WIS": 12}, "race": "Human", "feats": []}
        res_sleep = mechanics.apply_pixie_dust_effect(target, dust_choice="sleep", dc=15)
        self.assertEqual(res_sleep["effect_applied"], "incapacitated")
        self.assertEqual(res_sleep["dc"], 15)
        self.assertEqual(res_sleep["target_wis_mod"], 1)

        # 2. Confusion effect
        res_conf = mechanics.apply_pixie_dust_effect(target, dust_choice="confusion", dc=15)
        self.assertEqual(res_conf["effect_applied"], "confused")

        # 3. WIS modifier derivation property
        for wis_val in range(4, 25):
            t_state = {"stats": {"WIS": wis_val}, "race": "Human", "feats": []}
            res = mechanics.apply_pixie_dust_effect(t_state, dust_choice="sleep")
            expected_mod = (wis_val - 10) // 2
            self.assertEqual(res["target_wis_mod"], expected_mod)

        # 4. Immunity for synthetic, construct, and sleepless creatures
        immune_targets = [
            {"stats": {"WIS": 14}, "race": "synthetic android", "feats": []},
            {"stats": {"WIS": 10}, "race": "stone construct", "feats": []},
            {"stats": {"WIS": 12}, "race": "Elf", "feats": ["sleepless trance"]},
        ]
        for it in immune_targets:
            res_imm = mechanics.apply_pixie_dust_effect(it, dust_choice="sleep")
            self.assertTrue(res_imm.get("immune"))
            self.assertTrue(res_imm.get("saved"))
            self.assertIsNone(res_imm.get("effect"))


class TestMeadowNymphUnearthlyGraceAndAura(unittest.TestCase):
    """
    Adversarial property-based stress tests on Meadow Nymph:
    - Unearthly Grace CHA deflection AC calculation across CHA range 8 to 24
    - Strict armor restrictions (heavy armor disables deflection)
    - Blinding Beauty aura presence and DR 5/cold iron
    """

    def setUp(self):
        self.nymph = cg.generate_starting_character(name="Alseph", race_key="meadow_nymph_fey", start_tutorial=False)

    def test_unearthly_grace_cha_deflection_range_and_monotonicity(self):
        """Property: Unearthly Grace deflection bonus equals max(0, (CHA - 10) // 2) and is monotonically non-decreasing."""
        prev_ac = 0
        for cha in range(8, 25):
            nymph_state = {
                "race": self.nymph["race"],
                "racial_abilities": self.nymph["racial_abilities"],
                "feats": [],
                "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": cha},
                "equipped": {},
                "physical": {"height_in": 64.0, "weight_lbs": 120.0, "age": 120}
            }
            ac = mechanics.calculate_ac(nymph_state)
            expected_deflection = max(0, (cha - 10) // 2)
            expected_ac = 10 + expected_deflection

            self.assertEqual(
                ac, expected_ac,
                f"CHA {cha} produced AC {ac}, expected {expected_ac} (deflection +{expected_deflection})"
            )
            # Monotonicity invariant: higher CHA must never produce lower AC
            self.assertGreaterEqual(ac, prev_ac)
            prev_ac = ac

    def test_unearthly_grace_armor_exclusion_boundary(self):
        """Property: Unearthly Grace deflection applies ONLY in light/no armor and is disabled by heavy armor."""
        cha = 20  # +5 deflection bonus
        base_state = {
            "race": self.nymph["race"],
            "racial_abilities": self.nymph["racial_abilities"],
            "feats": [],
            "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": cha},
            "equipped": {},
            "physical": {"height_in": 64.0, "weight_lbs": 120.0, "age": 120}
        }

        # 1. Unarmored: AC = 10 (base) + 5 (deflection) = 15
        ac_unarmored = mechanics.calculate_ac(base_state)
        self.assertEqual(ac_unarmored, 15)

        # 2. Light Armor (Leather Jerkin: armor bonus 3 <= 3): AC = 10 + 3 + 5 = 18
        light_state = dict(base_state, equipped={"chest": "Leather Jerkin"})
        ac_light = mechanics.calculate_ac(light_state)
        self.assertEqual(ac_light, 18)

        # 3. Heavy Plate Armor (Heavy Steel Plate Armor: armor bonus 8, contains "plate"):
        # Deflection bonus MUST be disabled -> AC = 10 + 8 = 18 (NOT 18 + 5 = 23)
        heavy_plate = dict(base_state, equipped={"chest": "Heavy Steel Plate Armor"})
        ac_heavy_plate = mechanics.calculate_ac(heavy_plate)
        self.assertEqual(ac_heavy_plate, 18)

        # 4. Chainmail (contains "chain"):
        # Deflection bonus MUST be disabled
        heavy_chain = dict(base_state, equipped={"chest": "Chainmail Hauberk"})
        ac_heavy_chain = mechanics.calculate_ac(heavy_chain)
        self.assertLess(ac_heavy_chain, 10 + 5 + 5)  # must not have full armor + deflection

    def test_meadow_nymph_racial_abilities_and_dr(self):
        """Property: Meadow Nymph has Blinding Beauty, Dimension Door, and DR 5/cold iron."""
        abilities_str = " ".join(self.nymph.get("racial_abilities", []))
        self.assertIn("Unearthly Grace", abilities_str)
        self.assertIn("Blinding Beauty", abilities_str)
        self.assertIn("Dimension Door", abilities_str)

        # Test DR 5/cold iron
        dmg_normal = mechanics.resolve_damage_reduction(self.nymph, 15, "physical", [])
        self.assertEqual(dmg_normal, 10)
        dmg_ci = mechanics.resolve_damage_reduction(self.nymph, 15, "physical", ["cold iron"])
        self.assertEqual(dmg_ci, 15)


class TestSavageSpeciesMonstrousAdversarial(unittest.TestCase):
    """
    Adversarial property-based testing of Monstrous Playable Lineages (Savage Species):
    Minotaur, Gargoyle, Centaur, Half-Ogre, Ogre Titan-Brute, Troll, and Medusa.
    """

    def test_minotaur_mechanics_and_cunning(self):
        """Property: Minotaur has Large build (10ft reach, 2.0x carry, -1 AC, +4 grapple) and Natural Cunning."""
        mino = cg.generate_starting_character(name="Asterion", race_key="minotaur_labyrinth_breaker", start_tutorial=False)
        phys = mechanics.get_physical_profile(mino)

        self.assertEqual(phys["size"], "Large")
        self.assertEqual(phys["reach_ft"], 10)
        self.assertEqual(phys["reach_bonus_ft"], 5)
        self.assertEqual(phys["ac_mod"], -1)
        self.assertEqual(phys["carry_mult"], 2.0)
        self.assertEqual(phys["grapple_mod"], 4)

        abilities = " ".join(mino.get("racial_abilities", []))
        self.assertIn("Natural Cunning", abilities)
        self.assertIn("Gore Charge Attack", abilities)
        self.assertIn("Hammering Horns", abilities)

    def test_gargoyle_dr_10_magic_and_flight(self):
        """Property: Gargoyle has DR 10/Magic (bypassed by magic) and natural flight with wings graft slot."""
        garg = cg.generate_starting_character(name="Goliath", race_key="gargoyle_lithic_sentinel", start_tutorial=False)

        # DR 10/magic tests
        dmg_normal = mechanics.resolve_damage_reduction(garg, 25, "physical", [])
        self.assertEqual(dmg_normal, 15)
        dmg_bypassed = mechanics.resolve_damage_reduction(garg, 25, "physical", ["magic longsword"])
        self.assertEqual(dmg_bypassed, 25)

        # Minimum clamp to 1
        dmg_small = mechanics.resolve_damage_reduction(garg, 8, "physical", [])
        self.assertEqual(dmg_small, 1)

        # Anatomy: wings and flight
        limb = mechanics.get_limb_anatomy_profile(garg)
        self.assertTrue(limb.get("is_winged"))
        self.assertIn("wings", limb.get("unlocked_graft_slots", []))

        abilities = " ".join(garg.get("racial_abilities", []))
        self.assertIn("Stone Hide Damage Reduction", abilities)
        self.assertIn("Natural Flight", abilities)
        self.assertIn("Freeze", abilities)

    def test_centaur_equine_mechanics_and_barding(self):
        """Property: Centaur has Large build (2.0x carry), dedicated equine_barding slot, and +80 lbs capacity."""
        centaur = cg.generate_starting_character(name="Chiron", race_key="centaur_plains_vanguard", start_tutorial=False)
        phys = mechanics.get_physical_profile(centaur)

        self.assertEqual(phys["size"], "Large")
        self.assertEqual(phys["carry_mult"], 2.0)

        # Equipment slots must include equine_barding
        slots = mechanics.get_character_equipment_slots(centaur)
        self.assertIn("equine_barding", slots)

        # Encumbrance includes +80 lbs bonus capacity scaled by 2.0x
        enc = mechanics.calculate_encumbrance(centaur)
        str_val = centaur["stats"]["STR"]
        expected_max = round((str_val * 15.0 + 80.0) * 2.0, 1)
        self.assertEqual(enc["max_weight_lbs"], expected_max)

        abilities = " ".join(centaur.get("racial_abilities", []))
        self.assertIn("Large Equine Build & Barding Slot", abilities)
        self.assertIn("Galloping Overland Speed", abilities)
        self.assertIn("Trample", abilities)

    def test_half_ogre_and_ogre_titan_natural_armor_stacking(self):
        """Property: Half-Ogre grants +2 Natural AC; Ogre Titan-Brute grants +3 Natural AC."""
        # Unarmored baseline state with DEX 10 (mod 0) and Medium size (ac_mod 0)
        def _get_naked_natural_bonus(race_key):
            r_data = cg.RACIAL_LINEAGES[race_key]
            dummy = {
                "race": r_data["name"],
                "racial_abilities": r_data["racial_abilities"],
                "feats": [],
                "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
                "equipped": {},
                "physical": {"height_in": 70.0, "weight_lbs": 170.0, "age": 25}
            }
            return mechanics.calculate_ac(dummy) - 10

        self.assertEqual(_get_naked_natural_bonus("half_ogre_crusher"), 2)
        self.assertEqual(_get_naked_natural_bonus("ogre_titan_brute"), 3)

        # Test stats
        half_ogre_mods = cg.RACIAL_LINEAGES["half_ogre_crusher"]["stat_mods"]
        self.assertEqual(half_ogre_mods["STR"], 6)
        self.assertEqual(half_ogre_mods["CON"], 4)

        ogre_mods = cg.RACIAL_LINEAGES["ogre_titan_brute"]["stat_mods"]
        self.assertEqual(ogre_mods["STR"], 8)
        self.assertEqual(ogre_mods["CON"], 4)

    def test_feral_troll_living_regeneration_and_natural_armor(self):
        """Property: Troll has +2 Natural AC, Living Regeneration, and Large build."""
        troll = cg.generate_starting_character(name="Grendel", race_key="troll_fleshwarped", start_tutorial=False)
        phys = mechanics.get_physical_profile(troll)

        self.assertEqual(phys["size"], "Large")
        self.assertEqual(phys["carry_mult"], 2.0)

        abilities = " ".join(troll.get("racial_abilities", []))
        self.assertIn("Living Regeneration", abilities)
        self.assertIn("Rubbery Hide Natural Armor (+2 AC)", abilities)
        self.assertIn("Acid & Fire Suppression", abilities)
        self.assertIn("Rend Attack", abilities)

    def test_medusa_petrifying_gaze_and_toxic_immunity(self):
        """Property: Medusa has Petrifying Gaze (DC 15), Gorgon Venom, and Toxic/Petrification immunity."""
        medusa = cg.generate_starting_character(name="Stheno", race_key="medusa_gorgon_scion", start_tutorial=False)
        abilities = " ".join(medusa.get("racial_abilities", []))

        self.assertIn("Petrifying Gaze", abilities)
        self.assertIn("Gorgon Venom", abilities)
        self.assertIn("Lithic & Toxic Immunity", abilities)

        mods = cg.RACIAL_LINEAGES["medusa_gorgon_scion"]["stat_mods"]
        self.assertEqual(mods["CHA"], 4)
        self.assertEqual(mods["DEX"], 3)


class TestBackwardCompatibilityAndGlennyParity(unittest.TestCase):
    """
    Ensures Glenny's 4-armed chimera configuration, 2H grip, 9 grafts, and AC 14/16
    load with zero regressions alongside legacy baseline suites.
    """

    def test_glenny_4_armed_chimera_parity(self):
        """Property: Glenny retains 4 hand slots, 2H bow grip, 9 grafts, AC 14 base / 16 shielded."""
        glenny = cg.generate_starting_character(name="Glenny", start_tutorial=False)
        player = glenny.get("player", glenny)

        # 4 Hand slots
        eq = player.get("equipped", {})
        self.assertIn("main_hand", eq)
        self.assertIn("off_hand", eq)
        self.assertIn("lower_main_hand", eq)
        self.assertIn("lower_off_hand", eq)

        # 2H Bow grip binding
        self.assertIn("Bow", eq.get("main_hand", ""))
        self.assertIn("[2H Grip:", eq.get("off_hand", ""))

        # 9 Graft slots
        graft_slots = mechanics.get_character_graft_slots(player)
        self.assertEqual(len(graft_slots), 9)

        # AC baseline: 14 unshielded, 16 shielded
        ac_base = mechanics.calculate_ac(player)
        self.assertEqual(ac_base, 14)

        # Equip shield to off-hand (replacing 2H grip for shield test)
        player_shielded = dict(player, equipped=dict(eq, off_hand="Steel Buckler Shield"))
        ac_shielded = mechanics.calculate_ac(player_shielded)
        self.assertEqual(ac_shielded, 16)


if __name__ == "__main__":
    unittest.main()
