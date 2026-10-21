# Second retrieval frame (checklist B4, partial)

`second_frame.py` ran 10 fixed arXiv API queries on 2026-10-21. They returned 749
unique records. Of the 58 core families, 37 appear in this frame, 39 appear in the
565-record first frame and 46 appear in at least one. The remaining 12 were found only
by seed snowballing. Of the 24 adjacent families, 10 appear in at least one frame.

`frame2_screening_queue.csv` lists the 617 returns that match neither the family index
nor the first frame. They have not been screened.

These queries were written by the corpus authors, so they are not independent of the
first frame. **No recall estimate is claimed.** To produce one:
1. A second searcher who has not seen the corpus writes queries for IEEE Xplore, ACM DL,
   USENIX, NDSS and arXiv.
2. Blinded coders screen both frames with the C1–C5 criteria (`../coding/CODEBOOK.md`).
3. Report a Chapman estimate (n1+1)(n2+1)/(m+1)−1 of eligible core studies and state
   the independence assumption.
