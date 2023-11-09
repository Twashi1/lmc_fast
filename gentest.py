import random
import time

# TODO: test this actually works as intended
random.seed(time.time())

MAX_INSTRUCTIONS = 50_000
TEST_CASES = 10_000

def mean(a, b, c):
    return (a + b + c) // 3

with open("cases.txt", "w+") as f:
    for i in range(TEST_CASES):
        a = random.randint(0, 999)
        b = random.randint(0, 999)
        c = random.randint(0, 999)
        f.write(f"{i};{a};{b};{c};{mean(a, b, c)};{MAX_INSTRUCTIONS}\n")