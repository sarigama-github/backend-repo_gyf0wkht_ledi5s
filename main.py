import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Any
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def serialize_doc(doc: dict) -> dict:
    d = {**doc}
    if "_id" in d and isinstance(d["_id"], ObjectId):
        d["id"] = str(d.pop("_id"))
    # Convert datetime fields to isoformat if present
    for key in ("created_at", "updated_at"):
        if key in d and hasattr(d[key], "isoformat"):
            d[key] = d[key].isoformat()
    return d

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# ---------------- Budgie Food API ----------------
DEFAULT_PRODUCTS = [
    {
        "title": "Premium Budgie Seed Mix",
        "description": "Balanced seed blend with canary, millet, and nutritional pellets.",
        "price": 9.99,
        "category": "seed mix",
        "in_stock": True,
    },
    {
        "title": "Vitamin-Enriched Pellets",
        "description": "Complete daily pellets formulated for budgerigars.",
        "price": 12.49,
        "category": "pellets",
        "in_stock": True,
    },
    {
        "title": "Millet Spray Treats",
        "description": "Natural golden millet sprays — perfect training reward.",
        "price": 5.49,
        "category": "treats",
        "in_stock": True,
    },
    {
        "title": "Calcium Cuttlefish Bone",
        "description": "Essential calcium source for beak and bone health.",
        "price": 3.99,
        "category": "supplement",
        "in_stock": True,
    },
]

@app.get("/api/products")
def list_products() -> List[dict]:
    if db is None:
        # Return defaults if db unavailable
        return [serialize_doc({**p, "_id": ObjectId()}) for p in DEFAULT_PRODUCTS]
    # Fetch
    items = get_documents("product")
    if not items:
        # seed defaults into DB
        for p in DEFAULT_PRODUCTS:
            try:
                create_document("product", Product(**p))
            except Exception:
                pass
        items = get_documents("product")
    return [serialize_doc(doc) for doc in items]

@app.post("/api/products", status_code=201)
def create_product(item: Product) -> dict:
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    _id = create_document("product", item)
    # Fetch inserted
    doc = db["product"].find_one({"_id": ObjectId(_id)})
    return serialize_doc(doc)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
