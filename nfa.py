"""nfa.py
File with definition of NFA and its operations
such as: creations of new state, state prunning,
adding transition, transition prunning, state prunning, atc.
Author: Michal Šedý
Last change: 19.02.2021 - creation
             06.03.2021 - basic NFA opearation done
             07.03.2021 - getFamilies, makeOneInitialState, isBackwardEQ, isForwardEQ
             08.03.2021 - Bugs repaired: 
                          printTimbuk - final state on one line,
                          makeOneInitialState - The old initial state will be removed
                                                if is dead.
                          isBackwardEq and isForwardEQ - the difference between keys
                          of two dict is tested as: set(dist1).symetris_difference(set(dict2)),
                          the emtines of obscure structures such as {[[]]} is tested 
                          as: any(var) - False if empty.
             13.03.2021 - getFamilies - family is only set of states with nondeterminism.
             14.03.2021 - Repair bugs in state pruning.
"""


from error import error, warning, printStats
from collections import deque
import algorithms


class BadType(Exception):
    """Raises when the bad type of function behavior is selected.
    """
    pass


class NameCollision(Exception):
    """Raises when the new state is made, but the state with the same name already exists.
    """
    pass


class Nfa:
    """Class of Nondeterministic Finite Automaton
    Automaton consits of: states, initial states, accepting states
                          transitions, and alphabet.   
    """
    def __init__(self):
        self.states = set()
        self.initialStates = set()
        self.acceptingStates  = set()
        self.forwardTrans = dict()
        self.backwardTrans = dict()
        self.__mergeCnt = 0
        self.__tmpCnt = 0
        self.__initStateCnt = 0
        self.__finalStateCnt = 0


    def getAlphabet(self):
        """Function calculate alphabet of an automaton.

        The aplhabete is calculated only from forward transitions.
        That means, the forward and backward transitions must coresponded.

        Returns:
            set: automaton alphabet
        """
        alphabet = set()
        for s in self.forwardTrans:
            for l in self.forwardTrans[s]:
                alphabet.add(l)
        
        return alphabet


    def printRaw(self):
        """Print automaton as it is represented in the computer.
        """
        print("Automaton:")
        print("-----------")
        print("Alphabet:")
        print(self.getAlphabet())
        print("States:")
        print(self.states)
        print("Initial states:")
        print(self.initialStates)
        print("Accepting states:")
        print(self.acceptingStates)
        print("Forward transitions:")
        print(self.forwardTrans)
        print("Backward transitions:")
        print(self.backwardTrans)


    def printTimbuk(self):
        """Print automaton in Timbuk format.
        Use forward transitions which must coresponded with backward.

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
        """

        # Print alphabet
        print("Ops", end='')
        for l in self.getAlphabet():
            print(" {0}:1".format(l), end='')
        print(" x:0")

        print("Automaton A")

        # Print states
        print("States", end='')
        for s in self.states:
            print(" {0}".format(s), end='')
        print("")

        # Print Final States
        print("Final States", end='')
        for s in self.acceptingStates:
            print(" {0}".format(s), end='')
        print("")

        print("Transitions")

        # Print Initial States
        for s in self.initialStates:
            print("x -> {0}".format(s))
        
        # Print Transitions
        for fromS in self.forwardTrans:
            for byL in self.forwardTrans[fromS]:
                for toS in self.forwardTrans[fromS][byL]:
                    print("{0}({1}) -> {2}".format(byL, fromS, toS))


    def printBa(self):
        """Print automaton in Ba format.

        Use forward transitions which must coresponded with backward.

        Ba format:
        [q0]             (initial states)
        a,[q0]->[q1]     (transitions)
        a,[q0]->[q2]
        b,[q0]->[q1]
        a,[q1]->[q3]
        a,[q2]->[q4]
        [q3]             (accepting states)
        [q4]
        """
        
        if not self.states:
            print("[0]")
            print("[0]")
            return

        # Print initial states
        for s in self.initialStates:
            print("[{0}]".format(s))
        
        # Print transitions
        for fromS in self.forwardTrans:
            for byL in self.forwardTrans[fromS]:
                for toS in self.forwardTrans[fromS][byL]:
                    print("{0},[{1}]->[{2}]".format(byL, fromS, toS))
        
        # Print accepting states
        for s in self.acceptingStates:
            print("[{0}]".format(s))


    def addTransition(self, fromState, toState, byLetter):
        """Function add new forward transtion (fromState)----byLetter--->(toState).

        States from and to will be added into the set of automaton states.
        The coresponding backward transition will be created too.

        Args:
            fromState (string): state from which the transition leads
            toState (string): letter of the transtion
            byLetter (string): state to which the transtion leads
        """

        # Add states to automaton set of states, for sure.
        # states is a set, so adding of allready existing item has no effect.
        self.states.add(fromState)
        self.states.add(toState)

        # Set FORWARD TRANSITION
        # Check if allready exists some transition from "fromState".
        if fromState not in self.forwardTrans:
            self.forwardTrans[fromState] = dict()      
        # Check if fromState allready has some transition with "byLetter".
        if byLetter not in self.forwardTrans[fromState]:
            self.forwardTrans[fromState][byLetter] = set()     
        # Create transition
        self.forwardTrans[fromState][byLetter].add(toState)

        # Set BACKWARD TRANSITION
        # Check if allready exists some transition from "toState".
        if toState not in self.backwardTrans:
            self.backwardTrans[toState] = dict()       
        # Check if toState allready has some transition with "byLetter".
        if byLetter not in self.backwardTrans[toState]:
            self.backwardTrans[toState][byLetter] = set()        
        # Create transition
        self.backwardTrans[toState][byLetter].add(fromState)


    def pruneTransition(self, fromState, toState, byLetter):
        """Function will prune the transition between
        "fromState" and "toState" which is marked with "byLetter".

        States from and to will reamain in the automaton. Only a transition will
        be removed. The corresponding prune will be make in both transiton dictionaries.
        If the transtion (states, or letter) not exists, nothing will be changed,
        but warning will be printed to stderr.

        Args:
            fromState (string): state from which the transition leads
            toState (string): letter of the transtion
            byLetter (string): state to which the transtion leads
        """

        # Prune forward transition
        try:
            self.forwardTrans[fromState][byLetter].remove(toState)
            # If the set is empty the key byLetter will be removed from
            # a dictionary of transitons form "fromState".
            if not self.forwardTrans[fromState][byLetter]:
                del self.forwardTrans[fromState][byLetter]
        except KeyError as e:
            warning("pruneTransition()",
                    "forward, try to prune ({0})--{1}-->({2})".format(fromState, byLetter, toState))
            if fromState not in self.forwardTrans:
                warning("pruneTransition()", "state FROM ({0}) not exists.".format(fromState))
            elif byLetter not in self.forwardTrans[fromState]:
                warning("pruneTransition()", "By letter ({0}) not exists.".format(byLetter))
            elif toState not in self.forwardTrans[fromState][byLetter]:
                warning("pruneTransition()", "state TO ({0}) not exists.".format(toState))
            else:
                error("pruneTransition()", "Unknown error.")
                raise e
        
        # Prune backward transition
        try:
            self.backwardTrans[toState][byLetter].remove(fromState)
            # If the set is empty the key byLetter will be removed from
            # a dictionary of transitions from "toState".
            if not self.backwardTrans[toState][byLetter]:
                del self.backwardTrans[toState][byLetter]
        except KeyError as e:
            warning("pruneTransition()",
                    "backward, try to prune ({0})--{1}-->({2})".format(toState, byLetter, fromState))
            if toState not in self.backwardTrans:
                warning("pruneTransition()", "state TO ({0}) not exists.".format(toState))
            elif byLetter not in self.backwardTrans[toState]:
                warning("pruneTransition()", "By letter ({0}) not exists.".format(byLetter))
            elif fromState not in self.backwardTrans[toState][byLetter]:
                warning("pruneTransition()", "state FROM ({0}) not exists.".format(fromState))
            else:
                error("pruneTransition()", "Unknown error.")
                raise e


    def isDeadState(self, state):
        """Function will test, if the state is dead.

        Args:
            state (string): tested state

        Returns:
            bool: True if the state is dead, otherwise False.
        """

        # If the state does not exists in automaton the warning is printed.
        if state not in self.states:
            warning("isDeadState()", 
                    "The asked state ({0}) does not exists in an automaton.".format(state))

        # Test Forward Dead (no road to accepting state)
        if state not in self.forwardTrans or not self.forwardTrans[state]:
            # state does not have succesor
            if state not in self.acceptingStates:
                # If the state does not have succesor and is not accepting,
                # than is dead.
                return True
        else:
            # Test if there is not only self loop.
            if not algorithms.dictValToSet(self.forwardTrans[state]).difference({state}):
                # There is only self loop.
                # Test if is at least accepting state
                if state not in self.acceptingStates:
                    return True

        # Test Backward Dead (no road to initial state)
        if state not in self.backwardTrans or not self.backwardTrans[state]:
            # State does not have predecesor.
            if state not in self.initialStates:
                # If the state does not have predecesor and is not initial,
                # than is dead.
                return True
        else:
            # Test if there is not only self loop.
            if not algorithms.dictValToSet(self.backwardTrans[state]).difference({state}):
                # There is only self loop.
                # Test if is at least initial state.
                if state not in self.initialStates:
                    return True
        
        # Otherwise is live, not dead.
        return False


    def removeState(self, state):
        """Function will delete current state.

        The state must not have any transtions.

        Args:
            state (string): state to remove
        """

        # If the state does not exists, the warning is printed.
        if state not in self.states:
            warning("removeState()",
                    "The deleted state ({0}) does not exists in an automaton.".format(state))

        if state in self.states:
            self.states.remove(state)
        if state in self.initialStates:
            self.initialStates.remove(state)
        if state in self.acceptingStates:
            self.acceptingStates.remove(state)
        if state in self.forwardTrans:
            del self.forwardTrans[state]
        if state in self.backwardTrans:
            del self.backwardTrans[state]

    
    def pruneState(self, state):
        """Function will prune state and its transtions (to and from).

        Args:
            state (string): state to prune
        """
        # Check if state exists.
        if state not in self.states:
            warning("pruneState()",
                    "The pruned state ({0}) no longer exists".format(state))
        
        # Prune FORWARD TRANSITIONS
        # Check if state has forward transitions
        if state in self.forwardTrans:
            for byL in list(self.forwardTrans[state].keys()):
                if state in self.forwardTrans and byL in self.forwardTrans[state]:
                    for toS in list(self.forwardTrans[state][byL]):
                        # Prune [state]---byL--->(toS)
                        self.pruneTransition(state, toS, byL)
                        # Check if toS is not dead state after prunning.
                        # If yes, remove it.
                        if self.isDeadState(toS) and toS != state:
                            self.pruneState(toS)

        # Prune BACKWARD TRANSITIONS
        # Check if state has backward transitions
        if state in self.backwardTrans:
            for byL in list(self.backwardTrans[state].keys()):
                if state in self.backwardTrans and byL in self.backwardTrans[state]:
                    for toS in list(self.backwardTrans[state][byL]):
                        # Prune (toS)---byL--->[state]
                        self.pruneTransition(toS, state, byL)
                        # Check if toS (predecesor) is not dead state after prunning.
                        # If, yes, remove it.
                        if self.isDeadState(toS) and toS != state:
                            self.pruneState(toS)
        
        # Prune (remove) state itself.
        self.removeState(state)


    def createNewState(self, type):
        """Function creates new state of specified type (merge, tmp or init).

        New state will be added only into automaton.states. Further state
        adding into acceping or initial states is in charge of a user.

        Args:
            type (string): type of new state (merge - use for merge, tmp,
                           or init - for new inital state)

        Raises:
            BadType: If a tyme is not merge or tmp.
            NameCollision: If a newly created state has allready used name.
                           (It should not happend)

        Returns:
            string: name of new state
        """

        # Create new name in dependance on selected type of state.
        if type == "merge":
            newState = "m{0}".format(self.__mergeCnt)
            self.__mergeCnt += 1
        elif type == "tmp":
            newState = "t{0}".format(self.__tmpCnt)
            self.__tmpCnt += 1
        elif type == "init":
            newState = "init{0}".format(self.__initStateCnt)
            self.__initStateCnt += 1
        elif type == "final":
            newState = "Final{0}".format(self.__finalStateCnt)
            self.__finalStateCnt += 1
        else:
            raise BadType("Bad type {0}".format(type))

        # Check name collision.
        if newState in self.states:
            error("createNewState()", "Name of state {0} allready exists".format(newState))
            raise NameCollision("Name of state {0} allready exists".format(newState))
        
        # Add state only into the set of automaton states.
        self.states.add(newState)

        return newState


    def mergeStates(self, states):
        """Function will merge all states into one (new) state.

        All transtions going throught the states will be redirected
        to the newly created one state.
        States must be in at least forward, backward language equivalenc
        or bilateral language inctiusion.

        Args:
            states (set): set of states to merge
        
        Returns:
            string: Name of the new one state.
        """

        # Create new state (result state)
        newState = self.createNewState("merge")

        # Duplicate transitions
        for state in states:
            # Duplicate all FORWARD transitions if exists
            if state in self.forwardTrans:
                for byL in self.forwardTrans[state]:
                    for toS in self.forwardTrans[state][byL]:
                        self.addTransition(newState, toS, byL)
            
            # Duplicate all BACKWARD transitions if exists
            if state in self.backwardTrans:
                for byL in self.backwardTrans[state]:
                    for toS in self.backwardTrans[state][byL]:
                        self.addTransition(toS, newState, byL)
            
        # If some of the merged state is accepting,
        # than the new state will be acceptin too.
        if states.intersection(self.acceptingStates):
            self.acceptingStates.add(newState)
        
        # If some of the merged state is initial,
        # than the new state will be initial too.
        if states.intersection(self.initialStates):
            self.initialStates.add(newState)
        
        # Prune (delete) all states.
        # The new (better) state allready exists.
        for state in states:
            self.pruneState(state)
        
        return newState


    def mergeTwoStates(self, first, second):
        """Auxiliary function for mergini only two states.

        Function will call mergeStates and pass two states in the set.
        All transtions going throught the states will be redirected
        to the newly created one state.
        States must be in at least forward, backwardl language equivalenc
        or bilateral language inctiusion.

        Args:
            first (string): fist state to merge
            second (string): second state to merge
        
        Returns:
            string: Name of the new one state.
        """
        return self.mergeStates({first, second})


    def makeOneInitialState(self):
        """Function make one initial state in NFA.
        If the automaton has ony one initial state, no change is made.
        Existing initial states whill be raplaced with one central intial state.
        These states will ramain. Only their initial behavior will be removed.
        For each forward transition from replaced states will be created
        a tansition from new initial state to the exact succesor.
        """

        # Test if an automaton has more than one initial state.
        # If not, return.
        if len(self.initialStates) <= 1:
            return
        
        # Create new central initial state
        newInitS = self.createNewState("init")
        # Add new state into automaton, but not makred it as initial yet.
        self.states.add(newInitS)

        # For each transtion from existing initial states make transition
        # from new initial state (newInitS).
        for initS in self.initialStates:
            # Test if has succesor
            if initS in self.forwardTrans:
                for letter in self.forwardTrans[initS]:
                    for toS in self.forwardTrans[initS][letter]:
                        # Created transition (newInitS)--letter-->(toS)
                        self.addTransition(newInitS, toS, letter)
        
        # Test if some of existing initial state is accepting too.
        if self.initialStates.intersection(self.acceptingStates):
            # If yes, than the newly created ctral initila state must be accepting.
            self.acceptingStates.add(newInitS) 
        
        # Backup old initial states
        oldInitialStates = self.initialStates

        # Replace all initial states with newInitS
        self.initialStates = {newInitS}

        # Test if old initial state are not dead now.
        # If yes, prune it.
        for oldInitial in oldInitialStates:
            if self.isDeadState(oldInitial):
                self.pruneState(oldInitial)


    def makeCentralFinalState(self):
        """Function make one central final state in NFA.
        If the automaton has ony one final state, no change is made.
        Existing finale states (int they are not initial) will be
        raplaced with one central final state.
        These states will ramain. Only their final behavior will be removed.
        For each backward transition from replaced states will be created
        a tansition from new initial state to the exact succesor.
        """

        # Test if an automaton has more than one final state
        if len(self.acceptingStates) <= 1:
            return

        newFinalS = self.createNewState("final")
        self.states.add(newFinalS)

        # For each transtion to existing final states make transition
        # to new final state (newFinalS).
        for finalS in self.acceptingStates.difference(self.initialStates):
            # Test if has ancestor
            if finalS in self.backwardTrans:
                for letter in self.backwardTrans[finalS]:
                    for fromS in self.backwardTrans[finalS][letter]:
                        # Created transition (fromS)--letter-->(newFinal)
                        self.addTransition(fromS, newFinalS, letter)
        
        # # Test if some of existing final state is initial too.
        # if self.acceptingStates.intersection(self.initialStates):
        #     self.initialStates.difference_update(self.acceptingStates)
        #     # If yes, than the newly created ctral initila state must be accepting.
        #     self.initialStates.add(newFinalS) 
        
        # Backup old initial states
        oldFinalStates = self.acceptingStates

        # Replace all initial states with newInitS + the states that are initial and final
        self.acceptingStates = {newFinalS}.union(self.initialStates.intersection(oldFinalStates))

        if self.isDeadState(newFinalS):
            self.pruneState(newFinalS)

        # Test if old initial state are not dead now.
        # If yes, prune it.
        for oldFinal in oldFinalStates:
            if self.isDeadState(oldFinal):
                self.pruneState(oldFinal)


    def getFamilies(self, allowSelfLoops=True):
        """Function will return the list of famili sets.
        Family set is a set of state, which are connected througth
        the ancestor of succesor with the some same letter.

        Example of a two families.
        --------------------------

        ***-->(q0)---a--->[f1.1]---b--->(q1)--***>  }
                  /---c,d--^                        }
        ***-->(q2)---d--->[f1.2]---g,r->(q3)--***>  } FAMILY 1
                             |                      } (f1.1, f1.2, f1.3)
                             -----h,r-->(q5)--***>  }
        ***-->(q4)---e--->[f1.3]---h-----^          }

        ***-->(q6)---f--->[f2.1]---a--->(q7)--***>  } FAMILY 2
                                |--a,b->(q8)--***>  } (f2.1)

        Returns:
            list: Function returns list of sets of states in famili ralation.
        """

        # List of families. Each family is set of members.
        families = set()

        # Find families with common ancestor (use FORWARD transitions)
        # with some same letters.
        for fromS in self.forwardTrans:
            succesors = set()
            for letter in self.forwardTrans[fromS]:
                possibleSucc = self.forwardTrans[fromS][letter].difference({fromS})
                # if possibleSucc:
                #     possibleSucc.difference_update(*(algorithms.getPureSuccesors(self.forwardTrans, states) for states in possibleSucc))
                # There must be nondeterminism, but self loop does not count.
                if len(possibleSucc) > 1:
                    succesors.update(possibleSucc)
            # If similar succesors of center state exists, mark them as family.
            if succesors:
                families.add(frozenset(succesors))
        
        # Find families with common ancestor (use BACKWARD transitions)
        # with some same letters.
        for fromS in self.backwardTrans:
            ancestor = set()
            for letter in self.backwardTrans[fromS]:
                possibleAnc = self.backwardTrans[fromS][letter].difference({fromS})
                # if possibleAnc:
                #     possibleAnc.difference_update(set.union(*(algorithms.getPureSuccesors(self.backwardTrans, states) for states in possibleAnc)))
                # There must be nondeterminism, but self loop does not count.
                if len(possibleAnc) > 1:
                    ancestor.update(frozenset(possibleAnc))
            # if the similar ancestors of center state exists, mark them as family.
            if ancestor:
                families.add(frozenset(ancestor))

        if not allowSelfLoops:
            # If the self loop ober family state is forbined,
            # remove this states from family
            familiesToCheck = families
            families = set()
            for family in familiesToCheck:
                # Create new family withou self loops
                newFamily = set()
                for state in family:
                    if state in self.forwardTrans:
                        # If the state does not have self loop add it to the new family
                        if state not in algorithms.dictValToSet(self.forwardTrans[state]):
                            newFamily.add(state)
                # If the family has only one ore non member, dont marked it
                if len(newFamily) > 1:
                    families.add(frozenset(newFamily))

        # Merge families with common states. These families are distant families.
        way = 0 # STATS
        newFamilies = set()
        for family in {frozenset(family) for family in algorithms.mergeSets(families)}:
            newFamily = set()
            for state in family:
                if not (algorithms.getPureSuccesors(self.backwardTrans, state).union(algorithms.getPureSuccesors(self.forwardTrans, state))).intersection(newFamily):
                    newFamily.add(state)
                else:
                    way += 1    # STATS
            if len(newFamily) > 1:
                newFamilies.add(frozenset(newFamily))
        
        return newFamilies


    def isBackwardEQ(self, r, s, steps=1):
        """Function test if two states r and s are in backward language equivalenc.
        Two states are backward equivalent if all backward routs ended in the same
        states. The variable steps stands for the len of routs.


        Args:
            r (string): First state to determine backward language equivalency.
            s (string): Second state to determine backward language equivalency.
            steps (int, optional): Length of the route of whit a language equivalence is
                                   calculated. Defaults to 1.
        
        Returns:
            bool: True if states r and s are backward equivalent. Otherwise False.
        """

        # Test if the steps is greater than 0
        if steps < 1:
            error("isBackwardEQ()", 
                  "The parameter steps must be positiv number. Given value: steps = {0}".format(steps))
            raise ArithmeticError

        # Initial open and close lists (queue, set, visitedStates).
        openItems = deque()
        closeItems = set()
        visitedStates = set()

        makedSteps = 0
        # Open will be a queue of lists(next step) of tuples (corresponding pair)
        # of frozensets (states from r or s).
        openItems.append([(frozenset({r}), frozenset({s}))])

        while any(openItems):
            itemsInStep = openItems.popleft()
            closeItems.update(itemsInStep)
            toBeAppended = list()
            for rStates, sStates in itemsInStep:
                # If two sets of states (rStates and sStates) are
                # equal, than they are language equivalent.
                if rStates == sStates:
                    continue

                # If one state from some set belongs into initial states,
                # than there must exists state in the other set, wthich
                # belong into initial states too.
                if self.initialStates.intersection(rStates):
                    if not self.initialStates.intersection(sStates):
                        return False
                elif self.initialStates.intersection(sStates):
                    if not self.initialStates.intersection(rStates):
                        return False

                rAncestorsDict = algorithms.mergeDicts(self.backwardTrans, rStates)
                sAncestorsDict = algorithms.mergeDicts(self.backwardTrans, sStates)
                # If this two groups does not lead to its ancestors with the same set
                # of letters, than they are not equivalent.
                if set(rAncestorsDict).symmetric_difference(set(sAncestorsDict)):
                    return False
                
                # Generate new tuples of set of states to which leads transition
                # with same symbol.
                for key in rAncestorsDict:
                    # After the maximum step count is reached, only allready visited states
                    # can be marked as ancestors.
                    if makedSteps >= steps:
                        if rAncestorsDict[key].difference(visitedStates) or sAncestorsDict[key].difference(visitedStates):
                            return False
                    # If the tuble is not in closeItems, it will be added.
                    tmp = (frozenset(rAncestorsDict[key]), frozenset(sAncestorsDict[key]))
                    if not tmp in closeItems:
                        toBeAppended.append(tmp)
                    visitedStates.update(rAncestorsDict[key])
                    visitedStates.update(sAncestorsDict[key])
            
            openItems.append(toBeAppended)
            makedSteps += 1
        
        return True

    def isForwardEQ(self, r, s, steps=1):
        """Function test if two states r and s are in forward language equivalence.
        Two states are forward equivalent if all forward routs ended in the same
        states. The variable steps stands for the len of routs.


        Args:
            r (string): First state to determine forward language equivalency.
            s (string): Second state to determine forward language equivalency.
            steps (int, optional): Length of the route of whit a language equivalence is
                                   calculated. Defaults to 1.
        
        Returns:
            bool: True if states r and s are forward equivalent. Otherwise False.
        """

        # Test if the steps is greater than 0
        if steps < 1:
            error("isForwardEQ()", 
                  "The parameter steps must be positiv number. Given value: steps = {0}".format(steps))
            raise ArithmeticError

        # Initial open and close lists (queue, set, visitedStates).
        openItems = deque()
        closeItems = set()
        visitedStates = set()

        makedSteps = 0
        # Open will be a queue of lists(next step) of tuples (corresponding pair)
        # of frozensets (states from r or s).
        openItems.append([(frozenset({r}), frozenset({s}))])

        while any(openItems):
            itemsInStep = openItems.popleft()
            closeItems.update(itemsInStep)
            toBeAppended = list()
            for rStates, sStates in itemsInStep:
                # If two sets of states (rStates and sStates) are
                # equal, than they are language equivalent.
                if rStates == sStates:
                    continue

                # If one state from some set belongs into accepting states,
                # than there must exists state in the other set, wthich
                # belong into accepting states too.
                if self.acceptingStates.intersection(rStates):
                    if not self.acceptingStates.intersection(sStates):
                        return False
                elif self.acceptingStates.intersection(sStates):
                    if not self.acceptingStates.intersection(rStates):
                        return False

                rSuccesorsDict = algorithms.mergeDicts(self.forwardTrans, rStates)
                sSuccesorsDict = algorithms.mergeDicts(self.forwardTrans, sStates)
                # If this two groups does not lead to its succesors with the same set
                # of letters, than they are not equivalent.
                if set(rSuccesorsDict).symmetric_difference(set(sSuccesorsDict)):
                    return False
                
                # Generate new tuples of set of states to which leads transition
                # with same symbol.
                for key in rSuccesorsDict:
                    # After the maximum step count is reached, only allready visited states
                    # can be marked as succesors.
                    if makedSteps >= steps:
                        if rSuccesorsDict[key].difference(visitedStates) or sSuccesorsDict[key].difference(visitedStates):
                            return False
                    # If the tuple is not in closeItems, it will be added.
                    tmp = (frozenset(rSuccesorsDict[key]), frozenset(sSuccesorsDict[key]))
                    if not tmp in closeItems:
                        toBeAppended.append(tmp)
                    visitedStates.update(rSuccesorsDict[key])
                    visitedStates.update(sSuccesorsDict[key])
            
            openItems.append(toBeAppended)
            makedSteps += 1
        
        return True

    
    def cleanDeadStates(self):
        beforeSTATS = len(self.states) # STATS
        openSet = set(self.initialStates)
        reachableFromInit = set()
        while openSet:
            state = openSet.pop()
            if state in reachableFromInit:
                continue
            reachableFromInit.add(state)
            if state in self.forwardTrans:
                for letter in self.forwardTrans[state]:
                    openSet.update(self.forwardTrans[state][letter])
        
        openSet = set(self.acceptingStates)
        reachableFromFin = set()
        while openSet:
            state = openSet.pop()
            if state in reachableFromFin:
                continue
            reachableFromFin.add(state)
            if state in self.backwardTrans:
                for letter in self.backwardTrans[state]:
                    openSet.update(self.backwardTrans[state][letter])
        
        # print("ReachablefromInit", reachableFromInit)
        # print("ReachablefromFin", reachableFromFin)

        for state in self.states.difference(reachableFromInit.intersection(reachableFromFin)):
        # for state in reachableFromFin.symmetric_difference(reachableFromInit):
            if state in self.states:
                self.pruneState(state)
