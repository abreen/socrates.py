import yaml
from datetime import datetime, timedelta

from util import warn
import filetypes
import config

DATE_FORMAT = '%B %d, %Y %I:%M %p'


class Criteria:
    """Represents requirements for student submissions."""

    def __init__(self, dict_):
        self.name = dict_['name']
        self.group = dict_['group']

        due = []
        for multiplier, date in dict_['due'].items():
            due_date_obj = datetime.strptime(date, DATE_FORMAT)
            due.append((multiplier, due_date_obj))

        self.due = due

        files = []
        for file_dict in dict_['files']:
            file_cls = filetypes.find_file_class(file_dict['type'])
            files.append(file_cls(file_dict))

        self.files = files

        self.total_points = sum([f.point_value for f in self.files])


    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        if type(new_name) is not str or len(new_name) == 0:
            raise ValueError("invalid criteria name")

        self._name = new_name

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, new_group):
        if type(new_group) is not str or len(new_group) == 0:
            raise ValueError("invalid group")

        self._group = new_group

    @property
    def total_points(self):
        return self._total_points

    @total_points.setter
    def total_points(self, new_points):
        if type(new_points) is not int:
            raise ValueError("invalid total points value")

        self._total_points = new_points

    @property
    def due(self):
        return self._due

    @due.setter
    def due(self, new_dict):
        if len(new_dict) == 0:
            raise ValueError("must have at least one due date")

        def valid_tuple(a):
            return type(a) is tuple and \
                   len(a) == 2 and \
                   type(a[1]) is datetime and \
                   (type(a[0]) is int or type(a[0]) is float)

        if not all(map(valid_tuple, new_dict)):
            raise ValueError("invalid due date tuples")

        self._due = sorted(new_dict)

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, new_files):
        if len(new_files) == 0:
            warn("warning: criteria contains no files")

        def valid_file(f):
            return isinstance(f, filetypes.basefile.BaseFile)

        if not all(map(valid_file, new_files)):
            raise ValueError("invalid files: not subclasses of BaseFile")

        self._files = new_files


    def get_late_penalty(self, mdate):
        """Given a datetime object representing the date and time that
        a file was last modified, return the deduction multiplier
        (e.g., 0.10 for a 10 percent late penalty). This method takes
        into account the grace period (config.grace_period).
        """
        mult = 0.0
        for multiplier, date in self.due:
            if mdate > date + config.grace_period:
                mult = multiplier
            else:
                break

        return mult


    @staticmethod
    def from_yaml(path):
        """Given a path to a .criteria.yml file, create and return a new
        Criteria object matching the specifications of the YAML file.
        """
        file = open(path, 'r')
        crit_dict = yaml.load(file)
        return Criteria(crit_dict)
