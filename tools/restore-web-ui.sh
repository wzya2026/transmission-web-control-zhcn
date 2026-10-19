#!/bin/sh
set -eu
test "$(id -u)" = 0 || { echo '请使用管理员权限运行：sudo sh restore-web-ui.sh'; exit 1; }
PACKAGE=$(readlink -f /var/packages/transmission/target)
case "$PACKAGE" in /volume[0-9]*/@appstore/transmission) ;; *) echo '未找到标准 Transmission 套件目录。'; exit 1;; esac
if test -d "$PACKAGE/share/transmission/public_html"; then TARGET="$PACKAGE/share/transmission/public_html";
elif test -d "$PACKAGE/share/transmission/web"; then TARGET="$PACKAGE/share/transmission/web";
else echo '没有找到网页目录。'; exit 1; fi
BACKUP=''
for item in "${TARGET}".before-zhCN-*; do if test -d "$item"; then BACKUP="$item"; fi; done
test -n "$BACKUP" || { echo '没有找到本工具制作的原网页备份。'; exit 1; }
SAVED="${TARGET}.saved-zhCN-$(date +%Y%m%d-%H%M%S)"
test ! -e "$SAVED"
mv "$TARGET" "$SAVED"
if ! mv "$BACKUP" "$TARGET"; then mv "$SAVED" "$TARGET"; echo '恢复失败，已保留当前网页。'; exit 1; fi
echo '已恢复原网页，中文网页另行保留。请按 Ctrl+F5 刷新。'
