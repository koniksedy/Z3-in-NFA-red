# Z3-in-NFA-reduction

This program reduces nondeterministic finite automata (NFA) size using SAT solver Z3. The program was implemented for evaluation of newly investigated techniques of reduction of the size of NFA, which was presented in https://wis.fit.vutbr.cz/FIT/st/rp.php/rp/2020/BP/23436.pdf. 

The program supports automata in BA and Timbuk format.

Author: Michal Šedý <xsedym02@stud.fit.vutbr.cz>  
Supervisor: Mgr. Lukáš Holík, Ph.D.

## BA format
```
[initial state]
[initial state]
...
letter,[from state]->[to state]
...
[final state]
[final state]
...
```

## Timbuk format
```
Automaton A
States state1 state2 ...
Final States fin1 fin2 ...
Transitions
x -> initial
a(q0) -> q1
letter(from state) -> toState
```

## Requirements:
- Python 3.8
- Z3 solver https://github.com/Z3Prover/z3

`pip install z3-solver`

## reduce.py
reduce.py is used for the reduction of the NFA automata in BA of Timbuk format. The program takes three attributes.

`python3 reduce.py inputAutomaton -format EQLookAhead`
- _format_: -B for BA format and -T for Timbuk format
- _EQLookAhead_: -Lookahead of language equivalence approximation. If the EQLookAhead is set to 1, the two states of the automaton are equivalent only if the equivalence is confirmed to the maximal distance 1 from the examined states. A bigger number means more accurate results, but slower calculation.

The program saves reduced automaton to the as imputAutomaton-_EQLookAhead_-solver._format_
