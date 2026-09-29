# GenieForge

> A modern modding workbench for **Age of Empires II: Definitive Edition**. Stop re-doing all your edits every time the game updates.

**Language**: English（current）· [简体中文](README.md)

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#)　[![License](https://img.shields.io/badge/License-MIT-blue)](#)　[![Release](https://img.shields.io/badge/Release-Auto--update-orange)](#)

---

## What is GenieForge?

All of AoE2 DE's gameplay data lives in a single ~10 MB file, `empires2_x2_p1.dat` — units, technologies, effects, civilization bonuses, costs, and more. Traditional tools like AGE only let you "open → edit → save". So whenever the official game updates, ID drift and newly inserted content invalidate all your hard-coded edits, forcing you to redo everything from scratch on the new version.

GenieForge fully parses the dat file and provides three capabilities that change the way you work:

- **Incremental modding** — store your changes as *semantic patches*; after an official update, re-apply them with one click and handle only the few remaining conflicts.
- **Batch diffing** — see every difference between two dat files at a glance, no more manual eyeballing.
- **Cross-reference navigation** — jump between techs ↔ effects ↔ units in both directions, no more guessing from raw IDs.

---

## Key Features

### ✨ Incremental modding — write once, reuse forever
Express your changes as **patches** (e.g. "set Loom's gold cost to 30", "double every `C-Bonus*` tech"). After an official update, apply the patches onto the new dat — the tool auto-locates targets (name → signature → relative position), leaving only a handful of cases for manual confirmation.

### 🔍 Batch diff
Open two dat files and get a three-level diff:
- **Table level** — how many techs / civs / effects were added or removed;
- **Record level** — which fields changed on same-named entries (side-by-side red/green highlighting);
- **Reference level** — which same-named techs had their IDs shifted (the exact thing that breaks hard-coded mods).

### 🔗 Cross-reference navigation
Click any tech to see the effect it references, its prerequisite techs, and its owning civilization; reverse-lookups show "who references this effect". Every numeric ID is translated to a readable name, with hover previews.

### 🧰 Batch editing
Multi-select bulk edits, condition-based filtering, find & replace, and reusable templates (e.g. "double civ bonus"). Preview the affected rows before applying, and undo in one step.

### 📦 Generate / apply mod patches
- Reverse-generate a patch from the diff of "official dat vs. my modded dat";
- Or export the current editing session as a patch;
- Patches are plain-text files — versionable, shareable, and reusable.

### 🕘 Version management
Track every change with full history and rollback to any point. A project is "baseline official version + a set of patches", and GenieForge prompts you to rebase when the game updates.

### 🔄 GitHub auto-update
The app connects to GitHub and checks for new releases on startup with one-click update; patch projects can also sync to GitHub for backup and collaboration.

### 🤖 Public API (advanced)
A full HTTP API lets your own scripts or an AI agent automate "read data → batch edit → apply patch → save", no manual clicking required.

---

## Getting Started

### Installation

1. Download the latest release from [GitHub Releases](../../releases);
2. Unpack and run (first launch walks you through initial setup);
3. The app auto-updates with official releases (switchable to manual in settings).

### First-time setup

1. In **Settings**, select your **game directory** (the tool auto-detects Steam / Microsoft Store installs);
2. Confirm it found `empires2_x2_p1.dat` and the language file (used to show unit/tech names in your language);
3. Done.

### Open & edit

1. Click **Open dat** and choose an `empires2_x2_p1.dat`;
2. Use the left navigation to switch between Techs / Effects / Civs / Units tables;
3. Double-click a cell to edit; reference fields (e.g. effect ID) use a dropdown picker;
4. Press `Ctrl+S` to save.

---

## Usage Guide

### Recommended workflow after an official update (the core scenario)

```
① Open the new official dat
② Click "Apply patch" and select your patch set
③ The tool auto-matches targets and lists conflicts (usually only a few)
④ Resolve conflicts manually; everything else applies automatically
⑤ Save as your new mod and commit the version record
```

