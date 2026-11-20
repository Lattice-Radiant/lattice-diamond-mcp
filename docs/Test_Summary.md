# Lattice Diamond MCP Server: Test Summary

## 1. Run Details

- Plan: [Test_Plan.md](Test_Plan.md)
- Date: 2026-11-20
- Source: branch `main`, commit 3ae6b10 (working tree clean apart from an untracked user guide PDF)
- Platform: Linux 4.18 (el8), x86_64
- Python 3.11.17, pytest 9.1.1, tclsh 8.6.10
- Dependencies installed from `uv.lock` with `uv sync --extra test`; `bandit==1.9.4` added for the scans
- Command: `pytest -q -rs`, followed by `python security_scan/run_scans.py`

## 2. Overall Result

- Unit, component and packaging tests: 499 passed, 0 failed, 5 skipped, in 36.6 s.
- Security scans: 5 of 5 steps passed.
- Real Diamond 3.14.0.75.0, one design: the 4 integration tests passed (Section 5) and the design script compiled the same design (Section 6.1).
- Real Diamond 3.14.0.75.0, driven through the installed MCP server tools: 57 projects of the `customer_Mach_XO4` set were compiled with `compile_project`. 41 reached route completion and a bitstream, 16 did not (15 refused by the pre-flight check, 1 anomaly). See Section 6.2.
- Not executed: the wheel-download installer test (1 test), and the full run of the 229 in-scope designs by the design script. See Sections 5 and 6.

## 3. Results by Test File

| File | Executed | Passed | Failed | Skipped |
|---|---|---|---|---|
| test_audit.py | 37 | 37 | 0 | 0 |
| test_combine.py | 23 | 23 | 0 | 0 |
| test_config_discovery.py | 27 | 27 | 0 | 0 |
| test_create_export.py | 20 | 20 | 0 | 0 |
| test_embedded.py | 72 | 72 | 0 | 0 |
| test_hardening.py | 58 | 58 | 0 | 0 |
| test_installer.py | 72 | 71 | 0 | 1 |
| test_integration.py | 4 | 0 | 0 | 4 |
| test_linux_embedded.py | 30 | 30 | 0 | 0 |
| test_packaging.py | 9 | 9 | 0 | 0 |
| test_project.py | 15 | 15 | 0 | 0 |
| test_reports.py | 20 | 20 | 0 | 0 |
| test_security_scan.py | 20 | 20 | 0 | 0 |
| test_server.py | 57 | 57 | 0 | 0 |
| test_session.py | 38 | 38 | 0 | 0 |
| test_stdio_server.py | 2 | 2 | 0 | 0 |
| Total | 504 | 499 | 0 | 5 |

Some tests are parametrised, so 504 executed cases come from 381 distinct test functions.

## 4. Security Scan Results

| Step | Result |
|---|---|
| Bandit (static analysis) | 0 high, 0 medium, 45 low (low findings are informational) |
| Secrets scan | 95 files, 0 hits |
| OSV advisory check | 27 runtime and 11 build-only packages, 0 with advisories |
| Parser fuzzing (DAST) | 0 findings |
| Stdio protocol probes (DAST) | 24 probes, 24 passed, 0 failed |

- An earlier run dated 2026-10-29 is stored in `security_scan/results/rerun_2026-10-29/`. The present results are consistent with it; the Bandit low count and file count rose because files were added since.
- The present scan output was written to the git-ignored `security_scan/out/` and not committed.
- These scans have not been triaged by an SDLC security team.

## 5. Skipped Tests and Integration Run

- `test_installer.py:434` (1 test): skipped because `DIAMOND_TEST_INSTALLER=1` is not set; it downloads wheels.
- `test_integration.py` (4 tests): skipped in the default run (Section 2 counts), because `DIAMOND_TEST_LDF` was not set. They were then run separately against real Diamond 3.14.0.75.0 on one design (`8N1_uart_transiver_XO4`, device LCMXO3LF-1300E-5TG100C, a scratch copy): 4 passed in 81 s. They cover environment readiness, a full compile with bitstream, five open and close cycles without a Diamond crash, and failure reporting with hints.
- A first attempt at the integration run failed 3 of 4 tests in 0.5 s with a licence error. Cause: the licence on this host is configured only in `~/.flexlmrc`, and the test fixtures replace `HOME` with an empty folder. Setting `LM_LICENSE_FILE` explicitly resolved it. This is a setup requirement, not a server defect; it is recorded in the plan.

