import threading
import time
import unittest

from node import Node


class NodeTests(unittest.TestCase):

    def testNextNonce(self):
        node = Node()
        node.mode = "0"
        node.nonce = node.max_int
        node.next_nonce()
        self.assertTrue(- node.max_int == node.nonce)
        node.mode = "1"
        node.nonce = - node.max_int
        node.next_nonce()
        self.assertTrue(node.max_int == node.nonce)
        node.mode = "3"
        node.next_nonce()
        self.assertTrue(-node.max_int <= node.nonce <= node.max_int)

    def testGenerateBlock(self):
        node = Node()
        for i in range(0, 5):
            block = node.generate_block()
            self.assertTrue(block.check_hash())
            self.assertTrue(block.index == node.get_last_index() + 1)
            self.assertTrue(node.check_block(block))

    def testAddBlock(self):
        node = Node()
        for i in range(0, 5):
            block = node.generate_block()
            self.assertTrue(node.add_block(block))
        block = node.generate_block()
        block.index += 1
        self.assertFalse(node.add_block(block))
        block.index -= 2
        self.assertFalse(node.add_block(block))
        block.index += 1
        block.prev_hash = "1"
        self.assertFalse(node.add_block(block))

    def testCheckBlock(self):
        node = Node()
        for i in range(0, 5):
            block = node.generate_block()
            self.assertTrue(node.check_block(block))
            if i % 2 == 1:
                self.assertTrue(node.add_block(block))
        block = node.generate_block()
        block.data += "a"
        self.assertFalse(node.check_block(block))
        block = node.generate_block()
        block.hash += "a"
        self.assertFalse(node.check_block(block))
        block = node.generate_block()
        block.prev_hash += "1"
        self.assertFalse(node.check_block(block))
        block = node.generate_block()
        block.nonce += 1
        self.assertFalse(node.check_block(block))
        block.nonce -= 0.9
        self.assertFalse(node.check_block(block))
        node.stop = True
        block = node.generate_block()
        self.assertFalse(node.check_block(block))

    def testAddBlockWithCheck(self):
        node = Node()
        for i in range(0, 5):
            block = node.generate_block()
            self.assertTrue(node.add_block_with_check(block))
        block = node.generate_block()
        block.data += "a"
        self.assertFalse(node.add_block_with_check(block))
        block = node.generate_block()
        block.hash += "a"
        self.assertFalse(node.add_block_with_check(block))
        block = node.generate_block()
        block.prev_hash += "1"
        self.assertFalse(node.add_block_with_check(block))
        block = node.generate_block()
        block.nonce += 1
        self.assertFalse(node.add_block_with_check(block))
        block.nonce -= 0.9
        self.assertFalse(node.add_block_with_check(block))
        node.stop = True
        block = node.generate_block()
        self.assertFalse(node.add_block_with_check(block))

    def testGetBlock(self):
        node = Node()
        self.assertRaises(ValueError, node.get_block_from_chain, 2)
        self.assertRaises(ValueError, node.get_block_from_chain, 1)
        self.assertRaises(ValueError, node.get_block_from_chain, 0)
        self.assertRaises(ValueError, node.get_block_from_chain, -1)
        blocks = []
        for i in range(0, 5):
            blocks.append(node.generate_block())
            node.add_block(blocks[i])
        for i in range(0, 5):
            self.assertTrue(node.get_block_from_chain(i + 1) == blocks[i])

    def testChainBuild(self):
        node = Node()
        t = threading.Thread(target=node.chain_build)
        t.start()
        self.assertTrue(t.is_alive())
        time.sleep(10)
        self.assertTrue(node.get_last_index() > 0)
        node.stop = True
        t.join()
        self.assertFalse(t.is_alive())