"""algorithms.py
File with mathematict, set, dict , atc. algorithms.
Author: Michal Šedý
Last change: 06.03.2021 - Function dictValToSet and mergeSets
             07.03.2021 - mergeDicts
             13.03.2021 - improve simplifieTransition (now counting with loops),
                          class Backup, getPureOneBetweenAlphabet(), getPureSuccessor()
             14.03.2021 - Transiton pruning bug repaired. Chnage solver logic from
                          one big OR to more AND as assert-soft.
"""


from collections import defaultdict
from itertools import combinations
import nfa
import sys
from error import warning, printStats, debugMsg, debugPrintAutomaton
from z3 import Implies, Optimize, Not, Bool, And, Or, is_true
import time


class Backup():
    """Class for the backup of a set of states.
    This class is widely used in family minimization. In the cases, where
    a minimization returns worst result as a original states layout,
    the backup will be restored.
    """

    def __init__(self, automaton, states):
        """Initial function backup given states set of automaton.
        Transitions, initial and accepting behavior is stored for
        the futured reuses.

        Args:
            automaton (Nfa): Automaton, which states are backuped.
            states (set): The set of states to backup.
        """
        self.automaton = automaton
        self.states = states
        self.trans = list()
        # Transitions are backuped in the forward order.
        for state in states:
            # Backup of backward transitions.
            if state in automaton.backwardTrans:
                for letter in automaton.backwardTrans[state]:
                    for fromS in automaton.backwardTrans[state][letter]:
                        self.trans.append((fromS, letter, state))
            # Backup of forward transitions.
            if state in automaton.forwardTrans:
                for letter in automaton.forwardTrans[state]:
                    for toS in automaton.forwardTrans[state][letter]:
                        self.trans.append((state, letter, toS))
        # Backup initial and accepting states
        self.initial = automaton.initialStates.intersection(states)
        self.accepting = automaton.acceptingStates.intersection(states)


    def restore(self):
        """Function restore previously backuped states, its behavior and transitions.
        """

        for fromS, letter, toS in self.trans:
            self.automaton.addTransition(fromS, toS, letter)
        self.automaton.initialStates.update(self.initial)
        self.automaton.acceptingStates.update(self.accepting)


def dictValToSet(dictionary):
        """Function returns the set of unique values from dicitonary.

        Args:
            dictionary (dict): Dictionary with values to get.

        Returns:
            set: Set of unique values from dicitionary.
        """

        values = set()
        for key in dictionary:
            values.update(dictionary[key])
        return values


def mergeSets(listOfSets): 
    """Function will merge sets in given list with common items.
    Function merges all sets, whitch has some common item.
    The merge problem is solved as commection problem in graph.

    The function is taken from:
    https://www.geeksforgeeks.org/python-merge-list-with-common-elements-in-a-list-of-lists/

    Args:
        listOfSets (list): list of sets to merge in dependance of its items.

    Yields:
        Object generator: Return object generator for list of merged sets
                          it is required to call list(mergeSets()).
    """

    neigh = defaultdict(set) 
    visited = set() 
    for each in listOfSets: 
        for item in each: 
            neigh[item].update(each) 
    def comp(node, neigh = neigh, visited = visited, vis = visited.add): 
        nodes = set([node]) 
        next_node = nodes.pop 
        while nodes: 
            node = next_node() 
            vis(node) 
            nodes |= neigh[node] - visited 
            yield node 
    for node in neigh: 
        if node not in visited: 
            yield set(comp(node))


def mergeDicts(dictOfDicts, keysOfDicts):
    """Function merge dicts in dict. Current dicts are given by its key.

    Args:
        dictOfDicts (dict): Dictionary of dictionaries to merge.
        keysOfDicts (set): Keys of current dictionaries to merge.

    Returns:
        dict: Merged dictionary.
    """

    mergedDict = dict()

    for currentDictKey in keysOfDicts:
        # Check if asked dictionary exists.
        if currentDictKey in dictOfDicts:
            for key in dictOfDicts[currentDictKey]:
                if key not in mergedDict:
                    mergedDict[key] = set()
                mergedDict[key].update(dictOfDicts[currentDictKey][key])

    return mergedDict


