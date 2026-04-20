#!/usr/bin/env bash
# 从待打入安装包的后端目录中剔除私钥、签发工具、明显垃圾文件。
set -euo pipefail
TARGET="${1:?usage: $0 <backend_resources_dir>}"
if [[ ! -d "$TARGET" ]]; then
  echo "prune_backend_bundle: not a directory: $TARGET" >&2
  exit 1
fi

find "$TARGET" -type f \( \
  -name 'error.txt' -o -name 'errors.txt' \
  -o -name '*.p12' -o -name '*.pfx' \
  -o -name '*_private*.pem' -o -name 'activation_ed25519_private.pem' \
  -o -name 'license_issuer_web.py' -o -name 'issue_license.py' \
\) -print | while read -r f; do echo "prune: remove $f"; rm -f "$f"; done || true

echo "prune_backend_bundle: done ($TARGET)"
