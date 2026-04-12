# 激活码签发（维护者）

## 文件

| 文件 | 说明 |
|------|------|
| `issue_license.py` | 命令行签发（需本机 `activation_ed25519_private.pem`） |
| `license_issuer_web.py` | 本机网页 `http://127.0.0.1:8000/`（依赖同目录 `issue_license.py`） |
| `start_license_issuer_web.sh` | 启动网页签发 |

私钥路径默认：**仓库根目录** `activation_ed25519_private.pem`（已在 `.gitignore`，**勿提交**）。

## 常用命令

```bash
# 首次：在仓库根生成密钥对（会打印公钥，需写入 hotspot/backend/routes/activation.py 的 ACTIVATION_PUBLIC_KEY_B64）
python3 scripts/issue_license.py --generate-keys

# 签发一条激活码（UUID 与软件内设备 UUID 一致）
python3 scripts/issue_license.py -u "用户的UUID"

# 网页签发
./scripts/start_license_issuer_web.sh
```

## 密钥能否一直用？

可以。**Ed25519 密钥对没有内置过期时间**，只要你不轮换公钥/私钥，同一套可以一直签发、客户端内置公钥不变即可长期验证。需要作废旧码时，应**轮换密钥对**并更新客户端内的 `ACTIVATION_PUBLIC_KEY_B64`，旧码将全部失效。

## 备份

请自行备份 `activation_ed25519_private.pem`（加密盘/U 盘）；丢失则无法再签发与历史公钥匹配的许可证。
