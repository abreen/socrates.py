import json


class Criteria:
    """Represents requirements for student submissions."""

    def __init__(self, assignment_name, short_name, course_name,
                 files, group=None):
        self.assignment_name = assignment_name      # nice name ("PS 0")
        self.short_name = short_name                # safe for filename ("ps0")
        self.course_name = course_name
        self.files = files
        self.group = group                          # grading group

        self.total_points = sum([f.point_value for f in self.files])


    def __str__(self):
        return "criteria for {}".format(self.assignment_name)


    def to_dict(self):
        return {'assignment_name': self.assignment_name,
                'short_name': self.short_name,
                'course_name': self.course_name,
                'files': [f.to_dict() for f in self.files]}


    def to_json(self):
        filename = self.short_name + ".criteria.json"

        f = open(filename, 'w')
        json.dump(self, f, indent=4, cls=SocratesEncoder)


    @staticmethod
    def from_json(path):
        """Given a path to a .criteria.json file, create and return a new Criteria
        object matching the specifications of the JSON file.
        """
        f = open(path, 'r')
        crit_dict = json.load(f)
        return Criteria.from_dict(crit_dict)


    @staticmethod
    def from_dict(d):
        """Given a dict (the result of a JSON decode), create and return a new
        Criteria object with the contents of the dict.
        """
        import filetypes

        args = {'assignment_name': d['assignment_name'],
                'short_name': d['short_name'],
                'course_name': d['course_name'],
                'files': []}

        for f in d['files']:
            file_cls = filetypes.find_file_class(f['type'])
            args['files'].append(file_cls.from_dict(f))

        if 'group' in d:
            args['group'] = d['group']

        return Criteria(**args)



class SocratesEncoder(json.JSONEncoder):
    def default(self, obj):
        # see Criteria.to_dict
        return obj.to_dict()
