# Publication repository

- Keep task tracking, issues, research work, work logs, and backups in the parent project. Do not create ginit workspace directories inside this repository.
- The editable sources are `data/databases.csv` and `data/supplement.json`. `data/databases.xml` is generated from these; do not replace sources from a research export without reviewing changes.
- Keep this repository limited to the current listed XML/CSV, runtime code, assets, validation schemas, tests, documentation, and GitHub Pages workflow.
- Do not import collection snapshots, raw HTML, original intake CSV/XML, review manifests, previous metadata values, or scraping/migration tools. Those remain in the separate local work project.
- Do not commit files larger than 50 MB.
- `sh build.sh` refreshes `data/databases.xml` from CSV + JSON and builds `dist/`. Commit regenerated XML alongside source edits; never overwrite the editorial CSV from XML.
- The website publishes only the standard `dist/data/jpcoar.xml`; `data/databases.xml` and `data/databases.csv` are linked from README on GitHub.
- Keep hierarchy derived from JPCOAR `hasPart`/`isPartOf`. Short inline HTML belongs in `nihu:listSummary`; detailed modal text stays in `Abstract`.
- Run `sh check.sh` after meaningful changes; inspect staged paths and sizes before committing.

## Current editorial pipeline

- The user explicitly approved canonical CSV + supplemental JSON. CSV owns all matching basic fields; JSON holds only additional structure, display settings, resource-type decisions and provenance.
- Generate the integrated XML with `sh prepare.sh`; never directly edit generated XML or regenerate the canonical CSV from XML. Builds must not overwrite editorial CSV/JSON.
- The shared profile is `catalogue_source/README.md` with `schema/catalogue.xsd`. Keep compiler/profile changes identical in both catalogue repositories; each remains independently buildable.
- Original exports and historical XML correction reports are archival evidence, never normal build inputs. New corrections belong in the canonical CSV and its audit trail, not the originals.
