# CI/CD with GitHub Actions

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

These are my concept notes for the CI/CD session. I use my capstone app
GearLoan (FastAPI backend, React frontend, PostgreSQL) as the running example.

## 1. CI vs CD

| Term | Full form | What it means |
|------|-----------|---------------|
| CI | Continuous Integration | Every push is built and tested automatically. Problems are found early. |
| CD | Continuous Delivery | Every change that passes CI is ready to release. A human clicks "deploy". |
| CD | Continuous Deployment | Every change that passes CI goes to production by itself. No manual step. |

The only difference between the two CDs is the **manual approval** before production.

```
CI:                    code -> build -> test
Continuous Delivery:   code -> build -> test -> staging -> [approve] -> prod
Continuous Deployment: code -> build -> test -> staging -> prod
```

Small example: in GearLoan, if I push a change to `backend/` and the pytest
tests run on their own, that is CI. If the image is then pushed and the
cluster is updated without me doing anything, that is continuous deployment.

## 2. CI/CD pipeline stages

A pipeline is the full path a change takes from commit to running app.

| Stage | What happens | GearLoan example |
|-------|--------------|------------------|
| Source | Code is pushed or a PR is opened | `git push` to `master` |
| Build | Install deps, compile, build image | `pip install`, `npm run build`, `docker build` |
| Test | Unit tests, lint, type checks | `pytest`, `npm test`, `ruff` |
| Package | Save the output somewhere | Push image to a registry, upload artifact |
| Deploy | Release to an environment | Helm upgrade or Argo CD sync |
| Verify | Check the release is healthy | Readiness probes, `/health`, Grafana |

If any stage fails, the later stages do not run. This is the main safety idea.

## 3. GitHub Actions

GitHub Actions is the CI/CD system built into GitHub. You write YAML files
inside `.github/workflows/` and GitHub runs them when an event happens.

The building blocks, from big to small:

```
Workflow  (one YAML file)
 └── Job   (runs on one runner)
      └── Step  (one command or one action)
```

### 3.1 Workflow

- A workflow is one `.yml` file in `.github/workflows/`.
- It has a `name`, an `on:` section (triggers) and a `jobs:` section.
- A repo can have many workflows, for example `ci.yml` and `release.yml`.

### 3.2 Jobs

- A job is a group of steps that run on the **same runner** (same machine).
- Jobs run **in parallel** by default.
- Use `needs:` to make one job wait for another.
- Steps in one job share the file system. Different jobs do not.

### 3.3 Steps

A step is either a shell command (`run:`) or a reusable action (`uses:`).

```yaml
steps:
  - uses: actions/checkout@v7          # an action (reusable code)
  - run: echo "Hello from a step"      # a shell command
```

Steps run one after another. If one step fails, the job stops.

## 4. Runners

A runner is the machine that runs a job.

| Type | Who manages it | Good for |
|------|----------------|----------|
| GitHub-hosted | GitHub | Most projects. Fresh VM every job, no setup. |
| Self-hosted | You | Special hardware, private network access, own cache. |

- `runs-on: ubuntu-latest` picks the newest stable Ubuntu image GitHub offers.
  The exact version behind the label changes over time, so for fixed builds
  you can write `ubuntu-24.04` instead.
- Other hosted labels: `windows-latest`, `macos-latest`.
- A self-hosted runner is chosen with labels, for example
  `runs-on: [self-hosted, linux]`.
- GitHub-hosted runners start clean every time, so nothing is left from the
  previous run. Self-hosted runners can keep old files, so be careful.

## 5. Secrets

Secrets hold passwords, tokens and keys. They are encrypted and are hidden
(`***`) in logs.

| Kind | Where set | Used for |
|------|-----------|----------|
| Repository secret | Settings -> Secrets and variables -> Actions | Shared by all workflows in the repo |
| Environment secret | Settings -> Environments -> (env) | Only jobs that say `environment: <name>`. Can need approval. |
| Organization secret | Org settings | Shared across many repos |

Using a secret:

```yaml
- run: docker login -u "$USER" --password-stdin <<< "$TOKEN"
  env:
    USER: ${{ secrets.DOCKERHUB_USER }}
    TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
```

Rules I follow:
- Never `echo` a secret.
- Pass secrets through `env:` and not straight into the command text.
- Secrets are not given to workflows triggered from forked PRs.

