import copy
import hashlib
import random
import string
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from json import JSONDecodeError
import requests

from block import Block

lock = threading.RLock()


class Node:
    max_int = sys.maxsize
    difficult = "00000"
    neighbors = ["127.0.0.1:8081", "127.0.0.1:8082"]
    port = 8080
    stop = False
    nonce = 0

    def __init__(self, nonce_mode="0"):
        self.__chain = []
        self.mode = nonce_mode

    def next_nonce(self):
        if self.mode == "0":
            if self.nonce == self.max_int:
                self.nonce = - self.max_int
            else:
                self.nonce += 1
        elif self.mode == "1":
            if self.nonce == - self.max_int:
                self.nonce = self.max_int
            else:
                self.nonce -= 1
        else:
            self.nonce = random.randint(-self.max_int, self.max_int)

    def generate_block(self):
        prev_hash = ''
        index = 1
        with lock:
            if len(self.__chain) != 0:
                prev_hash = self.__chain[-1].hash
                index = self.__chain[-1].index + 1
            data = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(256))
            block_hash = hashlib.sha256((str(index) + prev_hash + data + str(self.nonce)).encode('utf-8')).hexdigest()
            while not block_hash.endswith(self.difficult) and not self.stop:
                self.next_nonce()
                block_hash = hashlib.sha256(
                    (str(index) + prev_hash + data + str(self.nonce)).encode('utf-8')).hexdigest()
            new_block = Block(index, prev_hash, data, self.nonce, block_hash)
            return new_block

    def add_block(self, block):
        with lock:
            if len(self.__chain) != 0:
                if self.__chain[-1].hash == block.prev_hash and self.__chain[-1].index + 1 == block.index:
                    self.__chain.append(block)
                    return True
                else:
                    return False
            elif block.index == 1:
                self.__chain.append(block)
                return True
            else:
                return False

    def check_block(self, block):
        with lock:
            if hashlib.sha256((str(block.index) + block.prev_hash + block.data + str(block.nonce)).encode(
                    'utf-8')).hexdigest() != block.hash or \
                    not block.hash.endswith(self.difficult):
                return False
            if block.index > 1:
                if len(self.__chain) > 0:
                    if block.index > len(self.__chain) + 1 or \
                            block.prev_hash != self.__chain[int(block.index) - 2].hash or \
                            block.index != self.__chain[int(block.index) - 2].index + 1:
                        return False
                else:
                    return False
            return True

    def add_block_with_check(self, block):
        with lock:
            if self.check_block(block):
                return self.add_block(block)
            return False

    def get_block_from_chain(self, index):
        if index < 1 or index > len(self.__chain):
            raise ValueError
        return self.__chain[index - 1]

    def send_index_req(self, link, json):
        try:
            requests.post(link, json=json)
        except Exception as e:
            print(e)

    def distribute(self, block):
        with ThreadPoolExecutor(max_workers=2) as executor:
            [executor.submit(self.send_index_req, "http://{}/add_block".format(neighbour),
                             json={"index": block.index, "port": self.port}) for neighbour in
             self.neighbors]

    def chain_build(self):
        while not self.stop:
            block = self.generate_block()
            res = self.add_block_with_check(block)
            if res:
                print("self generated: {}".format(block))
                distributor = threading.Thread(target=self.distribute, args=(block,))
                distributor.start()

    def fix_minority(self, index, s_ip, s_port):
        with lock:
            stack = []
            temp_index = index
            dump_chain = copy.deepcopy(self.__chain)
            while temp_index > 0:
                result = requests.get("http://{}:{}/get_block".format(s_ip, s_port), params={'index': temp_index})
                try:
                    block_data = result.json()
                except JSONDecodeError:
                    self.__chain = dump_chain
                    return False
                block = Block(block_data['index'], block_data['prev_hash'], block_data['hash'], block_data['data'],
                              block_data['nonce'])
                if not block.check_hash():
                    self.__chain = dump_chain
                    return False
                if block.index == len(self.__chain) + 1:
                    added = self.add_block_with_check(block)
                    if added:
                        print("fix minority: {}".format(block))
                        break
                    del self.__chain[-1]
                stack.append(block)
                temp_index -= 1

            while len(stack) > 0:
                block = stack.pop()
                added = self.add_block_with_check(block)
                if not added:
                    self.__chain = dump_chain
                    return False
                else:
                    print("fix minority: {}".format(block))

            if len(self.__chain) > len(dump_chain):
                return True
            else:
                self.__chain = dump_chain
                return False
