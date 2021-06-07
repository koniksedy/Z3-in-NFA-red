"""reduce.py
File with the main part, that controls the minimiazion of the given automaton.
Run as: python3 reduce.py imputAutomaton.ba iterationCnt [-noloop]
Author: Michal Šedý
Last change: 13.03.2021 - creation
"""
from algorithms import solverMinimization, transitionsCount
from parse import parseBa, parseTimbuk
import time
import sys


def timeMS():
    """Gives a count of miliseconds from 1.1.1970.

    Returns:
        int: Miliseconds form 1.1.1970
    """
    return round(time.time() * 1000)


def automatonToFile(automaton, fileName):
    """Print automatu in BA format to the file.

    Args:
        fileName (string): Output file
    """
    originalStdout = sys.stdout
    with open(fileName, "w") as fd:
        sys.stdout = fd
        automaton.printBa()
        sys.stdout = originalStdout


def main():
    """Main function. Parse automaton. Run minimization. Print results.
    Run as: python3 reduce.py imputAutomaton.ba eqLookAhead

    Raises:
        AttributeError: Program attribute is missing, or many attributes given.
    """
    sys.setrecursionlimit(10**5)
    # Control the count of the program arguments.
    if len(sys.argv) < 3 or len(sys.argv) > 3:
        raise AttributeError("Small or big count of program attributes.")
    
    automaton = parseBa(sys.argv[1])


    # Calculate automaton state befor minimization.
    statesCountBefore = len(automaton.states)
    transCountBefore = transitionsCount(automaton.forwardTrans)

    # Run minimization n-time and count duration.
    startTime = timeMS()
    automaton.cleanDeadStates()
    # automaton.makeCentralFinalState()
    solverMinimization(automaton, int(sys.argv[2]))
    automaton.cleanDeadStates()
    # Print automaton to file.
    automatonToFile(automaton, "{}-{}_solver.ba".format(sys.argv[1][:-3], sys.argv[2]))
    duration = timeMS() - startTime
    # Calculate automaton state after minimization.
    statesCountAfter = len(automaton.states)
    transCountAfter = transitionsCount(automaton.forwardTrans)

    # Print automaton states to stdout.

    print("Result automaton was save as {}-{}_solver.ba".format(sys.argv[1][:-3], sys.argv[2]))
    print("States before: {}".format(statesCountBefore))
    print("States after: {}".format(statesCountAfter))
    print("Transitions before: {}".format(transCountBefore))
    print("Transitions after: {}".format(transCountAfter))
    print("Time: {} ms".format(duration))


if __name__ == '__main__':
    main()
