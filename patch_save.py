import json
import base64
import time

save_path = "save_game.json"
patched_path = "patched_save.json"

img1_path = r"C:\Users\sline\.gemini\antigravity\brain\1869f60e-76ac-40bd-99a3-3b51578ede14\.user_uploaded\media_1791682168362_31c2090d.jpg"
img2_path = r"C:\Users\sline\.gemini\antigravity\brain\1869f60e-76ac-40bd-99a3-3b51578ede14\.user_uploaded\media_1791682168564_3a095690.jpg"

with open(save_path, 'r') as f:
    data = json.load(f)

# Base64 encode the images
def encode_img(path):
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

img1_b64 = encode_img(img1_path)
img2_b64 = encode_img(img2_path)

# We will append two new system messages with the images so they appear at the bottom
data["messages"].append({
    "role": "system",
    "content": "### 🛠️ Developer Root Command: Asset Re-Injection\n\nManually syncing [Einherjar Rig] visual asset to player databanks...",
    "image_data": img1_b64
})

data["messages"].append({
    "role": "system",
    "content": "Manually syncing [Fenrir's Tusk & Mjölnir-Null] visual assets to player databanks...",
    "image_data": img2_b64
})

# Update last_saved
data["last_saved"] = time.time()

with open(patched_path, 'w') as f:
    json.dump(data, f)

print("Saved patched_save.json successfully!")
