# Publication repository

- Keep task tracking, issues, research work, work logs, and backups in the parent project. Do not create ginit workspace directories inside this repository.
- The canonical public metadata is `data/databases.xml`. Do not replace it from a research export without reviewing changes.
- Keep this repository limited to the current listed XML/CSV, runtime code, assets, validation schemas, tests, documentation, and GitHub Pages workflow.
- Do not import collection snapshots, raw HTML, original intake CSV/XML, review manifests, previous metadata values, or scraping/migration tools. Those remain in the separate local work project.
- Do not commit files larger than 50 MB.
- `sh build.sh` refreshes `data/databases.csv` from the XML and builds `dist/`. Commit the refreshed CSV alongside XML edits.
- The website publishes only the standard `dist/data/jpcoar.xml`; `data/databases.xml` and `data/databases.csv` are linked from README on GitHub.
- Keep hierarchy derived from JPCOAR `hasPart`/`isPartOf`. Short inline HTML belongs in `nihu:listSummary`; detailed modal text stays in `Abstract`.
- Run `sh check.sh` after meaningful changes; inspect staged paths and sizes before committing.
