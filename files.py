"""Tools to encode Criteria objects into JSON files and back."""

import json
import os

from util import *
from criteria import *


def module_name_from_path(path):
    py_file = os.path.split(path)[1]

    if '.py' in py_file:
        module_name = py_file[:py_file.index('.py')]
    else:
        module_name = py_file

    return module_name



def generate(path):
    """Given a path to a Python file, create a new Criteria object based on
    the Python file, requiring the presence of all functions in the Python
    module. All point values are initialized to zero and no tests are added.
    """

    import inspect

    module_name = module_name_from_path(path)

    solution = __import__(module_name)

    crit = Criteria(assignment_name="assignment based on " + module_name,
                    short_name=module_name,
                    total_points=0)

    m = Module(module_name=module_name)

    for f in inspect.getmembers(solution, inspect.isfunction):
        func_name = f[0]

        sig = inspect.signature(f[1])
        param_names = [p for p in sig.parameters]

        f_obj = Function(function_name=func_name,
                         parameters=param_names,
                         point_value=0)
        m.add_function(f_obj)

    crit.modules.append(m)

    return crit



def to_json(crit):
    """Writes a .criteria.json file containing the contents of the specified
    Criteria object, returning the name of the new file.
    """

    filename = crit.short_name + ".criteria.json"

    f = open(filename, 'w')
    json.dump(crit, f, indent=4, cls=SocratesEncoder)

    return filename



def from_json(path):
    """Given a path to a .criteria.json file, create and return a new Criteria
    object matching the specifications of the JSON file.
    """

    f = open(path, 'r')
    crit_dict = json.load(f)
    return _from_dict(crit_dict)



def _from_dict(d):
    """Given a dict (the result of a JSON decode), create and return a new
    Criteria object with the contents of the dict.
    """

    crit = Criteria(assignment_name=d['assignment_name'],
                    short_name=d['short_name'],
                    total_points=d['total_points'])

    for m in d['modules']:
        m_obj = Module(module_name=m['module_name'])

        # add required functions
        for f in m['functions']:
            f_obj = Function(function_name=f['function_name'],
                             parameters=f['parameters'],
                             point_value=f['point_value'])

            # add function-level tests
            if 'tests' in f:
                for func_test in f['tests']:
                    f_obj.add_test(Test.from_dict(func_test, f_obj))

            m_obj.add_function(f_obj)

        # add module-level tests
        if 'tests' in m:
            for mod_test in m['tests']:
                m_obj.add_test(Test.from_dict(mod_test, m_obj))

        crit.add_module(m_obj)

    return crit



class SocratesEncoder(json.JSONEncoder):

    def default(self, obj):
        if type(obj) is not Criteria:
            raise ValueError()

        # see Criteria.to_dict
        return obj.to_dict()