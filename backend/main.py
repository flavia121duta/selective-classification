from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json, time
from tqdm import tqdm
from openai import OpenAI
import uvicorn
import tempfile
import os
from sse_starlette.sse import EventSourceResponse
import asyncio
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORIES_SCHEMA = """
FRAGRANCE/ FRAGRANCE TOTAL JUICES/ FRAGRANCE EDT
FRAGRANCE/ FRAGRANCE TOTAL JUICES/ FRAGRANCE EDP
FRAGRANCE/ FRAGRANCE ANCILLARIES/ FRAGRANCE LOTION/CREME
FRAGRANCE/ FRAGRANCE ANCILLARIES/ FRAGRANCE DEODORANT/ANTIPERSPIRANT
FRAGRANCE/ FRAGRANCE TOTAL SET/ FRAGRANCE SET
FRAGRANCE/ FRAGRANCE ANCILLARIES/ FRAGRANCE AFTER SHAVE
FRAGRANCE/ FRAGRANCE TOTAL JUICES/ FRAGRANCE COLOGNE
FRAGRANCE/ FRAGRANCE ANCILLARIES/ FRAGRANCE BATH/SHOWER
FRAGRANCE/ FRAGRANCE ANCILLARIES/ FRAGRANCE OTHER
FRAGRANCE/ FRAGRANCE HOME SCENTS/ FRAGRANCE CANDLES
FRAGRANCE/ FRAGRANCE HOME SCENTS/ FRAGRANCE DIFFUSERS
FRAGRANCE/ FRAGRANCE HOME SCENTS/ FRAGRANCE ROOM FRESHENERS
FRAGRANCE/ FRAGRANCE HOME SCENTS/ FRAGRANCE ALL OTHER HOME ANCILLARIES
FRAGRANCE/ FRAGRANCE HOME SCENTS/ FRAGRANCE OTHER
HAIRCARE/ HAIR STYLING/ ALL OTHER STYLING
HAIRCARE/ HAIR CARE/ MASK
HAIRCARE/ HAIR CARE/ DAILY RINSE SHAMPOO
HAIRCARE/ HAIR CARE/ ALL OTHER CARE
HAIRCARE/ HAIR STYLING/ HAIR GEL
HAIRCARE/ HAIR CARE/ DAILY RINSE CONDITIONER
HAIRCARE/ HAIR STYLING/ HAIR SPRAY
HAIRCARE/ HAIR STYLING/ HAIR MOUSSE / FOAM
HAIRCARE/ HAIRCARE SET/ HAIRCARE SET
HAIRCARE/ HAIR COLOR/ HAIR COLOR
HAIRCARE/ HAIR CARE/ DRY SHAMPOO
MAKEUP/ MAKEUP TOTAL LIP/ MAKEUP LIP COLOR
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP EYE LINER
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP POWDER
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP MASCARA
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP FOUNDATION
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP TINTED MOISTURISER
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP EYE TOOLS AND ACCESSORIES
MAKEUP/ MAKEUP TOTAL LIP/ MAKEUP LIP GLOSS
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP EYE PENCIL
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP EYE BROW
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP BLUSH
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP CONCEALER
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP EYE SHADOW
MAKEUP/ MAKEUP TOTAL LIP/ MAKEUP LIP LINER
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP SETTING SPRAY/POWDER
MAKEUP/ MAKEUP TOTAL LIP/ MAKEUP LIP BALM
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP FACE OTHER
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP FACE PRIMER
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP HIGHLIGHTER
MAKEUP/ MAKEUP TOTAL NAIL/ MAKEUP NAIL TREATMENT
MAKEUP/ MAKEUP TOTAL NAIL/ MAKEUP COLOR ENAMEL
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP EYELASHES
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP BRONZER
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP FALSEEYELASHES
MAKEUP/ MAKEUP TOTAL NAIL/ MAKEUP NAIL TOOLS AND ACCESSORIES
MAKEUP/ MAKEUP OTHER/ MAKEUP ALL OTHER TOOLS AND ACCESSORIES
MAKEUP/ MAKEUP TOTAL SET/ MAKEUP SET
MAKEUP/ MAKEUP TOTAL EYE/ MAKEUP EYE PRIMER
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP FACE TOOLS AND ACCESSORIES
MAKEUP/ MAKEUP TOTAL FACE/ MAKEUP PALETTE
MAKEUP/ MAKEUP TOTAL NAIL/ MAKEUP NAIL OTHER
MAKEUP/ MAKEUP TOTAL LIP/ MAKEUP LIP OTHER
MAKEUP/ MAKEUP TOTAL NAIL/ MAKEUP BASE COATS/TOP COATS
MAKEUP/ MAKEUP TOTAL LIP/ MAKEUP LIP TOOLS AND ACCESSORIES
MAKEUP/ MAKEUP TOTAL LIP/ MAKEUP LIP PRIMER
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE DEODORANT
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACIAL CLEANSER
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE MAKEUP REMOVER
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE EYE TREATMENT
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY CLEANSER
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE TONERS/CLARIFYERS
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACE CREAM
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE MASK
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE SHAVE BODY
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE LIP TREATMENT
SKINCARE/ SKINCARE TOTAL SUN/ SKINCARE BODY IN SUN
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACE SERUM
SKINCARE/ SKINCARE TOTAL SET/ SKINCARE SET
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE ALL OTHER FACE
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE ALL OTHER BODY
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY OIL
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY SERUM
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACE LOTION
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY CREAM/LOTION
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY SPRAY
SKINCARE/ SKINCARE TOTAL SUN/ SKINCARE SELF-TANNER
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACIAL EXFOLIATOR
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACE GEL
SKINCARE/ SKINCARE TOTAL SUN/ SKINCARE FACE IN SUN
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACE OIL
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY DEVICES
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY EXFOLIATOR
SKINCARE/ SKINCARE TOTAL SUN/ SKINCARE AFTER SUN
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACE SPRAY/MIST
SKINCARE/ SKINCARE TOTAL FACE/ SKINCARE FACIAL DEVICES
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE HAND SOAP
SKINCARE/ SKINCARE TOTAL BODY/ SKINCARE BODY SUPPLEMENT
"""