## 6. Design-Based Test (design-migration, Diamond 3.14)

### 6.1 Pilot with the design script

- Tool: `scripts/run_design_tests.py` (new), described in Test_Plan.md Section 3.9.
- Inventory found: 229 in-scope projects (12 XO2, 35 XO3, 182 XO3D) plus 10 in other families. The `perforce` tree holds 57 projects in 41 design folders; the XO3D designs are in `xo3d_primitive_tests`.
- Run in this session: 1 design, `perforce/.../8N1_uart_transiver_XO4/diamond_proj/xo2_verilog.ldf` (XO3 family).

| Stage | Result |
|---|---|
| open, Synthesis, Translate, Map, PAR, Bitgen | all ok |
| PAR run status | Completed, 0 unrouted connections, 0 errors |
| Bitstream (.bit) | produced |
| Resources | 63 of 640 SLICEs (10 percent), 85 of 1520 registers |
| Time | about 40 to 45 s |
| Timing constraint | not met: 125 MHz required, 111 MHz achieved (setup worst slack -1.009 ns); hold met |

- The original design folder was not modified (nothing in it is newer than the run); the scratch copy was deleted.
- The unmet timing is a property of the design on this device and is not a server defect. The server reported it correctly in its timing summary. The script counts such designs as flow passes and lists them separately.
- Result: 1 of 1 passed. This is not a result for the other 228 designs. The table below is to be replaced with the output of a full run.

| Family | In scope | Run | Passed | Failed |
|---|---|---|---|---|
| XO2 | 12 | 0 | not run | not run |
| XO3 | 35 | 1 | 1 | 0 |
| XO3D | 182 | 0 | not run | not run |

To complete: run `python scripts/run_design_tests.py --family xo2 --family xo3 --family xo3d --out results/` and paste `results/summary.md` here. Expect a long run (the pilot took under a minute; 229 designs sequentially is of the order of hours).

### 6.2 Compile run through the MCP server tools (customer_Mach_XO4)

- Method: the 57 `.ldf` projects in 41 design folders of `perforce/regtest/diamondng/trunk/benchmark/customer_Mach_XO4` were copied to `design-migration/dist/customer_Mach_XO4` (73 MB). Each was compiled in turn with the `compile_project` tool (open, Synthesis, Translate, Map, PAR, Bitgen) in one Diamond console session, with Diamond 3.14.0.75.0 and server version 0.1.0 (embedded Python 3.12.10 package). The source tree was not modified: it contains no bitstream and no file newer than the run log.
- Devices: LCMXO2, LCMXO3L and LCMXO3LF parts, with 1280 to 6864 LUT4s.

| Outcome | Projects |
|---|---|
| Compiled to route completion and bitstream | 41 |
| Of these, all timing constraints met | 10 |
| Of these, setup not met (counted as flow passes) | 31, of which 5 also had hold not met |
| Refused by the pre-flight check, before any flow ran | 15 |
| Anomaly: wrong implementation built, no bitstream | 1 |
| Total | 57 |

- Every one of the 41 compiled projects completed PAR with 0 unrouted connections and 0 errors, and a .bit file was found for each (41 bitstreams on disk). Individual compiles took 41 s to 130 s, except `A3_XO4/top` (LCMXO3LF-9400E), which took 1484 s (24.7 minutes), 1438 s of it in PAR. That project was moved to the background by the server and completed through its notification.
- Resource and timing figures were returned by the tool for each project. Unmet timing is a property of the designs on these devices, and the tool reported it correctly. This is not a server defect.
- Pre-flight refusals (15, each returned in 0 ms with the file names): 12 sub-projects of `rd1005_XO4` (`ecp3`, `ecp5`, `lptm`, `xo2`, `xo`, `xp2`, each in Verilog and VHDL) reference VHDL sources whose letter case differs from the file on disk (for example `I2C_Arb_Blk.vhd` against `i2c_arb_blk.vhd`); 3 projects reference a strategy file that is not in the folder (`SDFlashControllerUsingSDBus_XO4` and `SPISerialPeripheralInterfaceWISHBONEController_XO4` name `xo3l_verilog_syn1.sty` where the folder holds `xo3l_verilog1.sty`; `Simple_Sigma_Delta_XO4` names `xo2_verilog_lse1.sty`). These are defects in the project data or Linux case-sensitivity issues, and the server's diagnosis and hints were correct. The tool did not repair them, which is the intended behaviour.
- The full per-project log is held outside the repository (scratch results file) and is not committed.

