import uvicorn
from fastapi import FastAPI

from app.api.add_router import add_router
from app.api.main_router import main_router

app = FastAPI()


app.include_router(add_router)
app.include_router(main_router)

if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=8004, reload=True)