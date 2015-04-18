# demonstration script for writing custom tests

# any imports are allowed
from os import listdir

# also note: the student's module is automatically given
# to this script's globals, so no import is needed --- just
# use the module's contents as if a simple "import <module>"
# was already done

# after this script runs, socrates will inspect this variable
# for a deduction dictionary
_socrates_result = None

print("Hello, world!")
print(str(listdir()))

if False:
    # do the following to tell socrates to take a deduction
    _socrates_result = {}
    _socrates_result['deduction'] = 4           # points to deduct
    _socrates_result['description'] = "doesn't work"
