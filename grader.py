import sys
import os
import io
import datetime
import shutil

from util import *


def grade(criteria, submissions, filename):
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
            # in the case that the file is missing, we should prompt
            # the grader to pick the incorrect file name or declare
            # the file missing

            sprint(COLOR_YELLOW + "could not find "
                   "file '{}'".format(f.path) + COLOR_RESET)

            if len(submissions) < 1:
                continue

            # find the submission directory (it could be the
            # current working directory, but maybe not)
            submission_dir, _ = os.path.split(submissions[0])

            if not submission_dir:
                submission_dir = os.path.abspath(os.curdir)

            sprint("files in submission directory:")
            for s in submissions:
                print(s)

            sprint(COLOR_CYAN + "did the student name the file "
                   "incorrectly?" + COLOR_RESET)
            sname = input(COLOR_CYAN + "enter a file name, 0 to "
                          "declare file missing, or -1 to skip this "
                          "submission: " + COLOR_RESET)

            if sname == '0':
                num_missing += 1
                continue

            elif sname == '-1':
                sprint("deferring submission; no grade file written")
                sys.exit(EXIT_WITH_DEFER)

            else:
                # get absolute path to the old and new files
                opath = os.path.join(submission_dir, sname)
                npath = os.path.join(submission_dir, crit_name)

                try:
                    ofile = open(opath, 'r')
                    nfile = open(npath, 'w')
                except FileNotFoundError:
                    sprint("could not open the correct file", error=True)
                    sys.exit(ERR_GRADING_MISC)

                try:
                    shutil.copyfileobj(ofile, nfile)
                except:
                    sprint("error copying to correct file", error=True)
                    sys.exit(ERR_GRADING_MISC)

                ofile.close()
                nfile.close()

                # to preserve the modification time of the submission
                # and not mess up late penalty checking, we'll copy
                # the file data into the new file
                try:
                    shutil.copystat(opath, npath)
                except:
                    sprint("error copying stat to correct file", error=True)
                    sys.exit(ERR_GRADING_MISC)

                found.append(f)

    out = io.StringIO()

    try:
        for f in criteria.files:
            out.write(heading("{} [{} points]".format(f, f.point_value),
                              level=2))

            if f not in found:
                total -= f.point_value
                out.write("-{}\tnot submitted\n".format(f.point_value))
                continue

            sprint("running tests for " + str(f))

            points_taken = 0
            points_taken += _write_results(out, f.run_tests())

            file_stat = os.stat(f.path)
            mtime = datetime.datetime.fromtimestamp(file_stat.st_mtime)

            if mtime > criteria.due:
                if mtime > criteria.due + datetime.timedelta(hours=24):
                    sprint(COLOR_YELLOW + "taking all points for >24-hour "
                           "late-submitted {}".format(f) + COLOR_RESET)

                    late_penalty = f.point_value
                    out.write("-{}\tsubmitted >24 hours "
                              "late\n".format(late_penalty))

                else:
                    sprint(COLOR_YELLOW + "taking 10% penalty for "
                           "late-submitted {}".format(f) + COLOR_RESET)

                    late_penalty = f.point_value * 0.10
                    out.write("-{}\tsubmitted late\n".format(late_penalty))

                points_taken += late_penalty

            total -= min(f.point_value, points_taken)

            out.write("\n")

        out.write("\nTotal: {}\n".format(total))

    except KeyboardInterrupt:
        sprint("\nstopping (received interrupt)")

        out.close()
        sys.exit(ERR_INTERRUPTED)

    except:
        import traceback

        err = sys.exc_info()
        sprint("encountered an error while "
               "grading: {}".format(err[0].__name__), error=True)
        traceback.print_exc()
        sprint("you might have to grade the old-fashioned "
               "way (sorry)")

        out.close()
        sys.exit(ERR_GRADING_MISC)


    with open(filename, 'w') as f:
        out.seek(0)
        f.write(out.read())

    sprint("grading completed")
    return num_missing


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
