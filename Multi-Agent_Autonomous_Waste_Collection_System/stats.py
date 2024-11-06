from typing import Dict, List
from collections import defaultdict


class Stats:
    fuel_consumed: int = 0
    trucks_without_fuel: int = 0
    trucks_over_capacity: int = 0

    trash_collected: int = 0  # TODO:
    trash_deposited: int = 0  # TODO:
    trash_overspill: int = 0

    disasters: int = 0  # TODO:

    truck_collection_times: Dict[str, List[int]] = defaultdict(list)  # TODO:
    truck_distance_traveled: Dict[str, int] = defaultdict(lambda: 0)

    @staticmethod
    def print():
        print("======= Stats =======")
        for var_name in Stats.__annotations__:
            # Get the value of the class variable by accessing it directly
            var_value = getattr(Stats, var_name)
            print(f"{var_name}: {var_value}")
