#!/bin/bash
# Paket .deb "arunika-office" dari hasil build (tanpa sudo; fakeroot untuk kepemilikan root).
#
#   arunika/packaging/make-deb.sh [OUTDIR]          (bawaan: ~/aruni-build/debs-out)
#
# Isi: /usr/lib/arunika-office (instalasi lengkap, en-US + id), perintah arunika-dokumen/-lembar-kerja/
# -presentasi/-gambar/-rumus/-basis-data/arunika-office, berkas .desktop, ikon, asosiasi berkas Office
# untuk Cinnamon. Dependensi pustaka dihitung dpkg-shlibdeps.
set -euo pipefail

CORE="$(cd "$(dirname "$(readlink -f "$0")")/../.." && pwd)"
OUT="${1:-$HOME/aruni-build/debs-out}"
BENV="$CORE/../benv.sh"
PKG=arunika-office
LOVER=$(sed -n 's/^export LIBO_VERSION_MAJOR=//p' "$CORE/config_host.mk").$(sed -n 's/^export LIBO_VERSION_MINOR=//p' "$CORE/config_host.mk").$(sed -n 's/^export LIBO_VERSION_MICRO=//p' "$CORE/config_host.mk").$(sed -n 's/^export LIBO_VERSION_PATCH=//p' "$CORE/config_host.mk")
REV="${ARUNIKA_OFFICE_REV:-1}"
VERSION="$LOVER-arunika$REV"
ARCH=$(dpkg --print-architecture)
STAGE="$(mktemp -d /tmp/arunika-office-deb.XXXXXX)"
ROOTFS="$STAGE/$PKG"
INST="$ROOTFS/usr/lib/arunika-office"
trap 'rm -rf "$STAGE"' EXIT
say() { printf '\033[1;35m»\033[0m %s\n' "$*"; }
mkdir -p "$OUT"

say "instalasi ke $INST (dari instdir, di-strip)"
# instdir adalah instalasi lengkap yang siap jalan; ooinstall tidak menangani nama produk berspasi
mkdir -p "$INST"
cp -a "$CORE/instdir/." "$INST/"
rm -rf "$INST/sdk" "$INST/readmes" "$INST/program/.lock" 2>/dev/null || true
find "$INST" -type f \( -name '*.so*' -o -perm -u+x \) -exec sh -c 'head -c4 "$1" | grep -q ELF && strip --strip-unneeded "$1"' _ {} \; 2>/dev/null || true

say "perintah, berkas .desktop, ikon"
mkdir -p "$ROOTFS/usr/bin"
declare -A OPT=([dokumen]=--writer [lembar-kerja]=--calc [presentasi]=--impress [gambar]=--draw
                [rumus]=--math [basis-data]=--base [office]=)
for app in "${!OPT[@]}"; do
    cat > "$ROOTFS/usr/bin/arunika-$app" <<EOF
#!/bin/sh
exec /usr/lib/arunika-office/program/soffice ${OPT[$app]} "\$@"
EOF
    chmod 755 "$ROOTFS/usr/bin/arunika-$app"
done
python3 "$CORE/arunika/packaging/desktop.py" "$ROOTFS/usr/share/applications" >/dev/null
python3 "$CORE/arunika/icons/make-icons.py" "$ROOTFS/usr/share/icons/hicolor" >/dev/null
mkdir -p "$ROOTFS/etc/xdg"
python3 - "$ROOTFS" <<'EOF'
import os, re, sys
root = sys.argv[1]
apps = os.path.join(root, "usr/share/applications")
lines = ["[Default Applications]"]
seen = set()
# urutan: aplikasi utama dulu supaya .docx/.xlsx/.pptx dibuka oleh Dokumen/Lembar Kerja/Presentasi
for app in ("dokumen", "lembar-kerja", "presentasi", "gambar", "rumus", "basis-data"):
    text = open(os.path.join(apps, f"arunika-{app}.desktop")).read()
    for mime in re.search(r"^MimeType=(.*)$", text, re.M).group(1).split(";"):
        if mime and mime not in seen and mime != "application/pdf":
            seen.add(mime)
            lines.append(f"{mime}=arunika-{app}.desktop")
open(os.path.join(root, "etc/xdg/x-cinnamon-mimeapps.list"), "w").write("\n".join(lines) + "\n")
EOF
mkdir -p "$ROOTFS/usr/share/doc/$PKG"
cp "$CORE/COPYING.MPL" "$ROOTFS/usr/share/doc/$PKG/copyright"
cat > "$ROOTFS/usr/share/doc/$PKG/README.Arunika" <<EOF
Arunika Office $VERSION — paket perkantoran Arunika Linux berbasis LibreOffice $LOVER
dengan ribbon dan bawaan ala Microsoft Office. Sumber: https://github.com/rsamjkt/arunika-office
EOF

say "dependensi pustaka (dpkg-shlibdeps)"
mkdir -p "$STAGE/debian"
printf 'Source: %s\n\nPackage: %s\nArchitecture: any\n' "$PKG" "$PKG" > "$STAGE/debian/control"
mapfile -t ELFS < <(find "$INST/program" -type f \( -name '*.so*' -o -perm -u+x \) -exec sh -c 'head -c4 "$1" | grep -q ELF && echo "$1"' _ {} \;)
DEPS=$(cd "$STAGE" && dpkg-shlibdeps -O --ignore-missing-info -l"$INST/program" \
        -x"$PKG" "${ELFS[@]}" 2>"$STAGE/shlibdeps.log" | sed -n 's/^shlibs:Depends=//p')
[ -n "$DEPS" ] || { cat "$STAGE/shlibdeps.log" | tail -20; exit 1; }
# pustaka UNO dibawa sendiri di program/; jangan bergantung pada paket LibreOffice distro
DEPS=$(echo "$DEPS" | tr ',' '\n' | sed 's/^ *//' | grep -vE '^(libuno-|uno-libs-private|ure\b|libreoffice)' | paste -sd, | sed 's/,/, /g')

mkdir -p "$ROOTFS/DEBIAN"
SIZE=$(du -sk "$ROOTFS" | cut -f1)
cat > "$ROOTFS/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Architecture: $ARCH
Maintainer: Arunika <repo@arunika.cloud>
Installed-Size: $SIZE
Depends: $DEPS, python3, fontconfig, hicolor-icon-theme
Recommends: fonts-crosextra-carlito, fonts-crosextra-caladea, hunspell-id | hunspell-en-us
Suggests: default-jre
Section: editors
Priority: optional
Homepage: https://os.arunika.cloud
Description: Arunika Office - dokumen, lembar kerja & presentasi ala Microsoft Office
 Paket perkantoran bawaan Arunika Linux, dibangun dari LibreOffice $LOVER dengan
 tampilan ribbon seperti Microsoft Office 365 (Arunika Dokumen, Arunika Lembar
 Kerja, Arunika Presentasi), format bawaan .docx/.xlsx/.pptx, font Carlito/Caladea
 yang identik ukurannya dengan Calibri/Cambria, dan antarmuka berbahasa Indonesia.
EOF
echo "/etc/xdg/x-cinnamon-mimeapps.list" > "$ROOTFS/DEBIAN/conffiles"
(cd "$ROOTFS" && find . -type f ! -path './DEBIAN/*' -printf '%P\0' | xargs -0 -r md5sum > DEBIAN/md5sums)
DEB="$OUT/${PKG}_${VERSION}_${ARCH}.deb"
say "membangun $DEB"
fakeroot dpkg-deb -Zxz -z6 --build "$ROOTFS" "$DEB" >/dev/null
say "$DEB ($(du -h "$DEB" | cut -f1))"
