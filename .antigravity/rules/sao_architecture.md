# SAO Architecture Rules

- No context bleed: Subagents must only read `visible_room.json` and their own character sheet.
- All UI components must use Streamlit session state safely.
- Never overwrite master data files (like save.json) directly; always append or update via Python logic.
- All backend scripts must rely on structured JSON.
