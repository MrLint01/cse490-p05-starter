# Tests for inventory.py, based on its docstring rules.
# Run with: python -m unittest test_inventory
import unittest

import inventory


class TestInventory(unittest.TestCase):
    def setUp(self):
        # The ledger is module-level state, so start each check from an empty shelf.
        inventory._shelf.clear()

    def test_add(self):
        # Rule 1: add puts qty units on the shelf; qty must be a positive whole number.
        inventory.add("apple", 3, 2)
        self.assertEqual(inventory.quantity("apple"), 3)
        inventory.add("apple", 2, 2)
        self.assertEqual(inventory.quantity("apple"), 5)
        for bad in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                inventory.add("pear", bad, 1)
        self.assertEqual(inventory.quantity("pear"), 0)

    def test_remove(self):
        # Rule 2: remove takes qty off the shelf; removing more than on hand raises
        # ValueError and changes nothing.
        inventory.add("apple", 5, 2)
        inventory.remove("apple", 2)
        self.assertEqual(inventory.quantity("apple"), 3)
        with self.assertRaises(ValueError):
            inventory.remove("apple", 10)
        self.assertEqual(inventory.quantity("apple"), 3)

    def test_quantity(self):
        # Rule 3: quantity is the number on hand, and 0 for an item never added.
        self.assertEqual(inventory.quantity("ghost"), 0)
        inventory.add("apple", 4, 2)
        self.assertEqual(inventory.quantity("apple"), 4)

    def test_total_value(self):
        # Rule 4: total_value is the sum over every item of quantity times unit price.
        self.assertEqual(inventory.total_value(), 0)
        inventory.add("apple", 3, 2)
        inventory.add("pear", 4, 5)
        self.assertEqual(inventory.total_value(), 3 * 2 + 4 * 5)


if __name__ == "__main__":
    unittest.main()
