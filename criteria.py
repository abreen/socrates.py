import yaml
from datetime import datetime, timedelta
import util
import config

DATE_FORMAT = '%B %d, %Y %I:%M %p'


class Criteria:
    """Represents requirements for student submissions."""

    def __init__(self, dict_):
        import filetypes

        try:
            self.name = dict_['name']

            # note: self.due is a list of (datetime object, multiplier)
            self.due = []
            for multiplier, date in dict_['due'].items():
                due_date_obj = datetime.strptime(date, DATE_FORMAT)
                self.due.append((multiplier, due_date_obj))

            self.due.sort()

            self.files = []
            for file_dict in dict_['files']:
                file_cls = filetypes.find_file_class(file_dict['type'])
                # call the constructor of the right class with this part of the dict
                self.files.append(file_cls(file_dict))

            self.group = dict_['group']
            self.total_points = sum([f.point_value for f in self.files])

        except KeyError as e:
            raise IncompleteCriteriaError("criteria missing attribute: "
                                          "{}".format(e))


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



class IncompleteCriteriaError(Exception):
    pass
