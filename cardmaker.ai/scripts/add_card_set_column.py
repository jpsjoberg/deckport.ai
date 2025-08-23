#!/usr/bin/env python3
import csv
import os
import shutil

DEFAULT_SET = "Open Portal"


def main() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    art_csv = os.path.join(project_root, 'data', 'cards_art.csv')
    backup = art_csv + '.bak'

    # Backup original
    shutil.copyfile(art_csv, backup)

    # Read all rows
    with open(art_csv, 'r', encoding='utf-8', newline='') as r:
        reader = csv.DictReader(r)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    # Add column if missing
    if 'card_set' not in fieldnames:
        fieldnames.append('card_set')

    # Populate values
    for row in rows:
        val = (row.get('card_set') or '').strip()
        if not val:
            row['card_set'] = DEFAULT_SET

    # Write back
    tmp = art_csv + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as w:
        writer = csv.DictWriter(w, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # ensure all keys exist
            for k in fieldnames:
                if k not in row:
                    row[k] = ''
            writer.writerow(row)

    os.replace(tmp, art_csv)
    print(f"Updated {art_csv} (backup at {backup}); ensured 'card_set' populated with '{DEFAULT_SET}'")


if __name__ == '__main__':
    main()

