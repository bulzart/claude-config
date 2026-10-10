#!/usr/bin/env bash
# Claude Code status line (global) - wired up in ~/.claude/settings.json under "statusLine".
#
# Prints one line:
#   Sonnet 5.5 | ctx 23% (45.2k/200k) | ~/Documents | git:main
#   (model | context % used (tokens in context / context window) | current directory | git branch)
#
# Claude Code pipes a JSON document to stdin on every refresh and shows whatever this script
# prints. The few fields needed are read with bash regexes, so jq and Python are NOT required
# (fast under Git Bash on Windows, also fine on Linux/macOS). git runs with --no-optional-locks.
#
# Try it by hand:
#   printf '%s\n' '{"model":{"display_name":"Sonnet 5.5"},"workspace":{"current_dir":"C:\\Users\\me\\proj"},"context_window":{"total_input_tokens":45234,"context_window_size":200000,"used_percentage":23,"remaining_percentage":77}}' | bash ~/.claude/scripts/statusline.sh
#
# Tweaks: DIR_PARTS = how many trailing folders of the path to show; NO_COLOR=1 turns colours off.

DIR_PARTS=3

# Whole JSON payload from stdin (read is a builtin: no subshell, which is slow under Git Bash).
IFS= read -r -d '' input

# --- minimal JSON readers: first match wins, result is left in REPLY ----------------------------
get_str() {   # get_str KEY -> REPLY = string value of "KEY" (JSON escapes left untouched)
  local re='"'"$1"'"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)"'
  REPLY=
  [[ $input =~ $re ]] && REPLY=${BASH_REMATCH[1]}
}
get_num() {   # get_num KEY -> REPLY = integer part of the number stored under "KEY"
  local re='"'"$1"'"[[:space:]]*:[[:space:]]*([0-9]+)'
  REPLY=
  [[ $input =~ $re ]] && REPLY=${BASH_REMATCH[1]}
}

fmt_tokens() {   # fmt_tokens N -> FMT = 950 | 1.2k | 45.2k | 200k | 1.5M
  local n=$1 d
  if (( n >= 1000000 )); then
    d=$(( n % 1000000 / 100000 ))
    FMT=$(( n / 1000000 ))
    (( d > 0 )) && FMT+=".$d"
    FMT+=M
  elif (( n >= 1000 )); then
    d=$(( n % 1000 / 100 ))
    FMT=$(( n / 1000 ))
    (( d > 0 && n < 100000 )) && FMT+=".$d"
    FMT+=k
  else
    FMT=$n
  fi
}

# --- colours ----------------------------------------------------------------------------------
if [[ -n ${NO_COLOR:-} ]]; then
  c_rst= c_dim= c_model= c_dir= c_git= c_green= c_yellow= c_red=
else
  c_rst=$'\033[0m'  c_dim=$'\033[2m'
  c_model=$'\033[1;36m'                                  # bold cyan
  c_dir=$'\033[34m'                                      # blue
  c_git=$'\033[35m'                                      # magenta
  c_green=$'\033[32m'  c_yellow=$'\033[33m'  c_red=$'\033[31m'
fi

# --- model ------------------------------------------------------------------------------------
get_str display_name; model=$REPLY
[[ -z $model ]] && { get_str id; model=$REPLY; }
[[ -z $model ]] && model='unknown model'

# --- context window: percentage used + tokens in context / window size ------------------------
get_num context_window_size; win=$REPLY
get_num total_input_tokens;  used=$REPLY
pct=
re='"used_percentage"[[:space:]]*:[[:space:]]*([0-9]+)(\.[0-9]+)?[[:space:]]*,[[:space:]]*"remaining_percentage"'
[[ $input =~ $re ]] && pct=${BASH_REMATCH[1]}
# No percentage yet (e.g. before the first reply): work it out from the token counts.
if [[ -z $pct && -n $used && -n $win ]] && (( win > 0 )); then
  pct=$(( used * 100 / win ))
fi
c_ctx=$c_green
if [[ -n $pct ]]; then
  if (( pct >= 80 )); then c_ctx=$c_red
  elif (( pct >= 50 )); then c_ctx=$c_yellow
  fi
fi

# --- current directory (~ for home, forward slashes, last DIR_PARTS folders) -------------------
get_str current_dir; cwd=$REPLY
[[ -z $cwd ]] && { get_str cwd; cwd=$REPLY; }
bs='\' dbs='\\'
cwd=${cwd//"$dbs"//}    # JSON-escaped backslashes (C:\\Users\\x) -> /
cwd=${cwd//"$bs"//}     # any remaining backslash -> /
disp=$cwd
home_w=${USERPROFILE:-}
home_w=${home_w//"$bs"//}
for h in "$home_w" "${HOME:-}"; do
  if [[ -n $h && ( $disp == "$h" || $disp == "$h"/* ) ]]; then
    disp="~${disp#"$h"}"
    break
  fi
done
IFS=/ read -ra parts <<<"$disp"
n=${#parts[@]}
if (( n > DIR_PARTS )); then
  disp=...
  for (( i = n - DIR_PARTS; i < n; i++ )); do disp+="/${parts[i]}"; done
fi

# --- git branch (detached HEAD shows @shortsha; nothing outside a repository) -----------------
branch=
if [[ -n $cwd && -d $cwd ]]; then
  branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --quiet --short HEAD 2>/dev/null)
  if (( $? == 1 )); then
    branch=$(git -C "$cwd" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
    [[ -n $branch ]] && branch="@$branch"
  fi
fi

# --- assemble ---------------------------------------------------------------------------------
sep="${c_dim} | ${c_rst}"
out="${c_model}${model}${c_rst}"
if [[ -n $pct ]]; then
  out+="${sep}${c_ctx}ctx ${pct}%${c_rst}"
else
  out+="${sep}${c_dim}ctx --${c_rst}"
fi
if [[ -n $used && -n $win ]]; then
  fmt_tokens "$used"; u=$FMT
  fmt_tokens "$win";  w=$FMT
  out+=" ${c_dim}(${u}/${w})${c_rst}"
fi
[[ -n $disp ]]   && out+="${sep}${c_dir}${disp}${c_rst}"
[[ -n $branch ]] && out+="${sep}${c_git}git:${branch}${c_rst}"

printf '%s\n' "$out"