def classify_product(row, max_retries=3):
    product_info = json.dumps({
        "Retailer": row.get('Retailer',''),
        "ProductID": row.get('ProductID',''),
        "EAN": row.get('EAN',''),
        "ProductName": row.get('ProductName',''),
        "CategoryName": row.get('CategoryName',''),
        "CategoryName_1": row.get('CategoryName_1',''),
        "SubcategorName": row.get('SubLineName',''),
        "TypeName": row.get('TypeName',''),
        "Gender": row.get('Gender'),
        "LineName": row.get('LineName',''),
        "SubLineName": row.get('SubLineName',''),
        "ManufacturerName": row.get('ManufacturerName',''),
        "BrandName": row.get('BrandName',''),
        }, ensure_ascii=False)

    prompt = f"""
    Classify this cosmetic product into exactly one combination of Category_fin → Segment_fin → Subsegment_fin AND determine the Gender_fin.
    Gender_fin can be: MEN, WOMEN, UNISEX, HOME SCENTS.

    Schema:
    {CATEGORIES_SCHEMA}

    Product info (JSON):
    {product_info}

    Evertything that is for sexual wellness, intimate care, condoms, lubricants, etc. should be classified as SKINCARE → SKINCARE TOTAL BODY → SKINCARE ALL OTHER BODY.

    Everthing that is for babies/children should be classified as SKINCARE → UNISEX → SKINCARE TOTAL BODY → SKINCARE ALL OTHER BODY.

    Everything that is for tooth care, oral hygiene, toothpaste, toothbrushes, mouthwash, etc. should be classified as SKINCARE → UNISEX → SKINCARE TOTAL BODY → SKINCARE ALL OTHER BODY.

    Return ONLY JSON with: Category_fin, Gender_fin, Segment_fin, Subsegment_fin.
    If unsure, choose the most likely.
    """


    attempt = 0
    while attempt < max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )   
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = "\n".join(content.split("\n")[1:-1]).strip()
            data = json.loads(content)

            if data.get("Category_fin") == "MAKEUP":
                data["Gender_fin"] = "WOMEN"
            if data.get("Segment_fin") == "FRAGRANCE HOME SCENTS":
                data["Gender_fin"] = "HOME SCENTS"
            if data.get("Subsegment_fin") in ["FRAGRANCE DIFFUSERS", "FRAGRANCE CANDLES", "FRAGRANCE ROOM FRESHENERS", "FRAGRANCE ALL OTHER HOME ANCILLARIES"]:
                data["Gender_fin"] = "HOME SCENTS"
                
            return (
                data.get("Category_fin", "ERROR"),
                data.get("Gender_fin", "ERROR"),
                data.get("Segment_fin", "ERROR"),
                data.get("Subsegment_fin", "ERROR")
            )
        except:
            attempt += 1
            time.sleep(1)
    return "ERROR", "ERROR", "ERROR", "ERROR"


progress_value = 0  # shared progress variable

@app.get("/progress")
async def progress_stream():
    async def event_generator():
        last_val = -1
        global progress_value
        while True:
            if progress_value != last_val:
                yield {"data": progress_value}
                last_val = progress_value
            await asyncio.sleep(0.5)
    return EventSourceResponse(event_generator())


# Main Excel processing endpoint
@app.post("/classify")
async def classify_excel(file: UploadFile = File(...)):
    global progress_value
    df = pd.read_excel(file.file, dtype={"EAN": str})
    results = []

    for idx, row in df.iterrows():
        # run blocking function in thread
        category, gender, segment, subsegment = await asyncio.to_thread(classify_product, row)
        results.append([category, gender, segment, subsegment])

        # update progress
        progress_value = int((idx + 1) / len(df) * 100)
        await asyncio.sleep(0.01)  # give control to event loop

    df[["Category_fin","Gender_fin","Segment_fin","Subsegment_fin"]] = pd.DataFrame(results, index=df.index)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(tmp.name, index=False)

    # Reset progress
    progress_value = 0

    return FileResponse(tmp.name, filename="produse_clasificate_AI.xlsx")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)