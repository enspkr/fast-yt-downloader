#!/usr/bin/env python3
# fast_yt_downloader.py
# Quick, robust, multi-URL downloader built on yt-dlp.
# Works on Windows and Linux (and macOS).
#
# Usage examples (on Windows, use "python" or "py" instead of "python3"):
#   python3 fast_yt_downloader.py https://youtu.be/VIDEO_ID
#   python3 fast_yt_downloader.py --file urls.txt --workers 6 --out ~/Videos
#   python3 fast_yt_downloader.py --audio https://youtu.be/VIDEO_ID
#
# Notes:
# - Default output folder is the Downloads folder in your home directory.
# - For best speed, install aria2 (optional) and ffmpeg (recommended).
# - Only download content you have rights to and respect site TOS.

import argparse
import concurrent.futures as futures
import os
import sys
import tempfile
from typing import Iterator, List, Tuple

# Standard shell exit code for a process terminated by SIGINT
INTERRUPT_EXIT_CODE = 130

try:
    import yt_dlp
except Exception as e:
    print("[!] yt-dlp is not installed. Install it with:", file=sys.stderr)
    print(f"    {os.path.basename(sys.executable)} -m pip install -U yt-dlp", file=sys.stderr)
    sys.exit(1)


def build_opts(args, outdir: str):
    # Base options
    ydl_opts = {
        "verbose": args.verbose,
        "outtmpl": os.path.join(os.path.expanduser(outdir), "%(title).200B [%(id)s].%(ext)s"),
        "continue_dl": True,
        "quiet": False,
        "noprogress": False,
        "restrictfilenames": False,
        "ignoreerrors": False,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 8,  # works for HLS/DASH
        "merge_output_format": "mp4",
        "js_runtimes": {"node": {}, "deno": {}},
    }

    
    # Prefer best video+audio; fall back to single best
    fmt = args.format or "bv*+ba/b"
    if args.audio:
        fmt = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",  # fastest for most YT audio (usually AAC in m4a)
            "preferredquality": "0",
        }]
        # If user asked to embed thumbnail (good for music)
        if args.thumb:
            ydl_opts["postprocessors"].append({"key": "EmbedThumbnail"})
            ydl_opts["writethumbnail"] = True
        ydl_opts["merge_output_format"] = "m4a"

    ydl_opts["format"] = fmt

    # Live streams: capture from the start of the stream instead of the live edge
    if args.live_from_start:
        ydl_opts["live_from_start"] = True
        # Keeps an interrupted capture playable instead of leaving an unreadable file
        ydl_opts["hls_use_mpegts"] = True

    # Optional: external downloader (aria2c) for faster parallel chunks
    if args.aria2:
        if args.live_from_start:
            # aria2c cannot follow a fragment list that is still growing
            print("[!] Ignoring --aria2: not supported with --live-from-start.", file=sys.stderr)
        else:
            # If aria2 is installed, this will be used; otherwise yt-dlp falls back internally
            ydl_opts["external_downloader"] = "aria2c"
            # Reasonable defaults: 16 connections, 1 MiB piece size
            ydl_opts["external_downloader_args"] = {
                "aria2c": ["-x16", "-s16", "-k1M", "--min-split-size=1M"]
            }

    # Subtitles (optional)
    if args.subs:
        ydl_opts["writesubtitles"] = True
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = ["all"] if args.subs == "all" else [args.subs]
        # Try to embed if possible
        ydl_opts["embedsubtitles"] = True
    
    # Cookies: prefer explicit cookie file, then browser extraction
    if args.cookies:
        ydl_opts["cookiefile"] = args.cookies
    elif args.cookies_from:
        ydl_opts["cookiesfrombrowser"] = (args.cookies_from,)

    return ydl_opts


def load_urls(args) -> List[str]:
    urls = list(args.urls or [])
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    # Deduplicate preserving order
    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def download_one(url: str, ydl_opts) -> Tuple[str, bool, str]:
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return (url, True, "")
    except Exception as e:
        return (url, False, str(e))


