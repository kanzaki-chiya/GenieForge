# GenieForge — Feasibility Analysis & Solution Design

> Goal: resolve AGE's three pain points — ① no incremental modding (full rebuild after every official update) ② no diff (manually compare two dats) ③ no cross-reference navigation (techs/effects linked only by numeric IDs). End goal: after each official update, adapt your mod with minimal effort instead of a full rebuild.

---

## 1. TL;DR

| Question | Answer |
|----------|--------|
| Decompile AGE? | **Not needed, not recommended.** AGE is open source, and the dat format has mature open-source libraries. |
| Is the approach feasible? | **Fully feasible — already verified empirically.** |
| Best path | Build a "semantic patch + dat diff + reference index" tool on top of the open-source **genieutils-py**, rather than modifying or decompiling AGE. |
| Verified results | All three of your dats (`VER 7.8 / 8.4 / 8.8`) parse successfully; semantic edit + byte-level lossless write-back succeeded; version-to-version diff (ID drift, new civs) succeeded. |

Key evidence (reproducible via `genie_poc.py`):

```
back/empires2_x2_p1_1213.dat  VER 7.8   46 civs   981 techs   981 effects
back/empires2_x2_p1_0814.dat  VER 8.4   54 civs  1278 techs  1218 effects
原版/dat/empires2_x2_p1.dat   VER 8.8   54 civs  1268 techs  1218 effects

Loom gold cost 50 -> 30, written back with only 1 differing byte (fully lossless)
Version diff: +297 techs, +237 effects, +9 civs, 4 techs with shifted IDs
```

---

## 2. Current State Analysis

### 2.1 The AGE tool you have

`AdvancedGenieEditor3.exe` (9.8 MB, built 2025-08) is a **native C/C++ program (PE32+, no .NET CLR header)**, part of the classic Advanced Genie Editor (AGE) family. Bundled files:

- `AGE3NamesV0005/6/7.ini`: enum tables AGE uses to translate numeric IDs into readable names (armor types, terrain tables, 500 civ resources, etc.).
- `openal32.dll`: audio runtime.

AGE is a "full read/write editor" for dat/dll: **load → edit → save**, with no incremental, diff, or cross-reference capabilities.

### 2.2 The dat file format (key premise)

Empirically confirmed for the DE `empires2_x2_p1.dat`:

1. **Outer layer**: the whole file is a **zlib raw deflate stream** (`wbits=-15`, no zlib header), decompressing to ~83.8 MB.
2. **Inner layer**: decompressed data is the **Genie engine structured format**, starting with a version string `VER 8.4` (or `VER 7.8`, `VER 8.8`, etc.).
3. Followed by fixed-order sections: terrain restrictions, player colors, sounds, graphics, terrain block, random maps, **effects**, **unit headers**, **civs**, **techs**, tech tree, etc.

This format is **fully public with mature open-source implementations** — not a black box.

### 2.3 Root causes of the three pain points

| Pain point | Root cause |
|------------|-----------|
| ① No incremental modding | AGE only does full load-edit-save. Your mod is a set of **hard-coded ID** edits (e.g. "tech 22 gold cost = 30"); when the official update inserts new content, **IDs shift globally**, breaking all hard-coded edits. |
| ② No diff | AGE has no "load two dats → compare" flow; you compare manually against `修改清单.txt`. |
| ③ No cross-reference | tech → effect, tech → prerequisite tech, civ → unit overrides are all **numeric ID references**; AGE shows only numbers, no resolution/jump/reverse lookup. |

> Evidence (VER 7.8 → 8.4): +297 techs, +237 effects, +9 civs, and 4 same-named techs with shifted IDs (e.g. `C-Bonus, Infantry Cost -20%` moved from 344 → 731).

---

## 3. Decompilation Feasibility

**Conclusion: unnecessary and not recommended.**

1. **AGE is open source** (`Tapsa/AGE`, plus community forks like `kkpan11/Advanced-Genie-Editor`); the source is far clearer than any decompiled output.
2. **The exe is native C/C++ (MFC/Win32)**, not .NET, so dnSpy/ILSpy won't produce readable source; IDA/Ghidra disassembly is huge effort for little gain, plus copyright risk.
3. **What you actually need is dat-format knowledge**, already solved by the open-source community — independent of AGE's implementation.

