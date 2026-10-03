#!/bin/bash
# Lingkungan build Arunika Office: /usr host + build-deps (sysroot) lewat overlayfs di user namespace, tanpa root.
#   ./benv.sh PERINTAH…
H="$(dirname "$(readlink -f "$0")")"
U=${ARUNIKA_UID:-$(id -u)} G=${ARUNIKA_GID:-$(id -g)}
export ARUNIKA_UID=$U ARUNIKA_GID=$G
case "$ARUNIKA_BENV" in
  "") exec unshare -r -m -- env ARUNIKA_BENV=1 "$0" "$@" ;;
  1)  mount -t overlay overlay -o "lowerdir=$H/sysroot/usr:/usr" /usr || exit 1
      exec unshare --user --map-user="$U" --map-group="$G" -- env ARUNIKA_BENV=2 "$0" "$@" ;;
esac
exec "$@"
