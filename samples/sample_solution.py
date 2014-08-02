# sample_solution.py
# A simple solution to a problem set from an introductory CS course.

def hello():
    print("Hello, world!")


def greetings(name):
    print("Greetings, " + name + "!")


def my_add(a, b):
    return a + b


def my_mult(a, b):
    return a * b


def double(x):
    return x * 2


def series_sum(x):
    if x <= 0:
        return 0

    return x + series_sum(x - 1)
