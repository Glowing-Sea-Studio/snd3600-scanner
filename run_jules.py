import os
import json
import urllib.request

API_KEY = os.environ.get("JULES_API_KEY")
if not API_KEY:
    print("No JULES_API_KEY")
    exit(1)

with open("jules-tasks/next-gen-ui-20260905-2307.md") as f:
    spec_content = f.read()

prompt = f"""Please implement the features described in the spec file below.

{spec_content}

--- Guardrails (mandatory, do not skip) ---
- Do NOT run Playwright, Cypress, or any headless-browser / e2e / UI test
  runner. These frequently hang or crash this sandbox and kill the session.
  If the task needs UI verification, do it via static/type checks and unit
  tests only, and describe manual verification steps in the PR description
  instead of executing browser automation.
- Do NOT run any destructive git command: `git reset --hard`,
  `git checkout -- .` / `git restore .`, `git clean -fd`/`-fdx`, `git stash`
  without immediately restoring it, force-push, or history rewrite
  (amend/rebase) on commits already pushed. Never discard uncommitted
  changes, yours or pre-existing.
- Commit your work incrementally and frequently (small, working commits) so
  nothing is lost if the session stops early.
- If you are unsure whether a command is safe, don't run it — describe what
  you intended to do instead and ask.
"""

payload = {
    "prompt": prompt,
    "title": "Next-Gen UI & Features",
    "sourceContext": {
        "source": "sources/github/Glowing-Sea-Studio/snd3600-scanner",
        "githubRepoContext": { "startingBranch": "main" }
    },
    "automationMode": "AUTO_CREATE_PR",
    "requirePlanApproval": True
}

req = urllib.request.Request(
    "https://jules.googleapis.com/v1alpha/sessions",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode())
