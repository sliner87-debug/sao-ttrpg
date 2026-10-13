---
name: sao-ttrpg-sync
description: Synchronize the SAO TTRPG Persistent World (Cardinal System: Fractured Earth Overlay) between the Asus ROG G75VW (ROG_G75VW) and the Chromebook (CHROMEBOOK) using GitHub (v2-sandbox), Google Drive, Google Sheets, and NotebookLM.
---

# SAO TTRPG Cross-Laptop Agent Sync (`sao-ttrpg-sync`)

Use this skill whenever synchronizing lore, tasks, world state, or Streamlit code between the **Asus ROG G75VW (`ROG_G75VW`)** (main workhorse laptop) and the **Chromebook (`CHROMEBOOK`)** (portable secondary laptop).

## Device Roles & Staggered Schedule

1. **`ROG_G75VW` (Asus ROG G75VW — Main Workhorse Laptop)**:
   - Holds the primary development environment and complete campaign/lore archive.
   - **Scheduled Sync**: `CRON_TZ=America/New_York 0 9,14,20 * * *` (**9:00 AM, 2:00 PM, and 8:00 PM EDT**).
   - Pushes local engine updates, `System_Core` lore, and `Campaign_Data` JSONs to GitHub (`v2-sandbox`), Google Drive (`SAO Sandbox v2`), and NotebookLM (`sao-ttrpg`).
2. **`CHROMEBOOK` (Chromebook — Portable Companion)**:
   - Local workspace: `f:\antigravity\Notebook LM MCP\sao-ttrpg`.
   - **Scheduled Sync**: `CRON_TZ=America/New_York 30 9,14,20 * * *` (**9:30 AM, 2:30 PM, and 8:30 PM EDT** — 30 minutes after `ROG_G75VW`).
   - Pulls the latest `v2-sandbox`, Google Drive, and NotebookLM updates from `ROG_G75VW`, executes portable worldbuilding/lore tasks, and posts handoffs back to `ROG_G75VW`.

## Canonical Shared Resource IDs

- **GitHub Repository**: `https://github.com/sliner87-debug/sao-ttrpg` (Active branch: `v2-sandbox`)
- **Google Drive Root Folder (`SAO Sandbox v2`)**: `10N4BYRQ4g3-NOJsTm26ah3WD8fKPsBr3`
  - `System_Core` Subfolder ID: `1mP_-q79p5wbbKBU5fzttYRcv9EkgTG4B`
    - `cardinal_rules.md`: `15AfryNU8uXAoubhL3ngFSP-CYg_Fljm2`
    - `north_america_pre_and_post_initialization_atlas.md`: `1FkV0OrFRTBsUKueE1vI-QwZ6SDivHMX9`
  - `Campaign_Data` Subfolder ID: `1vL7G8rC1j-X0D4mK5sP9qW2eN6tB8yH1`
  - Shared `SKILL.md` File ID on Drive: `1DFX3eGpDv6mGVBb4EOPgHEWsB20-PJCd`
  - Shared Prompt Command Book Google Doc ID: `1y_x4SKQU9nNXaxmfAWAtedZ0fNNlFOxD56KQeyCKb8g`
- **Shared Agent Inbox & World State Google Sheet**:
  - Title: `SAO TTRPG Agent Sync & World State`
  - Spreadsheet ID: `1PpBPs7Cq3-ot6ab7wNnmto5ab-CS_vh_NFufOGm47e8`
  - Tabs:
    - `Agent_Inbox` (`Timestamp | Sender_Device | Target_Device | Task_Type | Message_Payload | Status | Reply_Summary`)
    - `World_State_Registry` (`Key | Value | Updated_By | Updated_At | Source_URI | Notes`)
- **Shared NotebookLM Persistent World Brain**:
  - Title: `SAO TTRPG: Fractured Earth Persistent World`
  - Notebook UUID: `3714db25-595d-46a6-a59c-0de95a323037` (CLI/MCP Alias: `sao-ttrpg`)
  - URL: `https://notebooklm.google.com/notebook/3714db25-595d-46a6-a59c-0de95a323037`

## Authentication Troubleshooting (Clickable Links Only)

- **Google Drive (`gdrive`) & Google Sheets (`gsheets`)**:
  - Always use the `readonly` and `mutate` subcommand namespaces (`gdrive readonly ...`, `gdrive mutate ...`, `gsheets readonly ...`, `gsheets mutate ...`).
  - If `gdrive auth status` or `gsheets auth status` reports `Not logged in`, run `gdrive auth login` or `gsheets auth login` in the background, read the `https://accounts.google.com/o/oauth2/auth...` URL from the task log, and give it to the user as a **clickable markdown link** in chat.
