from fastapi import FastAPI
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI()

@app.get("/services", response_class=JSONResponse)
def services():
    # Get all platforms yt-dlp supports dynamically
    extractors = yt_dlp.extractor.gen_extractors()
    supported_platforms = [e.IE_NAME for e in extractors]

    return JSONResponse({
        "status": "success",
        "Credit": "@xdshivay",
        "supported_platforms": supported_platforms
    })
