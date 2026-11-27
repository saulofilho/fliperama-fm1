#!/bin/sh
# FLIPERAMA: the site's share image and icons, printed by headless Chrome.
#   site/og.png              1200x630 link preview (tools/share/og.html: the site's cabinets in attract mode)
#   the icons: tools/share/icon.py (Pillow)
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
chrome=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
shot() { # page, out, width, height, ms
  "$chrome" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --allow-file-access-from-files \
    --virtual-time-budget="$5" --window-size="$3,$4" --screenshot="$2" "file://$root/tools/share/$1" 2>/dev/null
}
shot og.html "$root/site/og.png" 1200 630 9000
"$root/.venv/bin/python" "$root/tools/share/icon.py"
ls -l "$root/site/og.png"
