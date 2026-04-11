#!/usr/bin/env bash
set -euo pipefail

# 说明：
# - 默认：xattr -cr（清隔离属性），解决下载后「无法打开」。
# - 可选 ad-hoc：官方构建已在打包阶段关闭「嵌入式 ASAR 完整性」fuse（electron/after-pack.cjs），
#   因此对**当前流水线产出的 .app** 使用 `codesign --force --deep --sign -` 一般不会因 ASAR 秒退。
# - 仍建议优先使用 CI 已签名/公证的安装包；本脚本仅供本机自签。
# - 使用 ad-hoc：KPSR_ADHOC_CODESIGN=1 或参数 --adhoc-codesign

APP_PATH="${1:-/Applications/跨屏输入.app}"
DO_ADHOC="${KPSR_ADHOC_CODESIGN:-0}"
for arg in "$@"; do
  if [[ "$arg" == "--adhoc-codesign" ]]; then DO_ADHOC=1; fi
done

if [[ ! -d "${APP_PATH}" ]]; then
  echo "应用不存在: ${APP_PATH}"
  exit 1
fi

echo "清理扩展属性（隔离标记等）: ${APP_PATH}"
xattr -cr "${APP_PATH}" || true

if [[ "${DO_ADHOC}" == "1" ]]; then
  echo "执行 ad-hoc 完整签名（deep）: ${APP_PATH}"
  codesign --force --deep --sign - "${APP_PATH}"
  echo "验证 codesign:"
  codesign --verify --deep --strict --verbose=2 "${APP_PATH}"
  echo "评估 Gatekeeper（ad-hoc 通常为 rejected，可忽略）:"
  spctl --assess --type execute -vv "${APP_PATH}" || true
else
  echo "已跳过 codesign。若需本机 ad-hoc 完整签名，请使用: KPSR_ADHOC_CODESIGN=1 $0 \"${APP_PATH}\""
fi

echo "完成。"
