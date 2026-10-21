# Author confirmations required before submission (checklist B2, K8, K9)

These facts can only be confirmed by the authors. Fill in every field, commit the file,
and then remove the corresponding "not revalidated" sentences in §9.2 and §5.2.

## 1. Saved model outputs (K8)
- Model identifier and provider as recorded in `request.json`: `gpt-6-luna` / ______
- Generation dates (first and last request): ______
- Sampling configuration (temperature, top_p, max tokens, seed if any): ______
- Terms of use in force on those dates allow research use and publication of outputs: yes / no; link: ______
- Was any output edited after generation? yes / no (if yes, list the IDs)

## 2. AHB per-condition sample sizes (K9)
The manuscript does not report a matched effect for AHB because the per-condition
denominators could not be recovered. Draft request to the AHB authors:

> Dear authors, for a systematization we are reporting the Trip Planning success rates in
> Table 1 of arXiv:2604.09574v1 (Raw 0.75; Online+Fake 0.15; History+Long 0.7143). Could
> you share the number of episodes behind each condition, and whether the same task
> instances were used across conditions? We will cite your reply as a personal
> communication.

- Reply received: ______   n per condition: ______

## 3. Anonymous artifact (B2)
1. Run `python -B release/anonymize_package.py --names "<every author name>" "<handles>" "<affiliations>"`.
   It must report 0 hits.
2. Upload `artifact-anonymous.zip` to anonymous.4open.science (from a GitHub repo with no
   identifying history) or to a Zenodo draft with a reserved DOI.
3. Record the URL and the SHA-256 printed by the script: ______
4. Replace "An accessible immutable anonymous repository remains a submission task" in
   §9.2 with the URL.

## 4. Coding (B1)
- Coder IDs and signed declarations stored by the custodian: ______
- `coding/sheets/MANIFEST.json` committed before distribution (commit hash): ______
