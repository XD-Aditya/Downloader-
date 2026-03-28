from fastapi import FastAPI, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
import yt_dlp
import string, random
from urllib.parse import urlparse
import os

app = FastAPI()

# In-memory short link store
short_db = {}

# Generate unique short ID
def generate_short_id(length=6):
    while True:
        short_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        if short_id not in short_db:
            return short_id

# Create short link
def create_short_link(long_url):
    short_id = generate_short_id()
    short_db[short_id] = long_url
    return short_id

# URL validation
def is_valid_url(url: str):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc

# Base yt_dlp options
def get_ydl_opts(cookies_file=None):
    opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': False,
        'format': 'bestvideo+bestaudio/best',
    }
    if cookies_file and os.path.isfile(cookies_file):
        opts['cookiefile'] = cookies_file
    return opts

@app.get("/api/download")
def download(
    url: str, 
    request: Request, 
    cookies_file: str = Query(default=None, description="Optional path to cookies.txt for authenticated downloads")
):
    if not url or not is_valid_url(url):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "Credit": "", "details": "Invalid URL"}
        )

    try:
        ydl_opts = get_ydl_opts(cookies_file)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        videos = []

        entries = info.get("entries") or [info]

        for entry in entries:
            video_obj = {}
            audio_obj = {}

            for f in entry.get("formats", []):
                height = f.get("height")
                key = f"{height}p" if height else "audio_only"
                abs_url = str(request.base_url) + f"d/{create_short_link(f.get('url'))}"

                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    video_obj[key] = {
                        "url": abs_url,
                        "extension": f.get("ext"),
                        "filesize": f.get("filesize")
                    }
                elif f.get("vcodec") == "none" and f.get("acodec") != "none":
                    audio_obj[key] = {
                        "url": abs_url,
                        "extension": f.get("ext"),
                        "filesize": f.get("filesize")
                    }

            # Thumbnail short link
            thumbnail_url = entry.get("thumbnail")
            if thumbnail_url:
                thumb_short = str(request.base_url) + f"d/{create_short_link(thumbnail_url)}"
                thumbnail_info = {"url": thumb_short}
            else:
                thumbnail_info = {"url": None}

            # Optional width/height
            if entry.get("thumbnails"):
                thumb = entry.get("thumbnails")[-1]
                thumbnail_info["width"] = thumb.get("width")
                thumbnail_info["height"] = thumb.get("height")

            videos.append({
                "platform": entry.get("extractor_key"),
                "title": entry.get("title"),
                "uploader": entry.get("uploader"),
                "thumbnail": thumbnail_info,
                "duration": entry.get("duration"),
                "description": entry.get("description"),
                "video": dict(sorted(video_obj.items(), key=lambda x: int(x[0].replace('p','')) if x[0]!='audio_only' else 0, reverse=True)),
                "audio": audio_obj
            })

        return JSONResponse({
            "status": "success",
            "Credit": "@xdshivay",
            "videos": videos
        })

    except yt_dlp.utils.DownloadError as e:
        # Specific known yt-dlp error (private or blocked content)
        print(f"[yt-dlp ERROR] {e}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "Credit": "@xdshivay",
                "details": "The video is not accessible. It might be private, removed, or require login."
            }
        )
    except Exception as e:
        # Generic fallback error
        print(f"[ERROR] {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "Credit": "@xdshivay",
                "details": "Something went wrong while processing your request."
            }
        )

@app.get("/d/{short_id}")
def redirect_link(short_id: str):
    url = short_db.get(short_id)
    if not url:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "Credit": "@xdshivay",
                "details": "Invalid link"
            }
        )
    if not is_valid_url(url):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "Credit": "@xdshivay",
                "details": "Unsafe URL"
            }
        )
    return RedirectResponse(url)