### 6.3 Investigation of the 15 refused projects and the 1 anomaly

Method: the project files, the folders, the server source and the audit log were examined; each proposed fix was then applied only to the scratch copy in `design-migration/dist` (never to the original tree) and the project was recompiled with `compile_project`. The baseline counts in Section 6.2 are unchanged. Of the 16 projects, 5 were re-tested after a fix (listed below); the other 11 have the same cause as a tested one and were not re-run.

**A. Refused: letter-case mismatch (12 projects, `rd1005_XO4` sub-projects `ecp3`, `ecp5`, `lptm`, `xo2`, `xo`, `xp2`, Verilog and VHDL)**

- Cause: the `.ldf` files name nine VHDL sources in mixed case (`../../../source/vhdl/I2C_Arb_Blk.vhd`) while the files are lower case (`i2c_arb_blk.vhd`). The projects were written on a case-insensitive file system (Windows). Linux paths are case sensitive, so Diamond could not find the files, and the server's pre-flight check correctly stopped the run. The only other missing entries are simulation project files (`*.spf`), which do not block a compile.
- Fix: add the mixed-case names as symbolic links to the lower-case files (9 links in `source/vhdl`), or rename the files, or correct the references in the `.ldf` files. No change to the design logic is needed.
- Verification: with the 9 links in place, `xo2_vhdl` (LCMXO2-256 class, 37 s) and `ecp5_verilog` (ECP5, 50 s) compiled to route completion with a bitstream and all timing met. The other 10 sub-projects share the same sources and were not re-run.

**B. Refused: strategy file not found (3 projects)**

| Project | Names in `.ldf` | File in folder | Fix applied to the copy | Result |
|---|---|---|---|---|
| `SDFlashControllerUsingSDBus_XO4` | `xo3l_verilog_syn1.sty` | `xo3l_verilog1.sty` | link with the referenced name | compiled, bitstream, setup and hold not met (65.9 vs 150 MHz) |
| `SPISerialPeripheralInterfaceWISHBONEController_XO4` | `xo3l_verilog_syn1.sty` | `xo3l_verilog1.sty` | same link | not re-run (same cause) |
| `Simple_Sigma_Delta_XO4` | `xo2_verilog_lse1.sty` | `xo2_verilog.sty` | link with the referenced name | compiled, bitstream, all timing met |

- Cause: the strategy file was renamed after the `.ldf` was saved (the reference is stale). This is a defect in the project data, not a case problem. The pre-flight message listed the missing file but gave no hint, because no file differs only in letter case.
- Fix: correct the `Strategy` `file` attribute in the `.ldf`, or rename or link the file. The linked files are assumed to hold the intended strategy; this should be confirmed by the design owner, because a different strategy file changes the synthesis options.

**C. Anomaly: `xo3l_verilog_syn` built the sibling `xo3l_verilog_lse` project (1 project)**

- Cause (established): the folder holds two projects, and the server compiled `lse` first. The server deliberately never sends `prj_project close`, because that intermittently crashes Diamond 3.14.0.75.0; it restarts the console instead (`diamond_session.py`). Killing the console leaves Diamond's crash-recovery file `.recovery` in the project folder, and that file named the `lse` project. When the `syn` project was opened in the same folder, Diamond restored the project from `.recovery`, so the `lse` implementation was rebuilt (its files were rewritten, and no `syn` directory was created). The audit log shows the server sent the correct `prj_project open` each time; the open command returned success, so the server could not see the substitution.
- Fix (verified): remove or move aside the stale `.recovery` before opening. With the file moved aside in the copy, `compile_project` with `force=true` built `xo3l_verilog_syn` correctly in 41 s: a `syn` directory and its own bitstream were produced, and all timing was met.
- Scope: other folders that hold one project are exposed only if a different project is later opened there. Folders with several projects (for example this one) are exposed on every second open.

