#!/usr/bin/env python
#
# Implementation of a finite state machine
#

DEBUG = False


class FSMNode:
    """
    Node of a finite state machine
    """

    def __init__(self, name, onStart, onEnd, fns_states_map=None):
        self.onstart = onStart
        self.onend = onEnd
        self.name = name

        if fns_states_map is not None:
            self.setMap(fns_states_map)

    def setMap(self, fns_states_map):
        """
        Each node function maps to a state
        """
        self.the_fns = fns_states_map

    def nextState(self, observations):
        """
        From the current state, sees which function wants to transition
        """
        global DEBUG
        for (fn, state) in self.the_fns:
            if fn(observations):
                if DEBUG:
                    print(":: EXEC: Transition to " + state.name + " was successful.\n")
                return state
            else:
                if DEBUG:
                    print(":: EXEC: Transition to " + state.name + " was unsuccessful.")
        if DEBUG:
            print(":: EXEC: Staying in state\n")
        return self

    def onStart(self):
        """
        On start callback
        """
        if self.onstart is not None:
            self.onstart()

    def onEnd(self):
        """
        On end callback
        """
        if self.onend is not None:
            self.onend()


class FSM:
    """
    The whole finite stat machine with current state and encapsulates all states of the FSM
    """

    def __init__(self, states):
        self.all_states = states
        self.cur_state = states[0]

    def update(self, observations):
        """
        Update function takes observations and sees which state to move to
        """
        if self.cur_state is not None:
            prev_state = self.cur_state
            self.cur_state = self.cur_state.nextState(observations)
            if self.cur_state != prev_state:
                prev_state.onEnd()
                self.cur_state.onStart()
        return self.cur_state
