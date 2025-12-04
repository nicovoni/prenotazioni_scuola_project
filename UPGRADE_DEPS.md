# Dependency upgrade workflow

This document explains the recommended workflow to upgrade all Python dependencies
to their latest stable releases for the `aulamax` project.

Overview
--------
- Work on a dedicated branch (the helper script creates `upgrade/deps-latest`).
- Use `pip-tools` (`pip-compile`) to deterministically pin top-level dependencies.
- Run migrations and the test suite, then build the Docker image to validate the environment.

Quick steps (recommended)
-------------------------
1. From repository root, run the provided PowerShell helper (Windows):

```powershell
.\scripts\upgrade_deps.ps1
```

2. Review the changes to `requirements.txt` and `requirements.in`.
3. Run the app locally (migrations + runserver) and perform manual E2E tests for the
   setup wizard and forced password-change flow.
4. Commit and open a PR for review.

Notes and caveats
-----------------
- Major version upgrades (e.g. Django 6.x if you are on Django 5.x) may require
  code changes. Prefer incremental updates: upgrade patch/minor versions first,
  run tests, and then consider major upgrades.
- The script uses `pip-compile --upgrade` which will pin the newest available
  versions of your top-level dependencies. Inspect the result before committing.
- The Docker build step may require installing build dependencies in the Dockerfile
  (e.g. `gcc`, `libffi-dev`, etc.). If builds fail because of missing wheels, add
  the minimal build packages to the Dockerfile only for the build stage.

If you want me to proceed with the upgrades here (attempt to run the script), say
so and I'll try to run the upgrade workflow and report results/logs. If running
locally, expect network downloads and a multi-minute Docker build.
