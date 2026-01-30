import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Cho phép app mobile gọi API (tạm thời mở rộng cho MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
REPLICATE_VERSION = os.getenv(
    "REPLICATE_VERSION",
    # IDM-VTON version hash (Replicate)
    "0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985",
)

REPLICATE_PRED_URL = "https://api.replicate.com/v1/predictions"


def to_data_uri(file_bytes: bytes, content_type: str) -> str:
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


@app.get("/")
def health():
    return {"ok": True, "service": "virtual-tryon-backend"}


@app.post("/try-on")
async def try_on(
    person: UploadFile = File(...),
    cloth: UploadFile = File(...),
    category: str = Form("upper_body"),   # upper_body | lower_body | dresses (tuỳ model support)
    garment_des: str = Form(""),          # mô tả ngắn: "short sleeve t-shirt" (không bắt buộc)
    crop: bool = Form(False),             # bật nếu ảnh người không theo tỉ lệ 3:4
    steps: int = Form(30),
    seed: int = Form(42),
):
    if not REPLICATE_API_TOKEN:
        return {"ok": False, "error": "Missing REPLICATE_API_TOKEN"}

    person_bytes = await person.read()
    cloth_bytes = await cloth.read()

    # Replicate expects strings for images (URL or data URI)
    human_img = to_data_uri(person_bytes, person.content_type or "image/jpeg")
    garm_img = to_data_uri(cloth_bytes, cloth.content_type or "image/png")

    payload = {
        "version": REPLICATE_VERSION,
        "input": {
            "human_img": human_img,
            "garm_img": garm_img,
            "category": category,
            "garment_des": garment_des,
            "crop": crop,
            "steps": steps,
            "seed": seed,
        },
    }

    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
        # “sync wait” theo Replicate docs
        "Prefer": "wait=60",
    }

    r = requests.post(REPLICATE_PRED_URL, json=payload, headers=headers, timeout=75)
    data = r.json()

    # Nếu chạy xong: output thường là URL ảnh
    # Nếu chưa xong: sẽ có status starting/processing và cần poll (mình sẽ làm bước nâng cấp sau)
    return {"ok": True, "replicate": data}
