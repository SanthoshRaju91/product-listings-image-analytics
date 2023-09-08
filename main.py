import base64
import requests
from io import BytesIO

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
from typing import List
from concurrent.futures.thread import ThreadPoolExecutor

app = FastAPI()

THRESHOLD_IMAGE_COUNT = 10


def get_as_base64(url):
    return base64.b64encode(requests.get(url).content)


def get_image_resolution(url):
    try:
        data = get_as_base64(url)
        img = Image.open(BytesIO(base64.b64decode(data)))
        width, height = img.size

        if width >= 800 and height >= 800:
            return "good"
        else:
            return "bad"
    except Exception as e:
        return None


def get_image_res_score(urls, overall):
    overall_good = overall["good"]
    score = (overall_good / urls) * 100
    if score > 80:
        return 8
    if score > 60 and score <= 80:
        return 6
    if score > 40 and score <= 60:
        return 4
    if score > 20 and score <= 40:
        return 2
    else:
        return 2


def process_images(urls):
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(get_image_resolution, urls)

    res = []
    for result in results:
        res.append(result)

    overall = {i: res.count(i) for i in res}
    len_urls = len(urls)
    return {
        "image_count": len_urls,
        "image_count_score": 2 if len_urls > THRESHOLD_IMAGE_COUNT else 1,
        "images_res_score": get_image_res_score(len_urls, overall)
    }


class Images(BaseModel):
    urls: List[str]


@app.post("/check/images/quality")
def check_images_quality(images: Images):
    urls = images.urls
    res = process_images(urls)
    return JSONResponse(content=res)
