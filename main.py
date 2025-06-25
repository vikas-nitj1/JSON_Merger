from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Union, List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import razorpay
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# FastAPI App
app = FastAPI()

# Mount static files (JS, CSS, etc.)
app.mount("/static", StaticFiles(directory="./build/static"), name="static")

# Serve index.html for root and all non-API paths (SPA support)
@app.get("/")
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str = ""):
    return FileResponse("./build/index.html")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # or "*" for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Razorpay Setup
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

# Razorpay Endpoint
class RazorpayOrderRequest(BaseModel):
    amount: int
    currency: str = "INR"
    receipt: str

@app.post("/create-razorpay-order")
def create_razorpay_order(order: RazorpayOrderRequest):
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": order.amount * 100,
            "currency": order.currency,
            "receipt": order.receipt,
            "payment_capture": 1
        })
        return {"order_id": razorpay_order["id"]}
    except Exception as e:
        return {"error": str(e)}

# JSON Merge Logic
class MergeRequest(BaseModel):
    jsons: List[Union[Dict[str, Any], List[Dict[str, Any]]]]
    override: bool = True

def merge_json(json1, json2, override=True):
    if isinstance(json1, list) and isinstance(json2, list):
        return json1 + json2
    if isinstance(json1, dict) and isinstance(json2, dict):
        result = dict(json1)
        for key, value in json2.items():
            if key in result:
                result[key] = merge_json(result[key], value, override)
            else:
                result[key] = value
        return result
    return json2 if override else json1

@app.post("/merge-json")
def merge_json_endpoint(data: MergeRequest):
    merged = data.jsons[0]
    for next_json in data.jsons[1:]:
        merged = merge_json(merged, next_json, data.override)
    return {"merged": merged}
