# Participant flow

Only counts that are present in the analytic file are filled. Intermediate counts are not invented.

```mermaid
flowchart TD
    sib["SIB records<br/>Initial count: Not documented"]
    nut["Nutrition Unit records<br/>Initial count: Not documented"]
    hs["Healthy records selected<br/>Count: Not documented<br/>Method: unresolved<br/>Draft says simple random sampling<br/>Table 1 note says growth-percentile strata"]
    ms["Malnourished records selected<br/>Count: Not documented<br/>Draft mentions a 399-child file, not linked by a log"]
    ex["Duplicates removed: Not documented<br/>Age exclusions: Not documented<br/>Congenital-disease exclusions: Not documented"]
    fin["Analytic file<br/>504 rows and 504 unique children<br/>Healthy, code 7 only: 293<br/>Malnourished, any code 1-6: 211"]
    sib --> hs
    nut --> ms
    hs --> ex
    ms --> ex
    ex --> fin
```

Counts that appear in other project files and are not flow steps: 380 and 359 planned, 282 and 316 in an earlier draft, 598 rows in a working file with duplicate identifiers.

The analytic file has one row per national identifier, so the final unit is the child.
