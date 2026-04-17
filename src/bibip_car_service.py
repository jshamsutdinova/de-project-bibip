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

    def _find_line(self, index_fpath: Path, key: str) -> int | None:
        """Find line number by key in index file."""
        key = str(key)
        with open(index_fpath, 'r') as f:
            for row in f:
                idx, line_number = row.strip().split(';')
                if idx == key:
                    return int(line_number)
        return None

    def _read_line(self, data_fpath: Path, line_number: int) -> str:
        """Read a line by line_number from a fixed-length record file."""
        with open(data_fpath, 'r') as f:
            f.seek(line_number * 501)
            row = f.read(501)
            return row

    def _write_line(self, data_fpath: Path, line_num: int, row: str) -> None:
        """Write a row with fixed length 500 on the line number to the file."""
        with open(data_fpath, 'r+') as f:
            f.seek(line_num * 501)
            f.write(row)

    def _add_new_index(self, index_path: Path, line_num: int, new_obj) -> None:
        """Add new index to the index table. Sort by indexes."""
        indexes = []
        with open(index_path, 'r+') as f:
            for row in f:
                vin, ln = row.strip().split(';')
                indexes.append((vin, int(ln)))
            indexes.append((new_obj.index(), line_num))
            indexes = SortedList(indexes, key=lambda x: x[0])

            f.seek(0)  # delete old lines.
            f.truncate()

            for id, ln in indexes:
                f.write(f"{id};{ln}\n")

    def _parse_car(self, row: str) -> Car:
        """Parse the row of the Car data table."""
        vin, model, price, date_start, status = row.strip().split(';', 4)
        return Car(
            vin=vin,
            model=int(model),
            price=Decimal(price),
            date_start=datetime.fromisoformat(date_start),
            status=CarStatus(status)
        )

    def _parse_model(self, row: str) -> Model:
        """Parse the row of the Model data table."""
        id, name, brand = row.strip().split(';', 2)
        return Model(
            id=int(id),
            name=name,
            brand=brand
        )

    def _parse_sale(self, row: str) -> Sale:
        """Parse the row of the Sale data table."""
        s_num, car_vin, s_dt, cost, is_deleted = row.strip().split(';', 4)
        is_deleted = (is_deleted == 'True')
        return Sale(
            sales_number=s_num,
            car_vin=car_vin,
            sales_date=datetime.fromisoformat(s_dt),
            cost=Decimal(cost),
            is_deleted=is_deleted
        )

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        """Add new model to the database."""
        data_fpath = self._get_data_file('models')
        index_fpath = self._get_index_file('models')

        file_size = data_fpath.stat().st_size
        line_number = file_size // 501

        row = f"{model.id};{model.name};{model.brand}".ljust(500) + "\n"

        self._write_line(data_fpath, line_number, row)
        self._add_new_index(index_fpath, line_number, model)

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        """Add new car to the database."""
        data_fpath = self._get_data_file('cars')
        index_fpath = self._get_index_file('cars')

        file_size = data_fpath.stat().st_size
        line_number = file_size // 501

        row = f"{car.vin};{car.model};{car.price};{car.date_start.isoformat()};{car.status.value}"
        row = row.ljust(500) + "\n"

        self._write_line(data_fpath, line_number, row)
        self._add_new_index(index_fpath, line_number, car)

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        """Save car sale to the database."""
        data_fpath = self._get_data_file('sales')
        index_fpath = self._get_index_file('sales')

        file_size = data_fpath.stat().st_size
        line_number = file_size // 501

        row = f"{sale.sales_number};{sale.car_vin};{sale.sales_date.isoformat()};{sale.cost};{False}"
        row = row.ljust(500) + '\n'

        self._write_line(data_fpath, line_number, row)
        self._add_new_index(index_fpath, line_number, sale)

        # Find car index
        car_index_fpath = self._get_index_file('cars')
        car_data_fpath = self._get_data_file('cars')

        # Find record in the Car table
        car_line_num = self._find_line(car_index_fpath, sale.car_vin)

        with open(car_data_fpath, 'r+') as f_data:
            f_data.seek(car_line_num * 501)
            row = f_data.read(500).strip()
            car = self._parse_car(row)

            # Change status of car
            car.status = CarStatus.sold
            new_row = f"{car.vin};{car.model};{car.price};{car.date_start.isoformat()};{car.status.value}"
            new_row = new_row.ljust(500) + '\n'
            self._write_line(car_data_fpath, car_line_num, new_row)

        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        """Return available models of cars for selling right now."""
        car_data_fpath = self._get_data_file('cars')

        available_cars = []
        with open(car_data_fpath, 'r') as f:
            for row in f:
                car = self._parse_car(row)
                if car.status == status:
                    available_cars.append(car)

        return available_cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        """Return detailed info about car by VIN."""
        car_index_fpath = self._get_index_file('cars')  # find the path in the init()?
        car_data_fpath = self._get_data_file('cars')

        model_index_fpath = self._get_index_file('models')
        model_data_fpath = self._get_data_file('models')

        # Find a record in Car table
        car_line_num = None
        car_line_num = self._find_line(car_index_fpath, vin)

        if car_line_num is None:
            return None

        row = self._read_line(car_data_fpath, car_line_num)
        car = self._parse_car(row)

        # Find a record in Model table
        model_line_num = None
        model_line_num = self._find_line(model_index_fpath, car.model)

        if model_line_num is None:
            return None

        row = self._read_line(model_data_fpath, model_line_num)
        model = self._parse_model(row)

        sales_date = None
        sales_cost = None
        if car.status == CarStatus.sold:
            sales_data_fpath = self._get_data_file('sales')
            with open(sales_data_fpath, 'r') as f:
                for row in f:
                    sale = self._parse_sale(row)

                    if car.vin == sale.car_vin and not sale.is_deleted:
                        sales_date = sale.sales_date
                        sales_cost = Decimal(sale.cost)
                        break

        car_full_info = CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sales_date,
            sales_cost=sales_cost
        )

        return car_full_info

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        """Update VIN in car table."""
        car_index_path = self._get_index_file('cars')
        car_data_path = self._get_data_file('cars')
        sales_data_path = self._get_data_file('sales')

        line_number = None
        index_updated = []
        with open(car_index_path, 'r+') as f:
            for row in f:
                vin_idx, ln_num = row.strip().split(';')
                ln_num = int(ln_num)

                if vin_idx == vin:
                    vin_idx = new_vin
                    line_number = ln_num

                index_updated.append((vin_idx, ln_num))

        if line_number is None:
            return None

        index_updated = SortedList(index_updated, key=lambda x: x[0])

        with open(car_index_path, 'r+') as f:
            for vin_idx, ln in index_updated:
                f.write(f"{vin_idx};{ln}\n")

        row = self._read_line(car_data_path, line_number)
        car = self._parse_car(row)

        new_row = f'{new_vin};{car.model};{car.price};{car.date_start};{car.status}'
        new_row = new_row.ljust(500) + '\n'
        self._write_line(car_data_path, line_number, new_row)

        sales_updated = []
        with open(sales_data_path, 'r+') as f:
            for row in f:
                sale = self._parse_sale(row)

                if sale.car_vin == vin and not sale.is_deleted:
                    sale.car_vin = new_vin

                sales_updated.append((sale.sales_number,
                                      sale.car_vin,
                                      sale.sales_date,
                                      sale.cost,
                                      sale.is_deleted))

        with open(sales_data_path, 'r+') as f:
            f.seek(0)
            f.truncate()

            for s in sales_updated:
                row = f"{s[0]};{s[1]};{s[2]};{s[3]};{s[4]}".ljust(500) + '\n'
                f.write(row)

        car_updated = Car(
            vin=new_vin,
            model=car.model,
            price=car.price,
            date_start=car.date_start,
            status=car.status
        )

        return car_updated

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        """Delete sale from the database."""
        sale_index_path = self._get_index_file('sales')
        sales_data_path = self._get_data_file('sales')

        sale_line_number = self._find_line(sale_index_path, sales_number)

        if sale_line_number is None:
            return None

        sale_row = self._read_line(sales_data_path, sale_line_number)
        sale = self._parse_sale(sale_row)

        if not sale.is_deleted:
            new_row = f"{sales_number};{sale.car_vin};{sale.sales_date};{sale.cost};{True}"
            new_row = new_row.ljust(500) + '\n'
            self._write_line(sales_data_path, sale_line_number, new_row)

            car_index_fpath = self._get_index_file('cars')
            car_data_fpath = self._get_data_file('cars')

            car_line_number = self._find_line(car_index_fpath, sale.car_vin)
            car_row = self._read_line(car_data_fpath, car_line_number)
            car = self._parse_car(car_row)

            new_status = CarStatus.available.value
            car_new_row = f"{car.vin};{car.model};{car.price};{car.date_start};{new_status}"
            car_new_row = car_new_row.ljust(500) + '\n'
            self._write_line(car_data_fpath, car_line_number, car_new_row)

            car = Car(
                vin=car.vin,
                model=car.model,
                price=car.price,
                date_start=car.date_start,
                status=new_status
            )

            return car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        """Find top 3 models by sales number."""
        sale_data_path = self._get_data_file('sales')
        cars_data_path = self._get_data_file('cars')
        models_data_path = self._get_data_file('models')

        vin_to_model = {}
        model_max_price = {}
        with open(cars_data_path, 'r') as f:
            for row in f:
                car = self._parse_car(row)

                vin_to_model[car.vin] = car.model

                if car.model not in model_max_price:
                    model_max_price[car.model] = car.price
                else:
                    model_max_price[car.model] = max(
                        model_max_price[car.model],
                        car.price
                    )

        model_info = {}
        with open(models_data_path, 'r') as f:
            for row in f:
                model = self._parse_model(row)
                model_info[model.id] = (model.name, model.brand)

        saled_models = {}
        with open(sale_data_path, 'r') as f:
            for row in f:
                sale = self._parse_sale(row)

                if sale.is_deleted:
                    continue

                model_id = vin_to_model.get(sale.car_vin)
                saled_models[model_id] = saled_models.get(model_id, 0) + 1

        sorted_models = sorted(
            saled_models.items(),
            key=lambda x: (-x[1], -model_max_price[x[0]]))

        result = []
        for model_id, count in sorted_models[:3]:
            name, brand = model_info[model_id]
            result.append(
                ModelSaleStats(
                    car_model_name=name,
                    brand=brand,
                    sales_number=count
                )
            )

        return result
