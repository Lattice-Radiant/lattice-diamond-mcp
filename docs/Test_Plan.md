# Lattice Diamond MCP Server: Test Plan

## 1. Purpose and Scope

This plan describes how the Lattice Diamond MCP Server is tested, what each test level covers, the environments required, and the conditions under which a build is accepted. It was reconstructed from the test suite, the CI workflows and the developer README as they stand at commit 3ae6b10. Results of the execution described here are recorded in [Test_Summary.md](Test_Summary.md).

In scope:

- The MCP tool layer (`src/diamond_mcp/server.py`) and its 32 registered tools.
- The Diamond console session (`diamond_session.py`): process handling, command protocol, timeouts and crash recovery.
- Report and project-file parsers, configuration resolution and installation discovery.
- The command audit log.
- Security hardening of the server (file confinement, program restriction, stdio-only transport, XML entity refusal).
- The packaging and installer scripts, including the embedded Windows and Linux packages and the combined package.
- The security scan tooling in `security_scan/`.
- Compilation of real Diamond projects from the adjacent `design-migration` repository through the server's tools (Section 3.9).

Out of scope:

- Correctness of Lattice Diamond itself.
- Penetration testing or review by a security team. The scans in this repository have not been triaged by an SDLC security team and do not replace such a review (see `security_scan/README.md`).

Internal policy: no company policy document or policy number is referenced by the repository's test materials. None is cited here. Where a policy number is required for a compliance record, it must be added by the document owner.

## 2. Test Levels

| Level | Location | Needs | Default run |
|---|---|---|---|
| Unit | `tests/test_*.py` | Python 3.11 or later, `pytest`, `tclsh` 8.5 or later | Yes |
| Component, against the fake console | `tests/test_session.py`, `tests/test_server.py`, `tests/test_audit.py` | As above; `tests/fake_diamond` runs under the real `tclsh` | Yes |
| End to end over stdio | `tests/test_stdio_server.py`, `scripts/smoke_test.py` | As above | Yes |
| Packaging and installer | `tests/test_installer.py`, `test_embedded.py`, `test_linux_embedded.py`, `test_combine.py`, `test_create_export.py`, `test_packaging.py` | As above; some build steps use local fixtures | Yes, except one test that downloads wheels |
| Security scans | `security_scan/run_scans.py`, `tests/test_security_scan.py` | `bandit==1.9.4`, network for OSV | Scans run separately; scanner tests run by default |
| Integration, real Diamond | `tests/test_integration.py` | Diamond installation, licence, `DIAMOND_TEST_LDF` | No, skipped unless configured |
| Design-based, real Diamond 3.14 | `scripts/run_design_tests.py` | Diamond 3.14, licence, `design-migration` checkout | No, run manually |
| Installed-package smoke test | `scripts/smoke_test.py` in `.github/workflows/build-dist.yml` | A built package on its target OS | CI only |

## 3. Test Items and Coverage

### 3.1 MCP tool layer (`test_server.py`)

- Registration of every tool with a schema; invocation through the MCP protocol.
- Automatic session start; restart after a crash with a note to the caller.
- Project tools: open, close, create, info, add and remove sources, target device, synthesis tool, strategy options.
- Flow tools: individual stages, full compile, bitstream generation and verification, export, timing analysis, failure reporting and hints.
- Report tools: listing, summaries, pagination, refusal of other file types.
- Environment and configuration tools.
- Refusal of `prj_project close` through `run_tcl`, and the absence of look-alike false refusals.
- Stale crash-recovery file: `open_project` renames a `.recovery` file that names another project (so Diamond does not restore that project in place of the requested one), reports a warning, leaves a `.recovery` that names the same project, and adds no warning when there is no such file.

### 3.2 Session protocol (`test_session.py`)

- Tcl quoting round trips through real Tcl, including carriage returns.
- Start, stop and restart behaviour; idempotence.
- Result and output separation; failures as caught errors.
- Persistent interpreter state, multiline commands, output without a trailing newline.
- Timeout kill and reporting; crash detection, description and recovery.

### 3.3 Parsers, project files, configuration (`test_reports.py`, `test_project.py`, `test_config_discovery.py`)

- PAR, TWR and MRP parsing on trimmed real Diamond 3.14 reports (`tests/data`), including unconstrained, setup-only, wrapped-name and malformed cases, and linear-time behaviour on crafted input.
- `.ldf` parsing, missing-source detection (including letter-case mismatches), report-file location.
- `set_aside_stale_recovery`: no file, same project (left alone), other project (renamed to `.recovery.stale-<timestamp>`, not deleted), repeated renames that never overwrite an earlier file, and an unreadable file.
- Discovery of Diamond installations; configuration precedence (environment, file, auto-detection); the licence value is never leaked; a working-directory config file is not read.

