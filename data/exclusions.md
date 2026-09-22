# Job Search Exclusion List

Companies you have deliberately passed on. `scripts/screen.py` discards any role at a company
listed here before scoring, and `apply-assist` stops on one. Matching uses
`scripts/normalize.py` (case-insensitive, legal suffixes ignored).

This list is for **deliberate company-level passes** after a real evaluation (domain mismatch,
comp, culture). It is not the same as a rejection, and role-level passes do not belong here:
a company that posts one wrong-fit role is still eligible for its other roles. Role-level
screens live in `data/screens.json`.

| Company | Excluded on | Reason | Revisit condition |
|---|---|---|---|

**How to add an entry:** whenever an evaluation ends in "pass on this company entirely", add a
row with the date, the concrete reason, and, if there is one, a condition under which it is
worth revisiting. Keep reasons specific enough that a future run can tell whether the revisit
condition has been met.
