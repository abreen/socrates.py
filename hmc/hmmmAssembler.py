#!/usr/remote/python-3.2/bin/python
#
# $Id: hmmmAssembler.py,v 1.4 2007/10/08 08:10:11 geoff Exp $
#
# hmmmAssembler.py
# Ran Libeskind-Hadas, 2006
# modified by Peter Mawhorter, June 2006
# Extensively modified by Geoff Kuenning, October 2007
# modified by Kaya Woodall, June 2012
#
# Converted to Python 3.2 by Dan Hyde, October 12, 2013
#   Ran 2to3 python 2 to python 3 convertor. 
#
# Moved into 'hmc' package by Alex Breen, October 13, 2014
# The main() function was also altered so that it should not
# take command line arguments or prompt the user.

import sys, string, re, textwrap
from hmc.binary import *

#
# opcodes encodes the preferred opcode translations.  Each entry is a
# triple: match, mask, translation.  If the binary word matches
# "match" under the mask, the translated opcode is given by that
# entry.  Blanks are ignored in the match and mask fields.  The table
# is order-dependent; the first match is used.  Note that at present
# the masks are either 0x0 or 0xF in each hex digit, although the code
# doesn't enforce that restriction.
#
# This table is shared directly between the assembler and simulator.
# The assembler doesn't use all the fields.
#
opcodes = (
        ("0000 0000 0000 0000", "1111 1111 1111 1111", "halt"),
        ("0000 0000 0000 0001", "1111 0000 1111 1111", "read"),
        ("0000 0000 0000 0010", "1111 0000 1111 1111", "write"),
        ("0000 0000 0000 0011", "1111 0000 1111 1111", "jumpi"),
        ("0001 0000 0000 0000", "1111 0000 0000 0000", "loadn"),
        ("0010 0000 0000 0000", "1111 0000 0000 0000", "load"),
        ("0011 0000 0000 0000", "1111 0000 0000 0000", "store"),
        ("0100 0000 0000 0000", "1111 0000 0000 1111", "loadi"),
        ("0100 0000 0000 0001", "1111 0000 0000 1111", "storei"),
        ("0101 0000 0000 0000", "1111 0000 0000 0000", "addn"),
        ("0110 0000 0000 0000", "1111 1111 1111 1111", "nop"),
        ("0110 0000 0000 0000", "1111 0000 0000 1111", "mov"),
        ("0110 0000 0000 0000", "1111 0000 0000 0000", "add"),
        ("0111 0000 0000 0000", "1111 0000 1111 0000", "neg"),
        ("0111 0000 0000 0000", "1111 0000 0000 0000", "sub"),
        ("1000 0000 0000 0000", "1111 0000 0000 0000", "mul"),
        ("1001 0000 0000 0000", "1111 0000 0000 0000", "div"),
        ("1010 0000 0000 0000", "1111 0000 0000 0000", "mod"),
        ("1011 0000 0000 0000", "1111 1111 0000 0000", "jump"),
        ("1011 0000 0000 0000", "1111 0000 0000 0000", "call"),
        ("1100 0000 0000 0000", "1111 0000 0000 0000", "jeqz"),
        ("1101 0000 0000 0000", "1111 0000 0000 0000", "jnez"),
        ("1110 0000 0000 0000", "1111 0000 0000 0000", "jgtz"),
        ("1111 0000 0000 0000", "1111 0000 0000 0000", "jltz"),
        ("0000 0000 0000 0000", "0000 0000 0000 0000", "data"),
        )

#Choose a dictionary to use: OldDict uses HMMM 2006-2011 (also internal language used within the assembler),
# NewDict uses HMMM 2012+ (added ~n, ~m, and ~r suffixes w/ aliases).

OldDict = {"halt":"halt", "read":"read", "write":"write", "nop":"nop",
           "loadn":"loadn", "addn":"addn", "mov":"mov", "add":"add",
           "sub":"sub", "neg":"neg", "mul":"mul", "div":"div", "mod":"mod",
           "jump":"jump", "jeqz":"jeqz", "jnez":"jnez",
           "jgtz":"jgtz", "jltz":"jltz", "call":"call", "jumpi":"jumpi",
           "load":"load", "store":"store", "loadi":"loadi", "storei":"storei"}

