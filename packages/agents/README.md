# @noticedesk/agents

Python package for agent prompts and orchestration. Mostly empty in
Sprint 1 by design — runtime agent code begins in Sprint 2 (notice
parsing) and Sprint 3 (drafting). Don't add runtime agent code here
ahead of the sprint contract.

The package exists so that:

1. CI can include this directory in its lint paths once code lands.
2. Imports from `noticedesk_agents` resolve cleanly when Sprint 2 begins.

## What lives here today

- `noticedesk_agents/prompts/` — versioned Markdown prompt artifacts
  with `{{VAR}}` placeholders, plus a stdlib-only renderer
  (`prompts/render.py`) for strict substitution.
- `noticedesk_agents/prompts/gst_appellate/` — GST Appellate Authority
  (Section 107, CGST Act, 2017) prompts:
  - `mock_personal_hearing.md` — live, turn-by-turn quasi-judicial
    persona (v1.1, production).
  - `post_hearing_critique.md` — one-shot structured critique that runs
    after a hearing transcript has been captured (v1.0, production).
- `tests/` — pytest harness covering the renderer plus structural and
  scenario-level checks on the prompts. Run from the repo root:

  ```
  pytest packages/agents/tests
  ```

  Three mock hearing scenarios live in `tests/fixtures/gst_appellate/`
  (`thin_file`, `limitation_defect`, `strong_merits`) and exercise the
  empty-variable, required-variable, and full-file code paths.
