#!/bin/bash
# Pratinjau ribbon dengan LibreOffice sistem (tanpa build): file .ui di-bind-mount menggantikan
# notebookbar.ui ("Tabbed") di namespace terpisah, dijalankan di Xvfb, lalu di-screenshot.
#   preview-system.sh writer|calc|impress UI_FILE OUT.png [DETIK]
set -e
APP=$1 UI=$(readlink -f "$2") OUT=$3 WAIT=${4:-12}
DPY=:78
XVFB=$HOME/aruni-build/debs/x/usr/bin/Xvfb
HERE=$(dirname "$(readlink -f "$0")")
case $APP in
  writer) MOD=swriter; CFG=Writer ;;
  calc) MOD=scalc; CFG=Calc ;;
  impress) MOD=simpress; CFG=Impress ;;
esac
PROF=/tmp/aru-prof-$APP
rm -rf "$PROF"; mkdir -p "$PROF/user"
cat > "$PROF/user/registrymodifications.xcu" <<XCU
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.UI.ToolbarMode"><prop oor:name="Active$CFG" oor:op="fuse"><value>notebookbar.ui</value></prop></item>
<item oor:path="/org.openoffice.Office.UI.ToolbarMode/Applications/org.openoffice.Office.UI.ToolbarMode:Application['$CFG']"><prop oor:name="Active" oor:op="fuse"><value>notebookbar.ui</value></prop></item>
<item oor:path="/org.openoffice.Setup/Office"><prop oor:name="ooSetupInstCompleted" oor:op="fuse"><value>true</value></prop></item>
<item oor:path="/org.openoffice.Office.Common/Misc"><prop oor:name="FirstRun" oor:op="fuse"><value>false</value></prop><prop oor:name="ShowTipOfTheDay" oor:op="fuse"><value>false</value></prop></item>
</oor:items>
XCU
if ! xdpyinfo -display $DPY >/dev/null 2>&1; then
  "$XVFB" $DPY -screen 0 1600x1000x24 -nolisten tcp >/dev/null 2>&1 &
  sleep 2
fi
T=/usr/lib/libreoffice/share/config/soffice.cfg/modules/$MOD/ui/notebookbar.ui
DISPLAY=$DPY unshare -r -m sh -c "mount --bind '$UI' '$T' && exec /usr/lib/libreoffice/program/soffice --$APP --norestore -env:UserInstallation=file://$PROF" >/tmp/aru-preview.log 2>&1 &
PID=$!
sleep "$WAIT"
DISPLAY=$DPY python3 "$HERE/shot.py" "$OUT"
kill $PID 2>/dev/null || true
sleep 1
