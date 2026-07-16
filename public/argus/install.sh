#!/bin/sh
set -eu

REGISTRY_URL="${ARGUS_NPM_REGISTRY:-https://registry.npmjs.org}"
INSTALL_BIN="${ARGUS_INSTALL_BIN:-$HOME/.local/bin}"
PACKAGE_PATH="@argusevolve%2fargus"

fail() {
  printf 'Argus installer: %s\n' "$1" >&2
  exit 1
}

[ "$(uname -s)" = "Linux" ] || fail "this installer currently supports Linux x64 only"
case "$(uname -m)" in
  x86_64|amd64) ;;
  *) fail "unsupported architecture $(uname -m); Linux x64 is required" ;;
esac

for command in curl tar sha256sum install sed; do
  command -v "$command" >/dev/null 2>&1 || fail "missing required command: $command"
done

tags_json=$(curl -fsSL "$REGISTRY_URL/-/package/$PACKAGE_PATH/dist-tags")
beta_version=$(printf '%s' "$tags_json" | sed -n 's/.*"beta"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -n "$beta_version" ] || fail "npm beta tag is unavailable"

platform_version="${beta_version}-linux-x64"
if version_json=$(curl -fsSL "$REGISTRY_URL/$PACKAGE_PATH/$platform_version" 2>/dev/null); then
  :
else
  # Transitional fallback for the first beta, before platform variants moved
  # under the single @argusevolve/argus package name.
  version_json=$(curl -fsSL "$REGISTRY_URL/@argusevolve%2fargus-linux-x64/$beta_version")
fi
tarball_url=$(printf '%s' "$version_json" | sed -n 's/.*"tarball"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -n "$tarball_url" ] || fail "could not resolve Linux binary tarball"

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/argus-install.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM

curl -fsSL "$tarball_url" -o "$tmp_dir/argus.tgz"
tar -xzf "$tmp_dir/argus.tgz" -C "$tmp_dir" \
  package/bin/argus-core package/bin/argus-core.sha256
(
  cd "$tmp_dir/package/bin"
  sha256sum -c argus-core.sha256 >/dev/null
)

mkdir -p "$INSTALL_BIN"
install -m 0755 "$tmp_dir/package/bin/argus-core" "$INSTALL_BIN/argus"
cat > "$INSTALL_BIN/argus-skill" <<'EOF'
#!/bin/sh
ARGUS_BINARY_MODE=cli exec "$(dirname "$0")/argus" "$@"
EOF
chmod 0755 "$INSTALL_BIN/argus-skill"

printf 'Argus %s installed to %s\n' "$beta_version" "$INSTALL_BIN/argus"
case ":${PATH:-}:" in
  *":$INSTALL_BIN:"*) ;;
  *) printf 'Add %s to PATH, then run: argus --setup\n' "$INSTALL_BIN" ;;
esac
