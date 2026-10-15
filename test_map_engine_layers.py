"""
test_map_engine_layers.py
Authoritative verification test suite for the Multi-Sector, 5-Layer Deep-GIS Map Engine.
Tests sector configuration, layer metadata, coordinate math, skill thresholds,
subterranean telemetry, and fallback rendering using unittest.
"""

import os
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

class TestMapEngineLayers(unittest.TestCase):
    def test_sectors_and_layers_registry(self):
        import map_engine
        self.assertTrue(hasattr(map_engine, "SECTORS"))
        self.assertTrue(hasattr(map_engine, "LAYERS"))

        expected_sectors = [
            "sector0_core",
            "sector1_primary",
            "sector2_west_nw",
            "sector3_north_east",
            "sector4_south_sw",
            "master_100mi",
            "global_raid"
        ]
        for s_id in expected_sectors:
            self.assertIn(s_id, map_engine.SECTORS)
            s = map_engine.SECTORS[s_id]
            self.assertIn("name", s)
            self.assertIn("radius_miles", s)
            self.assertIn("center_gps", s)

        expected_layers = [
            "usgs_topo",
            "satellite_ortho",
            "lidar_hillshade",
            "bathymetry_underground",
            "vertical_cross_section"
        ]
        for l_id in expected_layers:
            self.assertIn(l_id, map_engine.LAYERS)
            layer = map_engine.LAYERS[l_id]
            self.assertIn("label", layer)

    def test_gps_to_grid_conversion(self):
        import map_engine

        # Washington Borough origin (40.7584 N, -74.9793 W) should be centered at (50, 50)
        center_gx, center_gy = map_engine.gps_to_grid(40.7584, -74.9793, "sector1_primary")
        self.assertEqual(round(center_gx), 50)
        self.assertEqual(round(center_gy), 50)

        # Sector 0 center should also be (50, 50)
        s0_gx, s0_gy = map_engine.gps_to_grid(40.7584, -74.9793, "sector0_core")
        self.assertEqual(round(s0_gx), 50)
        self.assertEqual(round(s0_gy), 50)

        # Clamping checks
        far_north_gx, far_north_gy = map_engine.gps_to_grid(45.0, -74.9793, "sector1_primary")
        self.assertEqual(far_north_gy, 0)

        far_south_gx, far_south_gy = map_engine.gps_to_grid(35.0, -74.9793, "sector1_primary")
        self.assertEqual(far_south_gy, 100)

    def test_sector_zones_integration(self):
        import map_engine

        s1_zones = map_engine.get_sector_zones("sector1_primary")
        self.assertGreaterEqual(len(s1_zones), 3)
        zone_ids = [z["id"] for z in s1_zones]
        self.assertIn("washington_borough", zone_ids)

    def test_cartography_skill_thresholds(self):
        import map_engine

        # V1 list compatibility
        self.assertTrue(map_engine.has_cartography_skill("Cartography I", ["Cartography I", "Swordsmanship"]))
        self.assertFalse(map_engine.has_cartography_skill("Cartography II", ["Cartography I"]))
        self.assertTrue(map_engine.has_cartography_skill("Aether-Mapping", ["Aether-Mapping"]))
        self.assertTrue(map_engine.has_cartography_skill("Cartography I", ["Omniscience (DEV)"]))

        # V2 1-1000 mastery dictionary compatibility
        v2_skills = {
            "Cartography": {"mastery": 120, "tier": "Adept"},
            "Survival": {"mastery": 50, "tier": "Novice"}
        }
        self.assertTrue(map_engine.has_cartography_skill("Cartography I", v2_skills)) # >= 50
        self.assertTrue(map_engine.has_cartography_skill("Cartography II", v2_skills)) # >= 100
        self.assertFalse(map_engine.has_cartography_skill("Cartography III", v2_skills)) # requires >= 250

        v2_master_skills = {
            "Cartography": {"mastery": 550, "tier": "Master"}
        }
        self.assertTrue(map_engine.has_cartography_skill("Cartography IV", v2_master_skills)) # >= 500

    def test_subterranean_depth_telemetry(self):
        import map_engine

        # Oxford Mines: 2,700 ft depth
        oxford_telemetry = map_engine.calculate_depth_telemetry(
            collar_asl_ft=600,
            bottom_asl_ft=-2100,
            phreatic_table_asl=400
        )
        self.assertEqual(oxford_telemetry["depth_ft"], 2700)
        self.assertTrue(oxford_telemetry["submerged"])
        # (400 - (-2100)) * 0.433 = 2500 * 0.433 = 1082.5 PSI
        self.assertEqual(round(oxford_telemetry["hydrostatic_psi"], 1), 1082.5)

        # Surface location (above water table)
        surface_telemetry = map_engine.calculate_depth_telemetry(
            collar_asl_ft=460,
            bottom_asl_ft=460,
            phreatic_table_asl=400
        )
        self.assertEqual(surface_telemetry["depth_ft"], 0)
        self.assertFalse(surface_telemetry["submerged"])
        self.assertEqual(surface_telemetry["hydrostatic_psi"], 0.0)

    def test_render_sector_layer_execution(self):
        import map_engine

        player_state = {
            "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
            "skills": {"Cartography": {"mastery": 75}},
            "coords": {"x": 50, "y": 50}
        }

        # Render Sector 1 USGS Topo
        out_path, telemetry = map_engine.render_sector_layer(
            sector_id="sector1_primary",
            layer_id="usgs_topo",
            player_state=player_state
        )
        self.assertIsNotNone(out_path)
        self.assertTrue(os.path.exists(out_path))
        self.assertIsInstance(telemetry, dict)

        # Render Subterranean layer
        sub_path, sub_telemetry = map_engine.render_sector_layer(
            sector_id="sector1_primary",
            layer_id="bathymetry_underground",
            player_state=player_state
        )
        self.assertIsNotNone(sub_path)
        self.assertTrue(os.path.exists(sub_path))

        # Render Vertical Cross-Section
        cross_path, cross_telemetry = map_engine.render_sector_layer(
            sector_id="sector1_primary",
            layer_id="vertical_cross_section",
            player_state=player_state
        )
        self.assertIsNotNone(cross_path)
        self.assertTrue(os.path.exists(cross_path))

    def test_all_5_sectors_and_master(self):
        import map_engine
        sectors_to_test = [
            "sector0_core",
            "sector1_primary",
            "sector2_west_nw",
            "sector3_north_east",
            "sector4_south_sw",
            "master_100mi"
        ]
        for s_id in sectors_to_test:
            out_p, tel = map_engine.render_sector_layer(s_id, "usgs_topo")
            self.assertIsNotNone(out_p)
            self.assertTrue(os.path.exists(out_p))

    def test_legacy_wrapper_compatibility(self):
        import map_engine

        legacy_overlay = map_engine.generate_overlay(player_skills=["Cartography I"])
        self.assertIsNotNone(legacy_overlay)
        self.assertTrue(os.path.exists(legacy_overlay))

        legacy_global = map_engine.generate_global_atlas_overlay(player_state={})
        self.assertIsNotNone(legacy_global)
        self.assertTrue(os.path.exists(legacy_global))

if __name__ == "__main__":
    unittest.main()
