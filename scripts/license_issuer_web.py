#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地激活码签发 Web（仅绑定 127.0.0.1，需同目录 issue_license.py + 私钥 PEM）。

启动:
  cd 仓库根目录
  python3 scripts/license_issuer_web.py

浏览器: http://127.0.0.1:8000/

可选环境变量:
  ACTIVATION_PRIVATE_KEY_PATH  私钥路径（默认仓库根 activation_ed25519_private.pem）
  LICENSE_ISSUER_TOKEN         若设置，表单需填写相同令牌才能签发（防本机其他进程误触）
"""
from __future__ import annotations

import html
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

# 与 issue_license.py 同目录，便于 import
_SCRIPTS = os.path.abspath(os.path.dirname(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

try:
    from issue_license import issue_license, _repo_root
except ImportError as e:
    print(
        "无法导入 issue_license.py，请确保 scripts/issue_license.py 存在（可从 git 历史恢复）。\n"
        "  git show 59e8e5c^:scripts/issue_license.py > scripts/issue_license.py",
        file=sys.stderr,
    )
    raise SystemExit(1) from e

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def _pem_path() -> str:
    return os.environ.get(
        "ACTIVATION_PRIVATE_KEY_PATH",
        os.path.join(_repo_root(), "activation_ed25519_private.pem"),
    )


def _page_html(msg: str | None = None, err: str | None = None, last_uuid: str = "") -> bytes:
    msg_e = html.escape(msg) if msg else ""
    err_e = html.escape(err) if err else ""
    uuid_e = html.escape(last_uuid)
    token_hint = (
        '<p class="hint">本机已设置 <code>LICENSE_ISSUER_TOKEN</code>，请在下方填写令牌。</p>'
        if os.environ.get("LICENSE_ISSUER_TOKEN")
        else ""
    )
    body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>跨屏输入 · 激活码签发（本地）</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; color: #1a1a1a; }}
    h1 {{ font-size: 1.25rem; }}
    .hint {{ color: #666; font-size: 13px; }}
    label {{ display: block; margin-top: 16px; font-weight: 600; }}
    input[type=text], textarea {{ width: 100%; box-sizing: border-box; padding: 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 6px; }}
    textarea {{ min-height: 100px; font-family: ui-monospace, monospace; }}
    button {{ margin-top: 12px; padding: 10px 18px; font-size: 14px; cursor: pointer; border-radius: 6px; border: 1px solid #333; background: #1a1a1a; color: #fff; }}
    button.secondary {{ background: #fff; color: #1a1a1a; }}
    .ok {{ color: #15803d; margin-top: 12px; white-space: pre-wrap; word-break: break-all; }}
    .bad {{ color: #b91c1c; margin-top: 12px; }}
    code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>激活码签发（私钥本地）</h1>
  <p class="hint">仅监听本机 · 请勿将端口暴露到公网。私钥路径：<code>{html.escape(_pem_path())}</code></p>
  {token_hint}
  <form method="post" action="/issue">
    <label for="uuid">设备 UUID（与软件内显示一致）</label>
    <input type="text" id="uuid" name="uuid" value="{uuid_e}" placeholder="粘贴用户 UUID" autocomplete="off"/>
    <label for="token">访问令牌（可选）</label>
    <input type="password" id="token" name="token" placeholder="若设置了 LICENSE_ISSUER_TOKEN 则必填" autocomplete="off"/>
    <div><button type="submit">签发激活码</button></div>
  </form>
  <p class="ok">{msg_e}</p>
  <p class="bad">{err_e}</p>
</body>
</html>"""
    return body.encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    server_version = "LicenseIssuer/1.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_page_html())
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/issue":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        data = parse_qs(raw, keep_blank_values=True)
        uuid_val = (data.get("uuid") or [""])[0].strip()
        token_in = (data.get("token") or [""])[0]
        expect = os.environ.get("LICENSE_ISSUER_TOKEN", "").strip()
        if expect and token_in != expect:
            body = _page_html(
                err="令牌不正确或未填写。",
                last_uuid=uuid_val,
            )
            self.send_response(403)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        pem = _pem_path()
        if not os.path.isfile(pem):
            body = _page_html(
                err=f"找不到私钥文件：{pem}\n请先运行：python3 scripts/issue_license.py --generate-keys",
                last_uuid=uuid_val,
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        if not uuid_val:
            body = _page_html(err="请填写设备 UUID。", last_uuid=uuid_val)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        try:
            lic = issue_license(uuid_val, pem)
        except Exception as e:
            body = _page_html(err=f"签发失败：{e}", last_uuid=uuid_val)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        body = _page_html(msg=f"激活码（整行复制给用户）：\n\n{lic}", last_uuid=uuid_val)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    host = os.environ.get("LICENSE_ISSUER_HOST", DEFAULT_HOST)
    port = int(os.environ.get("LICENSE_ISSUER_PORT", str(DEFAULT_PORT)))
    if host not in ("127.0.0.1", "localhost", "::1"):
        print("警告：仅建议在 127.0.0.1 监听，避免私钥签发暴露到局域网。", file=sys.stderr)

    httpd = HTTPServer((host, port), _Handler)
    print(f"激活码签发页： http://{host}:{port}/", file=sys.stderr)
    print("按 Ctrl+C 停止", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。", file=sys.stderr)


if __name__ == "__main__":
    main()
