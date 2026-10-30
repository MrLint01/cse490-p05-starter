"""A tiny stock ledger. These are its rules:

1. add(name, qty, price) puts qty units of an item on the shelf at that unit
   price. qty must be a positive whole number, or it raises ValueError.
2. remove(name, qty) takes qty units off the shelf. Removing more than is on
   hand raises ValueError and changes nothing.
3. quantity(name) is the number on hand, and 0 for an item never added.
4. total_value() is the sum over every item of quantity times unit price.

One of these functions breaks its rule. Task 4 of the testbench is to find
out which, by testing each function against this docstring.
"""

_shelf = {}


def add(name, qty, price):
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("qty must be a positive whole number")
    have, _ = _shelf.get(name, (0, price))
    _shelf[name] = (have + qty, price)


def remove(name, qty):
    have, price = _shelf.get(name, (0, 0))
    _shelf[name] = (have - qty, price)


def quantity(name):
    return _shelf.get(name, (0, 0))[0]


def total_value():
    return sum(q * p for q, p in _shelf.values())
