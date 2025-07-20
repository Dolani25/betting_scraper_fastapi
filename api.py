from fastapi import FastAPI, HTTPException, Header
from main import scrape_all_sites

app = FastAPI()

API_KEY = "my_secret_key"

@app.get("/")
def read_root():
    return {"status": "Betting scraper is live"}

@app.post("/scrape")
def scrape(credentials: dict, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    try:
        result = scrape_all_sites(credentials)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