> From now on, each official update costs you a few small adaptations — not a full rebuild.

### Batch editing examples

- **Bulk costs**: filter "all siege units" → select all → right-click "Batch operation" → cost ×1.2.
- **Apply a template**: pick "Double civ bonus" → preview affected tech count → confirm.
- **Find & replace**: `Ctrl+F` to search and bulk-replace by field.

### Compare two versions

1. **Tools → Compare dat**, pick base and target files;
2. View the summary cards (added / removed / changed counts);
3. Click any change for side-by-side red/green comparison;
4. Export the difference as a patch if needed.

### Cross-reference navigation

- Click any ID / name to jump to that entry;
- `Ctrl+Click` to open in a new panel;
- Right-click → "Who references this" for reverse lookups.

---

## UI Overview

```
┌──────────┬───────────────────────────────┬──────────────┐
│          │                               │              │
│  Nav tree │        Main table            │  Detail panel │
│  Techs/   │  name · value · ref · multi- │  field edit / │
│  Effects  │  select                      │  jump         │
│  Civs/    │                               │              │
│  Units    │                               │              │
├──────────┴───────────────────────────────┴──────────────┤
│  Bottom drawer: diff / patches / version history / log  │
└──────────────────────────────────────────────────────────┘
```

- Dark / light themes, draggable layout, remembered window state.
- Shortcuts: save `Ctrl+S`, find `Ctrl+F`, undo `Ctrl+Z`, jump ref `Ctrl+Click`.

---

## Public API (for scripts / agents)

By default the API runs at `http://127.0.0.1:8342` with full docs at `/docs`.

Example — let an agent perform an edit:

```bash
# Load a dat
curl -X POST http://127.0.0.1:8342/api/dat/load \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1.dat"}'

# Apply a semantic patch (Loom gold cost -> 30)
curl -X POST http://127.0.0.1:8342/api/patch/apply \
     -H "Content-Type: application/json" \
     -d '{"patch":"steps:\n  - target: {table: techs, name: Loom}\n    op: set\n    field: resource_costs.2.amount\n    value: 30"}'

# Save
curl -X POST http://127.0.0.1:8342/api/dat/save \
     -H "Content-Type: application/json" \
     -d '{"path":"D:/AoE2DE/resources/_common/dat/empires2_x2_p1_mod.dat"}'
```

---

## FAQ

**Q: Will it corrupt my game files?**
A: GenieForge reads/writes the dat copies you specify (back up first). Writes are byte-level lossless and fully compatible with the official format.

**Q: Do patches break after an official update?**
A: No. Patches locate targets by name/signature, not fixed IDs, so official ID drift is handled automatically; the few ambiguous cases are listed for you to confirm.

**Q: Names aren't showing in my language?**
A: In Settings, confirm the language file path (e.g. `key-value-strings-utf8.txt` in the game directory).

**Q: Which dat versions are supported?**
A: Definitive Edition `VER 7.8 / 8.4 / 8.8` and onward, kept up to date with official releases.

---

## Technical Notes (for the curious)

- Data core is built on the open-source [genieutils-py](https://github.com/SiegeEngineers/genieutils-py);
- dat format = zlib compression + Genie engine structured data (public format);
- Backend FastAPI + frontend Vue 3, wrapped in a native desktop window; the API and the desktop UI share the same logic.

> For the full product & technical spec, see [`technical-design.en.md`](technical-design.en.md); for the feasibility analysis, see [`feasibility-analysis.en.md`](feasibility-analysis.en.md).

---

## Acknowledgements

- [Advanced Genie Editor (AGE)](https://github.com/Tapsa/AGE) — long-standing format reference;
- [genieutils / genieutils-py](https://github.com/SiegeEngineers/genieutils-py) — dat read/write library;
- The AoE2 DE modding community.

## License

MIT License (data-parsing libraries retain their own licenses).