def run_downloads(urls: List[str], ydl_opts, workers: int) -> Iterator[Tuple[str, bool, str]]:
    """Yield one (url, success, error) per URL as each download settles.

    A lone URL runs in the main thread so that Ctrl-C reaches yt-dlp directly
    and it can finalize the file. Inside a worker thread the interrupt never
    arrives, so a live stream that never ends would block the pool forever.
    """
    if len(urls) == 1:
        yield download_one(urls[0], ydl_opts)
        return

    ex = futures.ThreadPoolExecutor(max_workers=max(1, workers))
    try:
        yield from ex.map(lambda u: download_one(u, ydl_opts), urls)
        ex.shutdown(wait=True)
    except BaseException:
        # Running downloads cannot be interrupted; abandon them instead of
        # blocking on shutdown. main() exits hard so they cannot delay it.
        ex.shutdown(wait=False, cancel_futures=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fast multi-URL YouTube downloader (yt-dlp based)")
    parser.add_argument("urls", nargs="*", help="Video/playlist/channel URLs")
    parser.add_argument("--file", "-f", help="Text file with URLs (one per line)")
    parser.add_argument("--cookies-from", "-c", help="Use cookies from a browser (e.g., 'chrome', 'firefox')")
    parser.add_argument("--cookies", help="Path to a Netscape-format cookies.txt file")
    parser.add_argument("--out", "-o", default=os.path.join(os.path.expanduser("~"), "Downloads"),
                        help="Output directory (default: your user's Downloads folder)")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Concurrent downloads (default: 4)")
    parser.add_argument("--audio", "-a", action="store_true", help="Audio only (extract as .m4a)")
    parser.add_argument("--thumb", action="store_true", help="If --audio, also embed thumbnail")
    parser.add_argument("--format", help="yt-dlp format selector (advanced)")
    parser.add_argument("--aria2", action="store_true", help="Use aria2c external downloader for extra speed (optional)")
    parser.add_argument("--subs", nargs="?", const="all",
                        help="Download subtitles (default all langs if flag used; or pass a code like 'en'/'tr')")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable yt-dlp verbose logging")
    parser.add_argument("--live-from-start", action="store_true",
                        help="For live streams, download from the start instead of the live edge")

    return parser


def main():
    args = build_parser().parse_args()

    urls = load_urls(args)
    if not urls:
        print("No URLs provided. Give URLs as arguments or via --file.", file=sys.stderr)
        sys.exit(2)

    os.makedirs(os.path.expanduser(args.out), exist_ok=True)

    # Pre-extract browser cookies to a temp file so all workers share
    # a single consistent cookie jar (avoids SQLite lock / race conditions).
    cookie_tempfile = None
    if args.cookies_from and not args.cookies:
        try:
            cookie_tempfile = tempfile.NamedTemporaryFile(
                suffix=".txt", prefix="yt_cookies_", delete=False, mode="w"
            )
            cookie_path = cookie_tempfile.name
            # Seed with Netscape header so yt-dlp accepts it as a valid cookie jar
            cookie_tempfile.write("# Netscape HTTP Cookie File\n")
            cookie_tempfile.close()
            print(f"[i] Extracting cookies from {args.cookies_from}...")
            extract_opts = {
                "cookiesfrombrowser": (args.cookies_from,),
                "cookiefile": cookie_path,
                "quiet": True,
            }
            # Cookies are loaded on init, saved to cookiefile on close.
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                pass
            # Override: use the extracted cookie file instead of browser extraction
            args.cookies = cookie_path
            args.cookies_from = None
            print(f"[i] Cookies extracted successfully.")
        except Exception as e:
            print(f"[!] Cookie extraction failed: {e}", file=sys.stderr)
            print("[!] Falling back to per-worker browser extraction.", file=sys.stderr)
            if cookie_tempfile and os.path.exists(cookie_tempfile.name):
                os.unlink(cookie_tempfile.name)
            cookie_tempfile = None

    ydl_opts = build_opts(args, args.out)

    print(f"[i] Starting downloads: {len(urls)} item(s) | workers={args.workers}")
    ok, fail = 0, 0
    results: List[Tuple[str, bool, str]] = []

    interrupted = False
    try:
        for url, success, err in run_downloads(urls, ydl_opts, args.workers):
            results.append((url, success, err))
            if success:
                ok += 1
                print(f"[OK] {url}")
            else:
                fail += 1
                print(f"[FAIL] {url} :: {err}", file=sys.stderr)
    except KeyboardInterrupt:
        interrupted = True
        print("\n[!] Interrupted. Partial downloads can be resumed by rerunning.", file=sys.stderr)
    finally:
        if cookie_tempfile and os.path.exists(cookie_tempfile.name):
            os.unlink(cookie_tempfile.name)

    if interrupted:
        # Skip interpreter shutdown, which would join abandoned worker threads
        os._exit(INTERRUPT_EXIT_CODE)

    print(f"[i] Done. Success: {ok} | Failed: {fail}")
    if fail:
        print("[!] Some downloads failed. You may try again with --aria2 or adjust --workers.", file=sys.stderr)


if __name__ == "__main__":
    main()
