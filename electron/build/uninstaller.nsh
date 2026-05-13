; NSIS 卸载时由 electron-builder 引入
; 清理新旧路径的用户数据（含 activation.json），确保卸载重装后为未激活状态

!macro customUnInstall
  RMDir /r "$APPDATA\KPSR"
  RMDir /r "$APPDATA\kpsr-desktop"
!macroend
