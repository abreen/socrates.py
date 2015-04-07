class BaseTest:
    # the test's type from the YAML file (e.g., 'review')
    yaml_type = None

    def __init__(self, dict_, file_type=None):
        if 'description' in dict_:
            self.description = dict_['description'].strip()
        else:
            self.description = None

        if 'deduction' in dict_:
            self.deduction = dict_['deduction']
        else:
            self.deduction = None


    # note: when implemented, this method should return a dict
    # with (at least) 'deduction', 'description', and 'notes' keys,
    # or None if the test did not fail
    def run(self):
        raise NotImplementedError()


    def __str__(self):
        return "'{}' test of".format(self.yaml_type)