def statesEQ(automaton, states, st=1):
    """Function calculates language equivalency (backward and forward)
    of states set.

    Args:
        automaton (Nfa): NFA on which the equivalency is computed.
        states (set): Set of states to compute equivalecy.
        st (int): Optional arrtibute (default 1). Steps on which the 
                  equivalence is calculated.

    Returns:
        tuple: Tuple of eqivalent states: tuple(backwardEQ, forwardEQ)
               backwardEQ or forwardEQ are sets of frozen sets. Frozen
               set represents equivalent pair. Self equivalence is not
               included.
    """
    backwardEQ = set()
    forwardEQ = set()

    # Equivalence of each conbination of two states is calculated.
    # Combination of two same states is not included.
    for r, s in combinations(states, 2):
        if automaton.isForwardEQ(r, s, steps=st):
            forwardEQ.add(frozenset({r, s}))
        if automaton.isBackwardEQ(r, s, steps=st):
            backwardEQ.add(frozenset({r, s}))

    return backwardEQ, forwardEQ


def familyClustering(backwardEq, forwardEq, groupsContent):
    """Function clusters family members to the set gepending on
    the groupsContent redirection predicate.

    Args:
        backwardEq (set): set of backward equivalent states pairs
        forwardEq (set): set of forward equivalent states pairs
        groupsContent (set): redirectiong rouls

    Returns:
        dict: Dictionary of dictionaries with only two keys (B and F),
              containing backward and forward equivalent states.
    """

    # Create empty 
    clustersDict = {frozenset(k):{'B':set(), 'F':set()} for k in groupsContent}

    for r, s in backwardEq:
        for key in groupsContent:
            if r in key:
                clustersDict[frozenset(key)]['B'].add(frozenset({r, s}))
    
    for r, s in forwardEq:
        for key in groupsContent:
            if r in key:
                clustersDict[frozenset(key)]['F'].add(frozenset({r, s}))
 
    return clustersDict


def softDuplicateState(automaton, state):
    """Create new state in the automaton and if the duplicated state is
    initial or accepting, the new state will be too.

    Args:
        automaton (Nfa): Automaton in which the new state will be added.
        state (string): Duplicated state.

    Returns:
        string: The name of new state.
    """

    newState = automaton.createNewState("tmp")
    if state in automaton.initialStates:
        automaton.initialStates.add(newState)
    if state in automaton.acceptingStates:
        automaton.acceptingStates.add(newState)
    
    return newState


def getPureSuccesors(trans, state):
    """Function returns the succesors of the state on the basis of
    the transition dictionary (could be backward transition dictionary,
    than the ancestor is returned). The state it self is not counted.

    Args:
        trans (dict): Transition dictionary.
        state (string): State whose succesors is returned.

    Returns:
        set: The set of a pure succesors of the state. If the state has
             no succesor/ancestor, then the set containing None is returned.
    """

    succesors = set()
    if state in trans:
        for letter in trans[state]:
            # Self loops does not count.
            succesors.update(trans[state][letter].difference({state}))
    
    # If the set of succesors is emtpy, the set containging None will be reutrned.
    if not succesors:
        succesors.add(None)
    
    return succesors


def getPureOneBetweenAlphabet(trans, fromS, toS):
    """Function returned the set of alphabete used between the states
    "fromS" and "toS", without multipy uses (self loops) of the state "fromS".
    The alphabet is calculated only to the distance of one transition from
    the state "fromS".

    Args:
        trans (dict): Transtion dictionary.
        fromS (string): Source state.
        toS (string): Destination state.

    Returns:
        set: The set of the alphabet between states "fromS" and "toS" calculated
             on a distatnce of one transition.
    """

    alphabet = set()
    if fromS in trans:
        for letter in trans[fromS]:
            # Only transtions which leads to the "toS" counts.
            if toS in trans[fromS][letter]:
                alphabet.add(letter)
    
    # If the alphabet is empty (no transition leads from "fromS" to "toS"),
    # the set containing only None will be returned.
    if not alphabet:
        alphabet.add(None)
    
    return alphabet



