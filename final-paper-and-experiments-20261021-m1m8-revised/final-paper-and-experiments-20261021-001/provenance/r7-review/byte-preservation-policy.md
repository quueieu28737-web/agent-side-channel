# Exact publication bytes across Git checkouts

The package manifest hashes raw bytes, including text line endings. The repository now marks the entire publication package `-text` in `.gitattributes`, extending the prior protections for frozen R4/R6 directories. This prevents a reader's `core.autocrlf` setting from altering hashed code, data or receipts on checkout. It does not change existing experiment files or suppress normal text diffs.

Before committing, `verify_staged_bytes.py` compares the Git index blob identity with each staged file's unfiltered working-tree bytes. The package verifier separately checks SHA-256, membership and LaTeX closures. A later intentional manuscript edit requires a new manifest; it must not silently rewrite a frozen experiment.