NewDict = {"halt":"halt", "read":"read", "write":"write", "nop":"nop",
           "setn":"loadn", "addn":"addn", "mov":"mov", "copy":"mov",
           "add":"add",
           "sub":"sub", "neg":"neg", "mul":"mul", "div":"div",
           "mod":"mod", "jumpn":"jump", "jeqz":"jeqz", "jeqzn":"jeqz",
           "jnez":"jnez", "jnezn":"jnez", "jgtz":"jgtz", "jgtzn":"jgtz",
           "jltz":"jltz", "jltzn":"jltz", "call":"call", "calln":"call",
           "jump":"jumpi", "jumpr":"jumpi", "loadn":"load", "storen":"store",
           "load":"loadi", "loadi":"loadi", "loadr":"loadi",
           "store":"storei", "storei":"storei", "storer":"storei"}
    

#
# The assembler would prefer a dictionary for the opcodes; that's not
# possible in the simulator because ordering matters.  Convert the
# above table into a dictionary that translates opcodes into encodings.
#
opcodeDict = {}
for i in range(len(opcodes)):
    opcodeDict[opcodes[i][2]] = opcodes[i][0]

registers = {"r0":"0000","r1":"0001","r2":"0010","r3":"0011","r4":"0100",
        "r5":"0101","r6":"0110","r7":"0111","r8":"1000","r9":"1001",
        "r10":"1010", "r11":"1011", "r12":"1100", "r13":"1101",
        "r14":"1110", "r15":"1111",
        "R0":"0000","R1":"0001","R2":"0010","R3":"0011","R4":"0100",
        "R5":"0101","R6":"0110","R7":"0111","R8":"1000","R9":"1001",
        "R10":"1010", "R11":"1011", "R12":"1100", "R13":"1101",
        "R14":"1110", "R15":"1111"}

#
# arguments encodes the required arguments for each operation.  "r"
# means a register; "s" means a signed 8-bit number in decimal; "u"
# means an unsigned 8-bit number in decimal, and "n" means a signed or
# unsigned 16-bit number in hex (0x notation) or decimal.  Actually,
# all numbers are accepted in all bases.
#
# In addition, "z" means insert four bits of zeros without swallowing
# an argument.
#
arguments = {"halt": "",
        "read": "r",
        "write": "r",
        "jumpi": "r",
        "loadn": "rs",
        "load": "ru",
        "store": "ru",
        "loadi": "rr",
        "storei": "rr",
        "addn": "rs",
        "add": "rrr",
        "mov": "rr",
        "nop": "",
        "sub": "rrr",
        "neg": "rzr",
        "mul": "rrr",
        "div": "rrr",
        "mod": "rrr",
        "jump": "zu",
        "call": "ru",
        "jeqz": "ru",
        "jgtz": "ru",
        "jltz": "ru",
        "jnez": "ru",
        "data": "n"}

#
# insertBits performs a logical "OR" on A and B
def insertBits(a, b):
    """Perform logical OR on a and b, preserving blanks in a.  Both a and
b must consist exclusively of blanks, 0s, and 1s."""
    if a == ''  or  b == '':
        return a
    elif a[0] == ' ':
        return ' ' + insertBits(a[1:], b)
    elif b[0] == ' ':
        return insertBits(a, b[1:])
    elif a[0] == '1'  or  b[0] == '1':
        return '1' + insertBits(a[1:], b[1:])
    else:
        return '0' + insertBits(a[1:], b[1:])