def simplifieTransitions(automaton, states):
    """Function simplifies transition leads to or from state from the set setates.
    The simplification lies in the createing new states with the same lanugage
    as the original state, but to or from each state leads only one transition.
    The new count of state generate from one state is transIn*transLoop*transOut.

    Args:
        automaton (Nfa): Automaton on which the simplification is made.
        states (set): Set of states for simplification.

    Returns:
        set: New set of new states covering the language of the previons set of states.
    """

    newStatesSet = set()

    # Simplifie each state
    for state in states:
        # If the state if dead, prune it.
        if automaton.isDeadState(state):
            automaton.pruneState(state)
            continue
        
        # Make new pseudoState for each combination fo ancestor and succesor.
        for ancestor in getPureSuccesors(automaton.backwardTrans, state):
            for succesor in getPureSuccesors(automaton.forwardTrans, state):
                # For the ancestor and succesor gemerate new set of state over
                # which will represent the original language between ancestor and succesor.
                # The new count of state transFromAnc*transLoop*transToSucc.
                for backwardLetter in getPureOneBetweenAlphabet(automaton.backwardTrans, state, ancestor):
                    for forwardLetter in getPureOneBetweenAlphabet(automaton.forwardTrans, state, succesor):
                        # Create new state
                        newState = softDuplicateState(automaton, state)
                        newStatesSet.add(newState)
                        # If the any of ancestor, succesor, or loopLetter is None, than
                        # the state does not have ancestor, succesor, or self loop.
                        if ancestor is not None:
                            # Create transition (ancestor)---backwardLetter--->(newState)
                            automaton.addTransition(ancestor, newState, backwardLetter)
                        if succesor is not None:
                            # Create transition (newState)---forwardLetter--->(succesor)
                            automaton.addTransition(newState, succesor, forwardLetter)

                        for loopLetter in getPureOneBetweenAlphabet(automaton.forwardTrans, state, state):
                            if loopLetter is None:
                                break
                            # Create loop (newState)---loopLetter--->(newState)
                            automaton.addTransition(newState, newState, loopLetter)

        # After creating new states and fully duplication of old state, it could be pruned.
        automaton.pruneState(state)
    return newStatesSet


def calculateSolver(backwardEq, forwardEq):
    """In dependace of backward and forward equivalent states, the function
    calsulates optimal groups of states, which can be merged into one.
    The optimization is done by Z3 solver.

    Args:
        backwardEq (set): The set of backward equivalent pairs of states.
        forwardEq (set): The set of forward equivalent paris of states.

    Returns:
        list: The list of sets of states, which can be merged into one.
    """
    # Init Z3 solver (optimizer).
    opt = Optimize()
    opt.set("timeout", 60000)

    # Calculate states used in backward and forward language equivalence.
    backwardStates = frozenset.union(*backwardEq) if backwardEq else set()
    forwardStates = frozenset.union(*forwardEq) if forwardEq else set()

    # # Create Bool variables for backward and forward equivalence.
    # # forward = "q1_F", backward = "q1_B"
    # for v in {Bool("{}_B".format(s)) for s in backwardStates}:
    #     opt.add_soft(v)
    # for v in {Bool("{}_F".format(s)) for s in forwardStates}:
    #     opt.add_soft(v)
    
    # Add possibly merged pairs of state into solver as assert.
    # (q1_B /\ q2_B) stands for backward equivalent states q1 and q2.
    cnt = 0
    for backwardPair in {And(Bool("{}_B".format(r)), Bool("{}_B".format(s))) for r, s in backwardEq}:
        opt.add_soft(backwardPair)
        cnt += 1
    for forwardPair in {And(Bool("{}_F".format(r)), Bool("{}_F".format(s))) for r, s in forwardEq}:
        opt.add_soft(forwardPair)
        cnt += 1
    # setOfAnds = {And(Bool("{}_B".format(r)), Bool("{}_B".format(s))) for r, s in backwardEq}
    # setOfAnds.update({And(Bool("{}_F".format(r)), Bool("{}_F".format(s))) for r, s in forwardEq})
    # opt.add(Or(setOfAnds))


    # Declare merge rules. If the state s is used in merge on the basis of
    # backward language inslustion, than state s can not be used in forward merge.
    # Rule = "q1_B => ~q1_F"
    cnt = 0
    for state in backwardStates.intersection(forwardStates):
        opt.add(Implies(Bool("{}_B".format(state)), Not(Bool("{}_F".format(state)))))
        cnt += 1
    
    # # Add possibly merged pairs of state into solver as assert.
    # # All paris are concatenated by OR. Pair is defined as:
    # # (q1_B /\ q2_B) stands for backward equivalent states q1 and q2.
    # setOfAnds = {And(Bool("{}_B".format(r)), Bool("{}_B".format(s))) for r, s in backwardEq}
    # setOfAnds.update({And(Bool("{}_F".format(r)), Bool("{}_F".format(s))) for r, s in forwardEq})
    # opt.add(Or(setOfAnds))
    timeNow = round(time.time() * 1000)

    # Calculate problem
    opt.check()
    model = opt.model()
    # Sets for states merged with some other state in backward or forward.
    backwardTrue = set()
    forwardTrue = set()

    # Find all states merged with some other state and marked it.
    for key in model:
        if is_true(model[key]):
            if str(key)[-1] == "B":
                backwardTrue.add(str(key)[:-2])
            elif str(key)[-1] == "F":
                forwardTrue.add(str(key)[:-2])
            else:
                warning("calculateSolver()",
                        "Solver variable: {0} makes no sense.".format(key))
    
    # Based of the sets backwardTrue and forwardTrue find pairs of state
    # from backwardEq or forwardEq, where both states are marked ad true.
    # This states will be merged.
    mergablePairs = set()
    for r, s in backwardEq:
        if r in backwardTrue and s in backwardTrue:
            mergablePairs.add(frozenset({r, s}))
    for r, s in forwardEq:
        if r in forwardTrue and s in forwardTrue:
            mergablePairs.add(frozenset({r, s}))
    
    # Make the biggest sets of states which can be merged into one.
    return list(mergeSets(mergablePairs))


