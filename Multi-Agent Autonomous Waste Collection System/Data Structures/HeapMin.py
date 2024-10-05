class Qnode:
    """
    Class representing a node in the priority queue, containing a vertex (vert)
    and its associated key (vertkey).
    """
    def __init__(self, v:int, key:any) -> None:
        """
        # Description
            -> Initializes a new node with a vertex and a key.

        := param: v - Vertex identifier.
        := param: key - Key associated with the vertex.
        """

        # Saving given parameters
        self.vert = v
        self.vertkey = key

class Heapmin:
    """
    Implementation of a priority queue using a min-heap.
    Supports operations such as insertion, extracting the minimum element, 
    and decreasing the key.
    """
    
    # Constant to indicate an invalid position.
    posinvalida = 0  

    def __init__(self, vec:list[any], n:int) -> None:
        """
        # Description
            -> Initializes a min-heap with n elements.

        := param: vec - List of keys for the vertices.
        := param: n - Number of vertices.
        """

        self.sizeMax = n  # Maximum heap size.
        self.size = n  # Current heap size.
        self.a = [None] * (n + 1)  # List of Qnodes, indexed from 1.
        self.pos_a = [None] * (n + 1)  # Positions of the nodes, indexed from 1.

        for i in range(1, n + 1):
            self.a[i] = Qnode(i, vec[i])  # Create nodes with vertices and their keys.
            self.pos_a[i] = i  # Store the position of each vertex in the heap.

        # Build the min-heap by adjusting the elements.
        for i in range(n // 2, 0, -1):
            self.heapify(i)

    def isEmpty(self) -> bool:
        """
        # Description
            -> Checks if the heap is empty.

        := return: True if the heap is empty, False otherwise.
        """

        return self.size == 0

    def extractMin(self) -> Qnode:
        """
        # Description
            -> Removes and returns the vertex with the smallest key in the heap.

        := return: The vertex with the smallest key.
        """

        vertv = self.a[1].vert
        self.swap(1, self.size)
        self.pos_a[vertv] = self.posinvalida  # Marks the vertex as removed.
        self.size -= 1
        self.heapify(1)
        return vertv

    def decreaseKey(self, vertv:int, newkey:any) -> None:
        """
        # Description
            -> Decreases the key associated with a vertex and adjusts its position in the heap.

        := param: vertv - The vertex whose key will be decreased.
        := param: newkey - The new key value.
        """

        i = self.pos_a[vertv]
        self.a[i].vertkey = newkey

        # Adjust the position of the vertex while its key is smaller than its parent's.
        while i > 1 and self.compare(i, self.parent(i)) < 0:
            self.swap(i, self.parent(i))
            i = self.parent(i)

    def insert(self, vertv:int, key:any) -> None:
        """
        # Description
            -> Inserts a new vertex into the heap with an associated key.

        := param: vertv - The vertex to be inserted.
        := param: key - The key associated with the vertex.
        """

        if self.sizeMax == self.size:
            raise ValueError("Heap is full")

        self.size += 1
        self.a[self.size] = Qnode(vertv, key)  # Insert the new vertex.
        self.pos_a[vertv] = self.size  # Store the position of the vertex in the heap.
        self.decreaseKey(vertv, key)  # Fix the position of the vertex in the heap.

    def writeHeap(self) -> None:
        """
        # Description
            -> Displays the current content of the heap, showing the vertices and their respective keys.
        """

        print(f"Max size: {self.sizeMax}")
        print(f"Current size: {self.size}")
        print("(Vert,Key)\n---------")
        for i in range(1, self.size + 1):
            print(f"({self.a[i].vert},{self.a[i].vertkey})")

        print("-------\n(Vert,PosVert)\n---------")
        for i in range(1, self.sizeMax + 1):
            if self.validPosition(self.pos_a[i]):
                print(f"({i},{self.pos_a[i]})")

    def parent(self, i:int) -> int:
        """
        # Description
            -> Returns the index of the parent node of a given node.

        := param: i - The index of the current node.
        := return: The index of the parent node.
        """

        return i // 2

    def left(self, i:int) -> int:
        """
        # Description
            -> Returns the index of the left child of a given node.

        := param: i - The index of the current node.
        := return: The index of the left child.
        """

        return 2 * i

    def right(self, i:int) -> int:
        """
        # Description
            -> Returns the index of the right child of a given node.

        := param: i - The index of the current node.
        := return: The index of the right child.
        """

        return 2 * i + 1

    def compare(self, i:int, j:int) -> int:
        """
        # Description
            -> Compares the keys of two nodes in the heap.

        := param: i - The index of the first node.
        := param: j - The index of the second node.
        := return: -1 if the key of i is smaller, 1 if larger, 0 if equal.
        """

        if self.a[i].vertkey < self.a[j].vertkey:
            return -1
        elif self.a[i].vertkey == self.a[j].vertkey:
            return 0
        return 1

    def heapify(self, i:int) -> None:
        """
        # Description
            -> Fixes the structure of the heap from a given index.

        := param:  i - The index of the node to adjust.
        """

        l = self.left(i)
        r = self.right(i)
        smallest = i

        # Find the smallest value between the current node and its children.
        if l <= self.size and self.compare(l, smallest) < 0:
            smallest = l
        if r <= self.size and self.compare(r, smallest) < 0:
            smallest = r

        # If the smallest value is not the current node, swap and continue adjusting.
        if smallest != i:
            self.swap(i, smallest)
            self.heapify(smallest)

    def swap(self, i:int, j:int) -> None:
        """
        # Description
            -> Swaps two nodes in the heap and adjusts their positions.

        := param: i - The index of the first node.
        := param: j - The index of the second node.
        """

        self.pos_a[self.a[i].vert] = j
        self.pos_a[self.a[j].vert] = i
        self.a[i], self.a[j] = self.a[j], self.a[i]

    def validPosition(self, i:int) -> bool:
        """
        # Description
            -> Checks if a vertex position is valid in the heap.

        := param: i - The position of the vertex.
        := return: True if the position is valid, False otherwise.
        """
        return 1 <= i and i <= self.size