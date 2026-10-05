# GenieForge — Product & Technical Design (Option C: Python Backend + Web Frontend)

> Version: v1.0　|　Date: 2026-09-29
> Goal: build a **Python backend + web frontend** desktop app on top of `genieutils-py`, resolving AGE's three pain points, with GitHub auto-update, version management, batch editing, beautiful batch diff, mod patch generation, and a public API for agents.

---

## 1. Overview

### 1.1 Background & pain points

| Pain point | Current state | Goal |
|------------|---------------|------|
| No incremental modding | every official update shifts IDs → full rebuild | semantic patches, one-click re-apply, minimal adaptation |
| No diff | compare two dats manually | structured batch diff, visual, filterable, batch-operable |
| No cross-reference | techs/effects searched by raw ID | reference graph + reverse index, two-way jump |
| No version management | changes scattered in `修改清单.txt` | patch files + Git, traceable / replayable |
| No automation API | manual UI only | public REST API so an agent can edit for you |

### 1.2 Design principles

1. **Core/UI decoupled**: all capabilities are backend services (Python functions + REST API); the UI is just a consumer. Agents and the desktop UI share one capability set.
2. **Parse once**: dat parsing takes ~10–14s; cache the in-memory object model, don't re-parse per request.
3. **Byte-level lossless**: writes must be lossless (latin-1 bidirectional strings) to stay fully compatible with the official format.
4. **Desktop-first, browser-compatible**: the same frontend runs in a desktop window and in a browser (for debugging / agent access).
5. **Beautiful + efficient UX**: virtual scrolling, keyboard shortcuts, themes, prominent batch-action entry points.

---

## 2. Architecture

### 2.1 Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  Desktop window (pywebview native window)                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Frontend SPA (Vue 3 + TS + Element Plus)                  │  │
│  │  table edit · batch · diff · ref jump · patch · version    │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │  HTTP / WebSocket                  │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                 ┌────────────▼─────────────┐
                 │  FastAPI (localhost:PORT) │──> /docs (OpenAPI auto docs)
                 │   REST API + WS push      │<── the "public API" for agents
                 └────────────┬─────────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
┌───────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Data core     │   │ diff / patch      │   │ reference index   │
│ parse/cache/  │   │ 3-level diff +    │   │ forward/reverse   │
│ write         │   │ patch engine      │   │ + name resolution │
└───────┬───────┘   └──────────────────┘   └──────────────────┘
        │
        ▼
   genieutils-py (after latin-1 fix) + language file + AGE3Names metadata
```

### 2.2 Why this structure

- **FastAPI backend**: built-in OpenAPI/Swagger (`/docs`) naturally satisfies the "public API for agents"; Pydantic for validation.
- **pywebview desktop shell**: Python opens a native window (Edge WebView2 on Windows), no bundled Chromium, small footprint; the same frontend also runs in a browser.
- **Vue 3 + Element Plus**: mature Chinese ecosystem, rich table/tree/dialog components, ideal for "beautiful UI + lots of tabular data".

---

## 3. Tech Stack

### 3.1 Backend

| Component | Choice | Notes |
|-----------|--------|-------|
| Language | Python 3.11+ | matches genieutils-py requirement |
| Web framework | FastAPI + Uvicorn | REST + auto OpenAPI + WebSocket |
| Data model | Pydantic v2 | request/response validation |
| dat core | genieutils-py (with latin-1 fix) | DE dat parse/write |
| Task queue | threads + `asyncio` | heavy tasks async |
| Config | `platformdirs` + JSON | cross-platform config |

### 3.2 Frontend

| Component | Choice | Notes |
|-----------|--------|-------|
| Framework | Vue 3 + TypeScript | Composition API |
| Build | Vite | fast HMR |
| UI lib | Element Plus (alt: Naive UI) | tables/tree/drawer/forms |
| Table | virtual scrolling (`vue-virtual-scroller` or EP v2 built-in) | 10k+ rows smooth |
| diff render | custom structure-diff tree + red/green | side-by-side compare |
| State | Pinia | global state (dat, selection, index) |
| Charts | ECharts (optional) | summary stats |

### 3.3 Desktop shell

| Item | Choice | Notes |
|------|--------|-------|
| Shell | **pywebview** (primary) | Python native window loading `http://127.0.0.1:PORT` |
| Fallback | browser mode | dev debugging / remote access |