def translate (flds) :
    try :
            operation = flds[0]
            flds[0] = NewDict[operation] # Substitute OldDict here if using code written pre-2012.
            opval = opcodeDict[flds[0]]
    except KeyError :
        print("\nOPERATION ERROR:")
        print("'" + str(flds[0]), "' IS NOT A VALID OPERATION.")
        return "***OPERATION ERROR HERE***"
    encoding = opval
    extraBits = '0000'
    argsRequired = arguments[flds[0]]
    parts  = re.split(r'[,\s]+',flds[1].strip())    # split args into parts
    argc = len(parts)
    if argc == 1  and  parts[0] == '':
        argc = 0
        parts = []
    numArgsRequired = 0
    for i in argsRequired:
        if i != 'z':
            numArgsRequired += 1
    if argc != numArgsRequired:
        print("\nARGUMENT ERROR:")
        print("WRONG NUMBER OF ARGUMENTS.")
        print("DETECTED", argc, "ARGUMENTS, EXPECTED", \
          numArgsRequired, "ARGUMENTS.")
        print(flds[0], flds[1])
        return "***ARGUMENT ERROR HERE***"
    #print 'parts is', parts
    for p in parts :
        if p == '' :
            print("\nARGUMENT ERROR:")
            print("EMPTY ARGUMENT.")
            return "***ARGUMENT ERROR HERE***"

        arg = re.match(r'([Rr][0-9]+|-?[0-9]+|-|0[xX][0-9a-fA-F]+)$',p)
        if arg == None:
            print("\nARGUMENT ERROR:")
            print("'" + p + "' IS NEITHER A REGISTER NOR A NUMBER.")
            return "***ARGUMENT ERROR HERE***"
        code = argsRequired[0]
        argsRequired = argsRequired[1:]
        while code == 'z':
            extraBits += '0000'
            code = argsRequired[0]
            argsRequired = argsRequired[1:]
        if code == 'r':
            try:
                bits = registers[p]
            except KeyError:
                print("\nREGISTER ERROR:")
                print("'" + str(p) + "' IS NOT A VALID REGISTER.")
                return "***REGISTER ERROR HERE***"
            extraBits += bits
        elif p[0] == 'r'  or  p[0] == 'R':
            print("\nARGUMENT ERROR:")
            print("'" + str(p) + "' IS NOT A VALID NUMBER.")
            return "***ARGUMENT ERROR HERE***"
        else:
            #
            # We have already ensured that p is a valid number, so we
            # can just evaluate it here.
            #
            #value = eval(p)
            value = int(p)
            if code == 's':
                ok = -128 <= value <= 127
                width = 8
            elif code == 'u':
                ok = 0 <= value <= 255
                width = 8
            elif code == 'n':
                ok = -32768 <= value <= 65535
                width = 16
                extraBits = ''          # No padding in this case
            else:
                print("\nINTERNAL ERROR:")
                print("HMMMASSEMBLER ENCOUNTERED AN UNEXPECTED SITUATION.")
                return "***INTERNAL ERROR HERE***" 
            if not ok:
                print("\nARGUMENT ERROR:")
                print("'" + str(p) + "' IS OUT OF RANGE FOR THE ARGUMENT.")
                return "***ARGUMENT ERROR HERE***"
            extraBits += numToTwosComplement(value, width)

    return insertBits(encoding, extraBits)

def assemble (program) :
    output = []
    linenum = 0
    for line in program :
        # nasty regular expression to parse line number, instruction, and arguments
        if len(re.findall(r'^([0-9]+)[\s]+([a-z]+)[\s]*(([-r0-9xXa-fA-F]+[,\s]*)*)([\s]+(#.*)*)*$', line)) != 1 :
            print("\nSYNTAX ERROR ON LINE", str(linenum) + ":")
            print(line)
            output.append([linenum, "***SYNTAX ERROR HERE***", line])
            linenum += 1
            continue

        flds = re.sub(r'^([0-9]+)[\s]+([a-z]+)[\s]*(([-r0-9xXa-fA-F]+[,\s]*)*)([\s]+(#.*)*)*$', r'\1~\2~\3', line).split('~')



        if (not flds[0].isdigit()) :
            print("\nMISSING LINE NUMBER AT LINE", str(linenum) + ":")
            print("FOUND:", flds[0])
            output.append([linenum, "***MISSING LINE NUMBER HERE***", line])
            linenum += 1
            continue


        else:
            instruction = translate(flds[1:])
            triplet = [linenum, instruction, line]

            if (not instruction[0] == '*') and (not linenum == int(flds[0])) :
                print("\nBAD LINE NUMBER AT LINE", str(linenum) + ":")
                print("LINE NUMBER:", flds[0], "EXPECTED:", linenum)
                output.append([linenum, "***BAD LINE NUMBER HERE***", line])
                linenum += 1
                continue

            output.append(triplet)
            linenum += 1
    return output


