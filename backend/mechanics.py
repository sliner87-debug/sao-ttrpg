"""
Mechanics Engine for The Fractured Overlay (SAO TTRPG)
Handles mathematical crunch, dice logic, encumbrance physics, and equipment state.
"""

import math

# --- ITEM WEIGHT HEURISTICS ---
DEFAULT_WEIGHT_MAP = {
    # Weapons
    "axe": 4.5,
    "sword": 3.5,
    "hammer": 6.0,
    "dagger": 1.0,
    "bow": 3.0,
    "pistol": 2.5,
    "rifle": 8.0,
    "spear": 5.0,
    # Armor & Apparel
    "rig": 30.0,
    "hauberk": 25.0,
    "plate": 45.0,
    "leather": 12.0,
    "chain": 28.0,
    "cloak": 3.0,
    "pelt": 5.0,
    "boots": 4.0,
    "helm": 5.0,
    "shield": 8.0,
    # Utility & Hardware
    "spool": 12.0,
    "cord": 8.0,
    "line": 6.0,
    "tripwire": 3.0,
    "snare": 5.0,
    "trap": 7.0,
    "jar": 3.5,
    "marrow": 2.5,
    "water": 1.5,
    "ration": 1.0,
    "clipboard": 2.0,
    "deck": 3.0,
    "usb": 0.1,
    "scroll": 0.5,
    "ore": 5.0,
    "scrap": 1.0
}

def get_item_weight(item):
    """Calculates total weight for a single item entry (considering quantity)."""
    if isinstance(item, str):
        name = item.lower()
        qty = 1
        if " x" in name:
            parts = name.rsplit(" x", 1)
            name = parts[0]
            try:
                qty = int(parts[1])
            except ValueError:
                pass
        base_w = 1.0
        for kw, w in DEFAULT_WEIGHT_MAP.items():
            if kw in name:
                base_w = w
                break
        return round(base_w * qty, 1)

    if isinstance(item, dict):
        qty = item.get("qty", 1)
        if "weight" in item and item["weight"] is not None:
            try:
                return round(float(item["weight"]) * qty, 1)
            except (ValueError, TypeError):
                pass
        
        name = item.get("name", "").lower()
        desc = item.get("desc", "").lower()
        full_text = f"{name} {desc}"
        
        base_w = 1.0
        for kw, w in DEFAULT_WEIGHT_MAP.items():
            if kw in full_text:
                base_w = w
                break
        return round(base_w * qty, 1)

    return 1.0

def calculate_encumbrance(player_state):
    """
    Calculates total carrying weight, slot capacity, encumbrance tier, and modifiers.
    Base STR * 15 = Max Carry Weight (lbs).
    10 + (STR // 2) = Max Inventory Slots.
    """
    stats = player_state.get("stats", {})
    str_val = stats.get("STR", 10)
    
    max_weight = round(str_val * 15.0, 1)
    max_slots = 10 + (str_val // 2)
    
    current_weight = 0.0
    used_slots = 0
    
    # Calculate weight of equipped gear
    equipped = player_state.get("equipped", {})
    if isinstance(equipped, dict):
        for slot, item_name in equipped.items():
            if item_name and item_name != "None":
                current_weight += get_item_weight({"name": item_name, "qty": 1})
                
    # Calculate weight and slots of backpack inventory
    inventory = player_state.get("inventory", [])
    for item in inventory:
        w = get_item_weight(item)
        current_weight += w
        # Stacking slots: each entry takes 1 slot, or 1 slot per 5 units for small items
        qty = item.get("qty", 1) if isinstance(item, dict) else 1
        slots_taken = max(1, math.ceil(qty / 5)) if w < 2.0 else qty
        used_slots += slots_taken
        
    current_weight = round(current_weight, 1)
    
    # Determine Encumbrance Tier
    weight_ratio = current_weight / max_weight if max_weight > 0 else 1.0
    
    if weight_ratio <= 0.50:
        tier = "Unencumbered"
        label = "🟢 Unencumbered"
        penalties = {"dex_mod": 0, "speed_pct": 100, "disadvantage_stealth": False}
    elif weight_ratio <= 0.75:
        tier = "Light Load"
        label = "🟢 Light Load"
        penalties = {"dex_mod": 0, "speed_pct": 100, "disadvantage_stealth": False}
    elif weight_ratio <= 1.0:
        tier = "Heavy Load"
        label = "🟠 Heavy Load"
        penalties = {"dex_mod": -2, "speed_pct": 85, "disadvantage_stealth": True}
    else:
        tier = "Overencumbered"
        label = "🔴 Overencumbered"
        penalties = {"dex_mod": -5, "speed_pct": 50, "disadvantage_stealth": True}
        
    return {
        "current_weight_lbs": current_weight,
        "max_weight_lbs": max_weight,
        "weight_percent": min(1.0, current_weight / max_weight) if max_weight > 0 else 1.0,
        "used_slots": used_slots,
        "max_slots": max_slots,
        "slots_percent": min(1.0, used_slots / max_slots) if max_slots > 0 else 1.0,
        "tier": tier,
        "label": label,
        "penalties": penalties
    }

def calculate_ac(player_state, encumbrance=None):
    """Calculates Armor Class based on DEX, equipped armor, and encumbrance penalties."""
    if encumbrance is None:
        encumbrance = calculate_encumbrance(player_state)
        
    stats = player_state.get("stats", {})
    dex_val = stats.get("DEX", 10)
    dex_mod = (dex_val - 10) // 2
    
    # Encumbrance penalty to DEX
    dex_mod += encumbrance["penalties"]["dex_mod"]
    
    base_ac = 10 + dex_mod
    
    # Armor checks
    equipped = player_state.get("equipped", {})
    chest = equipped.get("chest", "").lower()
    
    armor_bonus = 0
    if "einherjar" in chest or "plate" in chest or "gr. 5" in chest:
        armor_bonus = 8
    elif "chain" in chest or "hauberk" in chest:
        armor_bonus = 5
    elif "leather" in chest or "fur" in chest:
        armor_bonus = 3
        
    # Off-hand shield checks
    off_hand = equipped.get("off_hand", "").lower()
    shield_bonus = 2 if "shield" in off_hand else 0
    
    return max(10, base_ac + armor_bonus + shield_bonus)
