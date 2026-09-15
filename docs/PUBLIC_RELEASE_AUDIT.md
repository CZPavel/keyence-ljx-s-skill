# Public release audit

Checked: copyright/raw text, internal content, absolute paths, secrets, and large/generated artifacts.

Findings/remediation: manufacturer native-text excerpts were retained only in ignored `local_evidence`; public evidence blocks now contain metadata locators and hashes. Raw conflict-table text was replaced with a local-source notice. Corpus, manuals, OCR/VLM, installers, images, logs, caches and old smoke benchmarks are ignored. Public raw-corpus fallback is optional and reports unavailable when no local corpus is supplied.

Remaining risk: normalized facts and short command syntax require independent review against official documentation before operational use.
