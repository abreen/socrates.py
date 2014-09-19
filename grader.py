import sys
import os
import io
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

    out = io.StringIO()

    try:
        sprint("writing to '{}'".format(filename))
        _write_header(out, criteria)

        for f in criteria.files:
            out.write(heading("{} [{} points]".format(f, f.point_value),
                              level=2))

            if f not in found:
                total -= f.point_value
                out.write("-{}\tnot submitted\n".format(f.point_value))
            else:
                sprint("running tests")
                total -= _write_results(out, f.run_tests())

            out.write("\n")

        out.write("\nTotal: {}\n".format(total))

    except KeyboardInterrupt:
        sprint("\nstopping (received interrupt)")

        out.close()
        sys.exit(ERR_INTERRUPTED)

    except:
        e = sys.exc_info()[0]
        sprint("encountered an error while "
               "grading: {}".format(e), error=True)
        sprint("you might have to grade the old-fashioned "
               "way (sorry)")

        out.close()
        sys.exit(ERR_GRADING_MISC)


    with open(filename, 'w') as f:
        out.seek(0)
        f.write(out.read())

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
    if not results:
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
