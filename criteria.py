import yaml
from datetime import datetime


class Criteria:
    """Represents requirements for student submissions."""

    def __init__(self, dict_):
        import filetypes

        self.name = dict_['name']
        self.due = datetime.strptime(dict_['due'], '%B %d, %Y %I:%M %p')

        self.files = []
        for f in dict_['files']:
            file_cls = filetypes.find_file_class(f['type'])
            self.files.append(file_cls(f))

        self.group = dict_['group']
        self.total_points = sum([f.point_value for f in self.files])


    @staticmethod
    def from_yaml(path):
        """Given a path to a .criteria.yml file, create and return a new
        Criteria object matching the specifications of the YAML file.
        """
        f = open(path, 'r')
        crit_dict = yaml.load(f)
        return Criteria(crit_dict)
