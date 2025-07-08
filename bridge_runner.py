import os
import uvicorn
from web_scraper import check_tesseract_available

if __name__ == "__main__":
    # Test OCR functionality on startup
    print("🔍 Testing OCR capabilities...")
    if check_tesseract_available():
        print("✅ Tesseract OCR is available on Railway!")
    else:
        print("❌ Tesseract OCR not available")
    
    print("\n🚀 Starting FastAPI server...")
    
    # Get port from environment variable (Railway sets this)
    port = int(os.getenv("PORT", 8000))
    
    # Start the FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
