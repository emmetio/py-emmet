__doc__ = "Utility methods for lists"

def some(fn: callable, items: list):
    "Tests whether at least one element in the array passes the test implemented by the provided function. It returns a `bool` value."
    if items:
        for item in items:
            if fn(item):
                return True
    return False


def find_index(fn: callable, items: list):
    "Returns the index of the first element in the array that satisfies the provided testing function. Otherwise, it returns -1, indicating that no element passed the test."
    for i, item in enumerate(items):
        if fn(item):
            return i
    return -1

def get_item(items: list, index: int):
    "Returns item by index from given list or `None` if index is out of range"
    return items[index] if 0 <= index < len(items) else None
