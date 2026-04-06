---
id: HS-030
title: "Build system: genrules sandboxed for RBE/Bazel; Python 2 fully removed"
skill: L2-build-system-expert
date: 2026-04-07
source: research-session
---

## Insight

Recent AOSP build system changes relevant to BSP work:

1. **Genrule sandboxing**: Genrules now run sandboxed and can only access their
   listed `srcs`. This enforces compatibility with Remote Build Execution (RBE)
   and the ongoing Bazel migration. Vendor genrules that implicitly depend on
   files not in their `srcs` list will break.

2. **Python 2 removal**: Python 2 is fully removed from the AOSP build. All
   build scripts, code generators, and test harnesses must use Python 3. Any
   vendor `.mk` or `.bp` rules invoking `python` (not `python3`) will fail.

3. **Partition image cleanup**: Partition images now only include what a clean
   build would produce, not stale artifacts from staging directories. This
   may cause "missing file" surprises when vendor builds relied on leftover
   artifacts.

4. **Bazel migration progress**: Soong can run either Ninja or Bazel as the
   executor. The migration is incremental — each Soong plugin needs manual
   porting.

## Lesson

When migrating vendor build rules to A16, audit all genrules for implicit
`srcs` dependencies. Grep for `python` (without `3` suffix) in all `*.mk`
and `*.bp` files. Run a clean build early to catch stale artifact dependencies.

## Cross-Skill Impact

- **L2-version-migration-expert**: Add genrule/Python audit to migration checklist.
- **L2-kernel-gki-expert**: Kernel build scripts must be Python 3 only.
- **L2-hal-vendor-interface-expert**: Vendor HAL genrules need srcs audit.
