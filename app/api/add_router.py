from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.api.schemas import AddData
from app.dao.base import Repository, get_session


add_router = APIRouter(tags=['Add data'], prefix='/add')

@add_router.post("/add_data/", response_model=dict, status_code=201)
async def add_data_route(data: AddData, session: Repository = Depends(get_session)):
    """Эндпоинт для ввода тестовых данных в бд"""
    await session.add_data(data)
    return JSONResponse(status_code=201, content={"message": "Data added successfully"})