**D. Is making these projects compile within the scope of the server?**

| Item | Within scope | Beyond scope |
|---|---|---|
| C (stale `.recovery`) | Yes. Implemented after this run (`project.set_aside_stale_recovery`, called from `open_project`; 8 new tests, full suite 507 passed, 5 skipped). The set-aside is renamed, not deleted, and a warning is returned. The post-open title check below is not implemented. This is a server defect: the restart-instead-of-close design leaves state that changes the next open. Proposed change: before `prj_project open`, if `.recovery` exists in the project folder and does not name the requested project, rename it (for example `.recovery.stale`, so unsaved work is not lost) and report a warning; then check, after opening, that `prj_project` reports the requested title and fail with a clear error if it does not. Add a test with two projects in one folder. | |
| A (case mismatch) | Diagnosis, hints and an optional documented remedy in the hint text: already done and correct. | Automatically renaming files or creating links in a user's source tree. The server would change customer files without consent and could hide a real portability defect. Repair belongs to the design owner or a separate, opt-in migration tool (for example the design-migration workflow). |
| B (stale strategy name) | Adding a hint that names the closest file in the folder (for example `xo3l_verilog1.sty`), as already done for case differences. | Choosing and substituting a strategy file: this changes the synthesis options and needs a decision by the design owner. |

### 6.4 Experiment: the 15 refused projects, repaired outside the server and compiled through it

Purpose: to show that, once the project-data defects are repaired, the server can run these projects. The repairs were made by hand in the scratch copy under `design-migration/dist` (case-correcting links for the 9 differing VHDL sources, and links from the stale strategy names to the existing `.sty` files); the Perforce originals and the server were not changed. Each project was then compiled once with the source-tree server's `compile_project` tool, `force=true`, one fresh call per project.

- Pre-flight: all 15 passed (0 blocking missing files).
- Result: 7 of 15 compiled end to end with a bitstream; 8 of 15 were reported as a Bitgen failure. In all 8, the flow had reached PAR, and Bitgen wrote its output file. None failed in synthesis, translate, map or PAR.

| Group | Projects | Server result | Output file | Cause |
|---|---|---|---|---|
| Compiled | `SDFlashControllerUsingSDBus` (xo3l_verilog), `Simple_Sigma_Delta` (xo2_verilog), `SPISerialPeripheralInterfaceWISHBONEController` (xo3l_verilog), rd1005 `ecp3` (2), `ecp5` (2), `xo2` (2) | Success, 45 s to 60 s each | `.bit` | None |
| lptm, xo (4 projects) | rd1005 `lptm` and `xo`, Verilog and VHDL | Bitgen failed | `.bit` written (20,218 and 9,224 bytes for the Verilog projects) | After the `.bit` is written, Diamond runs `ddtcmd` to convert it to `.jed`; `ddtcmain` fails with `libusb-0.1.so.4: cannot open shared object file`. This is a missing system library on this host. |
| xp2 (2 projects) | rd1005 `xp2`, Verilog and VHDL | Bitgen failed | `.jed` written (about 1.25 MB) | Bitgen succeeded but writes a JEDEC file, not a `.bit`. The server's check expects a `.bit`, so it reports "Bitgen returned success but no .bit file was written". |

Assessment:
- xp2 is a server defect (a false failure). The result check should also accept `.jed` for devices whose bitstream is a JEDEC file. This is within the scope of the server. It was not fixed in this experiment.
- lptm and xo: the server reported the failure correctly, because Diamond itself reported the milestone as failed. The cause is host setup (install the 32-bit/compat `libusb-0.1` package, or ignore the `.jed` conversion), which is beyond the scope of the server. The `.bit` file was produced.
- Conclusion for the experiment: with the project data repaired, the server ran all 15 projects through PAR without any server error. 7 completed fully, and the other 8 each wrote their output file before the failure described above. For the strict criterion "reports success", 7 of 15 passed; for "output produced", 15 of 15.
- Timing was not collected for these runs, and the repairs are manual. Not covered: the other 56 designs were not re-run with the `.recovery` fix.

