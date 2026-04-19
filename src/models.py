from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class CarStatus(StrEnum):
    available = "available"
    reserve = "reserve"
    sold = "sold"
    delivery = "delivery"


class Car(BaseModel):
    vin: str
    model: int
    price: Decimal
    date_start: datetime
    status: CarStatus

    def index(self) -> str:
        return self.vin

    def serialize(self) -> str:
        row = ';'.join([
            self.vin,
            str(self.model),
            str(self.price),
            self.date_start.isoformat(),
            self.status.value
        ])
        row = row.ljust(500) + '\n'
        return row

    @classmethod
    def parse_row(cls, row: str):
        vin, model, price, date_start, status = row.strip().split(';', 4)
        return cls(
            vin=vin,
            model=int(model),
            price=Decimal(price),
            date_start=datetime.fromisoformat(date_start),
            status=CarStatus(status)
        )


class Model(BaseModel):
    id: int
    name: str
    brand: str

    def index(self) -> str:
        return str(self.id)

    def serialize(self) -> str:
        row = ';'.join([
            str(self.id),
            self.name,
            self.brand
        ])
        row = row.ljust(500) + '\n'
        return row

    @classmethod
    def parse_row(cls, row: str):
        id, name, brand = row.strip().split(';', 2)
        return cls(
            id=int(id),
            name=name,
            brand=brand
        )


class Sale(BaseModel):
    sales_number: str
    car_vin: str
    sales_date: datetime
    cost: Decimal
    is_deleted: bool = False

    def index(self) -> str:
        return self.sales_number

    def serialize(self) -> str:
        row = ';'.join([
            self.sales_number,
            self.car_vin,
            self.sales_date.isoformat(),
            str(self.cost),
            str(self.is_deleted)
        ])
        row = row.ljust(500) + '\n'
        return row

    @classmethod
    def parse_row(cls, row: str):
        s_num, car_vin, s_dt, cost, is_deleted = row.strip().split(';', 4)
        is_deleted = (is_deleted == 'True')
        return cls(
            sales_number=s_num,
            car_vin=car_vin,
            sales_date=datetime.fromisoformat(s_dt),
            cost=Decimal(cost),
            is_deleted=is_deleted
        )


class CarFullInfo(BaseModel):
    vin: str
    car_model_name: str
    car_model_brand: str
    price: Decimal
    date_start: datetime
    status: CarStatus
    sales_date: datetime | None
    sales_cost: Decimal | None


class ModelSaleStats(BaseModel):
    car_model_name: str
    brand: str
    sales_number: int
