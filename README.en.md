# GenieForge

> A modding workbench for **Age of Empires II: Definitive Edition**. Stop redoing all your edits every time the game updates.

**Language**: English (current) · [简体中文](README.md)

[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](#installation)　[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

---

## What is GenieForge?

All of AoE2 DE's gameplay data lives in a single ~10 MB file, `empires2_x2_p1.dat` — units, technologies, effects, civilization bonuses, costs and more. Traditional tools like AGE only let you "open → edit → save", so whenever the game updates, ID drift and newly inserted content force you to redo your edits on the new version.

GenieForge fully parses the dat file and offers three core capabilities:

- **Semantic patches** — write your changes as patches that locate targets by *name*, then re-apply them to the new dat after an update, fixing only the few entries that no longer match.
- **Dat diff** — list the entries added, removed and modified between two dat files, plus same-named entries whose IDs drifted.
- **AGE-style editing** — edit techs, units, civs and effects directly in forms, with IDs shown as readable names.

---

## Features

### Data editing
- A persistent top bar shows the dat status (file name, version, unsaved changes) with save / undo / redo always at hand (`Ctrl+S` / `Ctrl+Z`).
- `Ctrl+K` global search: look up techs / units / effects / civs by name, or type `#ID` to jump straight to an entry.
- Tech / Unit / Civ / Effect pages with AGE-style field groups; edits apply immediately, with undo / redo.
- Enum fields (types, resources, armor classes, effect commands, …) use dropdowns; sub-tables (costs, attacks, armors, effect commands, …) support adding and removing rows.
- Conditional search on every data page: pick a dimension (techs: type / civ / effect; units: Class, Type, HP, …; effects: command-count range; civs: player type, …) and filter by value.
- The Unit page lets you switch civilizations; names are resolved to localized names through the game's language file.
- Whole-entry copy / paste (`Ctrl+C` / `Ctrl+V`) copies every field of one entry onto another.
- The effect field on the Tech page jumps to the referenced effect.
- With the game's language file configured, entries show their in-game names.

### Diff
- **Diff page** — pick a base and a target dat to see added / removed / modified counts, per-entry changes (readably formatted, not raw JSON) and ID drift, and export the result as a patch.
- **Side-by-side in-page compare** — click **Compare** on any data page to render the same form twice (left: current dat, editable; right: comparison version, read-only), with differing fields highlighted; apply differences one by one or all at once. The comparison target can be a saved version or a dat file.

### Patches
- Visual patch editor: create a patch, fill in each step's target and operation, preview what it hits, then apply. Patches are saved as YAML files in `patches/`.
- Targets are matched by exact name first, then by name regex, then by a signature (costs + prerequisite techs + effect). Steps that match nothing or several entries are reported as conflicts for you to resolve.
- Supported operations: `set`, `add`, `multiply`, `append` / `remove` (list items).
- An applied patch can be undone as a whole.

### Version records
- Every save records a version (file path + hash); the **Versions** page can roll back to that file. Records are kept for the current session only.

### Public API
- A built-in HTTP API lets scripts or AI agents run the full "load → query → edit / apply patch → save" flow. See the [API reference](docs/api.md) and the [agent guide](docs/agent.md) (both in Chinese).

---

## Installation

### Release build (Windows)

1. Download `GenieForge-<version>-windows.zip` from [GitHub Releases](../../releases);
2. Unzip and run `GenieForge.exe`.

Click **Check for updates** on the Workbench to see whether a newer version is available.

### Run from source

Requires Python 3.11+ and Node.js 18+.

```bash
pip install -r backend/requirements.txt -r desktop/requirements.txt
cd frontend && npm install && npm run build && cd ..
python desktop/run.py
```

To build a package yourself, see [`build/README.md`](build/README.md).

---

## Quick start

> The interface is currently in Chinese; button names below are translated.

1. In **Settings**, choose the game's language file `key-value-strings-utf8.txt` (under `resources/<language>/strings/key-value/` in the game folder; optional, used for display names);
2. On the **Workbench**, choose the `empires2_x2_p1.dat` to edit and click **Load** (parsing takes about 10–15 s);
3. Switch between Techs / Units / Civs / Effects in the sidebar and edit fields directly;
4. Click **Save** on the Workbench.

> The game locks the dat file while running — close the game first, and back up the original file before editing.

### Recommended flow after an official update

```
① Diff the old official dat against your mod dat and "Export as patch" (or maintain patch files directly)
② Load the new official dat
③ Open the patch on the Patches page and Preview it
④ Fix conflicting / unmatched steps by hand
⑤ Apply, then save as the new mod
```

### Patch example

```yaml
version: 1
based_on: "VER 8.8"
steps:
  - name: "Loom gold cost 30"
    target: { table: techs, name: "Loom" }
    op: set
    field: "resource_costs.gold.amount"   # located by resource type, not by index
    value: 30
```

---

## FAQ

**Q: Can this break my game files?**
A: The tool only reads and writes the files you choose. Saving is byte-for-byte lossless and fully compatible with the official format; backing up first is still recommended.

**Q: Will my patches always apply after an update?**
A: Steps located by name are immune to ID drift, so most apply directly. If an entry was renamed, or its signature (costs / prerequisites) changed, the step is reported as a conflict or as unmatched and needs a manual fix.

**Q: Display names don't show up?**
A: Check the language file path in **Settings**, then click **Refresh**.

**Q: Which dat versions are supported?**
A: Verified with DE `VER 7.8 / 8.4 / 8.8`.

---

## Acknowledgements

- [Advanced Genie Editor (AGE)](https://github.com/Tapsa/AGE) — format reference and comparison tool;
- [genieutils-py](https://github.com/SiegeEngineers/genieutils-py) — dat read/write library;
- The AoE2 DE modding community.

## License

[MIT License](LICENSE) (dependencies follow their own licenses).
