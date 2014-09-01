import sys
import os
import datetime

from util import *


def grade(criteria, submissions, filename):
    found = []
    total = criteria.total_points

    for s in submissions:
        directory, name = os.path.split(s)

        for f in criteria.files:
            d, n = os.path.split(f.path)

            if n == name:
                found.append(f)

    with open(filename, 'w') as out:
        sprint("writing to '{}'".format(filename))
        _write_header(out, criteria)

        for f in criteria.files:
            out.write(heading("{} [{} points]".format(f, f.point_value),
                              level=2))

            if f not in found:
                total -= f.point_value
                out.write("-{}\tnot submitted\n".format(f.point_value))
            else:
                total -= _write_results(out, f.run_tests())

            out.write("\n")

        out.write("\ntotal: {}\n".format(total))

    sprint("grading completed")


def _write_header(f, crit):
    f.write("Grade Report: {}\n".format(crit.assignment_name))
    f.write("{}\n".format(crit.course_name))

    today = datetime.date.today()
    day = today.strftime("%d")
    if day[0] == "0":
        day = day[1]
    f.write(today.strftime("%B {}, %Y".format(day)) + "\n\n")


def _write_results(f, results, indent='\t'):
    if len(results) == 0:
        return 0

    total = 0
    for r in results:
        desc = r['description']
        if 'deduction' in r:
            ded = r['deduction']
            total += ded
            f.write("-{}{}{}\n".format(ded, indent, desc))
        else:
            f.write("{}{}\n".format(indent, desc))

        if 'notes' in r and r['notes']:
            for n in r['notes']:
                f.write(indent + '\t' + n + '\n')

        if 'subresults' in r and r['subresults']:
            for subr in r['subresults']:
                total += _write_results(f, [subr], '\t' + indent)

    return total


if __name__ == '__main__':
    print("To start a grading session, run the 'socrates' module.")
