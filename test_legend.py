import map_engine
try:
    map_engine.generate_overlay()
    print("Overlay generated successfully.")
except Exception as e:
    with open("error.txt", "w") as f:
        f.write(str(e))
