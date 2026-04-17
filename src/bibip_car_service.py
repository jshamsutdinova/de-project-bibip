from decimal import Decimal
from datetime import datetime
from itertools import islice
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
            return f.read(501)

    def _write_line(self, data_fpath: Path, line_number: int, row: str) -> None:
        """Write a row with fixed length (500) on the line number to the file."""
        with open(data_fpath, 'r+') as f:
            f.seek(line_number * 501)
            f.write(row)

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

        row = f"{sale.sales_number};{sale.car_vin};{sale.sales_date.isoformat()};{sale.cost};{False}"
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

            with open(car_index_fpath, 'r+') as f_idx:
                lines = f_idx.readlines()
                for _, row in enumerate(lines):
                    vin, ln = row.strip().split(';')
                    if vin == sale.car_vin:
                        line_num = int(ln)

            with open(car_data_fpath, 'r+') as f_data:
                f_data.seek(line_num * 501)
                row = f_data.read(500).strip()

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

                f_data.seek(line_num * 501)
                f_data.write(new_row)

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
        """Return detailed info about car by VIN."""
        car_index_fpath = self._get_index_file('cars')  # find the path in the init()?
        car_data_fpath = self._get_data_file('cars')

        model_index_fpath = self._get_index_file('models')
        model_data_fpath = self._get_data_file('models')

        line_num = None

        with open(car_index_fpath, 'r') as f:
            for row in f:
                vin_idx, ln = row.strip().split(';')
                if vin_idx == vin:
                    line_num = int(ln)
                    break
        if line_num is None:
            return None

        with open(car_data_fpath, 'r') as f:
            f.seek(line_num * 501)  # separate to method.
            row = f.read(500).strip()
            car_vin, model, car_price, date, status = row.split(';')

        line_num_model = None

        with open(model_index_fpath, 'r') as f:
            for row in f:
                model_id, ln = row.strip().split(';')
                if model_id == model:
                    line_num_model = int(ln)
                    break

        if line_num_model is None:
            return None

        with open(model_data_fpath, 'r') as f:
            f.seek(line_num_model * 501)  # separate to method for finding row.
            row = f.read(500)
            _, name, brand = row.strip().split(';')

        sales_date = None
        sales_cost = None

        if status == CarStatus.sold.value:
            sales_data_fpath = self._get_data_file('sales')
            with open(sales_data_fpath, 'r') as f:
                for row in f:
                    vals = row.strip().split(';')
                    _, s_car_vin, s_date, cost, is_deleted = vals
                    is_deleted = (is_deleted == 'True')

                    if car_vin == s_car_vin and not is_deleted:
                        sales_date = datetime.strptime(
                            s_date, '%Y-%m-%dT%H:%M:%S').date()
                        sales_cost = Decimal(cost)
                        break

        car_full_info = CarFullInfo(
            vin=car_vin,
            car_model_name=name,
            car_model_brand=brand,
            price=Decimal(car_price),
            date_start=datetime.strptime(
                date, '%Y-%m-%dT%H:%M:%S').date(),  # why date recorded with time?
            status=CarStatus(status),
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

        with open(car_data_path, 'r+') as f:
            f.seek(line_number * 501)
            row = f.read(500)

            vin_car, model, price, date_start, status = row.strip().split(';')

            new_row = f'{new_vin};{model};{price};{date_start};{status}'
            new_row = new_row.ljust(500) + '\n'

            f.seek(line_number * 501)  # return to the line.
            f.write(new_row)

        sales_updated = []
        with open(sales_data_path, 'r+') as f:
            for row in f:
                row = row.strip()
                sales_num, car_vin, sales_dt, cost, is_deleted = row.split(';')
                is_deleted = (is_deleted == 'True')

                if car_vin == vin and not is_deleted:
                    car_vin = new_vin

                sales_updated.append((sales_num, car_vin, sales_dt, cost,
                                      is_deleted))

        with open(sales_data_path, 'r+') as f:
            f.seek(0)
            f.truncate()

            for s in sales_updated:
                row = f"{s[0]};{s[1]};{s[2]};{s[3]};{s[4]}".ljust(500) + '\n'
                f.write(row)

        car_updated = Car(
            vin=new_vin,
            model=int(model),
            price=Decimal(price),
            date_start=datetime.strptime(
                date_start, '%Y-%m-%dT%H:%M:%S').date(),
            status=CarStatus(status)
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
        vals = sale_row.strip().split(';')
        sales_number, car_vin, sales_date, cost, is_deleted = vals
        is_deleted = (is_deleted == 'True')

        if not is_deleted:
            new_row = f"{sales_number};{car_vin};{sales_date};{cost};{True}"
            new_row = new_row.ljust(500) + '\n'
            self._write_line(sales_data_path, sale_line_number, new_row)

            car_index_fpath = self._get_index_file('cars')
            car_data_fpath = self._get_data_file('cars')

            car_line_number = self._find_line(car_index_fpath, car_vin)
            car_row = self._read_line(car_data_fpath, car_line_number)
            car_vals = car_row.strip().split(';')
            vin, model, price, date_start, status = car_vals

            new_status = CarStatus.available.value
            car_new_row = f"{vin};{model};{price};{date_start};{new_status}"
            car_new_row = car_new_row.ljust(500) + '\n'
            self._write_line(car_data_fpath, car_line_number, car_new_row)

            car = Car(
                vin=vin,
                model=int(model),
                price=Decimal(price),
                date_start=datetime.strptime(
                    date_start, '%Y-%m-%dT%H:%M:%S').date(),
                status=CarStatus(new_status)
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
                vals = row.strip().split(';')
                vin, model_id, price, date_start, status = vals
                model_id = int(model_id)

                vin_to_model[vin] = model_id

                if model_id not in model_max_price:
                    model_max_price[model_id] = Decimal(price)
                else:
                    model_max_price[model_id] = max(
                        model_max_price[model_id],
                        Decimal(price)
                    )

        model_info = {}
        with open(models_data_path, 'r') as f:
            for row in f:
                id, name, brand = row.strip().split(';', maxsplit=2)
                model_info[int(id)] = (name, brand)

        saled_models = {}
        with open(sale_data_path, 'r') as f:
            for row in f:
                vals = row.strip().split(';')
                sales_num, car_vin, sales_dt, cost, is_deleted = vals
                is_deleted = (is_deleted == 'True')

                if is_deleted:
                    continue

                model_id = vin_to_model.get(car_vin)
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
