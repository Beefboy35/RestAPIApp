from typing import List

from sqlalchemy import Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dao.database import Base


class Building(Base):
    __tablename__ = 'buildings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    organizations: Mapped[List['Organization']] = relationship("Organization", back_populates="building")


class Activity(Base):
    __tablename__ = 'activities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('activities.id'))

    parent: Mapped['Activity'] = relationship("Activity", remote_side=[id], backref='children')
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey('organizations.id'))

    organization: Mapped['Organization'] = relationship("Organization", back_populates="activities")


class Organization(Base):
    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    phone_numbers: Mapped[List[str]] = mapped_column(JSON)
    address: Mapped[str] = mapped_column(String, nullable=False)
    building_id: Mapped[int] = mapped_column(Integer, ForeignKey('buildings.id'))


    building: Mapped[Building] = relationship('Building', back_populates='organizations')
    activities: Mapped[List[Activity]] = relationship("Activity", back_populates="organization")