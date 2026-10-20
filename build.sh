#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python tools/export_csv.py
python tools/build.py "$@"
