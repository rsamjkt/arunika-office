#!/bin/bash
# Bangun Arunika Office dari awal sampai paket .deb.
#
#   arunika/build.sh [--deps] [--configure] [--no-deb]
#
#   --deps       unduh build-deps Ubuntu ke ../sysroot (tanpa root; dipakai lewat ../benv.sh)
#   --configure  jalankan autogen.sh --with-distro=Arunika (otomatis bila belum pernah)
#   --no-deb     berhenti setelah make
#
# Build berjalan di user namespace (../benv.sh) yang meng-overlay /usr dengan ../sysroot/usr,
# jadi sistem host tidak perlu dipasangi paket -dev apa pun.
set -euo pipefail
CORE="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
TOP="$(dirname "$CORE")"
BENV="$TOP/benv.sh"
say() { printf '\033[1;35m»\033[0m %s\n' "$*"; }
DEPS=0 CONF=0 DEB=1
for a in "$@"; do case $a in --deps) DEPS=1 ;; --configure) CONF=1 ;; --no-deb) DEB=0 ;; esac; done

if [ $DEPS = 1 ] || [ ! -d "$TOP/sysroot/usr" ]; then
    say "build-deps → $TOP/sysroot"
    mkdir -p "$TOP/debs" "$TOP/sysroot"
    (cd "$TOP/debs" && apt-get -s install --no-install-recommends $(cat "$CORE/arunika/build-deps.txt") 2>/dev/null \
        | awk '/^Inst /{print $2}' > need.txt && apt-get download $(cat need.txt))
    for d in "$TOP"/debs/*.deb; do dpkg-deb -x "$d" "$TOP/sysroot"; done
    for d in lib bin sbin; do [ -d "$TOP/sysroot/$d" ] && cp -a "$TOP/sysroot/$d/." "$TOP/sysroot/usr/$d/" && rm -rf "${TOP:?}/sysroot/$d"; done
    ln -sf aclocal-1.16 "$TOP/sysroot/usr/bin/aclocal"; ln -sf automake-1.16 "$TOP/sysroot/usr/bin/automake"
    ln -sf bison.yacc "$TOP/sysroot/usr/bin/yacc"
fi
[ -x "$BENV" ] || cp "$CORE/arunika/benv.sh" "$BENV"

say "ribbon, terjemahan Indonesia, branding"
python3 "$CORE/arunika/ribbon/generate.py"
python3 "$CORE/arunika/l10n/apply.py"
python3 "$CORE/arunika/branding/make-branding.py" "$TOP/branding" >/dev/null

if [ $CONF = 1 ] || [ ! -f "$CORE/config_host.mk" ]; then
    say "configure"
    (cd "$CORE" && "$BENV" ./autogen.sh --with-distro=Arunika)
fi

say "make (lama: beberapa jam saat pertama kali)"
(cd "$CORE" && "$BENV" make build gb_SUPPRESS_TESTS=1)

[ $DEB = 1 ] && "$CORE/arunika/packaging/make-deb.sh"
