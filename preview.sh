#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
sh build.sh
python -m http.server "${NIHU_PREVIEW_PORT:-8893}" --bind 127.0.0.1 --directory dist
