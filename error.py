"""error.py
File with function for printing given error and warning
informations in collor to stderr.
Author: Michal Šedý
Last change: 06.03.2021 - warning, error
             07.03.2021 - comments (warning, error)
             14.03.2021 - debugMsg, debugPrintAutomaton, debugPrintbackup
"""


import sys


def warning(functino, message):
    """Function print message into stderr. On the begin of a message the LightYellow
    text "WARNING" is printed. 

    Args:
        functino (string): Name of the function in which the warning raises.
        message (string): Warning message.
    """
    pass
    # WARNING = '\033[93m'
    # END = '\033[0m'
    # print(WARNING, end='', file=sys.stderr)
    # print("WARNING {0}: {1}".format(functino, message), end='', file=sys.stderr)
    # print(END, file=sys.stderr)


def error(function, message):
    """Functino print error message into stderr. On the begin of a message the Red
    text "ERROR" is printed.

    Args:
        function (string): Name of the function in which the error ocures.
        message (string): Error message.
    """
    ERROR = '\033[91m'
    END = '\033[0m'
    print(ERROR, end='', file=sys.stderr)
    print("ERROR {0}: {1}".format(function, message), end='', file=sys.stderr)
    print(END, file=sys.stderr)


def debugMsg(message):
    """Debuging function prints given mesage to stderr.

    Args:
        message (whatever): Debug mesage to print on stderr.
    """
    pass
    # print(message, file=sys.stderr)
    # print("="*60, file=sys.stderr)


def debugPrintAutomaton(automaton):
    """Debuging function prints automaton in comuputer form to stderr.

    Args:
        automaton (Nfa): Printed automaton.
    """
    pass
    # sys.stderr, sys.stdout = sys.stdout, sys.stderr
    # automaton.printRaw()
    # sys.stderr, sys.stdout = sys.stdout, sys.stderr
    # print("="*60, file=sys.stderr)


def debugPrintBackup(backup):
    """Debuging fuction prints content of a backup.

    Args:
        backup (Backup): Backup to print.
    """
    pass
    # print("="*60, file=sys.stderr)
    # print("States: {0}".format(backup.states), file=sys.stderr)
    # print("+"*30, file=sys.stderr)
    # print("Initiail: {0}".format(backup.initial), file=sys.stderr)
    # print("+"*30, file=sys.stderr)
    # print("Accepting: {0}".format(backup.accepting), file=sys.stderr)
    # print("+"*30, file=sys.stderr)
    # print("Trans: {0}".format(backup.trans), file=sys.stderr)
    # print("="*60, file=sys.stderr)


def printStats(message):
    """Function print message to stdout.

    Args:
        message (string): Message to print.
    """
    pass
    # print(message)