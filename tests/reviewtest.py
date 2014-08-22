import inspect

from tests import basetest


class ReviewTest(basetest.BaseTest):
    handles_type = 'review'

    def __init__(self, target, description, deduction):
        super().__init__(target, description, deduction)


    def __str__(self):
        return "review of {}: {} ({} points)".format(self.target,
                                                     self.description,
                                                     self.deduction)


    def to_dict(self):
        test_dict = {'type': self.handles_type,
                     'description': self.description,
                     'deduction': self.deduction}

        return test_dict


    @staticmethod
    def from_dict(dict_obj, test_target):
        if not test_target:
            raise ValueError("the target of this test must be specified")

        args = {'target': test_target,
                'description': dict_obj['description'],
                'deduction': dict_obj['deduction']}

        return ReviewTest(**args)


    def run_test(self, actual_target, context):
        """Perform a 'review' test by acquring the source code of the function
        or module and printing it. The context is not used. A human is asked
        to confirm the deduction.
        """

        print(inspect.getsource(actual_target))
        print("Deduction description: {}".format(self.description))
        print("Deduction value: {}".format(self.deduction))

        while True:
            ans = input("Should this deduction be taken (y/n)? ")

            if ans in ['y', 'n', 'yes', 'no']:
                break

        if ans == 'y' or ans == 'yes':
            # the deduction *should* be taken, therefore this test fails
            return False
        else:
            # the deduction *should not* be taken, therefore this test passes
            return True

