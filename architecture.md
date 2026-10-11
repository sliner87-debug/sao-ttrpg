# SAO TTRPG: Cloud Architecture & Game Design

## Core Philosophy
A cloud-based, accessible-anywhere TTRPG built on Streamlit. The world is persistent, asynchronous, and procedurally dynamic, utilizing a "Director" AI pattern to optimize API limits while maintaining a deeply cohesive narrative.

## 1. Technical Stack
* **Frontend UI:** Streamlit (`app.py`). Handles chat, stats sidebar, and image rendering.
* **AI Engine:** Google Gemini API (`google-genai` Python SDK).
* **Database:** Firebase (Firestore) or Supabase (Free Tier) to store the World State, Player Stats, and generated Entities.
* **Hosting:** Streamlit Community Cloud (via GitHub).

## 2. The Agent Hierarchy & Optimization

### A. The Game Master (The "Encounter Director")
* To save on API limits and ensure characters don't contradict each other, the GM acts as the Director for the entire room. 
* Instead of calling 5 AIs for 5 goblins, the system passes the stats of all 5 goblins to the GM in a single prompt. The GM resolves the entire turn, formatting the output so the UI can display separate chat bubbles for each entity.

### B. The Cardinal System (Background & Catch-Up Engine)
* **Catch-Up Mechanic:** When a user logs in, the Cardinal System calculates the offline time delta and instantly simulates missed events (economy shifts, frontline progress) before loading the UI.

### C. System Initialization & Procedural Mutations
* **The "Glitch/Magic" Mechanic:** When the database first initializes (or when new floors are unlocked), the world does not spawn static monsters. 
* The system applies **Procedural Magical Mutations** to base templates. A standard "Frenzy Boar" might spawn as a "Crystalline Frenzy Boar" or "Aether-Touched Boar."
* These mutations are saved to the database and dynamically alter:
  1. **Stats:** (e.g., Crystalline adds high physical defense).
  2. **Behavior:** Passed to the GM Director to change how they fight.
  3. **Visuals:** Injected into the image generation prompt to ensure the art reflects the specific mutation.
