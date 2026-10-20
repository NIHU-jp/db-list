#!/usr/bin/env python3
"""Export the current listed XML as a 26-column working CSV."""
import argparse
import csv
import json
from pathlib import Path

from catalogue import NS, ROOT, LANG, read, records, record_view, text

CSV_HEADERS = ['ID', 'English Title', 'Japanese Title', 'Original Title', 'Created Date',
               'Access Rights', 'English Name of Creator', 'Alternative Name of Creator',
               'Institution Information', 'Description (in English)', 'Description (in Japanese)',
               'Resource URL', 'Parent Resource', 'Format of contents (in MIME Type)',
               'Types of contents', 'Language', 'Language in the user interface',
               'Language of contents', 'Category', 'DDC subject', 'LCSH subject',
               'NDLSH subject', 'Related discipline or field', 'Order weight',
               'アイキャッチ画像', 'Moderation state']


def listed_rows(root):
    headers = CSV_HEADERS
    rows = []
    for rec in records(root, listed=True):
        ja, en = record_view(rec, 'ja'), record_view(rec, 'en')
        row = {name: ja['admin'].get('csv_fields', {}).get(name, '') for name in headers}
        row.update({'Japanese Title': ja['title'], 'English Title': en['title'],
                    'Description (in Japanese)': ja['description'],
                    'Description (in English)': en['description'], 'Resource URL': ja['url']})
        meta = ja['meta']
        row['Alternative Name of Creator'] = text(meta, 'jpcoar:creator/jpcoar:creatorName', 'ja')
        row['English Name of Creator'] = text(meta, 'jpcoar:creator/jpcoar:creatorName', 'en')
        # No source ID is invented for a newly represented database.
        row['Moderation state'] = row.get('Moderation state') or 'published'
        rows.append(row)
    return rows


def export(root, destination):
    rows = listed_rows(root)
    if not rows:
        raise ValueError('No listed CSV rows')
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\r\n')
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--input', type=Path, default=ROOT / 'data/databases.xml')
    args.add_argument('--output', type=Path, default=ROOT / 'data/databases.csv')
    opts = args.parse_args()
    count = export(read(opts.input).getroot(), opts.output)
    print(f'Exported {count} rows to {opts.output}')


if __name__ == '__main__':
    main()
