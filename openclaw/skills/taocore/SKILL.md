# TaoCore Human Analysis (CLI)

Use this skill when a user asks for human-state analysis, scoring, or recommendations from photos/videos. It runs the local `taocore-human` CLI and returns JSON output.

## When to use
- Requests to analyze a folder of photos or a video for interaction dynamics.
- Requests for TaoCore-based scoring, balance/cluster/hub metrics, equilibrium status, or summary reports.

## Inputs you need
- For photos: a local folder path containing images.
- For video: a local video file path.

If the user doesn’t provide a path, ask for it before running.

## Commands
Preferred (if installed on PATH):
- `taocore-human photo-folder <FOLDER> [--output <FILE>]`
- `taocore-human video <VIDEO> [--output <FILE>]`

Fallback (run from repo path):
- `cd /Users/dadatoto/taocore-human && python -m taocore_human.cli photo-folder <FOLDER> [--output <FILE>]`
- `cd /Users/dadatoto/taocore-human && python -m taocore_human.cli video <VIDEO> [--output <FILE>]`

## Output
- The CLI returns JSON to stdout (or `--output` file). Provide the JSON (or a concise summary plus the JSON) back to the user.
- Do not invent metrics or interpretations beyond what the JSON provides.

## Examples
- `taocore-human photo-folder /path/to/photos --output /tmp/taocore_result.json`
- `taocore-human video /path/to/video.mp4`
