# Contributing to Android Software Owner Skill Set

Thank you for testing this in your BSP environment. Every gap you find makes the skill set more accurate for the next engineer.

---

## Ways to Contribute

### 1. Report a Routing Error (GitHub Issue)

When the agent routes to the wrong skill or cites a wrong path, open a GitHub Issue:

**Issue title:** `[Routing] <one-line description>`

**Include:**
- The task or question you gave the agent
- Which skill it loaded / which path it cited
- The correct skill or path
- Your Android version (`ro.build.version.release`) and SoC family (Qualcomm, MediaTek, etc.) if relevant

**Example:**
```
Task: "Debug a crash in our ATF BL31 PSCI suspend path"
Agent routed to: L2-kernel-gki-expert
Correct skill: L2-trusted-firmware-atf-expert
Android: 14, SoC: Qualcomm SM8650
```

---

### 2. Add a Hindsight Note (Pull Request)

If you solved a tricky BSP problem that isn't covered by the existing 22 notes (HS-001–HS-022), add one:

**File:** `memory/hindsight_notes/HS-NNN_short_description.md`

Use the next available HS number and follow this template:

```markdown
# HS-NNN: Short Title

**Category:** Subsystem / domain
**Skills involved:** L2-<skill1>, L2-<skill2>
**Android versions:** Android X+

## Insight

<What the problem is and what the non-obvious solution is.
Write for a peer BSP engineer who knows the stack but hasn't hit this specific trap.>

## Why This Matters

<Why is this easy to get wrong? What's the consequence of the mistake?>

## Trigger

<When should the agent apply this insight? What keyword or symptom should activate it?>
```

---

### 3. Fix or Extend a Skill (Pull Request)

Each skill lives in `skills/L2-<name>/SKILL.md`. If you find:
- A missing trigger condition
- A wrong or outdated AOSP path
- A forbidden action that should be added
- A handoff rule that's missing

Open a PR with the change. Keep diffs focused — one conceptual fix per PR.

**Do not modify** files under any AOSP source directory (if present). The AOSP tree is reference-only per `CLAUDE.md`.

---

### 4. Add a BSP-Specific Reference Document

If you have architectural knowledge about a specific SoC or vendor BSP component that would help other engineers, add a reference document:

```
skills/L2-<relevant-skill>/references/<your-doc>.md
```

Keep it factual and path-anchored. Avoid NDA-protected content.

---

### 5. Tune Vendor Paths for Your BSP

If your SoC vendor uses non-standard paths for LK, ATF, or other vendor-supplied trees, update the L1 router:

```
skills/L1-aosp-root-router/SKILL.md  ← routing table footnote entries
```

Submit the change as a PR with a comment explaining your BSP layout.

---

## Contribution Standards

### Path Discipline
Every routing entry, forbidden action, and architecture note **must** reference a real AOSP path or be explicitly marked as a vendor-supplied path (¹ footnote). Do not add vague references like "somewhere in vendor/".

### SKILL.md Template
New or modified skills must conform to the template in `ANDROID_SW_OWNER_DEV_PLAN.md §11`:
- `Path Scope` table
- `Trigger Conditions` (keyword list)
- `Architecture Intelligence` (at least one table or diagram)
- `Forbidden Actions` (minimum 5 entries)
- `Handoff Rules` (table + emit line)
- `References` section

### Hindsight Note Quality Bar
A good hindsight note:
- Describes a **non-obvious** trap that an experienced engineer could fall into
- Gives the **fix** clearly, not just the problem description
- Explains **why** the mistake is easy to make
- Is relevant to BSP or platform work, not general software engineering

---

## Running the Tests

After making changes:

```bash
# Validate dirty_pages.json stays in sync with skills/
python3 scripts/validate_dirty_pages.py

# Run the 100-case routing accuracy spec
python3 tests/routing_accuracy/test_router.py
```

Both must pass with 0 errors before submitting a PR.

---

## Alpha Feedback Priority

During Alpha v0.1, the highest-value feedback is:

1. **Wrong paths** — any path the agent cites that doesn't exist in your workspace
2. **Missing vendor path mappings** — LK/ATF paths that differ from the defaults
3. **Skill gaps for real tasks** — a daily task you do that no skill covers well
4. **Outdated architecture** — anything that was true on Android 13/14 but changed in 15

---

*CONTRIBUTING.md v1.0 — Alpha v0.1*
