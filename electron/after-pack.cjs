/**
 * electron-builder afterPack：关闭「嵌入式 ASAR 完整性校验」fuse，
 * 以便本地 ad-hoc `codesign --deep` 后应用仍可正常启动（否则易秒退）。
 * 正式分发仍建议用 CI 公证签名。
 */
'use strict';

const fs = require('fs');
const path = require('path');

module.exports = async function afterPack(context) {
  if (context.electronPlatformName !== 'darwin') return;
  const out = context.appOutDir;
  if (!out || !fs.existsSync(out)) return;
  const apps = fs.readdirSync(out).filter((f) => f.endsWith('.app'));
  if (!apps.length) return;
  const appPath = path.join(out, apps[0]);

  let flipFuses;
  let FuseVersion;
  let FuseV1Options;
  try {
    ({ flipFuses, FuseVersion, FuseV1Options } = require('@electron/fuses'));
  } catch (e) {
    console.warn('[after-pack] skip fuses (install @electron/fuses):', e && e.message);
    return;
  }

  await flipFuses(appPath, {
    version: FuseVersion.V1,
    [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: false,
  });
  console.log('[after-pack] EnableEmbeddedAsarIntegrityValidation=false', appPath);
};