> Correct posture: treat AGE as a *format reference / cross-check tool*, and build the core capabilities on open-source libraries.

---

## 4. Data Model (empirically confirmed)

### 4.1 Top-level structure

```
DatFile
├── version            : str   (e.g. "VER 8.4")
├── terrain_restrictions / player_colours / sounds / graphics / ...
├── effects            : list[Effect]      # global effects table
├── unit_headers       : list[UnitHeaders] # master unit table (1701 entries)
├── civs               : list[Civ]         # civilizations (with per-civ unit overrides)
├── techs              : list[Tech]        # technologies table
└── tech_tree          : TechTree          # tech-tree connections
```

### 4.2 Key references (the data basis for pain point ③)

```
Tech.effect_id                -> Effect (effects table)         # tech -> effect
Tech.required_techs[0..5]     -> Tech                           # prerequisite techs
Tech.resource_costs[0..2]     -> (type, amount, flag)           # costs (gold/wood/food/stone)
Tech.civ                      -> Civ
Civ.tech_tree_id / team_bonus_id -> TechTree / Tech             # civ -> tech tree / team bonus
Civ.units[unit_id]            -> Unit (per-civ unit override)    # civ -> unit attribute overrides
Civ.resources[0..600]         -> float                          # civ resources (efficiencies/bonuses)
Effect.effect_commands[]      -> EffectCommand(type,a,b,c,d)     # effect instructions
```

Measured size (VER 8.4): 54 civs, 1278 techs, 1218 effects, 1701 unit headers, 15794 graphics, 760 sounds.

Your core edits (double civ bonus, farm efficiency, trade rate, cost tweaks) **all map onto this structure**, so they can be described and located *semantically* rather than by ID.

---

## 5. Solution Design

The core idea: **upgrade the mod from "a pile of hard-coded ID edits" into "a semantic patch + diff/index tooling".**

### 5.1 Pain point ①: incremental modding → semantic patch engine

Store *what you changed* as a **patch**, locating targets by **name/semantics**, not raw ID.

```yaml
version: 1
patches:
  - target: { table: techs, name: "Loom" }      # locate by name (ID-drift-proof)
    set: { resource_costs[gold].amount: 30 }     # Loom gold 50 -> 30

  - target: { table: civs, name: "Byzantine" }
    apply: "double_civ_bonus"                    # custom rule: double this civ's bonuses

  - target: { table: techs, name: "Banking" }
    set: { effect_multiplier: 1.1 }              # Banking trade rate x1.1
```

**Workflow after each official update** (this is the "minimal adaptation" you want):

```
new official dat ──parse──> new object model
                              │
                              │  ① auto-match (below)
                              ▼
                         apply patches (set/multiply/rule)
                              │
                              │  ② conflict report (not found / multiple matches -> manual)
                              ▼
                         write back the new mod dat
```

**Three-tier target matching** (solves ID drift):

1. **Name match** (preferred): `name == "Loom"`. Most names are stable.
2. **Signature match** (name changed / duplicated): fingerprint by effect-command set + costs + prerequisite techs.
3. **Relative-position match** (fallback): relative position within the same civ's tech tree.

Match failure / ambiguity → report, human handles only those few — **not a full rebuild**.

### 5.2 Pain point ②: diff → structured dat diff

Diff two parsed dats on **three levels**:

| Level | Content | Use |
|-------|---------|-----|
| Table | count changes (techs +297, civs +9, effects +237) | quickly see what the update touched |
| Record | same-named entry field-by-field (Loom gold 50→30) | see exactly which value changed |
| Reference | ID drift detection (`C-Bonus...` 344→731) | **directly locate which mods need adapting** |

**Two typical uses**:
- **Official old vs. official new**: see what the devs changed, judge which of your mods are affected.
- **Official vs. my modded version**: auto-generate / verify patches, even reverse-generate the patch DSL from the diff.

### 5.3 Pain point ③: cross-reference → reference graph + reverse index

Build a full reference index with two-way jumps:

- **Forward**: Tech → its Effect / prerequisite techs / owning civ.
- **Reverse**: Effect → which Techs reference it; Unit → which civs/techs override it.
- **Name resolution**: use the language file (`key-value-strings-utf8.txt`) + `AGE3NamesV0007.ini` to translate IDs into readable names, with hover previews and click-through.

