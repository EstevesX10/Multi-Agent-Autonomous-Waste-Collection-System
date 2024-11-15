from typing import Dict, List
from collections import defaultdict


# This class contains all statistics
class Stats:
    fuel_consumed: int = 0
    trucks_without_fuel: int = 0
    trucks_over_capacity: int = 0

    trash_generated: int = 0
    trash_collected: int = 0
    trash_deposited: int = 0
    trash_overspill: int = 0

    disasters: int = 0

    bin_collection_times: Dict[str, List[int]] = defaultdict(list)
    truck_distance_traveled: Dict[str, int] = defaultdict(lambda: 0)

    @staticmethod
    def print():
        # Prints statistics in a more user friendly way
        print("======= Stats =======")
        for var_name in Stats.__annotations__:
            if var_name == "bin_collection_times":
                continue

            # Get the value of the class variable by accessing it directly
            var_value = getattr(Stats, var_name)
            print(f"{var_name}: {var_value}")

        print("Mean collection time per bin:")
        for id, vals in Stats.bin_collection_times.items():
            mean = sum(vals) / len(vals)
            print(f"{id}: {mean:.2f} s")
