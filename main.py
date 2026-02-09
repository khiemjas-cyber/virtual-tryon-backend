import io
import base64
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"ok": True, "service": "virtual-tryon-backend-free-demo"}

def img_to_base64_png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

@app.post("/try-on")
async def try_on(
    person: UploadFile = File(...),
    cloth: UploadFile = File(...),
    category: str = Form("upper_body"),
    scale: float = Form(0.62),   # chỉnh độ to nhỏ của áo
    y_offset: int = Form(80),    # chỉnh áo lên/xuống
):
    # đọc ảnh
    person_bytes = await person.read()
    cloth_bytes = await cloth.read()

    person_img = Image.open(io.BytesIO(person_bytes)).convert("RGBA")
    cloth_img = Image.open(io.BytesIO(cloth_bytes)).convert("RGBA")

    # resize ảnh người về kích thước dễ xử lý (giữ tỉ lệ)
    target_w = 768
    ratio = target_w / person_img.width
    target_h = int(person_img.height * ratio)
    person_img = person_img.resize((target_w, target_h))

    # scale áo theo bề ngang người
    new_cloth_w = int(person_img.width * scale)
    cloth_ratio = new_cloth_w / cloth_img.width
    new_cloth_h = int(cloth_img.height * cloth_ratio)
    cloth_img = cloth_img.resize((new_cloth_w, new_cloth_h))

    # vị trí dán áo (giữa thân trên)
    x = (person_img.width - cloth_img.width) // 2
    y = y_offset

    # ghép áo lên người (dùng alpha của PNG)
    out = person_img.copy()
    out.alpha_composite(cloth_img, (x, y))

    return {
        "ok": True,
        "mode": "free_demo_overlay",
        "image_base64_png": img_to_base64_png(out)
    }
