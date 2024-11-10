## Environment Layout

This file focuses on documenting the environment layouts used in the project's development.

### Configuration Layout

- First Line of the Configuration File:

  - Number of Nodes in the Network

- Following N lines, being N the number of Nodes in the Graph

  - Contain the positions of each node inside the GUI

- Remaining lines of the Configuration File:

  - Description of each edge in the network using the following format:

    **startNode** **endNode** **availability** **distance** **fuelConsumption** **batteryConsumption**

  1. **startNode** - Starting Node of the Edge [Start at index 0]
  2. **endNode** - Ending node of the Edge [Start at index 0]
  3. **availability** - If the road correspondent to the edge is not closed (0 - closed, 1 - open)
  4. **distance** - Distance covered between both start and end nodes (in km)
  5. **fuelConsumption** - How much vehicle running gas consumes between the locations
  6. **batteryConsumption** - How much a eletric vehicle consumes between the locations
