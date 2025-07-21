from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Optional
import json
from main import scrape_all_sites

app = FastAPI(title="Betting Scraper API", description="API for scraping betting site histories")

# API Key for authentication
API_KEY = "my_secret_key"

# Pydantic models for request/response
class Credentials(BaseModel):
    sportybet: Optional[Dict[str, str]] = None
    bet9ja: Optional[Dict[str, str]] = None
    msport: Optional[Dict[str, str]] = None

class ScrapeRequest(BaseModel):
    credentials: Credentials

@app.get("/")
def read_root():
    return {"status": "Betting scraper API is live", "version": "1.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.post("/scrape")
def scrape_betting_sites(request: ScrapeRequest, x_api_key: str = Header(...)):
    """
    Scrape betting sites with provided credentials
    
    Expected request format:
    {
        "credentials": {
            "sportybet": {"username": "xxx", "password": "xxx"},
            "bet9ja": {"username": "xxx", "password": "xxx"},
            "msport": {"username": "xxx", "password": "xxx"}
        }
    }
    """
    # Validate API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    try:
        # Convert Pydantic model to dict and filter out None values
        credentials_dict = {}
        if request.credentials.sportybet:
            credentials_dict['sportybet'] = request.credentials.sportybet
        if request.credentials.bet9ja:
            credentials_dict['bet9ja'] = request.credentials.bet9ja
        if request.credentials.msport:
            credentials_dict['msport'] = request.credentials.msport
        
        if not credentials_dict:
            raise HTTPException(status_code=400, detail="No valid credentials provided")
        
        # Perform scraping
        result = scrape_all_sites(credentials_dict)
        
        return {
            "success": True, 
            "message": "Scraping completed successfully",
            "data": result,
            "sites_scraped": list(credentials_dict.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.post("/scrape-single")
def scrape_single_site(site: str, username: str, password: str, x_api_key: str = Header(...)):
    """
    Scrape a single betting site
    
    Parameters:
    - site: One of 'sportybet', 'bet9ja', 'msport'
    - username: Site username
    - password: Site password
    """
    # Validate API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    if site not in ['sportybet', 'bet9ja', 'msport']:
        raise HTTPException(status_code=400, detail="Invalid site. Must be one of: sportybet, bet9ja, msport")
    
    try:
        credentials = {site: {"username": username, "password": password}}
        result = scrape_all_sites(credentials)
        
        return {
            "success": True,
            "message": f"Scraping {site} completed successfully", 
            "data": result,
            "site": site
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping {site} failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

