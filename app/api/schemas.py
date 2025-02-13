
from typing import List

from pydantic import BaseModel
from pydantic.v1 import Field
class SecondNestedActivity(BaseModel):
    name: str
    sub_activities: List["SecondNestedActivity"]
class NestedActivity(BaseModel):
    name: str
    sub_activities: List[SecondNestedActivity]


class AddData(BaseModel):
    #building
    address: str
    latitude: float
    longitude: float
    #activity
    activity_names: List[NestedActivity]
    #organization
    organization_name: str
    phone_numbers: List[str]


class Radius(BaseModel):
    radius: int
    latitude: float
    longitude: float