> The JS↔Python communication goes through HTTP REST (not pywebview's js_api bridge), so the desktop UI and agents use the *exact same* API — one logic path.

### 3.4 Packaging & auto-update

| Item | Choice | Notes |
|------|--------|-------|
| Packaging | PyInstaller (onedir / single exe) | bundle Vue build output |
| Update source | GitHub Releases | app self-update via GitHub |
| Updater | built-in lightweight updater | fetch release → SHA256 → swap & restart |
| Protocol | semver + `latest` tag | stable / prerelease channels |

### 3.5 Data-core dependencies

- `genieutils-py`: read/write `empires2_x2_p1.dat` (supports `VER 7.8 / 8.4 / 8.8`).
- **Language file**: `key-value-strings-utf8.txt` (in the game dir, `id "text"` format), for localized display names.
- **Enum metadata**: `AGE3NamesV0007.ini` (armor/terrain/500 civ resources enums), bundled and extensible.

---

## 4. Feature Requirements

### 4.1 Game directory config & name localization

- Configure game directory: manual pick or auto-detect AoE2 DE (Steam `steamapps/common/AoE2DE`; Microsoft Store via registry).
- Auto-discover data files: locate `empires2_x2_p1.dat` and `key-value-strings-utf8.txt` (allow manual override).
- Two-layer naming: **internal name** (English, e.g. `Loom`, `British`) used as stable match key; **display name** (Chinese, e.g. `织布机`, `不列颠`) resolved from `language_dll_name` against the language file.
- Lists/jumps show Chinese names by default, internal name as secondary (`织布机 (Loom) #22`).
- Language switch (zh/en) by swapping the language-file source.

### 4.2 Editing (covering AGE's scope)

- Table browse/edit: Techs, Effects, EffectCommands, Civs, per-civ unit overrides (`Civ.units`), UnitHeaders, TechTree.
- Cell edit with per-type validation (int / float / enum dropdown / reference picker).
- Reference fields use pickers, not raw IDs (e.g. `effect_id` shows the target effect's name).
- Undo/redo via command stack (cross-table).
- Search/filter by name, ID, any field; regex support.

### 4.3 Batch editing (core)

- Multi-select → right-click → batch op (set / add / multiply / relative).
- Condition batch: rule builder (conditions + actions), e.g. "all `C-Bonus*` techs gold cost ×2".
- Find & replace across a field.
- Batch templates: save common rules (e.g. "double civ bonus", "farming tech efficiency table").
- Preview affected rows + before/after values; confirm; undoable as a whole.

### 4.4 Beautiful batch diff (core)

- Three-level diff: table (counts), record (field diffs on same-named entries), reference (ID drift).
- Visualization: summary cards (added/removed/changed, clickable), side-by-side old/new with red/green, filterable/sortable change list, "only show tables I care about".
- Batch actions on diff results: accept / revert / copy-to-patch.

### 4.5 Generate / apply mod patches (core)

- Patch DSL (YAML) — semantic edits (§5.4), located by name/signature.
- Generate: reverse from "official vs. my modded" diff, or from the current edit session.
- Apply: pick official new dat → apply → preview conflict report → write new mod.
- Patch management: list, enable/disable, reorder, merge, export/import; each patch is an independent versionable file.

### 4.6 Cross-reference navigation

- Forward: Tech → Effect / prerequisite techs / owning civ; Civ → tech tree / team bonus / unit overrides.
- Reverse: Effect → referencing Techs; Unit → overriding civs.
- Interaction: click to jump, hover for name preview, back/forward navigation (breadcrumbs).

### 4.7 Version management

- Project model: `project = baseline official version + patch set`.
- History: snapshot of each apply/edit; rollback; diff any two versions.
- Git integration: patches + config under Git (commit/revert/branch), backup + collaboration.
- Baseline tracking: record which official dat the project is based on (version + file hash), prompt "rebase" on update.

### 4.8 GitHub connection & auto-update

- App self-update: check GitHub Releases on startup → prompt → download → verify → swap & restart; manual/auto switch.
- Mod-project GitHub sync: connect a repo, push/pull patches & config.

### 4.9 Public API (for agents)

- Full REST API (§7), auto OpenAPI docs (`/docs`).
- Local auth: localhost binding + optional `X-API-Key`.
- Goal: agent can "read → analyze → batch edit → apply patch → write back" with zero manual UI.

### 4.10 UX extras

- Dark/light theme (follow system).
- Shortcuts: save `Ctrl+S`, find `Ctrl+F`, jump ref `Ctrl+Click`, undo `Ctrl+Z`.
- Layout: left nav + main table + right detail panel + bottom drawer (diff/log), resizable, remembered.

---

## 5. Core Implementation Logic

### 5.1 Data core: parse / cache / write

```
DatCore (singleton, thread-safe)
  ├─ load(path) -> DatFile   # zlib decompress + genieutils parse (~10s, cached)
  ├─ get()    -> current DatFile
  ├─ save(path)              # object -> bytes (latin-1 fix) -> zlib -> disk
  ├─ dirty flag / undo stack
  └─ hash check (before parse & before write) to guarantee losslessness
```

- **Must-include fix**: latin-1 bidirectional strings (`String.from_bytes` / `String.to_bytes` / `write_debug_string`), else non-ASCII strings corrupt on write. Verified; packaged as `genieutils_fix.apply()`.
- **Async**: `load`/`save`/`diff` are heavy → background threads + frontend progress (WebSocket push).

### 5.2 Name resolution

```
NameResolver
  ├─ internal names : Tech.name / Civ.name / Effect.name (in-dat)
  ├─ language table : key-value-strings-utf8.txt -> {int: str}
  └─ enum tables    : AGE3Names*.ini -> {table: {int: str}}
  resolve(entity) -> { internal, display, id }
```

- Display-name priority: `language_dll_name` → language table → internal `name` → `#ID`.
- EffectCommand `type` semantics from enum table (maintained, editable).

### 5.3 Structured diff algorithm

```
diff(a, b) -> DiffReport
  for each table:
    1. build key map (default name, optional id alignment)
    2. set difference: added = keys(b) - keys(a); removed = keys(a) - keys(b)
    3. field-by-field compare on intersection (type-aware: numeric/enum/ref)
    4. reference level: detect same-named entity id shifts
  produce ChangeItem list grouped by table & change type
```

- **Performance**: compute a per-record fingerprint (field hash); skip identical; expand only changed records. Diff of two ~84 MB-class models completes in seconds.
- **ChangeItem**: `{ table, key, id_a, id_b, changes: [{field, old, new}] }`.

### 5.4 Semantic patch engine

```yaml
version: 1
based_on: "VER 8.4"
steps:
  - name: "Loom gold 30"
    target: { table: techs, name: "Loom" }
    op: set
    field: "resource_costs.2.amount"     # 2 = gold index
    value: 30
  - name: "Banking trade rate x1.1"
    target: { table: techs, name: "Banking" }
    op: multiply
    field: "effect.d"
    value: 1.1
  - name: "Double civ bonus"
    target: { table: techs, name_pattern: "C-Bonus*" }
    op: rule
    rule: "double_civ_bonus"
```

**Matching strategy (solves ID drift)**:

```
resolve_target(step.target, dat):
  1. exact name (name == ...)
  2. name pattern (regex)
  3. signature (fingerprint of effect-commands + costs + prerequisite techs)
  4. relative position (within the same civ's tech tree)
  -> unique hit / multiple candidates / not found
```

- unique → apply; multiple → conflict report, resolve manually/by rule; not found → flag "needs adaptation".
- **op types**: `set` / `add` / `multiply` / `relative` / `rule` (custom Python) / `append` / `remove`.
- **Result**: `ApplyReport` (success / conflict / skipped + details), frontend conflict panel for per-item resolution.

### 5.5 Reference index

```
RefIndex (built once after parse, incrementally updated on edit)
  ├─ forward: {table: {id: [(target_table, target_id, field), ...]}}
  └─ reverse: {table: {id: [(src_table, src_id, field), ...]}}
```

- Build from a hard-coded reference-relation table: `tech.effect_id → effects`, `tech.required_techs[] → techs`, `civ.tech_tree_id/team_bonus_id → techs`, `civ.units[] → unit_headers`, etc.
- Query: `lookup_forward(table,id)` / `lookup_reverse(table,id)`.

### 5.6 Batch execution

```
BatchExecutor
  ├─ collect targets (multi-select / condition filter / template)
  ├─ build op set
  ├─ preview (count + before/after)
  └─ execute (transactional: record command to undo stack -> apply -> mark dirty)
```

- All batch ops use the command pattern; fully undoable/redoable.

### 5.7 Undo / redo

- Command stack: `{undo, redo, desc}`; edits & batch ops unified.
- Field-level inverse commands (not full snapshots — too costly on a large model).

### 5.8 Performance & scale

- In-memory model ~80–100k objects, resident.
- API responses: pagination + field projection (only needed columns).
- Frontend tables: virtual scrolling.
- diff: fingerprint pre-filter + lazy field expansion.

---

## 6. Data Model (empirically confirmed)

```
DatFile
├─ version: str                  # "VER 8.4"
├─ effects: list[Effect]         # Effect { name, effect_commands[] }
│            └─ EffectCommand { type:int, a:int, b:int, c:int, d:float }
├─ unit_headers: list[UnitHeaders]   # current Python port only has { exists, task_list }
├─ civs: list[Civ]               # Civ { player_type, name, tech_tree_id, team_bonus_id,
│                                 #       resources[], icon_set, units[] }
│                                 #   units[]: list[Unit|None] (2382 slots)
├─ techs: list[Tech]             # Tech { required_techs[6], resource_costs[3], effect_id,
│                                 #        name, type, civ, repeatable, research_locations[],
│                                 #        language_dll_* }
└─ tech_tree: TechTree
```

> Note: `unit_headers` in genieutils-py 0.1.2 is minimal (`exists` / `task_list`); the full unit attributes live in `Civ.units[unit_id]` (the `Unit` class, the largest module). If "master-unit-level" metadata is needed, enhance `UnitHeaders` parsing — a follow-up item.

---

## 7. Public API Design

### 7.1 Conventions

- Base URL: `http://127.0.0.1:8342` (configurable port)
- Auth: `X-API-Key` (optional; localhost trusted by default)
- Docs: `/docs` (OpenAPI/Swagger, auto-generated)
- Format: JSON; large lists use `?page=&page_size=&fields=&q=` for pagination/projection/search

### 7.2 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | health & version |
| GET/PUT | `/api/config` | config (game dir, language, port, token) |
| POST | `/api/dat/load` | load dat `{path}`, return meta |
| GET | `/api/dat/info` | current dat version & table counts |
| POST | `/api/dat/save` | save (optional `{path}`) |
| GET | `/api/techs` | tech list (paginated/filtered/projected) |
| GET | `/api/techs/{id}` | tech detail (resolved effect/prereq names) |
| PATCH | `/api/techs/{id}` | update tech fields |
| GET | `/api/effects` / `/api/effects/{id}` | effects list/detail |
| GET | `/api/civs` / `/api/civs/{id}` | civs list/detail |
| GET | `/api/units` | units query (by civ/ID) |
| PATCH | `/api/units/{civ}/{unit_id}` | update per-civ unit override |
| POST | `/api/batch` | batch edit (targets + ops), returns preview/result |
| POST | `/api/diff` | diff two dats `{base, target}` |
| GET | `/api/diff/{job_id}` | query diff result |
| POST | `/api/patch/apply` | apply patch (content or path) |
| POST | `/api/patch/generate` | generate patch from diff/change |
| GET | `/api/search?q=` | global search (name/ID, cross-table) |
| GET | `/api/refs/forward/{table}/{id}` | forward references |
| GET | `/api/refs/reverse/{table}/{id}` | reverse references |
| GET | `/api/names/{id}` | name resolution (internal/localized) |
| GET | `/api/version/list` | version history |
| POST | `/api/version/checkout` | roll back to a version |
| GET | `/api/update/check` | check app update |

### 7.3 Example: batch edit + apply patch (agent call chain)

```http
POST /api/dat/load   { "path": "D:/.../empires2_x2_p1.dat" }

GET  /api/techs?q=Banking
GET  /api/techs/17

POST /api/batch
{ "targets": [ {"table":"techs","name":"Banking"} ],
  "ops":     [ {"op":"multiply","field":"effect.d","value":1.1} ] }

POST /api/patch/apply
{ "patch": "steps:\n  - target: {table: techs, name: Loom}\n    op: set\n    field: resource_costs.2.amount\n    value: 30" }

POST /api/dat/save   { "path": "D:/.../empires2_x2_p1_mod.dat" }
```

---

## 8. Directory Structure

```
aoe2-mod-tool/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry + route registration
│   │   ├── api/               # resource routes (techs/effects/civs/...)
│   │   ├── core/
│   │   │   ├── dat_core.py    # parse/cache/write
│   │   │   ├── genieutils_fix.py   # latin-1 fix
│   │   │   ├── diff.py        # 3-level diff
│   │   │   ├── patch.py       # semantic patch engine
│   │   │   ├── refs.py        # reference index
│   │   │   ├── names.py       # name resolution
│   │   │   └── batch.py       # batch exec + command stack
│   │   ├── schemas.py         # Pydantic models
│   │   └── config.py          # config read/write
│   ├── metadata/              # enum tables (effect type / armor / resources)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/             # table/edit/diff/patch/version/settings
│   │   ├── components/        # virtual table/diff tree/ref jump/batch dialog
│   │   ├── stores/            # Pinia
│   │   └── api/               # backend API wrapper
│   └── package.json
├── desktop/
│   └── run.py                 # pywebview launcher
├── patches/                   # user patches (Git-managed)
├── build/                     # PyInstaller config + update manifest
└── docs/
    └── api.md                 # public API doc (synced from /docs)
```

---

## 9. Auto-update & Version Management

### 9.1 App self-update

```
startup/periodic -> GET GitHub /repos/{owner}/{repo}/releases/latest
                 -> semver compare vs local
                 -> new version: download asset (.zip/exe)
                 -> verify SHA256 (checksum in release)
                 -> set update flag; updater swaps files & restarts
                 -> rollback on failure
```

- Config: channel (stable/prerelease), auto/manual, proxy.

### 9.2 Mod-project version management

```
patches/
  ├── 001_loom_cost.yaml
  ├── 002_farming_techs.yaml
  ├── 003_double_civ_bonus.yaml
  └── manifest.yaml   # baseline version + patch order + official dat hash

flow:
  official update -> load new dat -> rebase (replay patches -> conflict report -> resolve few)
                  -> generate new mod -> commit Git (with new baseline)
```

---

## 10. Phased Implementation Plan

| Phase | Content | Deliverable |
|-------|---------|-------------|
| P0 | data core wrapper + latin-1 fix + REST skeleton | `dat_core` + FastAPI shell (PoC verified) |
| P1 | read/write/list/detail APIs + name resolution | query/edit/localized names |
| P2 | 3-level diff + frontend diff view | batch diff visualization |
| P3 | semantic patch engine + conflict report | incremental modding (core) |
| P4 | reference index + jump + batch ops + undo | full editing experience |
| P5 | version management + Git + GitHub auto-update | project lifecycle |
| P6 | public API polish + agent docs + UX polish | automation interface |

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| String-encoding corruption | fixed latin-1 + pre-write hash check |
| `unit_headers` incomplete | enhance parsing; unit attrs via `Civ.units` |
| Missing effect-command `type` semantics | maintain built-in enum table (seed from AGE3Names) |
| Duplicate/renamed names → ambiguous match | 3-tier matching + signature/position fallback + human confirm |
| Official format upgrades | version-branched parsing (`VER 8.8` already handled), follow library updates |
| Large-model performance | pagination/projection/virtual scroll/fingerprint pre-filter |
| Unauthorized API calls | localhost binding + optional token |

---

## 12. Linkage with Existing Artifacts

- `scripts/genie_poc.py` (this repo): parse/write/diff PoC; its `apply_string_fix()` is reused as `core/genieutils_fix.py`.
- `feasibility-analysis.en.md`: the feasibility analysis of the three pain points; this doc is the "Option C" build spec.
- Your `修改清单.txt` / `新的清单.txt`: seed corpus for the first patches — translate entries into patch DSL examples.
