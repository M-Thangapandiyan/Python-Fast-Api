from fastapi import FastAPI
from router.document import router as document_router
from config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL
)

app.include_router(document_router)

@app.get("/")
def root():
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": settings.DOCS_URL,
        "endpoints": {
            "documents":f"{settings.API_V1_PREFIX}/{settings.APPLICATION_TAG}"
        }
    }

@app.get(settings.HEALTH_CHECK_ENDPOINT)
def health_check():
    return {"status": "healthy"}






















