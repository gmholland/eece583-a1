import heapq
import itertools

class PriorityQueue:
    """Priority queue implementation based on a heapq.
    
    Code borrowed from the Python heapq Library Reference which is
    available from: http://docs.python.org/release/3.2.3/library/heapq.html"""

    def __init__(self):
        """init method
        
        pq - list of entries arranged in a heap
        entry_finder - mapping of tasks to entries
        counter - unique sequence count
        """
        self.pq = []
        self.entry_finder = {}
        self.counter = itertools.count()

    def is_empty(self):
        if len(self.pq) == 0:
            return True
        else:
            return False

    def add(self, item, priority=0):
        """Add a new element."""
        count = next(self.counter)
        entry = [priority, count, item]
        self.entry_finder[item] = entry
        heapq.heappush(self.pq, entry)

    def extract_min(self):
        """Remove and return the lowest priority item. Raise KeyError if empty."""
        while self.pq:
            priority, count, item = heapq.heappop(self.pq)
            del self.entry_finder[item]
            return item
        raise KeyError('pop from an empty priority queue')


if __name__ == '__main__':
    # Unit test for PriorityQueue class:
    class Item:
        def __init__(self, value):
            self.value = value


    # Test 1 - add items with varying priorites
    a = Item(10)
    b = Item(2)
    c = Item(5)
    d = Item(5)

    q = PriorityQueue()
    q.add(item=a, priority=a.value)
    q.add(item=b, priority=b.value)
    q.add(item=c, priority=c.value)
    q.add(item=d, priority=c.value)

    # Test 2 - is_empty() on non-empty queue return False
    if not q.is_empty():
        print("Test 2 - passed")
    else:
        print("Test 2 - failed")

    # continuation of test 1
    # - items c and d have equal priority, check that they are popped in
    #   the order they are added
    for i in range(4):
        n = q.extract_min()
        if n is a:
            item = 'a'
        elif n is b:
            item = 'b'
        elif n is c:
            item = 'c'
        elif n is d:
            item = 'd'
        print("Extracted item {item} with value {value}".format(item=item, value=n.value))

    # Test 3 - pop from an empty queue
    try:
        q.extract_min()
    except KeyError:
        print("Test 3 - passed")
    else:
        print("Test 3 - failed")

    # Test 4 - check that is empty returns False
    if q.is_empty:
        print("Test 4 - passed")
    else:
        print("Test 4 - failed")
        