### GITHUB_TOKEN and `permissions:`

- GitHub creates a `GITHUB_TOKEN` for every run. It expires when the job ends.
- It can call the GitHub API for this repo only (comment on PRs, push to GHCR, etc).
- Use `permissions:` to give it only what it needs. Anything not listed is set to `none`.

```yaml
permissions:
  contents: read     # read the code
  packages: write    # push an image to ghcr.io
```

Keeping permissions small means a broken or bad step can do less damage.

## 6. Artifacts

An artifact is a file or folder saved from a run, for example a test report,
a coverage file or a built `dist/` folder.

```yaml
- uses: actions/upload-artifact@v7
  with:
    name: frontend-dist
    path: frontend/dist/
    retention-days: 7
```

- You can download artifacts from the run summary page.
- Another job in the same run can get it with `actions/download-artifact`.
- Default retention is 90 days (repo or org admins can change the limit).
  `retention-days` makes it shorter for one artifact.
- Artifacts are different from **cache** (`actions/cache`). Cache is to make
  later runs faster. Artifacts are outputs you want to keep or pass on.

## 7. Build and Test

**Build** means turning source code into something that can run.

| Part of GearLoan | Build step |
|------------------|------------|
| Backend (FastAPI) | `pip install -r requirements.txt` |
| Frontend (React) | `npm ci` then `npm run build` |
| Container | `docker build -t gearloan-backend .` |

**Test** means checking the build behaves correctly.

| Kind | Example |
|------|---------|
| Lint | `ruff check .`, `npm run lint` |
| Unit test | `pytest tests/` |
| API test | Call `/health` with FastAPI `TestClient` |

`npm ci` is used in CI instead of `npm install` because it installs exactly
what is in `package-lock.json` and fails if the lock file is out of date.

## 8. Pipeline execution

### 8.1 Triggers (`on:`)

| Trigger | When it runs |
|---------|--------------|
| `push` | Commit pushed to a branch (can filter by `branches` and `paths`) |
| `pull_request` | PR opened, updated or reopened |
| `workflow_dispatch` | Manual "Run workflow" button in the Actions tab |
| `schedule` | Cron time, for example nightly |

```yaml
on:
  push:
    branches: [master]
    paths: ["backend/**"]
  pull_request:
  workflow_dispatch:
```

### 8.2 Job ordering with `needs:`

```
 lint ──┐
        ├──> build-image ──> deploy
 test ──┘
```

```yaml
jobs:
  lint:  { ... }
  test:  { ... }
  build-image:
    needs: [lint, test]     # waits for both
  deploy:
    needs: build-image
```

If `test` fails, `build-image` and `deploy` are skipped.

### 8.3 How to read a run

1. Open the **Actions** tab and click the run.
2. The summary page shows the trigger, commit, and a graph of jobs.
3. Each job shows a status: success (green tick), failure (red cross),
   skipped (grey), or in progress (yellow).
4. Click a job to see each step. Expand a step to see its log.
5. The failing step is marked red. Read the last lines of its log first.
6. Artifacts are listed at the bottom of the summary page.
7. "Re-run failed jobs" runs only the jobs that failed.

## 9. Small annotated workflow

`.github/workflows/backend-ci.yml`

```yaml
name: backend-ci                       # name shown in the Actions tab

on:                                    # triggers
  push:
    branches: [master]
    paths: ["backend/**"]              # only when backend code changes
  pull_request:
    paths: ["backend/**"]
  workflow_dispatch:                   # manual run button

permissions:
  contents: read                       # GITHUB_TOKEN can only read code

jobs:
  test:
    runs-on: ubuntu-latest             # GitHub-hosted runner
    defaults:
      run:
        working-directory: backend     # all run: steps start here
    steps:
      - uses: actions/checkout@v7      # get the repo code
      - uses: actions/setup-python@v7  # install Python
        with:
          python-version: "3.12"
          cache: pip                   # reuse pip downloads between runs
      - run: pip install -r requirements.txt
      - run: pytest -q --junitxml=report.xml
      - uses: actions/upload-artifact@v7
        if: always()                   # upload even when tests fail
        with:
          name: pytest-report
          path: backend/report.xml
          retention-days: 7

  frontend-build:
    runs-on: ubuntu-latest
    needs: test                        # runs only after test passes
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: "22"
      - run: npm ci
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
```

