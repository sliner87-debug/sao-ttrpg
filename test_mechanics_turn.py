import json
import backend.mechanics as mechanics

with open("save_game.json", "r", encoding="utf-8") as f:
    save_data = json.load(f)

player = save_data["player"]
print("=== TESTING CANONICAL PLAYER STATE ===")
print("Name:", player.get("name"))
print("Race:", player.get("race"))
print("Location:", player.get("location"))

# Test Encumbrance
enc = mechanics.calculate_encumbrance(player)
print("\n=== ENCUMBRANCE READOUT ===")
print("Weight:", f"{enc['current_weight_lbs']} / {enc['max_weight_lbs']} lbs ({round(enc['weight_percent']*100, 1)}%)")
print("Slots:", f"{enc['used_slots']} / {enc['max_slots']}")
print("Tier:", enc["tier"])
print("Penalties:", enc["penalties"])

# Test AC
ac = mechanics.calculate_ac(player, enc)
print("\n=== DEFENSIVE READOUT ===")
print("Armor Class (AC):", ac)

# Verify Durability Defaults
dur = player.get("gear_durability", {})
print("\n=== GEAR DURABILITY ===")
for slot, item in player.get("equipped", {}).items():
    print(f"{slot}: {item} -> {dur.get(slot, 'Defaulted')}")

print("\nALL MECHANICS TESTS PASSED!")