def readfile(filename) :
    try:
            file = open(filename,"r")       # file with machine code
    except IOError:
        print("Cannot open file: ", filename)
        sys.exit()
    program = []
    while 1 :
        line = file.readline()
        if line == "" :         # End of file
            break       
        line = line.strip()     # Strip white space from front and end
        if line != ""   and  line[0] != '#' : # If it's not a comment...
            program.append(line) # ... then it's part of the program
    file.close()
    return program

def readstring(S) :
    program = []
    linesOfString = S.split("\n")
    for line in linesOfString:
        #print "line is", line
        if line == "" :         
            continue     
        line = line.strip()     # Strip white space from front and end
        if line != ""   and  line[0] != '#' : # If it's not a comment...
            program.append(line) # ... then it's part of the program
    return program

def writefile(machinecode, filename) :
    file = open(filename,"w")
    file.close

    print("\n" + "-"*22)
    print("| ASSEMBLY SUCCESSFUL |")
    print("-"*22 + "\n")

    nwidth = max([len(str(x[0])) for x in machinecode])
    for triplet in machinecode:
        print(textwrap.wrap((str(triplet[0])).ljust(nwidth) + " : " + (triplet[1]).ljust(27) + triplet[2], 76)[0])
        # wrap returns a list of strings limited in length
        # this should give a 76 character line
        file.write(triplet[1] + "\n")
    print("")

def main(inputname, outputname) :
    program = readstring(open(inputname, 'r').read())
    machinecode = assemble(program)

    # check whether there are any errors
    failure = 0
    for triplet in machinecode:
        if triplet[1][0] == '*':
            failure = 1

    if (not machinecode == []) and (not failure):
        writefile(machinecode, outputname)
        return True
    else:
        print("\n***** ASSEMBLY TERMINATED UNSUCCESSFULLY *****")
        print("              ASSEMBLY RESULTS:\n")
        try:
            nwidth = max([len(str(x[0])) for x in machinecode])
        except ValueError:
            print("                <EMPTY FILE>\n")
            return False
        for triplet in machinecode:
            print(textwrap.wrap((str(triplet[0])).ljust(nwidth) + " : " + (triplet[1]).ljust(31) + triplet[2], 76)[0])
            # wrap returns a list of strings limited in length
            # this should give a 76 character line
        print("")

        return False


# When this module is executed from the command line, as in "python filename.py"
# __name__ will be __main__, so main () will be executed.
# However, when this module is imported into the python environment __name__ will
# be something else, so main() will not be executed automatically
if __name__ == "__main__" : main () 

# Converted to Python 3.2 by Dan Hyde, October 12, 2013
#   Ran 2to3 python 2 to python 3 convertor.

# $Log: hmmmAssembler.py,v $
# Revision 1.5 2012/06/18 1:52:30 kaya
# Rewrote HMMM assembly code. New shortcuts can be found on the HMMM Directory page.
# Included dictionary so the program can be run in old or new mode, as internal commands
# remain unaltered. 
# 
# Revision 1.4  2007/10/08 08:10:11  geoff
# Add support for the neg instruction.  This required generalizing the
# "z" operand specifier.  Also get rid of the obsolete version of the
# opcodes table, which I neglected to delete earlier.
#
# Revision 1.3  2007/10/07 09:18:58  geoff
# Fix the masks on mov and data to correctly reflect the format of those
# two pseudo-operations.
#
# Revision 1.2  2007/10/07 07:47:14  geoff
# Major changes to improve the instruction architecture.  Unfortunately,
# as part of these changes I converted all tabs to blanks, so there are
# spurious diffs.  Modifications include:
#
# 1. Better table-driven encoding unified with simulator encoding tables.
# 2. Major rewrite of assembly code to use tables rather than if/elif.
#
