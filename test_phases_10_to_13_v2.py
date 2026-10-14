"""
Comprehensive Verification Suite for Phases 10–13 in SAO Sandbox V2:
- Phase 10: Planetary Patchwork Earth (6 Global 1-50 Floor Raids), Dual-Scale Transit (Leyline Gate vs. Overland Trek), Stratum & Checkpoint Floor Pacing, Mid-Boss & Apex Boss fights.
- Phase 11: 10-Second Revival Window (Revival Stone, Companion Emergency Save, Emergency Crystal), Rogue-Lite Legacy Reset (Monument of Life + Corpse Cache + Homestead/Vault/Guild persistence), Crimson Anti-Crystal Trap Floors, Info Broker 'Cipher', Raid Strategy Briefings, Last Attack (LA) 1-of-1 Unique Relics, and 1-of-1 Unique Skills.
- Phase 12: Macro Motivation 'The Stabilizer Merge' (Anomaly Bleed escalation vs. Permanent 0% Lock upon Mid-Boss defeat, Rival Frontline Ticker & SOS Rescue, Enclave Stewardship & Outbreak Siege).
- Phase 13: +1 to +50 Lisbeth Master Smith Enhancement, Companion 3-Stage Personal Quests & Tier 2 Ascension & 0 HP Crisis, and Player-Founded Guilds & Autonomous Strike Squads.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import backend.mechanics as mechanics
import backend.world_atlas as world_atlas
import backend.schemas as schemas
import map_engine


def make_test_player() -> dict:
    return {
        "name": "Banki",
        "level": 5,
        "xp": 0,
        "hp": 150,
        "max_hp": 150,
        "col": 5000,
        "race": "Pure-Blood Human",
        "class": "Aincrad Vanguard",
        "stats": {"STR": 16, "DEX": 14, "CON": 16, "INT": 12, "WIS": 14, "CHA": 12},
        "equipped": {
            "head": "Iron Helm",
            "chest": "Vanguard Breastplate",
            "main_hand": "Elucidator Prototype",
            "off_hand": "Kite Shield",
            "accessory": "Crucible Vanguard Signet",
        },
        "inventory": [
            {"name": "Elucidator Prototype", "rarity": "Rare", "slot": "main_hand", "qty": 1, "durability": 100, "max_durability": 100},
            {"name": "Divine Stone of Returning Soul", "rarity": "Legendary", "slot": "consumable", "qty": 1, "durability": 1, "max_durability": 1},
        ],
        "skills": {
            "One-Handed Sword Mastery": {"mastery": 260, "tier": "Adept"},
            "Dual-Wielding Reflex": {"mastery": 255, "tier": "Adept"},
            "Cartography & Navigation": {"mastery": 200, "tier": "Journeyman"},
        },
        "feats": [],
        "spells": [],
        "companions": {
            "Ren": {
                "name": "Ren",
                "hp": 35,
                "max_hp": 35,
                "ac": 16,
                "affinity": 55,
                "active": True,
                "recruited": True,
            }
        },
        "homestead": {
            "owned": True,
            "name": "Washington Borough Manor",
            "vault_col": 2500,
            "vault_items": [{"name": "Stored Mythic Core", "qty": 1}],
        },
        "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
    }


def test_phase_10_planetary_raids_and_transit():
    p = make_test_player()
    raids = mechanics.ensure_planetary_raid_system(p)
    assert len(mechanics.GLOBAL_RAID_REGISTRY) == 6
    assert "pohatcong_spire" in raids["raid_nodes"]
    assert "grand_canyon_monolith" in raids["raid_nodes"]
    assert mechanics.GLOBAL_RAID_REGISTRY["grand_canyon_monolith"]["total_floors"] == 50

    # Option 1 Fast Travel to sealed gate should fail
    gate_fail = mechanics.travel_to_global_raid(p, "tokyo_override", travel_mode="leyline_gate")
    assert not gate_fail["success"]

    # Option 3 Overland Expedition to Tokyo Override unseals the gate!
    overland_ok = mechanics.travel_to_global_raid(p, "tokyo_override", travel_mode="overland")
    assert overland_ok["success"]
    assert raids["raid_nodes"]["tokyo_override"]["gate_unsealed"] is True

    # Now Leyline Gate Fast Travel to Tokyo Override succeeds!
    gate_ok = mechanics.travel_to_global_raid(p, "tokyo_override", travel_mode="leyline_gate")
    assert gate_ok["success"]

    # Switch back to Pohatcong Spire (10F, Mid-Boss F5) and advance floors
    mechanics.travel_to_global_raid(p, "pohatcong_spire", travel_mode="leyline_gate")
    for target_f in range(2, 6):
        f_res = mechanics.advance_raid_floor(p, "pohatcong_spire", encounter_override="vanguard_skirmish")
        assert f_res["success"]
        assert f_res["current_floor"] == target_f

    # At Floor 5 (Mid-Boss Floor), advancing to Floor 6 is gated until Mid-Boss is defeated
    blocked = mechanics.advance_raid_floor(p, "pohatcong_spire")
    assert not blocked["success"] and blocked.get("at_mid_boss_gate") is True
    print("[PASS] Phase 10: Planetary Raids, Dual-Scale Transit & Floor Checkpoint Pacing")


def test_phase_11_revival_legacy_anticrystal_broker_la_uniques():
    p = make_test_player()
    mechanics.ensure_planetary_raid_system(p)

    # 1. Crimson Anti-Crystal Trap Floor jams Teleport Crystal
    f_ambush = mechanics.advance_raid_floor(p, "pohatcong_spire", encounter_override="anti_crystal_ambush")
    assert f_ambush["anti_crystal_active"] is True
    tp_jam = mechanics.use_teleport_crystal(p)
    assert not tp_jam["success"] and tp_jam.get("blocked_by_anti_crystal") is True

    # Disable Anti-Crystal Jammer -> Teleport Crystal works again!
    jam_off = mechanics.disable_anti_crystal_jammer(p, "pohatcong_spire")
    assert jam_off["success"]
    tp_ok = mechanics.use_teleport_crystal(p)
    assert tp_ok["success"]

    # 2. Info Broker 'Cipher' Floor Recon & Boss Dossier + Strategy Briefing
    recon = mechanics.purchase_broker_intel(p, "pohatcong_spire", "floor_recon")
    dossier = mechanics.purchase_broker_intel(p, "pohatcong_spire", "boss_dossier")
    brief = mechanics.conduct_raid_strategy_briefing(p, "pohatcong_spire", "Iron Vanguard Shield-Wall")
    assert recon["success"] and dossier["success"] and brief["success"]

    # With Cipher Floor Recon purchased, anti_crystal_ambush is automatically pre-empted!
    f_preempt = mechanics.advance_raid_floor(p, "pohatcong_spire", encounter_override="anti_crystal_ambush")
    assert f_preempt["anti_crystal_active"] is False

    # 3. 0 HP 10-Second Revival Window (Companion Save & Revival Stone)
    crisis = mechanics.trigger_zero_hp_crisis(p)
    assert crisis["crisis_active"] is True and p["hp"] == 0
    comp_save = mechanics.resolve_revival_window(p, method="companion_save")
    assert comp_save["success"] and p["hp"] > 0

    mechanics.trigger_zero_hp_crisis(p)
    stone_save = mechanics.resolve_revival_window(p, method="revival_stone")
    assert stone_save["success"] and p["hp"] == p["max_hp"]

    # 4. Rogue-Lite Legacy Reset & Corpse Cache Recovery
    mechanics.trigger_zero_hp_crisis(p)
    legacy = mechanics.resolve_revival_window(p, method="expire")
    assert legacy["legacy_reset_executed"] is True
    assert p["name"] == "Banki II"
    assert p["homestead"]["vault_col"] == 2500  # Homestead & Vault preserved!
    assert len(p["death_system"]["monument_of_life"]) == 1

    rec = mechanics.recover_corpse_cache(p)
    assert rec["success"] and rec["col_recovered"] > 0

    # 5. Hidden 1-of-1 Unique Skill Awakening
    u_res = mechanics.evaluate_unique_skill_awakening(p)
    assert u_res["awakened"] is True
    assert u_res["skill_id"] == "twin_titan_execution"
    print("[PASS] Phase 11: 10s Revival, Legacy Reset, Corpse Cache, Anti-Crystal, Cipher, Briefing & Unique Skills")


def test_phase_12_stabilizer_merge_and_enclave():
    p = make_test_player()
    mechanics.ensure_planetary_raid_system(p)

    # Unstabilized Pohatcong Spire builds Anomaly Bleed on daily ticks
    b0 = p["planetary_raids"]["raid_nodes"]["pohatcong_spire"]["anomaly_bleed"]
    mechanics.advance_living_world_day(p, days=3)
    b1 = p["planetary_raids"]["raid_nodes"]["pohatcong_spire"]["anomaly_bleed"]
    assert b1 > b0
    # Rival squad is now pinned at Floor 5 Mid-Boss!
    assert p["planetary_raids"]["raid_nodes"]["pohatcong_spire"]["rival_squad"]["status"] == "pinned_at_mid_boss"

    # Rescue pinned frontline squad
    sos = mechanics.rescue_pinned_frontline_squad(p, "pohatcong_spire")
    assert sos["success"]

    # Defeat Floor 5 Mid-Boss -> Activates THE STABILIZER BRAKE (is_stabilized=True, anomaly_bleed=0)!
    mb = mechanics.engage_raid_mid_boss(p, "pohatcong_spire", damage_dealt=500)
    assert mb["defeated"] is True
    assert mb["is_stabilized"] is True
    assert p["planetary_raids"]["raid_nodes"]["pohatcong_spire"]["anomaly_bleed"] == 0

    # Advance 5 more Living World days -> Pohatcong Spire Anomaly Bleed stays locked at 0%!
    mechanics.advance_living_world_day(p, days=5)
    assert p["planetary_raids"]["raid_nodes"]["pohatcong_spire"]["anomaly_bleed"] == 0

    # Waypoint Crystal to Floor 5 now works!
    wp = mechanics.use_waypoint_crystal(p, "pohatcong_spire")
    assert wp["success"] and wp["floor"] == 5

    # Defeat Floor 10 Apex Boss -> Unseals Delaware Abyss gate & grants 1-of-1 [LA-Unique] Relic!
    ab = mechanics.engage_raid_apex_boss(p, "pohatcong_spire", damage_dealt=1000)
    assert ab["defeated"] is True
    assert ab["unsealed_raid_id"] == "delaware_abyss"
    assert p["planetary_raids"]["raid_nodes"]["delaware_abyss"]["gate_unsealed"] is True

    # Enclave Stewardship upgrade
    enc = mechanics.contribute_to_enclave_stewardship(p, 250)
    assert enc["success"] and enc["defense_rating"] > 40
    print("[PASS] Phase 12: The Stabilizer Merge (0% Anomaly Bleed Lock), SOS Rescue & Enclave Stewardship")


def test_phase_13_smithing_companions_and_guilds():
    p = make_test_player()
    p["col"] = 25000

    # 1. +1 to +50 Master Smith Enhancement
    enh1 = mechanics.enhance_equipment(p, slot="main_hand", use_master_smith=True, target_levels=15)
    assert enh1["success"]
    assert enh1["enhancement_level"] == 15
    assert "+15" in p["equipped"]["main_hand"]

    # 2. Companion Personal Quest (3 Stages -> Tier 2 Ascension) & 0 HP Crisis
    for st_idx in range(1, 4):
        cq = mechanics.advance_companion_personal_quest(p, "Ren")
        assert cq["success"] and cq["stage"] == st_idx
    assert p["companions"]["Ren"]["ascended"] is True
    assert p["companions"]["Ren"]["affinity"] == 100

    c_crisis = mechanics.trigger_companion_crisis(p, "Ren")
    assert c_crisis["in_mortal_crisis"] is True and p["companions"]["Ren"]["hp"] == 0
    c_saved = mechanics.resolve_companion_crisis(p, "Ren")
    assert c_saved["success"] and p["companions"]["Ren"]["hp"] > 0

    # 3. Player-Founded Guilds & Autonomous Strike Squads
    g_charter = mechanics.charter_player_guild(p, "Aincrad Liberation Front", "Clear Every Spire.")
    assert g_charter["success"]
    g_rec = mechanics.recruit_guild_strike_squad(p, "Bravo Vanguard")
    assert g_rec["success"]
    g_disp = mechanics.dispatch_guild_squad(p, "squad_alpha", "pohatcong_spire", "farm_strata")
    assert g_disp["success"]
    g_col = mechanics.collect_guild_dispatch_rewards(p)
    assert g_col["success"] and g_col["col_collected"] > 0

    # 4. Global Map & World Atlas helpers
    g_locs = world_atlas.get_planetary_raid_locations()
    assert len(g_locs) == 6
    g_map = map_engine.generate_global_atlas_overlay(p)
    assert os.path.exists(g_map)
    print("[PASS] Phase 13: +1 to +50 Master Smithing, Companion Ascension, Player Guilds & Global Map Overlay")


if __name__ == "__main__":
    test_phase_10_planetary_raids_and_transit()
    test_phase_11_revival_legacy_anticrystal_broker_la_uniques()
    test_phase_12_stabilizer_merge_and_enclave()
    test_phase_13_smithing_companions_and_guilds()
    print("\nALL PHASES 10-13 V2 TESTS PASSED SUCCESSFULLY!")
