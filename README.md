# fast-yt-downloader

A small command-line downloader built on [yt-dlp](https://github.com/yt-dlp/yt-dlp). It downloads several URLs in parallel, records live streams from their very first second, extracts audio, embeds subtitles and cover art, and can use aria2 for extra speed.

Works on **Windows**, **macOS**, **Debian/Ubuntu**, **Fedora** and **Arch Linux** (and other Linux distros with the same tools installed).

> Only download content you have the right to download, and respect the site's terms of service.

## Features

### 🔴 Live stream recording from the start

Joined a stream late? `--live-from-start` records a live stream **from its beginning**, not from the moment you started the command.

```bash
python3 fast_yt_downloader.py --live-from-start https://www.youtube.com/watch?v=LIVE_ID
```

- **Catches up, then follows live.** It downloads everything already broadcast and keeps recording until the stream ends.
- **Stop whenever you want.** Press `Ctrl+C` and the file recorded so far stays playable. It isn't left half-written or corrupted.
- **Without the flag**, live streams are recorded from the current moment until they end.
- Works best on YouTube. Other sites may only support recording from the current moment.
- `--aria2` is ignored here because aria2 cannot follow a stream that is still growing.

### 🔑 Members-only videos with your browser cookies

Download **channel-membership videos, members-only live streams, age-restricted and private videos** that your own account can watch. The tool signs in with your browser's existing login, so you never type a password.

```bash
# 1. Log in to YouTube in your browser with the account that has the membership
# 2. Run the tool with that browser's name
python3 fast_yt_downloader.py --cookies-from firefox https://www.youtube.com/watch?v=MEMBERS_VIDEO_ID
```

- **Works with any browser yt-dlp supports:** `firefox`, `chrome`, `edge`, `brave`, `opera`, `vivaldi`, `chromium`, and `safari` on macOS.
- **Works with everything else too:** members-only playlists, live streams (`--live-from-start`), audio only, subtitles and parallel downloads.
- **Safe for parallel downloads.** The tool reads your cookies **once** at the start and shares them with every worker, so several downloads don't fight over your browser's cookie database. That temporary copy is **deleted automatically** when the tool exits, even after `Ctrl+C`.
- **No browser access?** Export a Netscape-format `cookies.txt` with a browser extension and pass `--cookies cookies.txt`.

```bash
# Download a whole members-only playlist as audio, 4 at a time
python3 fast_yt_downloader.py --cookies-from chrome --audio --workers 4 "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Record a members-only live stream from the start
python3 fast_yt_downloader.py --cookies-from firefox --live-from-start https://www.youtube.com/watch?v=LIVE_ID
```

> ⚠️ Cookies are your login. Anyone who has your `cookies.txt` can use your account. Never share it or commit it to git. This repo's `.gitignore` already blocks `cookies*.txt`.
>
> This only works for content your account already has access to. It does not get around paywalls or memberships.

### Everything else

| Feature | How |
|---|---|
| **Parallel downloads**: several videos at the same time | Pass several URLs, or `--file urls.txt`, and set `--workers N` |
| **Playlists and channels**: download a whole list with one URL | Pass the playlist or channel URL |
| **Best quality by default**: best video and best audio merged into `.mp4` | Automatic (needs ffmpeg) |
| **Audio only**: save the audio track as `.m4a` | `--audio` |
| **Cover art**: embed the thumbnail into audio files | `--audio --thumb` |
| **Subtitles**: download and embed manual and auto-generated subtitles | `--subs` (all languages) or `--subs en` |
| **Faster downloads**: 16 parallel connections per file | `--aria2` (needs aria2) |
| **Resume**: interrupted downloads continue where they stopped | Rerun the same command |
| **Retries**: network hiccups are retried automatically | Automatic (5 retries) |
| **Custom formats** for advanced users | `--format "<yt-dlp format selector>"` |
| **Duplicate URLs are skipped**, and `#` comments in URL files are ignored | Automatic |

## Requirements

| Tool | Needed? | Why |
|---|---|---|
| Python 3.9+ | Required | Runs the script |
| yt-dlp | Required | Does the downloading (installed from `requirements.txt`) |
| ffmpeg | Strongly recommended | Merges video + audio, needed for `--audio`, `--subs` and `--thumb` |
| Deno or Node.js | Recommended | yt-dlp uses a JavaScript runtime to handle YouTube's player challenges |
| aria2 | Optional | Only for `--aria2` |

## Installation

First clone the repo:

```
git clone https://github.com/enspkr/fast-yt-downloader.git
cd fast-yt-downloader
```

Then follow the section for your system.

### Windows

Install the system tools with winget (open a new terminal afterwards so they are on your PATH):

```powershell
winget install Python.Python.3.12 Gyan.FFmpeg DenoLand.Deno
winget install aria2.aria2        # optional
```

Install yt-dlp:

```powershell
py -m pip install -U -r requirements.txt
```

### macOS

Install [Homebrew](https://brew.sh) if you don't have it yet:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install the system tools:

```bash
brew install python ffmpeg deno
brew install aria2                # optional
```

Then install yt-dlp in a virtual environment, as shown in [Linux and macOS: install yt-dlp in a virtual environment](#linux-and-macos-install-yt-dlp-in-a-virtual-environment) below.

Homebrew also packages yt-dlp itself (`brew install yt-dlp`). If you prefer that, run `brew install yt-dlp` and skip the virtual environment step. Keep it current with `brew upgrade yt-dlp`.

### Debian / Ubuntu / Linux Mint

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip ffmpeg nodejs
sudo apt install aria2            # optional
```

### Fedora

```bash
sudo dnf install python3 python3-pip ffmpeg-free nodejs
sudo dnf install aria2            # optional
```

Fedora's default `ffmpeg-free` package leaves out some patent-encumbered codecs. Most downloads work with it, but if merging or audio extraction fails, switch to the full ffmpeg from RPM Fusion:

```bash
sudo dnf install https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
sudo dnf swap ffmpeg-free ffmpeg --allowerasing
```

### Arch Linux / Manjaro / EndeavourOS

```bash
sudo pacman -S --needed python python-pip ffmpeg deno
sudo pacman -S --needed aria2     # optional
```

Arch also packages yt-dlp itself and keeps it current. If you prefer that over pip, run `sudo pacman -S yt-dlp` and skip the virtual environment step below.

### Linux and macOS: install yt-dlp in a virtual environment

Most Linux distros (including Debian, Ubuntu and Arch) and Homebrew's Python block `pip install` into the system Python, so use a virtual environment. Run this inside the `fast-yt-downloader` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U -r requirements.txt
```

Activate it again (`source .venv/bin/activate`) in each new terminal before running the script.

## Usage

On Windows use `py` (or `python`). On Linux and macOS use `python3` (or `python` inside the virtual environment).

```bash
# One video
python3 fast_yt_downloader.py https://youtu.be/VIDEO_ID

# Several URLs at once
python3 fast_yt_downloader.py URL1 URL2 URL3

# URLs from a text file (one per line, lines starting with # are skipped)
python3 fast_yt_downloader.py --file urls.txt --workers 6

# Audio only, with the thumbnail embedded as cover art
python3 fast_yt_downloader.py --audio --thumb https://youtu.be/VIDEO_ID

# Record a live stream from its beginning (Ctrl+C to stop early)
python3 fast_yt_downloader.py --live-from-start https://www.youtube.com/watch?v=LIVE_ID

# Download and embed English subtitles
python3 fast_yt_downloader.py --subs en https://youtu.be/VIDEO_ID

# Use your Firefox login for members-only or age-restricted videos
python3 fast_yt_downloader.py --cookies-from firefox https://youtu.be/VIDEO_ID

# Choose the output folder
python3 fast_yt_downloader.py --out ~/Videos https://youtu.be/VIDEO_ID
py fast_yt_downloader.py --out "D:\Videos" https://youtu.be/VIDEO_ID
```

Files are saved to the `Downloads` folder in your home directory unless you pass `--out`.

## Options

| Option | Description |
|---|---|
| `urls` | One or more video, playlist or channel URLs |
| `-f`, `--file FILE` | Read URLs from a text file, one per line |
| `-o`, `--out DIR` | Output folder (default: `~/Downloads`) |
| `-w`, `--workers N` | Number of downloads to run at the same time (default: 4) |
| `-a`, `--audio` | Download audio only and save it as `.m4a` |
| `--thumb` | With `--audio`, embed the thumbnail as cover art |
| `--subs [LANG]` | Download and embed subtitles: all languages, or one code such as `en` or `tr` |
| `--format FMT` | Custom yt-dlp format selector (advanced) |
| `--aria2` | Use aria2c for faster downloads |
| `--live-from-start` | For live streams, record from the beginning instead of the current moment |
| `-c`, `--cookies-from BROWSER` | Use cookies from a browser (`firefox`, `chrome`, `edge`, `brave`, `safari`, ...) |
| `--cookies FILE` | Use a Netscape-format `cookies.txt` file |
| `-v`, `--verbose` | Show yt-dlp's detailed log |

Press `Ctrl+C` to stop. Rerun the same command to resume partial downloads.

## Troubleshooting

- **"yt-dlp is not installed"**: install it with the pip command for your system above. On Linux and macOS, make sure the virtual environment is activated.
- **Live stream recording stops right away or starts at the current moment**: `--live-from-start` mostly works on YouTube, and only while the stream is live. Update yt-dlp first, since live-stream handling changes often.
- **`--cookies-from safari` fails on macOS**: give your terminal app Full Disk Access in System Settings → Privacy & Security, then try again.
- **Downloads suddenly fail or return "Sign in to confirm" / format errors**: YouTube changes often. Update yt-dlp with `pip install -U -r requirements.txt` (or `sudo pacman -Syu` if you use the Arch package).
- **Video and audio come out as separate files, or `--audio` fails**: ffmpeg is missing or not on your PATH. Check with `ffmpeg -version`.
- **`--cookies-from chrome` fails**: close the browser first. Recent Chrome and Edge versions on Windows encrypt cookies in a way yt-dlp can't always read. Use Firefox instead, or export a `cookies.txt` with a browser extension and pass `--cookies cookies.txt`. Never commit that file to git.
