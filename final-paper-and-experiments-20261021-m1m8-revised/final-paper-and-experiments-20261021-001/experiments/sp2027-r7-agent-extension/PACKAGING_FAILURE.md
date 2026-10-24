# Packaging failure retained

The first publication-copy packaging attempt used the frozen package_raw.py and exited1 before creating an archive:

```
RuntimeError: Unredacted user path: connectivity\0\thread_request.json
```

Its exact-current-home replacement did not cover every Windows HOME-prefix spelling/alias. The fail-closed residual-path check caught the omission. package_raw.py and all original model/scientific files remain unchanged.

The separately versioned package_raw_v2.py expands only the publication-copy HOME-prefix rule to Windows drive:/Users/user-component spellings, including slash/backslash, case and short-name aliases. It serializes copies as UTF8 JSON/JSONL, records original/public SHA256 and substitution counts, and rejects credential patterns or residual absolute user paths. No task content, model decision, reward, usage or measured timing is changed. PACKAGING_AMENDMENT.json binds the failure, both source hashes and the unchanged formal plan. PUBLIC_REDACTION.json binds the final copy transformation.
