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
- Not executed: tests against a real Diamond installation (4 tests) and the wheel-download installer test (1 test). See Section 5.

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

## 5. Skipped Tests

- `test_integration.py` (4 tests): skipped because `DIAMOND_TEST_LDF` is not set and no licensed Diamond was used. Real-Diamond behaviour is therefore not verified by this run.
- `test_installer.py:434` (1 test): skipped because `DIAMOND_TEST_INSTALLER=1` is not set; it downloads wheels.

## 6. Slowest Tests

- `test_a_real_process_started_from_the_folder_is_found_and_stopped`: 5.0 s
- Four crash and restart tests in `test_session.py` and `test_server.py`: about 4.1 to 4.2 s each, due to deliberate crash and timeout waits

## 7. Findings and Observations

- No test failures and no defects were found in this run.
- The default `python3` on this host is 3.8.5, which does not meet the `>=3.11` requirement; the run used `python3.11` in an isolated environment.
- Windows packaging steps and the installed-package smoke tests run in CI on the target systems and were not executed here.
- Coverage was not measured.

## 8. Conclusion

On the tested Linux platform, the automated suite and the security scans pass in full, which meets the unit-level and scan exit criteria in the plan. Sign-off for a release that changes session handling, flow tools or report parsing still requires the integration tests on a machine with a licensed Diamond, and the CI package builds must pass for their target systems.

Internal policy: no policy number is available from the repository for citation. The document owner should add the applicable policy and compliance references before this summary is used as a formal record.
