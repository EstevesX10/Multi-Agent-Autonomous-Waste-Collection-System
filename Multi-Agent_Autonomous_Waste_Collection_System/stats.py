from typing import Dict, List
from collections import defaultdict


class Stats:
    fuel_consumed: int = 0
    trucks_without_fuel: int = 0

    trash_collected: int = 0  # TODO:
    trash_deposited: int = 0  # TODO:
    trash_overspill: int = 0

    disasters: int = 0  # TODO:

    truck_collection_times: Dict[str, List[int]] = defaultdict(list)  # TODO:
    truck_distance_traveled: Dict[str, int] = defaultdict(lambda: 0)
