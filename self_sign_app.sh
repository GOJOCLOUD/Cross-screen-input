#!/usr/bin/env bash
set -euo pipefail

# 说明：
# - 默认只做「清理隔离属性」(xattr)，解决从网络下载后「无法打开」等问题。
# - 请勿对 Electron 应用默认执行 `codesign --deep --sign -`：会破坏 ASAR 完整性校验
#   （ElectronAsarIntegrity / enableEmbeddedAsarIntegrityValidation），表现为双击后秒退/闪退。
# - 若你曾用旧版脚本对 .app 做过 ad-hoc deep 签名：请从 .dmg 重新安装一份，或删应用后重装。
# - 仍需要 ad-hoc 签名时（不推荐）：设置环境变量 KPSR_ADHOC_CODESIGN=1 或传入第二个参数 --adhoc-codesign

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
  echo ""
  echo "警告: 即将对 Electron 应用执行 ad-hoc deep 签名，可能导致 ASAR 校验失败并闪退。"
  echo "      若启动异常，请从官方 .dmg 重新安装，且勿再使用 --adhoc-codesign。"
  echo "执行 ad-hoc 自签名: ${APP_PATH}"
  codesign --force --deep --sign - "${APP_PATH}"
  echo "验证 codesign:"
  codesign --verify --deep --strict --verbose=2 "${APP_PATH}"
  echo "评估 Gatekeeper:"
  spctl --assess --type execute -vv "${APP_PATH}" || true
else
  echo "已跳过 codesign（避免 Electron 闪退）。首次打开请尝试：右键 → 打开。"
fi

echo "完成。"
