# ps0.py
# A flawed solution to a problem set from an introductory CS course.

PI = 3.149999

def hello():
    print("Hello, world! ")


def meet():
    name = input("What's your name? ")
    print("Nice to meet you, " + name + "!")


def greetings(name):
    print("Greetings, " + name + "!")


#def my_add(a, b):
#    return a + b


def my_mult(a, b):
    return a * b


def double(x):
    if x == 0:
        return 1

    return x * 2


def series_sum(x):
    if x <= 1:
        return 0

    return x + series_sum(x - 1)
