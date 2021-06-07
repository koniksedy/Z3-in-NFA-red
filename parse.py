"""parse.py
File with algorithms for parsing Timbuk and Ba NFA.
Author: Michal Šedý
Last change: 20.02.2021 - creation
             21.02.2021 - Timbuk and Ba parser done
             23.02.2021 - If initial or accepting state is added,
                          we must allso add new state into automaton.states
             08.03.2021 - The parsing bug repaired. REMEMBER: re.search returns group.
                          Index 0 belong to input string, first matched result is
                          on the intex 1.

"""

import nfa
import re


def parseTimbuk(fileName):
    """Function for parsing the automaton in Timbuk format.

    Timbuk format:
    Ops a0:1 a1:1 x:0
    Automaton A
    States q0 q1 q2 q3 
    Final States q3 
    Transitions
    x -> q0
    a0(q0) -> q1
    a1(q0) -> q2
    a1(q1) -> q3
    a1(q2) -> q3

    Args:
        fileName (string): name of the file with the automaton 
                           Timbuk format to parse

    Returns:
        automaton: parsed automaton
    """

    fh = open(fileName, 'r')
    automaton = nfa.Nfa()

    # Parse all file line by line.
    while True:
        # Read next line and check if exists.
        line = fh.readline()
        if not line:
            break
        
        # Delete white space on the right.
        # The deletion can not be done above, because the empty line
        # would cause end of parsing. (It should looks as the end of a file.)
        line = line.rstrip()
        
        if re.fullmatch(r"\w+(\(\))?[ ]*\->[ ]*\w+", line) is not None:
            # Finding initial state "x -> q0"
            newState = re.search(r"\w+(\(\))?[ ]*\->[ ]*(\w+)", line).group(2)
            automaton.initialStates.add(newState)
            automaton.states.add(newState)

        elif re.fullmatch(r"\w+\(\w+\)[ ]*\->[ ]*\w+", line) is not None:
            # Finding transition "a(q0) -> q1"
            result = re.search(r"(\w+)\((\w+)\)[ ]*\->[ ]*(\w+)", line)
            # Create new transition (add new states if not exists yet, in function).
            automaton.addTransition(result.group(2), result.group(3), result.group(1))
        
        else:
            # It is not transition. Check for final (accepting) states.        
            # Split line by space and check if it is not empty line.
            words = line.split()
            if not words:
                continue
   
            # Find "Final States f1 f2 ..."
            if words[0] == "Final": 
                automaton.acceptingStates.update(words[2:])
                automaton.states.update(words[2:])
    
    fh.close()
    return automaton
        

def parseBa(fileName):
    """Function for parsing the automaton in Ba format.

    Ba format:
    [q0]             (initial states)
    a,[q0]->[q1]     (transitions)
    a,[q0]->[q2]
    b,[q0]->[q1]
    a,[q1]->[q3]
    a,[q2]->[q4]
    [q3]             (accepting states)
    [q4]

    Args:
        fileName (string): name of the file with the automaton to parse

    Returns:
        automaton: parsed automaton
    """

    fh = open(fileName, 'r')
    automaton = nfa.Nfa()
    # Besause the format of initial states and final states are equal,
    # we create a variable for dedecting the end of the sequece of inital states.
    wasEndOfInitalStates = False

    while True:
         # Read next line and check if exists.
        line = fh.readline()
        if not line:
            break
        # Delete white space on the right.
        # The deletion can not be done above, because the empty line
        # would cause end of parsing. (It should looks as the end of a file.)
        line = line.rstrip()

        if re.fullmatch(r"\[\w+\]", line) is not None:
            # We found initial or accepting state "[q0]"
            newState = re.search(r"\[(\w+)\]", line).group(1)
            if wasEndOfInitalStates:
                automaton.acceptingStates.add(newState)
            else:
                automaton.initialStates.add(newState)
            automaton.states.add(newState)
        
        elif re.fullmatch(r"\w+[ ]*\,[ ]*\[\w+\][ ]*\->[ ]*\[\w+\]", line) is not None:
            # We found transition in the format "a,[q0]->[q1]".
            result = re.search(r"(\w+)[ ]*\,[ ]*\[(\w+)\][ ]*\->[ ]*\[(\w+)\]", line)
            # Create new transition (add new states if not exists yet).
            automaton.addTransition(result.group(2), result.group(3), result.group(1))

            # The detection of transitions means that the sequence of initial states ended.
            wasEndOfInitalStates = True
    
    fh.close()
    return automaton
