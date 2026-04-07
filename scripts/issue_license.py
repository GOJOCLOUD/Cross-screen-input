#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为指定设备 UUID 签发离线许可证（需私钥 PEM，勿分发到用户安装包）。

用法:
  python scripts/issue_license.py --uuid "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
  ACTIVATION_PRIVATE_KEY_PATH=/path/to/activation_ed25519_private.pem python scripts/issue_license.py -u "raw-uuid"

默认私钥路径: 仓库根目录 activation_ed25519_private.pem（应已加入 .gitignore）

首次生成密钥对（在仓库根目录执行一次，并妥善备份私钥）:
  python scripts/issue_license.py --generate-keys
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys

# 与 backend/routes/activation.py 保持一致
PRODUCT_ID = "cross-screen-input"
LICENSE_FORMAT_PREFIX = "cs1"


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def normalize_uuid_for_license(uuid_str: str) -> str:
    s = (uuid_str or "").strip()
    if not s:
        raise ValueError("UUID 不能为空")
    hexonly = re.sub(r"[^a-fA-F0-9]", "", s)
    if len(hexonly) >= 24:
        return hexonly[:24].lower()
    import hashlib

    seed = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return seed[:24]


def canonical_payload_bytes(device_norm: str) -> bytes:
    obj = {"v": 1, "device": device_norm, "product": PRODUCT_ID}
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _load_private_pem(path: str):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def issue_license(uuid_raw: str, pem_path: str) -> str:
    priv = _load_private_pem(pem_path)
    device = normalize_uuid_for_license(uuid_raw)
    msg = canonical_payload_bytes(device)
    sig = priv.sign(msg)  # type: ignore[union-attr]
    return f"{LICENSE_FORMAT_PREFIX}.{_b64url_encode(msg)}.{_b64url_encode(sig)}"


def generate_keypair_files() -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    root = _repo_root()
    priv_path = os.path.join(root, "activation_ed25519_private.pem")
    if os.path.exists(priv_path):
        print(f"已存在私钥文件，跳过生成: {priv_path}", file=sys.stderr)
        return
    k = Ed25519PrivateKey.generate()
    pem = k.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    open(priv_path, "wb").write(pem)
    pub_raw = k.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    pub_b64 = base64.b64encode(pub_raw).decode("ascii")
    print("已生成私钥（请备份，勿提交 Git）:", priv_path)
    print("请将下列公钥写入 hotspot/backend/routes/activation.py 中 ACTIVATION_PUBLIC_KEY_B64 = ")
    print(pub_b64)


def main() -> int:
    ap = argparse.ArgumentParser(description="签发跨屏输入离线许可证")
    ap.add_argument("-u", "--uuid", help="用户设备的原始 UUID 字符串（与软件内显示一致）")
    ap.add_argument(
        "--pem",
        default=os.environ.get(
            "ACTIVATION_PRIVATE_KEY_PATH",
            os.path.join(_repo_root(), "activation_ed25519_private.pem"),
        ),
        help="Ed25519 私钥 PEM 路径",
    )
    ap.add_argument("--generate-keys", action="store_true", help="生成密钥对到仓库根目录")
    args = ap.parse_args()

    if args.generate_keys:
        generate_keypair_files()
        return 0

    if not args.uuid:
        ap.print_help()
        return 2

    if not os.path.isfile(args.pem):
        print(f"找不到私钥: {args.pem}\n请先运行: python scripts/issue_license.py --generate-keys", file=sys.stderr)
        return 1

    lic = issue_license(args.uuid, args.pem)
    print(lic)
    return 0


if __name__ == "__main__":
    sys.exit(main())
