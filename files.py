"""Tools to encode Criteria objects into JSON files and back."""

import json
import criteria

_ALLOWED_CHARS = '-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def generate(path):
    """Given a path to a Python file, create a new Criteria object based on
    the Python file, requiring the existence of any and all functions in the
    Python file. All point values are initialized to zero and no tests are
    added.
    """

    import inspect
    import os

    py_file = os.path.split(path)[1]

    if '.py' in py_file:
        module_name = py_file[:py_file.index('.py')]
    else:
        module_name = py_file


    solution = __import__(module_name)

    crit = criteria.Criteria(module_name)

    em = criteria.ExpectedModule(module_name)

    for f in inspect.getmembers(solution, inspect.isfunction):
        func_name = f[0]

        sig = inspect.signature(f[1])
        param_names = [p for p in sig.parameters]

        ef = criteria.ExpectedFunction(func_name, param_names)
        em.add_function(ef)

    crit.modules.append(em)

    return crit



def to_json(crit, filename=None):
    """Writes a .criteria.json file containing the contents of the specified
    Criteria object, returning the name of the new file.
    """

    if not filename:
        safe_name = ''.join([c for c in crit.assignment_name if c in _ALLOWED_CHARS])
        filename = safe_name + ".criteria.json"

    f = open(filename, 'w')
    json.dump(crit, f, indent=4, cls=SocratesEncoder)

    return filename



def from_json(path):
    """Given a path to a .criteria.json file, create and return a new Criteria
    object matching the specifications of the JSON file.
    """

    if not path:
        raise ValueError("invalid path specified")

    f = open(path, 'r')
    crit_dict = json.load(f)
    return _from_dict(crit_dict)



def _from_dict(d):
    """Given a dict (the result of a JSON decode), create and return a new
    Criteria object with the contents of the dict.
    """

    crit = criteria.Criteria(d['assignment_name'])
    crit.total_points = d['total_points']

    for m in d['modules']:
        em = criteria.ExpectedModule(m['module_name'])

        for f in m['required_functions']:
            fname = f['function_name']
            params = f['formal_parameters']
            points = f['point_value']

            func = criteria.ExpectedFunction(fname, params, points)

            em.add_function(func)

        for t in m['tests']:
            test = criteria.Test(test_type=t['type'],
                                 target=t['target'],
                                 name=t['name'],
                                 args=t['arguments'] if 'arguments' in t else None,
                                 expected=t['expected'] if 'expected' in t else None,
                                 deduction=t['deduction'] if 'deduction' in t else None,
                                 desc=t['description'] if 'description' in t else None)

            em.add_test(test)


        crit.add_module(em)

    return crit



class SocratesEncoder(json.JSONEncoder):

    def default(self, obj):
        if type(obj) is not criteria.Criteria:
            raise ValueError()

        crit_dict = { 'assignment_name': obj.assignment_name,
                      'point_total': 0,
                      'modules': [] }

        for m in obj.modules:
            mod_dict = { 'module_name': m.module_name,
                         'required_functions': [] }

            for f in m.required_functions:
                func_dict = { 'function_name': f.function_name,
                              'formal_parameters': f.parameters,
                              'point_value': 0 }

                mod_dict['required_functions'].append(func_dict)

            crit_dict['modules'].append(mod_dict)


        return crit_dict
