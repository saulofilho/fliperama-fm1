#!/bin/sh
# Read the approved GitHub token from the terminal, never from a command argument.
set -eu
rhythmer_gh=/Volumes/SSD/Development/Toolchains/github-cli/gh_2.103.3_macOS_arm64/bin/gh
if [ ! -t 0 ]; then
  echo 'Run this helper in your Mac Terminal.' >&2
  exit 1
fi
rhythmer_tty=$(stty -g)
trap 'stty "$rhythmer_tty"; unset rhythmer_token' EXIT
trap 'exit 130' INT TERM HUP
printf 'Copy the NEW GitHub token. Paste it here, then press Return. Input is hidden: '
stty -echo
IFS= read -r rhythmer_token
stty "$rhythmer_tty"
printf '\n'
case "$rhythmer_token" in
  github_pat_*) ;;
  *) echo 'Expected a fine-grained token. No login attempted.' >&2; exit 1 ;;
esac
printf '%s' "$rhythmer_token" | "$rhythmer_gh" auth login --hostname github.com --git-protocol https --with-token
unset rhythmer_token
"$rhythmer_gh" auth status
printf '\nConnection finished. Report only the login status; never send the token.\n'
