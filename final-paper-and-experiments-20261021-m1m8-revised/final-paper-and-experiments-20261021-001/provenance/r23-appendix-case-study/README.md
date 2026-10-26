# R23: literature SoK with one appendix case

The main manuscript presents only the literature evidence model, complete audit, joint bindings, holdout synthesis and reuse procedure. Exp 1–4 are consolidated into one compact appendix case. Full empirical grids remain in the supplement; no experiments, raw results or coding were changed.

Build the committed manuscript with `build_pdfs.py`, render it with `render_review.py`, and run `verify_revision.py` for body scope, the single-page case, numerical bindings, preserved evidence, citations and published PDF copies. `update_metadata.py` registers the current sources. `release_ops.py anonymous` packages the paper/source closure; `release_ops.py manifest` updates the full artifact inventory after all outputs are final. `write_docs.py` generates the Chinese revision note from the verification receipt.

The committed sources are authoritative; historical editorial generators should not be used to recreate the current manuscript.
