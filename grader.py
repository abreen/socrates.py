import sys
import os
import io
import datetime

import util
from prompt import prompt


def grade(criteria, submissions, filename,
          assume_missing=False, late_check=True):
    found = []
    num_missing = 0
    total = criteria.total_points

    for f in criteria.files:
        crit_dir, crit_name = os.path.split(f.path)

        for s in submissions:
            sub_dir, sub_name = os.path.split(s)

            if crit_name == sub_name:
                found.append(f)
                break
        else:

            util.warning("could not find file '{}'".format(f.path))

            if len(submissions) < 1:
                continue

            if not assume_missing:
                # find the submission directory (it could be the
                # current working directory, but maybe not)
                submission_dir, _ = os.path.split(submissions[0])

                if not submission_dir:
                    submission_dir = os.path.abspath(os.curdir)

                choices = [f for f in os.listdir(submission_dir)
                           if os.path.isfile(os.path.join(submission_dir, f))]
                choices.append("skip grading this submission now")
                choices.append("mark the file as missing")

                util.info("this student may have named the file incorrectly")

                # we prompt the grader for zero or one choice
                got = prompt(choices, '1')
                got = got[0]

                if got == len(choices) - 1:
                    # declare the file missing
                    num_missing += 1
                    continue

                elif got == len(choices) - 2:
                    util.info("skipping this submission")
                    util.exit(util.EXIT_WITH_DEFER)

                else:
                    # get absolute path to the old and new files
                    sname = choices[got]

                    opath = os.path.join(submission_dir, sname)
                    npath = os.path.join(submission_dir, crit_name)

                    try:
                        os.rename(opath, npath)
                    except:
                        util.error("error renaming incorrectly named file")
                        util.print_traceback()
                        util.exit(util.ERR_GRADING_MISC)

                    found.append(f)

    out = io.StringIO()

    try:
        for f in criteria.files:
            out.write(util.heading("{} [{} points]".format(f, f.point_value),
                                   level=2))

            if f not in found:
                total -= f.point_value
                out.write("-{}\tnot submitted\n".format(f.point_value))
                out.write("\n\n")
                continue

            util.info("running tests for " + str(f))

            points_taken = 0
            points_taken += write_results(out, f.run_tests())

            if late_check:
                file_stat = os.stat(f.path)
                mtime = datetime.datetime.fromtimestamp(file_stat.st_mtime)

                mult = criteria.get_late_penalty(mtime)
                late_penalty = f.point_value * mult

                if late_penalty != 0:
                    util.warning("taking {}% late penalty".format(mult * 100))

                    adjusted = min(f.point_value - points_taken, late_penalty)
                    out.write("-{}\tsubmitted late\n".format(adjusted))
                    points_taken += adjusted

            total -= min(f.point_value, points_taken)

            out.write("\n")

        out.write("\nTotal: {}\n".format(total))

    except KeyboardInterrupt:
        out.close()

        util.warning("stopping (received interrupt)")
        util.exit(util.ERR_INTERRUPTED)

    except:
        out.close()

        util.exit(util.ERR_GRADING_MISC)

    with open(filename, 'w') as f:
        out.seek(0)
        f.write(out.read())

    return num_missing


def write_results(f, results, indent='\t'):
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
                total += write_results(f, [subr], '\t' + indent)

        f.write("\n")

    return total


if __name__ == '__main__':
    print("To start a grading session, run the 'socrates' module.")
