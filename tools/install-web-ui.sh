#!/bin/sh
set -eu
test "$(id -u)" = 0 || { echo '请使用管理员权限运行：sudo sh install-web-ui.sh'; exit 1; }
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE"
sha256sum -c web-ui.sha256
PACKAGE=$(readlink -f /var/packages/transmission/target)
case "$PACKAGE" in /volume[0-9]*/@appstore/transmission) ;; *) echo '没有找到标准路径下的 Transmission 套件，未修改任何文件。'; exit 1;; esac
if test -d "$PACKAGE/share/transmission/public_html"; then TARGET="$PACKAGE/share/transmission/public_html";
elif test -d "$PACKAGE/share/transmission/web"; then TARGET="$PACKAGE/share/transmission/web";
else echo '没有找到网页目录，未修改任何文件。'; exit 1; fi
STAMP=$(date +%Y%m%d-%H%M%S)
STAGE="${TARGET}.zhCN-new-${STAMP}"
BACKUP="${TARGET}.before-zhCN-${STAMP}"
test ! -e "$STAGE" && test ! -e "$BACKUP"
mkdir -m 755 "$STAGE"
tar -xzf transmission-web-control-zhCN.tar.gz -C "$STAGE"
test -f "$STAGE/index.html" && test -f "$STAGE/tr-web-control/script/rpc-compat.js"
chown -R root:root "$STAGE"
find "$STAGE" -type d -exec chmod 755 '{}' ';'
find "$STAGE" -type f -exec chmod 644 '{}' ';'
mv "$TARGET" "$BACKUP"
if ! mv "$STAGE" "$TARGET"; then mv "$BACKUP" "$TARGET"; echo '切换失败，已恢复原网页。'; exit 1; fi
echo '中文网页已安装。下载服务和现有任务未停止。'
printf '原网页备份：%s\n' "$BACKUP"
echo '请在网页中按 Ctrl+F5 强制刷新。'
echo '需要恢复时，在此目录运行：sudo sh restore-web-ui.sh'