This eliminates the "search techs and effects by raw ID" pain entirely.

---

## 6. Tech Selection & Architecture

### 6.1 Three routes compared

| Route | Approach | Verdict |
|-------|----------|---------|
| A. Modify AGE (C++/MFC) | Add diff/patch/jump in AGE's source | high effort, MFC steep, hard to maintain — **not recommended** |
| B. Python CLI on genieutils-py | parse/write/diff/patch as CLI | **recommended start**, fastest to value, already validated |
| C. Python backend + web frontend | add a visual UI on top of B | endgame target, best UX for jump/highlight |

**Recommended: B → C, incrementally.**

### 6.2 Key technical facts (verified)

- Library: `genieutils-py` (PyPI, SiegeEngineers), built for DE `empires2_x2_p1.dat`, supports `GV_C20+` (FileVersion 7.7+, covering your 7.8/8.4/8.8).
- **Must-fix pitfall (located and fixed)**: `genieutils-py 0.1.2` treats dat strings as UTF-8, but the dat uses a **custom single-byte encoding**; non-ASCII strings (Chinese/special chars) get corrupted on write. Apply **3 latin-1 bidirectional patches** (see `genie_poc.py` → `apply_string_fix()`) for byte-level lossless round-trip (verified: 1 differing byte).
- Write-back uses `zlib.compress(..., wbits=-15)`; compression level differs from official but the game only reads the decompressed content.

### 6.3 Architecture sketch

```
┌─────────────────────────────────────────────────────────┐
│  CLI / Web UI                                          │
│   diff view · patch editor · ref jump · conflict report │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│  Core layer (Python, on genieutils-py)                  │
│  ① parse/write (with latin-1 fix)                       │
│  ② structured diff (table / record / reference)         │
│  ③ semantic patch engine (locate + set/multiply/rule)   │
│  ④ reference index (forward/reverse jump + names)       │
└──────────────┬──────────────────────────────────────────┘
               │
        genieutils-py (model: techs/effects/civs/units/...)
```

---

## 7. Implementation Plan (phased)

| Phase | Content | Deliverable | Status |
|-------|---------|-------------|--------|
| P0 | parse/write validation + latin-1 fix | `genie_poc.py` | ✅ done |
| P1 | core wrapper: `load / save / object access` | Python module | todo |
| P2 | structured diff (3 levels) | `diff` command/function | todo |
| P3 | semantic patch engine + patch DSL + conflict report | `apply-patch` | todo |
| P4 | reference index + name resolution + reverse lookup | `index`/`lookup` | todo |
| P5 | web visualization (jump/highlight/diff tree) | web tool | todo |

**Suggested milestone**: ship P1+P2 (diff) first — it immediately lets you "see what changed and what needs adapting" after each official update; then P3 (patch) for "write once, apply forever".

---

## 8. Risks & Notes

1. **String encoding**: the latin-1 fix must stay in the code (otherwise write-back corrupts). Captured in the PoC.
2. **Version evolution**: `VER 8.8` differs slightly from `VER 8.4` in the Tech structure (an added `research_location_count`); genieutils-py already branches `from_bytes_84/88`. Follow library updates for new fields.
3. **Effect-command `type` semantics**: `EffectCommand.type` is a numeric enum; you need a "type → meaning" table (like `AGE3NamesV0007.ini`) or diff/rules won't be readable. This metadata is a follow-up task.
4. **Duplicate / renamed names**: a few tech names repeat (e.g. per-civ `C-Bonus...`); matching needs signature/position fallback + human confirmation.
5. **Language-file ↔ dat mapping**: the dat's `name` is an English internal name; the Chinese display name lives in `key-value-strings-utf8.txt`, requiring a mapping (internal name / `language_dll_name` ID → language table).

---

## 9. Suggested Next Steps

1. Deliver **P1+P2** first: a `dat-diff` CLI that takes two dats (e.g. `0814` and `原版`) and outputs "which techs/effects/civs changed, which IDs drifted" — immediately ending manual comparison.
2. Then **P3 patch engine**: translate your `修改清单.txt` / `新的清单.txt` entries (farming techs, double civ bonus, cost tweaks) into reusable patches for one-click re-application after each official update.
