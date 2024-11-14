class Config:
    # Trucks
    truckNumber: int = 8
    truckCapacity: int = 30
    truckFuelCapacity: int = 100
    maxTasks: int = 10

    # Bins
    binCount: int = 3
    trashGenCooldown: int = 30
    binCapacity: int = 30

    # God
    secondsPerHour: int = 30
    secondsBetweenDisasters: int = 30
    secondsBetweenTruckDeath: int = 80
    secondsForNewTruck: int = 60
