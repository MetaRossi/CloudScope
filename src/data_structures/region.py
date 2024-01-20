from pydantic import BaseModel


class Region(BaseModel):
    name: str
    description: str
