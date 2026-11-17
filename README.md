# Inner Numbers: video system

English channel "Inner Numbers — your body, counted". Owner: Mathias.

## How to rebuild in a new session
1. Download `innernumbers_system.tar.gz` from the Drive folder "Inner Numbers" and extract it.
2. `pip install --break-system-packages kokoro-onnx soundfile`
3. Voice model (free, local) from GitHub:
   - https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx  -> models/
   - https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin   -> models/
4. Render: `python3 engine/render.py episodes/epXXX.json out/epXXX` (add `--format long` for 16:9).
   Roughly 2 min per Short on 2 CPUs.

## Episode format (episodes/epXXX.json)
- `say`: one sentence of narration per scene. Write numbers as words for the voice.
- `visual.type`: `number` (value + label) | `heart` | `layers` (list of 4 layer names, cut from outside to inside) | `flow` (value + label, stream of particles) | `end`.
- `palette`: aurora | ember | lime | ice | blood. Change the palette, the scene order and the hook every episode, so videos don't look mass-produced.
- Every number needs a reliable source in `description` (Cleveland Clinic, NIH/PMC, AHA, peer-reviewed). No cures, no medical advice.

## Weekly routine
- Write 7 new episodes, render them, upload them to Drive, import them into vidIQ (Drive link shared with "anyone with the link"), draft 1 post a day at 12:00 America/Bogota to YouTube (public) + the Facebook Page, and show them to Mathias. Publish only after he approves.
- Sunday: one long 16:9 video (8–10 min) that expands that week's topics, with affiliate links in the description.

## Topics already used
ep001 heartbeats · ep002 blinking · ep003 breathing · ep004 red blood cells · ep005 skin · ep006 bones · ep007 brain

## Publishing (since 15 Nov 2026)
- Videos go to branch `media` (`media/w{N}_{topic}.mp4`); Buffer downloads them from raw.githubusercontent.com at publish time — never delete that branch.
- `publish/schedule.json` on `main` = the week to publish: `{"week": "...", "posts": [{"ep","dueAt" (UTC, 17:00Z = 12:00 Bogota),"video","title","text","text_youtube","text_tiktok","text_instagram"}]}`.
- n8n workflow "Inner Numbers – Publicar semana en Buffer" (n8n-n8n.ml7ihy.easypanel.host, active) runs every Sunday 18:00 Bogota: reads schedule.json, skips past dates, creates one Buffer post per channel (YouTube, TikTok, Instagram — Buffer free plan, 3 channels, 10 queued per channel). Running it twice duplicates posts.
- Only update schedule.json after Mathias approves the week's videos.

## Camera moves (opt-in, per scene)
In any `episodes_v2/*.json` scene, add to `visual`:
- `"camera": "pull_back" | "push_in" | "crane_up"` — camera move during that scene only.
- `"hud": true` — REC viewfinder (corners, blinking REC, timecode) during that scene only.
Scenes without these fields render exactly as before. Use them only at key moments (hook, big reveal). Full demo: `engine/camera_demo.py`.
