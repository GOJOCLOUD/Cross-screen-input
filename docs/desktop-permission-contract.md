# 桌面端权限状态字段契约

本文定义电脑端状态接口中鼠标权限字段的唯一契约，避免前后端文案与字段漂移。

## 接口

- 路径：`GET /api/desktop/status`
- 与权限相关字段：
  - `mouse_listener_status: boolean`
  - `mouse_permission: object`（主字段，前端应优先使用）
  - `mouse_permission_hint: string`（兼容字段，保留给旧前端）

## `mouse_permission` 结构

```json
{
  "platform": "macos | windows | linux | unknown",
  "has_accessibility": true,
  "has_input_monitoring": true,
  "all_granted": true,
  "message": "已获得辅助功能与输入监控权限，鼠标监听可用"
}
```

字段说明：

- `platform`：权限快照所属平台。
- `has_accessibility`：辅助功能权限是否通过。
- `has_input_monitoring`：输入监控权限是否通过。
- `all_granted`：是否满足监听器运行所需完整权限。
- `message`：给 UI 直接展示的统一文案。

## 前端读取规范

- 统一优先读取：`mouse_permission.message`
- 回退读取：`mouse_permission_hint`
- 建议展示逻辑：
  - `mouse_listener_status = true`：显示“运行中”。
  - `mouse_listener_status = false` 且有权限文案：显示权限文案。
  - `mouse_listener_status = false` 且无权限文案：显示“已停止”。

## 错误与兜底要求

- 后端异常时，`mouse_permission` 仍必须返回对象，不应返回 `null`。
- 允许使用：
  - `platform = "unknown"`
  - `all_granted = false`
  - `message = "权限状态读取失败"` 或 `"状态获取失败"`

## 兼容策略

- 新代码只依赖 `mouse_permission`。
- `mouse_permission_hint` 作为过渡字段保留，后续版本可逐步下线。