## 7. Slowest Tests

- `test_a_real_process_started_from_the_folder_is_found_and_stopped`: 5.0 s
- Four crash and restart tests in `test_session.py` and `test_server.py`: about 4.1 to 4.2 s each, due to deliberate crash and timeout waits

## 8. Findings and Observations

- No automated test failures were found in this run. The compile run of Section 6.2 gave the following observations about the server; none of them is a confirmed server defect, and each should be triaged:
  - Default implementation mismatch (`I2C_Slave_with_8_bit_out_XO4`): the `.ldf` names a default implementation that does not exist (`I2C_slave_with_8bit_out`; the only one is `impl_1`). The first call was refused with a clear message. With `implementation="impl_1"` the stages returned in milliseconds from stale results copied with the project, and Bitgen was reported as failed with a warning that no .bit file was written. With `force=true` the compile passed in 71 s. Improvement idea: fall back to the only implementation when there is one, and treat up-to-date results as a distinct state rather than a Bitgen failure.
  - Wrong implementation built (`I2SControllerwithWISHBONEInterface_vhdl_XO4/project/xo3l/verilog/xo3l_verilog_syn.ldf`): the cause is now established and the finding is a server defect (Section 6.3, item C). The server restarts the Diamond console instead of closing the project; the `.recovery` file left in the folder made Diamond reopen the sibling `lse` project. With the stale file moved aside the project compiled correctly. Recommended change: detect and set aside a stale `.recovery` before opening, and verify the opened project title.
  - Letter-case and missing-file refusals (15 projects): the pre-flight check works as intended and is correct. The causes are project-data defects (12 letter-case, 3 stale strategy file names). Fixes were verified on 4 of the 15 (Section 6.3); repairing them is beyond the scope of the server, except for a closer hint for the strategy file case.
  - Long PAR: `A3_XO4/top` took 24.7 minutes; the background and notification path worked.
  - Bitgen result check (Section 6.4): for devices whose bitstream is a JEDEC file (xp2), the server reports a false failure because it looks only for `.bit`. Recommended fix, within scope: accept `.jed`.
  - Host library: `libusb-0.1.so.4` is missing on this host, which makes Diamond's `.bit` to `.jed` conversion fail for the lptm and xo devices (Section 6.4). Not a server defect.
- The default `python3` on this host is 3.8.5, which does not meet the `>=3.11` requirement; the run used `python3.11` in an isolated environment.
- Windows packaging steps and the installed-package smoke tests run in CI on the target systems and were not executed here.
- Coverage was not measured.
- The count of 43 designs given for the `perforce` tree was not confirmed: the tree has 41 design folders and 57 projects, and the XO3D designs are elsewhere.

## 9. Conclusion

On the tested Linux platform, the automated suite and the security scans pass in full, which meets the unit-level and scan exit criteria in the plan. The integration tests also pass against real Diamond 3.14.0.75.0 on one design, and that design compiles end to end through the server's tools. A further compile run through the server tools on 57 customer designs (Section 6.2) produced 41 bitstreams with no server fault in those runs; 15 projects were correctly refused because of project-data defects (not server faults), and one anomaly (wrong implementation built in a two-project folder) was traced to a server defect: a stale `.recovery` file left because the server restarts the console instead of closing the project. A fix for that defect (set aside a stale `.recovery` before opening) has since been implemented and unit tested (Section 6.3, item D); it has not yet been re-run against the 57 designs or in an integration test with two projects in one folder. Wider assurance depends on the full design run of the 229 in-scope designs (Section 6.1), which has not been done. Sign-off for a release that changes session handling, flow tools or report parsing should include that run, and the CI package builds must pass for their target systems.

Internal policy: no policy number is available from the repository for citation. The document owner should add the applicable policy and compliance references before this summary is used as a formal record.