def minimizeFamily(automaton, family, lookahead):
    """Function minimize family of the state depending of their
    forward and backward language equivalence.

    Args:
        automaton (Nfa): The automaton of which the minimizaiton is calculated.
        family (set): The set of state which will be possibly merged.

    Returns:
        bool: Function returns True if the family was merged.
              Otherwise, if the family is at its minimum, returns False.
    """
    # Calculate backward and forward equivalent pairs in the family.
    timeNow = round(time.time() * 1000)
    backwardEq, forwardEq = statesEQ(automaton, family, st=lookahead)
    # If there is no equivalent pair, the family is at its minimum.
    if not backwardEq and not forwardEq:
        return False
    
    inputFamily = set(family)

    # Split family into small groups, which have no efect between each other.
    # It sped up computation.
    clusters = mergeSets(list(backwardEq.union(forwardEq)))
    splitedFamilyDict = familyClustering(backwardEq, forwardEq, list(clusters))
    # For each part of a family make calcution and merge.
    for splitedFamily in splitedFamilyDict:
        timeNow = round(time.time() * 1000)
        mergeSuggestion = calculateSolver(splitedFamilyDict[splitedFamily]['B'],
                                            splitedFamilyDict[splitedFamily]['F'])

        # For each mergable group, do merge, add new state into family and remove
        # all merged states from group from family.
        for states in mergeSuggestion:
            family.add(automaton.mergeStates(states))
            family.difference_update(states)

    # Family is at its minimim, when there was no merged pairs.
    if inputFamily == family:
        return False

    return True


def solverMinimization(automaton, lookahead, allowSelfLoops=True):
    """Function minimize automaton using transition multipliing and
    using Z3 solver for predicting the most optimal merging pairs.

    Args:
        automaton (Nfa): Automaton for minimization.
    """
    # Init closeSet, which will mark all calculated families.
    closedSet = set()
    # While there is unclosed family, do minimalizaciton.
    while True:

        # Substract from families thous, which has been alredy minimized.
        # Whe the family is larged than the family in the closedSte, minimize it.        
        families = automaton.getFamilies(allowSelfLoops=allowSelfLoops).difference(closedSet)

        # If there is not any suitable family, finish.
        if not families:
            break

        # Minimize each family
        for family in families:
            # Create backup of the transitions and initial or accepting states.
            # Backup will be used if the minimization ended with more states than started.
            backup = Backup(automaton, family)
            # Create new states with the same language as original family
            timeNow = round(time.time() * 1000)
            family = simplifieTransitions(automaton, family)
            # While the family has equivalent states (can be merged), do minimzation.
            while True:
                if not minimizeFamily(automaton, family, lookahead):
                    # Family can no longer be minimized.
                    # Test if the resul of a minimization is not worse than the begin
                    if len(family) > len(backup.states):
                        backup.restore()
                        # The first solution was more optimal.
                        # Restore the backup and the original family.
                        # Delete new bad (less optimal) solution.
                        for state in family:
                            if state not in automaton.states:
                                continue
                            automaton.pruneState(state)
                        family = backup.states
                    # Mark family's states as closed
                    closedSet.add(frozenset(family))
                    break


def transitionsCount(trans):
    """Statistic function. Returs the count of the atuomaton transtions.
    The calculation is done only from the a given transition dictionary.
    The forward and backward transtion dictionary might coresponded, for
    better results.

    Args:
        trans (dict): Transition dictionary.

    Returns:
        int: Count of a transtion from transition dictionary.
    """

    count = 0
    for fromS in trans:
        for letter in trans[fromS]:
            count += len(trans[fromS][letter])
    return count