import unittest

from node import Node
from block import Block


class BlockTests(unittest.TestCase):
    node = Node()

    def testCheckHash(self):
        block = Block(1, "addsa", "aaaaaaaaa", 0, "asdsdada")
        self.assertFalse(block.check_hash())

        block = self.node.generate_block()
        self.assertTrue(block.check_hash())

        block.nonce += 1
        self.assertFalse(block.check_hash())

        block.nonce -= 1
        block.hash += " "
        self.assertFalse(block.check_hash())

        str.strip(block.hash)
        block.data += " "
        self.assertFalse(block.check_hash())

        str.strip(block.data)
        block.prev_hash += " "
        self.assertFalse(block.check_hash())

        str.strip(block.prev_hash)
        block.index += 1
        self.assertFalse(block.check_hash())

    def testTypes(self):
        block = Block("1", "addsa", "aaaaaaaaa", "0", "asdsdada")
        self.assertFalse(block.check_hash())
        self.assertRaises(TypeError, Block(1, 2, 3, 4, 5))
        self.assertRaises(TypeError, Block([111, 12], 2, 3, 4, 5))
        self.assertRaises(TypeError, Block(1, 2, None, 4, 5))