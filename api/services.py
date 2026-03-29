from fastapi import FastAPI
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI()

@app.get("/")
def services():
    extractors = yt_dlp.extractor.gen_extractors()
    platforms = [e.IE_NAME for e in extractors]
    return JSONResponse({
        "status": "success",
        "Credit": "@xdshivay",
        "supported_platforms": platforms
    })
