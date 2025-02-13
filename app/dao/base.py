from abc import ABC, abstractmethod
from math import acos, sin, radians, cos
from typing import  Sequence, Any, Union

from fastapi import Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from sqlalchemy import insert, select

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api.schemas import AddData, NestedActivity, SecondNestedActivity
from app.dao.database import get_async_session
from app.dao.models import Organization, Building, Activity


class BaseRepository(ABC):
    """Абстрактный класс для основного репозитория"""
    @abstractmethod
    async def add_data(self, data: AddData):
        pass

    @abstractmethod
    async def get_organizations(self):
        pass

    @abstractmethod
    async def get_organizations_by_address(self, building_address: str):
        pass

    @abstractmethod
    async def get_organizations_by_radius(self, data: BaseModel):
        pass

    @abstractmethod
    async def get_organizations_by_activity(self, activity_name: str):
        pass

    @abstractmethod
    async def get_organization_by_id(self, org_id: int):
        pass

    @abstractmethod
    async def get_organization_by_name(self, name: str):
        pass



class Repository(BaseRepository):
    """Основной репозиторий со всей бизнес логикой"""
    def __init__(self, session: AsyncSession):
        self._session = session


    async def add_data(self, data: AddData):
        result= await self._session.execute(select(Organization).filter(Organization.name  == data.organization_name))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Organization {data.organization_name} already exists")
        try:

            building_stmt = insert(Building).values(
                address=str(data.address),  # address should be a string, not float
                latitude=data.latitude,
                longitude=data.longitude
            )
            result = await self._session.execute(building_stmt)
            building_id = result.inserted_primary_key[0]


            organization_stmt = insert(Organization).values(
                name=data.organization_name,
                phone_numbers=data.phone_numbers,
                address=data.address,
                building_id=building_id,
            )
            org_result = await self._session.execute(organization_stmt)
            org_id = org_result.inserted_primary_key[0]

            # Рекурсивная функция для добавления активностей
            async def add_activity(nested_activity: Union[NestedActivity, SecondNestedActivity], parent_id: int = None, level: int = 0):
                if level > 3:  # Проверка уровня вложенности
                    raise HTTPException(status_code=400, detail="Exceeded maximum activity nesting level of 3")

                activity_stmt = insert(Activity).values(
                    name=nested_activity.name,
                    parent_id=parent_id,
                    organization_id=org_id
                )
                activity_result = await self._session.execute(activity_stmt)
                activity_id = activity_result.inserted_primary_key[0]

                # Добавляем вложенные активности
                for sub_activity in nested_activity.sub_activities:
                    await add_activity(sub_activity, activity_id, level + 1)

            # Добавляем все корневые активности
            for activity in data.activity_names:
                await add_activity(activity)
            await self._session.commit()
            return {"message": "Data added successfully"}

        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


    async def get_organizations(self):
        """Извлекаем все организации"""
        try:
            result = await self._session.execute(select(Organization).order_by(Organization.name))
            organizations = result.scalars().all()
            if not organizations:
                raise HTTPException(status_code=404, detail=f"There are no organizations available")
            return await self.format_output(organizations)
        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


    async def get_organizations_by_address(self, building_address: str):
        """Извлекаем все организации по адресу"""
        try:
            result = await self._session.execute(select(Organization).filter(Organization.address == building_address))
            organizations_list = result.scalars().all()
            if not organizations_list:
                raise HTTPException(status_code=404, detail=f"There are no organizations placed at this address")
            return await self.format_output(organizations_list)
        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


    async def get_organizations_by_radius(self, data: BaseModel):
        """Получаем все организации находящиеся внутри определенной окружности"""
        lat, lon = data.latitude, data.longitude

        # Радиус Земли в километрах
        earth_radius = 6371.0

        # Сначала получаем все здания
        buildings_query = select(Building)
        try:
            buildings_result = await self._session.execute(buildings_query)
            buildings = buildings_result.scalars().all()


            organizations_info = []

            # Фильтруем только те здания, которые находятся в пределах заданного радиуса
            for building in buildings:
                # вычисления радиуса поиска на поверхности Земли
                distance = (
                    acos(
                        sin(radians(lat)) * sin(radians(building.latitude)) +
                        cos(radians(lat)) * cos(radians(building.latitude)) *
                        cos(radians(building.longitude) - radians(lon))
                    ) * earth_radius
            )

                if distance <= data.radius:
                    # Получаем организации, связанные со зданием
                    organizations_query = select(Organization).filter(Organization.building_id == building.id)
                    orgs_result = await self._session.execute(organizations_query)
                    organizations = orgs_result.scalars().all()

                    for org in organizations:
                        organizations_info.append({
                            "organization_name": org.name,
                            "address": building.address if building else "Not specified",
                            "phone_numbers": org.phone_numbers,
                            "latitude": building.latitude if building else None,
                            "longitude": building.longitude if building else None,
                        })
            return organizations_info
        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    async def get_organizations_by_activity(self, activity_name: str):
        """Извлекаем все организации по деятельности"""
        try:
            activity_result = await self._session.execute(
                select(Activity).filter(Activity.name == activity_name)
            )
            # получаем массив активностей с одинаковым именем, но принадлежащих разным организациям
            activities = activity_result.scalars().all()
            if not activities:
                raise HTTPException(status_code=404, detail=f"Activity {activity_name} not found")
            organization_ids = {activity.organization_id for activity in activities}
            organizations = await self._session.execute(
                select(Organization).filter(Organization.id.in_(organization_ids))
            )
            organizations_list = organizations.scalars().all()
            # вспомогательная функция для обработки ответа
            return await self.format_output(organizations_list)
        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    async def get_organization_by_name(self, name: str):
        """Извлекаем организацию по названию"""
        try:
            result = await self._session.execute(select(Organization).filter(Organization.name == name))
            result = result.scalar_one_or_none()
            if not result:
                    raise HTTPException(status_code=404, detail=f"Organization {name} does not exist")

            # Получить все активности и их подактивности
            activities = await self.get_activities_for_organization(result.id)
            coordinates = await self._session.execute(select(Building).filter(Building.address == result.address))
            coordinates = coordinates.scalars().first()
            return JSONResponse(status_code=200, content={
                "organization_name": str(result.name),
                "address": str(result.address),
                "phone_numbers": result.phone_numbers,
                "activity_names": activities,
                "latitude": coordinates.latitude,
                "longitude": coordinates.longitude
            })
        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    async def get_organization_by_id(self, org_id: int):
        """Извлекаем организацию по id"""
        try:
            result = await self._session.get(Organization, org_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Organization with id {org_id} does not exist")

            # Получить все активности и их подактивности
            activities = await self.get_activities_for_organization(result.id)
            coordinates = await self._session.execute(select(Building).filter(Building.address == result.address))
            coordinates = coordinates.scalars().first()
            return JSONResponse(status_code=200, content={
                "organization_name": str(result.name),
                "address": str(result.address),
                "phone_numbers": result.phone_numbers,
                "activity_names": activities,
                "latitude": coordinates.latitude,
                "longitude": coordinates.longitude
            })
        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")



    async def get_activities_for_organization(self, org_id):
        """Вспомогательная функция для извлечения деятельностей в правильном порядке древа"""
        try:
            activities_result = await self._session.execute(
                select(Activity).filter(Activity.organization_id == org_id)
            )
            activities = activities_result.scalars().all()

            activity_structure = {}

            for activity in activities:
                if activity.parent_id is None:
                    activity_structure[activity.id] = {
                        "name": activity.name,
                        "sub_activities": []
                    }
                else:
                    parent_activity = next((a for a in activities if a.id == activity.parent_id), None)
                    if parent_activity:
                        if parent_activity.id not in activity_structure:
                            activity_structure[parent_activity.id] = {
                                "name": parent_activity.name,
                                "sub_activities": []
                            }
                        activity_structure[parent_activity.id]["sub_activities"].append({
                            "name": activity.name,
                            "sub_activities": []  # Здесь можно добавить подактивности, если есть
                        })
        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"IntegrityError: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
        return list(activity_structure.values())

    async def format_output(self, data_array: Sequence[Any]):
        """Вспомогательная функция для правильного форматирования ответа"""
        response_content = []

        for org in data_array:
            coordinates = await self._session.execute(select(Building).filter(Building.address == org.address))
            coordinates = coordinates.scalars().first()
            activities_result = await self._session.execute(
                select(Activity).filter(Activity.organization_id == org.id)
            )
            activities = activities_result.scalars().all()

            activity_structure = {}

            for activity in activities:
                if activity.parent_id is None:
                    activity_structure[activity.id] = {
                        "name": activity.name,
                        "sub_activities": []
                    }
                else:
                    parent_activity = next((a for a in activities if a.id == activity.parent_id), None)
                    if parent_activity:
                        if parent_activity.id not in activity_structure:
                            activity_structure[parent_activity.id] = {
                                "name": parent_activity.name,
                                "sub_activities": []
                            }
                        activity_structure[parent_activity.id]["sub_activities"].append({
                            "name": activity.name,
                            "sub_activities": []  # Добавьте сюда логику, чтобы заполнить подактивности
                        })
            # Преобразование структуры активностей
            activity_names = []
            for activity in activity_structure.values():
                activity_names.append(activity)

            response_content.append({
                "name": str(org.name),
                "address": str(org.address),
                "phone_numbers": org.phone_numbers,
                "activity_names": activity_names,
                "latitude": coordinates.latitude,
                "longitude": coordinates.longitude
            })
        return response_content


async def get_session(session: AsyncSession = Depends(get_async_session)) -> Repository:
    """Функция для получения объекта класса Repository для создания сессии"""
    return Repository(session)

