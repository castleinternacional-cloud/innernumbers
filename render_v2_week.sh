#!/bin/bash
cd /home/claude/innernumbers
for e in blink breath blood skin bones brain; do
  python3 engine/short_v2.py episodes_v2/$e.json out/v2_$e > out/v2_$e.log 2>&1 && echo "$e ok" || echo "$e FAIL"
done
