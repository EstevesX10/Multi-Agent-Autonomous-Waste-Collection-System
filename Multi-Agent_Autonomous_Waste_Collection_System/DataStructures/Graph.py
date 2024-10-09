from spade.agent import Agent

class Edge:
    """
    Class representing an edge in a graph.
    An edge connects a vertex to another vertex and has an associated value (weight).
    """

    def __init__(self, endv: int, v: any) -> None:
        """
        # Description
            -> Initializes a new edge.

        := param: endv - The destination vertex of the edge.
        := param: v - The value or weight of the edge.
        """

        # Save given values
        self.enode = endv
        self.value = v

    def endnode(self) -> int:
        """
        # Description
            -> Returns the destination vertex of the edge.

        := return: The destination vertex (enode).
        """

        return self.enode

    def getValue(self) -> any:
        """
        # Description
            -> Returns the value (weight) of the edge.

        := return: The value or weight of the edge.
        """

        return self.value

    def newValue(self, v: any) -> None:
        """
        # Description
            -> Updates the value (weight) of the edge.

        := param: v - The new value or weight to be set.
        """

        self.value = v

class Node:
    """
    Class representing a node in a graph.
    Each node has a list of adjacent edges, representing its neighbors.
    """

    def __init__(self) -> None:
        """
        # Description
            -> Initializes a new node with an empty list of neighbors (adjacent edges) and another for agent related contents.
        """

        self.neighbours = []
        self.contents = []

    def adjs(self) -> list:
        """
        # Description
            -> Returns the list of adjacent edges (neighbors) of the node.

        := return: The list of adjacent edges.
        """

        return self.neighbours

    def addContent(self, agent:Agent) -> None:
        """
        # Description
            -> Inserts a given agent to the current node's contents.

        := return: None, since we are simply introducing a new agent to the network.
        """

        self.contents.append(agent)

    def getContents(self) -> list[Agent]:
        """
        # Description
            -> Returns the list with the Agents inside the current node.

        := return: The list with the contents of the current node.
        """

        return self.contents

class Graph:
    """
    Class representing a weighted directed graph.
    The graph is represented by an adjacency list, where each node has a list of edges.
    """

    def __init__(self, n: int) -> None:
        """
        # Description
            -> Initializes a graph with n vertices.
            -> Each vertex is represented by a Node, and an adjacency list is created.

        := param: n - The number of vertices in the graph.
        """

        self.nverts = n  # Number of vertices
        self.nedges = 0  # Number of edges
        # Create a list of nodes (indexed from 1 to n, with position 0 unused)
        self.verts = [Node() for _ in range(n + 1)]

    def numVertices(self) -> int:
        """
        # Description
            -> Returns the number of vertices in the graph.

        := return: The number of vertices (nverts).
        """

        return self.nverts

    def numEdges(self) -> int:
        """
        # Description
            -> Returns the number of edges in the graph.

        := return: The number of edges (nedges).
        """

        return self.nedges

    def adjsNodes(self, i: int) -> list:
        """
        # Description
            -> Returns the list of adjacent edges (neighbors) for a given vertex.

        := param: i - The index of the vertex.
        := return: The list of adjacent edges (neighbors) of vertex i.
        """
        return self.verts[i].adjs()

    def insertNewEdge(self, i: int, j: int, value_ij: any) -> None:
        """
        # Description
            -> Inserts a new edge from vertex i to vertex j with a given value (weight).
            -> The edge is added to the adjacency list of vertex i.

        := param: i - The source vertex.
        := param: j - The destination vertex.
        := param: value_ij - The value (weight) of the edge.
        """

        self.verts[i].adjs().insert(
            0, Edge(j, value_ij)
        )  # Insert the edge at the beginning of the list
        self.nedges += 1  # Increment the number of edges

    def findEdge(self, i: int, j: int) -> Node:
        """
        # Description
            -> Searches for an edge from vertex i to vertex j.

        := param: i - The source vertex.
        := param: j - The destination vertex.
        := return: The edge from vertex i to vertex j, or None if no such edge exists.
        """

        for adj in self.adjsNodes(i):
            if adj.endnode() == j:
                return adj  # Return the edge if found
        return None  # Return None if no edge is found

    def addAgentNode(self, nodeId:int, agent:Agent) -> None:
        """
        # Description
            -> Introduces a given agent to the node identified by the provided Node ID

        := param: nodeId - Vertex in which we pretend to insert a Agent.
        := param: agent - Agent to be inserted.
        := return: None, since we are only adding an agent to a node.
        """

        # Find the node to insert the agent into
        self.verts[nodeId].addContent(agent)