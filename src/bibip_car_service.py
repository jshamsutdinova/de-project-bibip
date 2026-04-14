from decimal import Decimal
from datetime import datetime
from pathlib import Path
from sortedcontainers import SortedList

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = Path(root_directory_path)

    def _get_data_file(self, table: str) -> Path:
        """Get data file for the table."""
        fpath = self.root_directory_path / f'{table}.txt'
        if not fpath.exists():
            fpath.touch()
        return fpath

    def _get_index_file(self, table: str) -> Path:
        """Get index file for the table."""
        fpath = self.root_directory_path / f'{table}_index.txt'
        if not fpath.exists():
            fpath.touch()
        return fpath

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        """Add new model to the database."""
        data_fpath = self._get_data_file('models')
        index_fpath = self._get_index_file('models')

        file_size = data_fpath.stat().st_size
        line_number = file_size // 501

        row = f"{model.id};{model.name};{model.brand}".ljust(500) + "\n"

        with open(data_fpath, 'r+') as f:
            f.seek(line_number * (501))
            f.write(row)

        with open(index_fpath, 'r+') as f:
            lines = f.readlines()
            index = []
            for row in lines:
                idx, ln = row.strip().split(';')
                index.append((int(idx), int(ln)))
            index.append((model.id, line_number))
            index = SortedList(index, key=lambda x: x[0])

            f.seek(0)  # delete old indexes.
            f.truncate()

            for idx, ln in index:
                f.write(f"{idx};{ln}\n")

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        """Add new car to the database."""
        data_fpath = self._get_data_file('cars')
        index_fpath = self._get_index_file('cars')

        file_size = data_fpath.stat().st_size
        line_number = file_size // 501

        row = f"{car.vin};{car.model};{car.price};{car.date_start.isoformat()};{car.status.value}"
        row = row.ljust(500) + "\n"

        with open(data_fpath, 'r+') as f:
            f.seek(line_number * (501))
            f.write(row)

        with open(index_fpath, 'r+') as f:
            lines = f.readlines()
            index = []
            for row in lines:
                vin, ln = row.strip().split(';')
                index.append((vin, int(ln)))
            index.append((car.vin, line_number))
            index = SortedList(index, key=lambda x: x[0])

            f.seek(0)  # delete old lines.
            f.truncate()

            for vin, ln in index:
                f.write(f"{vin};{ln}\n")

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        """Save car sale to the database."""
        data_fpath = self._get_data_file('sales')
        index_fpath = self._get_index_file('sales')

        file_size = data_fpath.stat().st_size
        line_number = file_size // 501

        row = f"{sale.sales_number};{sale.car_vin};{sale.sales_date.isoformat()};{sale.cost}"
        row = row.ljust(500) + '\n'

        with open(data_fpath, 'r+') as f:
            f.seek(line_number * (501))
            f.write(row)

        with open(index_fpath, 'r+') as f:
            lines = f.readlines()
            index = []
            for row in lines:
                number, ln = row.strip().split(';')
                index.append((number, int(ln)))
            index.append((sale.sales_number, line_number))
            index = SortedList(index, key=lambda x: x[0])

            f.seek(0)  # delete old lines.
            f.truncate()

            for number, ln in index:
                f.write(f"{number};{ln}\n")

            car_index_fpath = self._get_index_file('cars')
            car_data_fpath = self._get_data_file('cars')

            with open(car_index_fpath, 'r+') as f:
                lines = f.readlines()
                for num, row in enumerate(lines):
                    vin, ln = row.strip().split(';')
                    if vin == sale.car_vin:
                        line_num = int(ln)

            with open(car_data_fpath, 'r+') as f:
                f.seek(line_num * 501)
                row = f.read(500).strip()

                vin, model, price, date, status = row.split(';')

                car = Car(
                    vin=vin,
                    model=int(model),
                    price=Decimal(price),
                    date_start=datetime.strptime(
                        date, '%Y-%m-%dT%H:%M:%S').date(),
                    status=CarStatus(status)
                )

                # Change status of car
                car.status = CarStatus.sold

                new_row = f"{car.vin};{car.model};{car.price};{car.date_start.isoformat()};{car.status.value}"
                new_row = new_row.ljust(500) + '\n'

                f.seek(line_num * 501)
                f.write(new_row)

        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        """Return available models of cars for selling right now."""
        car_data_fpath = self._get_data_file('cars')

        available_cars = []
        with open(car_data_fpath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                vin_car, model, price, date, car_status = line.strip().split(';')

                if CarStatus(car_status) == status:
                    car = Car(
                        vin=vin_car,
                        model=int(model),
                        price=Decimal(price),
                        date_start=datetime.strptime(date, '%Y-%m-%dT%H:%M:%S').date(),
                        status=status
                    )
                    available_cars.append(car)

        return available_cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        """Return updated info about car after selling."""
        car_index_fpath = self._get_index_file('cars')
        car_data_fpath = self._get_data_file('cars')

        with open(car_index_fpath, 'r+') as f:
            lines = f.readlines()
            for num, row in enumerate(lines):
                vin_idx, ln = row.strip().split(';')
                if vin_idx == vin:
                    line_num = int(ln)

        with open(car_data_fpath, 'r+') as f:
            f.seek(line_num * 501)
            row = f.read(500).strip()

            vin, model, price, date, status = row.split(';')

            car = Car(
                vin=vin,
                model=int(model),
                price=Decimal(price),
                date_start=datetime.strptime(date, '%Y-%m-%dT%H:%M:%S').date(),  # is it date format obj?
                status=CarStatus(status)
            )

        return CarFullInfo(
            vin=vin,
            car_model_name="",
            car_model_brand="",
            price=Decimal(price),
            date_start=datetime.fromisoformat(date),
            status=CarStatus(status),
            sales_date=None,
            sales_cost=None,
        )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        raise NotImplementedError

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        raise NotImplementedError

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        raise NotImplementedError
