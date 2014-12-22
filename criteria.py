import yaml
from datetime import datetime

DATE_FORMAT = '%B %d, %Y %I:%M %p'

class Criteria:
    """Represents requirements for student submissions."""

    def __init__(self, dict_):
        import filetypes

        self.name = dict_['name']

        # note: self.due is a list of (datetime object, multiplier)
        self.due = []
        for multiplier, date in dict_['due'].items():
            dt = datetime.strptime(date, DATE_FORMAT)
            self.due.append((multiplier, dt))

        self.due.sort()

        self.files = []
        for f in dict_['files']:
            file_cls = filetypes.find_file_class(f['type'])
            self.files.append(file_cls(f))

        self.group = dict_['group']
        self.total_points = sum([f.point_value for f in self.files])


    def get_late_penalty(self, mdate):
        """Given a datetime object representing the date and time that
        a file was last modified, return the deduction multiplier
        (e.g., 0.10 for a 10% late penalty).
        """
        m = 0.0
        for multiplier, date in self.due:
            if mdate > date:
                m = multiplier
            else:
                break

        return m


    @staticmethod
    def from_yaml(path):
        """Given a path to a .criteria.yml file, create and return a new
        Criteria object matching the specifications of the YAML file.
        """
        f = open(path, 'r')
        crit_dict = yaml.load(f)
        return Criteria(crit_dict)
