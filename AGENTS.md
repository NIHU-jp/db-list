# Project Instructions

- Do not add or commit files under `repos/` to the outer project Git repository.
- Treat each directory under `repos/` as an independent repository with its own history.
- Do not commit files larger than 50MB to the outer project.
- If a large file is needed, leave it in place, add an ignore rule for it, and create `large-files.tsv` to record it when useful.
- Before committing, check `git status --short` and `git diff --cached --stat`.
- Keep day-to-day task data in `tasks/`: `tasks/todo.txt`, `tasks/done.txt`, and `tasks/notes/`.
- Use plain todo.txt lines: `Task text +tag due:YYYY-MM-DD note:foo.md`; do not use `[ ]` checkbox prefixes.
- Keep notes under `tasks/notes/` and link them from todo items with short paths such as `note:foo.md`.
- Use `issues/` for structured issue or decision records, not for live todo viewer files.
- Keep `inbox/` temporary. Move durable notes to `issues/`, `work/`, or `worklog/`.

# Publication repository

- The canonical public metadata is `data/databases.xml`. Do not replace it from a research export without reviewing changes.
- Keep this repository limited to the current listed XML/CSV, runtime code, assets, validation schemas, tests, documentation, and GitHub Pages workflow.
- Do not import collection snapshots, raw HTML, original intake CSV/XML, review manifests, previous metadata values, or scraping/migration tools. Those remain in the separate local work project.
- Do not commit files larger than 50 MB. Keep local ginit task/issue/backup directories ignored.
- `sh build.sh` refreshes `data/databases.csv` from the XML and builds `dist/`. Commit the refreshed CSV alongside XML edits.
- The website publishes only the standard `dist/data/jpcoar.xml`; `data/databases.xml` and `data/databases.csv` are linked from README on GitHub.
- Keep hierarchy derived from JPCOAR `hasPart`/`isPartOf`. Short inline HTML belongs in `nihu:listSummary`; detailed modal text stays in `Abstract`.
- Run `sh check.sh` after meaningful changes; inspect staged paths and sizes before committing.
