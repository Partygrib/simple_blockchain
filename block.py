import hashlib


class Block:
    def __init__(self, index, prev_hash, data, nonce, block_hash):
        self.index = index
        self.prev_hash = prev_hash
        self.data = data
        self.nonce = nonce
        self.hash = block_hash

    def check_hash(self):
        return hashlib.sha256((str(self.index) + self.prev_hash + self.data + str(self.nonce)).encode(
            'utf-8')).hexdigest() == self.hash

    def __str__(self):
        return "index = {} ; prev_hash = {} ; hash = {}".format(self.index, self.prev_hash, self.hash)