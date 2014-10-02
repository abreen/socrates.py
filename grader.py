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
            #Informing grader, gathering input filename
            sprint(COLOR_YELLOW + "could not find "
                   "file '{}'".format(f.path) + COLOR_RESET)

            if len(submissions) < 1:
                continue

            cur_dir = os.path.abspath(os.path.split(submissions[0])[0])            
            sprint(COLOR_YELLOW + "listing submissions..." + COLOR_RESET)
            sprint(COLOR_GREEN + " ".join(submissions) + COLOR_RESET)
            sname = input(COLOR_CYAN + "Enter a file to grade, 0 to declare file missing, -1 to skip this submission: " + COLOR_RESET)

            if sname == '0':
                num_missing += 1
                continue
            elif sname == '-1':
                sprint("Deferring submission.")
                sys.exit(EXIT_WITH_DEFER)
            else:
                #get absolute path to the old and new files
                opath = os.path.join(cur_dir,sname)
                npath = os.path.join(cur_dir,crit_name)
                
                try:
                    ofile = open(opath,'r')
                    nfile = open(npath,'w')
                except FileNotFoundError:
                    sprint("Could not open the specified file", error=True)
                    sys.exit(ERR_GRADING_MISC)

                try:    
                    shutil.copyfileobj(ofile,nfile)
                except (IOerror,os.error):
                    sprint("Could not copy the data to the new file", error=True)
                    sys.exit(ERR_GRADING_MISC)
                
                ofile.close()
                nfile.close()
                
                #copy file stat for use in late penalty checking
                try:
                    shutil.copystat(opath,npath)
                except os.error:
                    sprint("Could not copy the file stat to the new file", error=True)
                    sys.exit(ERR_GRADING_MISC)
                    
                found.append(f)

    out = io.StringIO()

    try:
        _write_header(out, criteria)

        for f in criteria.files:
            out.write(heading("{} [{} points]".format(f, f.point_value),
                              level=2))

            if f not in found:
                total -= f.point_value
                out.write("-{}\tnot submitted\n".format(f.point_value))
            else:
                sprint("running tests for " + str(f))
                deduction_total = _write_results(out, f.run_tests())
                total -= min(f.point_value, deduction_total)

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
