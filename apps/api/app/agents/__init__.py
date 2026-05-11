"""NoticeDesk agents (Sprint 3+).

Sprint 3 ships two agents:

- :mod:`app.agents.document_parsing` — LLM-driven classifier + extractor.
- :mod:`app.agents.notice_routing` — rule-based PAN-centric routing.

Both run inside :mod:`app.workflows.document_parsing_and_routing`, which is
triggered after the OCR workflow from Sprint 2 completes.
"""
