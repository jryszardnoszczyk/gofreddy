# A6 — Krippendorff α measurement

- Runs per fixture: 5
- Total wall time: 13m 12s
- Fixtures attempted: 10

## Per-axis α per lane

| Lane | Axis | α (interval) | n fixtures | flag |
|---|---|---|---|---|
| geo | GEO-1 | 0.625 | 2 | ⚠ panel |
| geo | GEO-2 | -0.108 | 2 | ✗ rewrite |
| geo | GEO-3 | -0.000 | 2 | ✗ rewrite |
| geo | GEO-4 | 0.751 | 2 | ✓ stable |
| geo | GEO-5 | 0.949 | 2 | ✓ stable |
| geo | GEO-6 | -0.065 | 2 | ✗ rewrite |
| geo | GEO-7 | -0.000 | 2 | ✗ rewrite |
| geo | GEO-8 | 0.625 | 2 | ⚠ panel |
| monitoring | MON-1 | 0.000 | 1 | ✗ rewrite |
| monitoring | MON-2 | 0.000 | 1 | ✗ rewrite |
| monitoring | MON-3 | n/a | 1 | n/a |
| monitoring | MON-4 | n/a | 1 | n/a |
| monitoring | MON-5 | 0.000 | 1 | ✗ rewrite |
| monitoring | MON-6 | 0.000 | 1 | ✗ rewrite |
| monitoring | MON-7 | 0.000 | 1 | ✗ rewrite |
| monitoring | MON-8 | n/a | 1 | n/a |

## Per-fixture composite CV

| Lane | Fixture | CV |
|---|---|---|
| geo | geo-ahrefs | 0.0073 |
| geo | geo-mayoclinic | 0.0202 |
| monitoring | monitoring-rippling | 0.0131 |

## Stream C decision matrix (plan §6.A7)

- α ≥ 0.7 on every essential axis: skip panel-of-3 in v1.
- 0.5 ≤ α < 0.7: panel-of-3 justified.
- α < 0.5 on any essential axis: rewrite that rubric prose first.