### 3.4 Audit log (`test_audit.py`)

- One JSON object per line, exact command text, truncation flags.
- Private permissions, rotation, concurrent writers, unwritable location.
- Attribution of commands to tool names, including nested calls; command written before it runs; enable and disable through environment and configuration.

### 3.5 Security hardening (`test_hardening.py`)

- Report reads confined to the open project's files; no link-following; size cap; chunked paging consistency.
- Only the Diamond console program may be started or configured by a tool; the operator can still choose a program by configuration.
- No network transport option exists.
- Project XML containing a DTD, entity or expansion bomb is refused; deep nesting does not crash the server.

### 3.6 Packaging and installers

- Wheel hash and lock verification, glibc floor, licence extraction, platform and interpreter checks.
- Installer registration, uninstall, dry runs, handling of folders the installer did not create, and processes holding files open.
- Embedded Windows package: pinned interpreter hash, PGP signature check against the pinned key, layout and notices checks, Microsoft clause check.
- Embedded Linux package: pinned archive hash, layout, glibc floor, execute-bit repair.
- Combined package and manifest (`MANIFEST.sha256`) verification, SBOM, sidecar files, refusal of mismatched or duplicate builds.
- Retired standalone kind refused with a pointer to the embedded package.

### 3.7 Security scans (`security_scan/`)

- Bandit static analysis (fails on unsuppressed Medium or High).
- Secrets scan (nine patterns over tracked files).
- OSV advisory check of every locked package (runtime packages fail the check).
- Seeded fuzzing of the report parsers, `.ldf` reader and config loader; Tcl quoting check.
- Stdio protocol probes against the running server.

### 3.8 Integration against real Diamond (`test_integration.py`)

- Environment readiness, a full compile, repeated open and close cycles, and failure reporting with the session surviving.

### 3.9 Design-based testing with Diamond 3.14 (`scripts/run_design_tests.py`)

Purpose: exercise the server's `compile_project` tool (open, Synthesis, Translate, Map, PAR, Bitgen, then timing and resource summaries) on real customer and primitive-test designs, using Diamond 3.14.0.75.0.

Design inventory (`design-migration` checkout, counted by the script from the device in each `.ldf`; projects under `tests/fixtures` are excluded as they are inputs of the migration tool):

| Family | Devices | Projects | Location |
|---|---|---|---|
| XO2 | LCMXO2 | 12 | `perforce/regtest/diamondng/trunk/benchmark/customer_Mach_XO4` |
| XO3 | LCMXO3L, LCMXO3LF, LAMXO3LF | 35 | same |
| XO3D | LCMXO3D | 182 | `xo3d_primitive_tests` |
| Other (opt-in) | LCMXO256C, LFE3, LFE5U, LFXP2, LPTM | 10 | same as XO2 and XO3 |
| Total in scope (XO2, XO3, XO3D) | | 229 | |

Note on the inventory: the `perforce` tree holds 57 `.ldf` projects in 41 design folders, not 43. The 57 comprise 12 XO2, 35 XO3 and 10 of other families. The XO3D designs are not in that tree; they are in `xo3d_primitive_tests`. Several design folders hold more than one project (`rd1005_XO4` holds 15), which is why projects outnumber folders.

Method:

- Each design is copied to a scratch folder (the closest folder holding the `.ldf` and every relative source it names), so the originals are never modified.
- Each design gets a fresh session and one `compile_project` call with a per-stage timeout (default 1200 s). Designs run one at a time, so one licence seat suffices.
- Verdict: PASS when every stage completes. Whether the design's own timing constraints were met is reported separately and does not fail the design, because the purpose is to test the server and not the designs.
- Output: `summary.md` (for pasting into the test summary) and `results.json` (per-stage status, PAR and timing results, resources, error text for failures).
- Exit status is 1 if any design failed.

Usage:

- `python scripts/run_design_tests.py --list` lists what would run.
- `--family xo2|xo3|xo3d|other|all` (repeatable) and `--select TEXT` (repeatable, case-insensitive on the path) choose designs; `--limit N` caps the count.
- `--diamond-version` (default 3.14), `--timeout`, `--no-bitstream`, `--out`, `--keep-work` adjust the run.
- A licence must resolve in the environment. If it comes from `~/.flexlmrc` only, set `LM_LICENSE_FILE` before running the pytest integration tests, because those tests replace `HOME` with an empty folder.

