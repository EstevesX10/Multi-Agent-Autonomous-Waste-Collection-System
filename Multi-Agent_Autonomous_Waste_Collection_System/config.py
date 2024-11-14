class Config:
    # Trucks
    truckNumber: int = 6
    truckCapacity: int = 50
    truckFuelCapacity: int = 50
    maxTasks: int = 10

    # Bins
    binCount: int = 7
    trashGenCooldown: int = 20
    binCapacity: int = 30

    # God
    secondsPerHour: int = 20
    secondsBetweenDisasters: int = 30
    secondsBetweenTruckDeath: int = 50
    secondsForNewTruck: int = 40
