#!/bin/sh
# Build one episode:  sh build.sh <n>      (n = 1..5)   → out/<id>.mp4
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$HOME/lemo-opuscar}
export LIB
N=${1:?episode number}
ID=$(python3 -c "import json;print(json.load(open('$HERE/scripts.json'))['episodes'][$N-1]['id'])")
mkdir -p "$HERE/out"
cd "$LIB"
node core/render/events.mjs "$HERE" --size 1080x1920 --q "ep=$N" --out "$HERE/out/$ID.events.json"
[ -n "$SKIPVIDEO" ] || node core/render/video.mjs "$HERE" --fps 24 --workers ${WORKERS:-2} --size 1080x1920 --q "ep=$N" --out "$HERE/out/$ID.video.mp4"
"$LIB/.venv/bin/python" "$HERE/mix.py" "$ID" "$HERE/out/$ID.events.json" "$HERE/out/$ID.mix.wav"
# master: two-pass loudnorm to -14 LUFS / -1.5 dBTP, picture copied
M=$(ffmpeg -hide_banner -i "$HERE/out/$ID.mix.wav" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
MI=$(echo "$M" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'])")
MTP=$(echo "$M" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_tp'])")
MLRA=$(echo "$M" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_lra'])")
MTH=$(echo "$M" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_thresh'])")
ffmpeg -hide_banner -loglevel error -y -i "$HERE/out/$ID.video.mp4" -i "$HERE/out/$ID.mix.wav" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:linear=true,aresample=192000,alimiter=limit=0.78:attack=1:release=60:level=disabled,aresample=48000" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$HERE/out/$ID.mp4"
ffmpeg -hide_banner -i "$HERE/out/$ID.mp4" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1
echo "DONE $HERE/out/$ID.mp4"