Acceptance: every in-scope design that the installed Diamond supports completes the flow. A failure is triaged as a server defect, a Diamond or licence limitation, or a design problem, and recorded in the summary.

## 4. Environment

- Python 3.11 or later (the project requires `>=3.11`; the installer path itself runs on 3.8 or later).
- Dependencies from `uv.lock`: `uv sync --extra test`.
- `tclsh` 8.5 or later. Tests that need it are skipped with a reason if it is absent.
- For integration and design tests: a Diamond installation (3.14.0.75.0 used), `LM_LICENSE_FILE` if the site needs it (required when the licence is configured only in `~/.flexlmrc`), and a small compilable project (`DIAMOND_TEST_LDF`, optionally `DIAMOND_TEST_ROOT`).
- For the wheel-download installer test: `DIAMOND_TEST_INSTALLER=1` and network access.

### 4.1 Diamond installation and licensing used for design testing

Reference configuration supplied for the design tests (Linux):

| Item | Value |
|---|---|
| Diamond installation (version 3.14, build 3_14p.156) | `/home/rel2/3_14p.156/rtf` |
| Console program | `/home/rel2/3_14p.156/rtf/bin/lin64/diamondc` |
| `LM_LICENSE_FILE` | `1850@ldc-virtlic02` |
| `SALT_LICENSE_SERVER` | `1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b` |

- Set `DIAMOND_EXE` to the console program and export both licence variables in the environment of the server process (or of `scripts/run_design_tests.py`).
- This installation is a different build from the 3.14.0.75.0 installation used for the pilot run recorded in Test_Summary.md. A run on this build must state its build in the summary.
- The licence servers are internal to the company network; the hosts are reachable only from it.

### 4.2 Installing the package for design testing (Linux)

Package: `dist/lattice-diamond-mcp-0.1.0-embedded-linux-x86_64.zip`, built from the working tree on 2026-11-20 (it includes uncommitted changes; rebuild with `--ref` for a release). Its SHA-256 is in the `.sha256` file beside it. Build check passed: installed with `install.py`, manifest verified, server answered over MCP (32 tools).

- Unzip, then run `python3 install.py --diamond-exe /home/rel2/3_14p.156/rtf/bin/lin64/diamondc` from the unzipped folder. It installs the bundled Python under `~/.local/share/lattice-diamond-mcp/python` and registers the server with Claude Code (user scope).
- Add `--name <other-name>` to keep an existing registration; the default name replaces an earlier one registered by the installer.
- Export `LM_LICENSE_FILE` and `SALT_LICENSE_SERVER` (Section 4.1) in the shell that starts Claude Code, or register them with `claude mcp add -e`. The installer does not store licence variables.
- Restart Claude Code, then ask it to run `check_environment`.
- The package holds the server only. `scripts/run_design_tests.py` is in the repository, not in the package.

## 5. Execution

- Unit and component tests: `pytest`.
- Integration tests: `pytest -m integration` with the variables in Section 4.
- Design tests: `python scripts/run_design_tests.py` (Section 3.9).
- Security scans: `python security_scan/run_scans.py` (`--skip-osv` without network, `--skip-dast` to omit dynamic probes).
- CI: `.github/workflows/security-scan.yml` runs the unit tests and the scans on every push to main, every pull request and weekly. `.github/workflows/build-dist.yml` builds each package and runs the install test and `scripts/smoke_test.py` on the target operating system.

## 6. Entry and Exit Criteria

Entry:

- Dependencies installed from the lock file; `tclsh` available.

Exit (acceptance for a release):

- All unit and component tests pass; no unexplained skips.
- All five security scan steps exit 0.
- Smoke test passes for each package built in CI.
- Integration tests pass on a machine with a real Diamond for any release that changes session handling, flow tools or report parsing.

## 7. Known Gaps and Risks

- Integration and design tests need a licensed Diamond and are not run in CI. Behaviour against real Diamond rests on manual runs and on the fake console reproducing recorded behaviour.
- The wheel-download installer test is opt-in and not part of the default run.
- Windows packaging steps are exercised in CI only; they were not executed on Linux in the summarised run.
- The fake console does not reproduce Diamond's recovery behaviour, so the stale `.recovery` tests check the server's file handling only. That Diamond then opens the requested project was verified by hand on real Diamond 3.14.0.75.0 (Test_Summary.md Section 6.3); an integration test with two projects in one folder is still advisable.
- No coverage measurement is configured, so statement coverage is unknown.
- No performance or load testing is defined beyond timeout and crafted-input checks.
