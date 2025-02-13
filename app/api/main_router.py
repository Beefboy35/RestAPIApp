from typing import Tuple

from fastapi import APIRouter, Depends

from app.api.schemas import Radius
from app.dao.base import Repository, get_session

main_router = APIRouter(tags=["Main"], prefix="/organizations")


@main_router.get("/get_by_address")
async def get_by_address(building_address: str, session: Repository =  Depends(get_session)):
    """Эндпоинт для получения организаций по адресу здания"""
    return await session.get_organizations_by_address(building_address)


@main_router.get("/get_by_name")
async def get_by_name(name: str, session: Repository = Depends(get_session)):
    """Эндпоинт для получения организации по имени"""
    return await session.get_organization_by_name(name)

@main_router.get("/get_by_id")
async def get_by_id(org_id: int, session: Repository = Depends(get_session)):
    """Эндпоинт для получения организации по id"""
    return await session.get_organization_by_id(org_id)
@main_router.get("/all")
async def get_all(session: Repository = Depends(get_session)):
    """Эндпоинт для получения всех организаций"""
    return await session.get_organizations()


@main_router.get("/get_by_activity")
async def get_by_activity(activity: str, session: Repository = Depends(get_session)):
    """Эндпоинт для получения всех организаций по заданной деятельности"""
    return await session.get_organizations_by_activity(activity)

@main_router.post("/get_by_radius")
async def get_by_radius(data: Radius, session: Repository = Depends(get_session)):
    """Эндпоинт для получения всех организаций находящихся в указанном радиусе"""
    return await session.get_organizations_by_radius(data)



