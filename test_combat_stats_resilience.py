import unittest
import backend.mechanics as mechanics

class TestCombatStatsResilience(unittest.TestCase):
    def test_recalculate_entity_combat_stats_none_and_types(self):
        """Ensure recalculate_entity_combat_stats never raises TypeError on None or malformed inputs."""
        self.assertIsNone(mechanics.recalculate_entity_combat_stats(None))
        self.assertEqual(mechanics.recalculate_entity_combat_stats("not_a_dict"), "not_a_dict")
        self.assertEqual(mechanics.recalculate_entity_combat_stats(123), 123)

    def test_recalculate_entity_combat_stats_null_fields(self):
        """Ensure entity with null ac, dr, base_ac, base_dr, or active_debuffs survives."""
        ent = {
            "id": "npc_bounty_board",
            "name": "Bounty Board",
            "type": "neutral",
            "status": ["Intact"],
            "ac": None,
            "dr": None,
            "base_ac": None,
            "base_dr": None,
            "active_debuffs": None
        }
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["base_ac"], 14)
        self.assertEqual(res["base_dr"], 0)
        self.assertEqual(res["ac"], 14)
        self.assertEqual(res["dr"], 0)
        self.assertEqual(res["active_debuffs"], [])

    def test_recalculate_entity_combat_stats_with_debuffs(self):
        """Ensure debuffs with null or string fields are parsed safely without crashing."""
        ent = {
            "id": "test_golem",
            "ac": 16,
            "dr": 4,
            "active_debuffs": [
                {"name": "Foundry Shred", "ac_penalty": -4, "dr_override": None},
                {"name": "Slag Dissolve", "ac_penalty": None, "dr_override": 0},
                None,
                "invalid_debuff"
            ]
        }
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["ac"], 12)  # 16 - 4
        self.assertEqual(res["dr"], 0)   # Overridden to 0

    def test_apply_entity_debuff_resilience(self):
        """Ensure apply_entity_debuff handles missing and null fields."""
        ent = {"id": "test_target", "ac": None, "dr": None}
        res = mechanics.apply_entity_debuff(ent, {
            "name": None,
            "ac_penalty": None,
            "dr_override": None,
            "turns_remaining": None
        })
        self.assertEqual(res["ac"], 14)
        self.assertEqual(res["dr"], 0)
        self.assertTrue(len(res["active_debuffs"]) >= 1)

if __name__ == "__main__":
    unittest.main()