- **NotebookLM (`notebooklm` MCP / `nlm` CLI)**:
  - On Windows, GUI browser windows spawned by `run_command` (`nlm login`) run inside an isolated terminal desktop (`MainWindowHandle = 0`) and will **never** appear on the user's screen.
  - **Never** expect `nlm login` to pop up a visible window. Instead, run the bundled localhost sign-in bridge script:
    ```powershell
    python ".agents/skills/sao-ttrpg-sync/scripts/nlm_web_login.py"
    ```
    Then give the user the clickable link **[Sign in to NotebookLM Bridge (http://localhost:8765)](http://localhost:8765)** in chat. Once they sign in via their normal browser, the script automatically saves the full domain cookie list (`list[dict]`) and CSRF/session tokens and exits cleanly.

## 5-Step Sync Workflow

### Step 1: Pull Latest GitHub & Check Architecture Rules
1. Read `.antigravity/rules/sao_architecture.md` before modifying any files.
2. **CRITICAL**: Never blindly overwrite master game state files (`save_game.json`, `world_history.md`, `npc_registry.json`, `active_quests.json`, `combat_state.json`, `initiative_tracker.json`, `System_Core/cardinal_rules.md`). Merge changes carefully.
3. Run `git fetch origin v2-sandbox` and `git pull origin v2-sandbox` in the repository root.

### Step 2: Check Shared Google Sheet Inbox (`Agent_Inbox`)
1. Read the inbox rows using the `gsheets` CLI (`readonly` namespace):
   ```powershell
   gsheets readonly read "1PpBPs7Cq3-ot6ab7wNnmto5ab-CS_vh_NFufOGm47e8" "Agent_Inbox!A1:G50"
   ```
2. Check for any rows where `Target_Device` matches your device (`ROG_G75VW` or `CHROMEBOOK`) or `ALL`, and `Status` is `PENDING` or `NEW`.
3. Also inspect `World_State_Registry!A1:F30` for any updated pointers or resource IDs.

### Step 3: Sync Google Drive Lore/Campaign Files & Execute Pending Tasks
1. List files in the shared Google Drive folders (`SAO Sandbox v2`: `10N4BYRQ4g3-NOJsTm26ah3WD8fKPsBr3`, `System_Core`: `1mP_-q79p5wbbKBU5fzttYRcv9EkgTG4B`, and `Campaign_Data`: `1vL7G8rC1j-X0D4mK5sP9qW2eN6tB8yH1`):
   ```powershell
   gdrive readonly list --parent "1mP_-q79p5wbbKBU5fzttYRcv9EkgTG4B"
   gdrive readonly list --parent "1vL7G8rC1j-X0D4mK5sP9qW2eN6tB8yH1"
   ```
2. Download any newer lore/campaign files from Google Drive or upload locally updated files (`gdrive mutate update` / `gdrive mutate upload`).
3. Execute any pending worldbuilding, lore expansion, initial upload, or Streamlit UI tasks requested in `Agent_Inbox`.

### Step 4: Sync Updated Lore into Shared NotebookLM (`3714db25-595d-46a6-a59c-0de95a323037`)
1. Use the `notebooklm` MCP server (`notebook_get`, `source_add`, `note`) with `notebook_id="3714db25-595d-46a6-a59c-0de95a323037"`.
2. Whenever a lore Markdown file is added or significantly updated, upload/refresh it in NotebookLM via `source_add` (`source_type="file"`, `wait=False`) and log a dated synthesis note via `note` (`action="create"`).

### Step 5: Commit/Push & Post Reply Summary to `Agent_Inbox`
1. If code or lore files in the repo changed and are clean, commit and push to `origin v2-sandbox`.
2. Update the processed row's `Status` to `DONE` and write a clear `Reply_Summary` using `gsheets mutate write`, or append a new handoff row for the other laptop using `gsheets mutate append`:
   ```powershell
   gsheets mutate append "1PpBPs7Cq3-ot6ab7wNnmto5ab-CS_vh_NFufOGm47e8" "Agent_Inbox" "<ISO_TIMESTAMP>,<THIS_DEVICE>,<OTHER_DEVICE>,SYNC_UPDATE,<SUMMARY>,PENDING,"
   ```
