#!/usr/bin/env python
#
# Simulate a hypothetical multi-party GANDALF model of turn taking for the machine
#

from sim.sim import Simulator, ModelInterface
from tt.FSM import FSM, FSMNode
from tt.sim_adapter import SimFeatureAdapter
import tt.fsm_adapter
from sim.util import timems
import time, signal
import threading

DEBUG = False


def ihave_igive(observations):
    """
    Function that is called from ihave state to igive state
    """
    global DEBUG
    if DEBUG:
        print("Ihave->Igive :->:")
    if observations[tt.fsm_adapter.f_action_queued] == 0:
        if DEBUG:
            print("   -> An action is queued...")
        if not observations[tt.fsm_adapter.f_running_action]:
            if DEBUG:
                print("   -> And nothing is running.. transitioning!")
            return True
    return False


def igive_ihave(observations):
    """
    Function that is called from igive state to ihave state
    """
    global DEBUG
    if DEBUG:
        print("Igive->Ihave :->:")
    if observations[tt.fsm_adapter.f_other_accepts] == 0:
        if DEBUG:
            print("   -> they didn't accept the turn")
        if observations[tt.fsm_adapter.f_action_queued]:
            if DEBUG:
                print("   -> I have an action ready")
            return True
    return False


def igive_otherhas(observations):
    """
    Function that is called from igive state to otherhas state
    """
    global DEBUG
    if DEBUG:
        print("Igive->Theyhave :->:")
    if observations[tt.fsm_adapter.f_wants_turn]:
        if DEBUG:
            print("   -> Someone wants the turn")
        return True
    if observations[tt.fsm_adapter.f_voice_activity]:
        if DEBUG:
            print("   -> Someone is talking")
        return True
    return False


def otherhas_itake(observations):
    """
    Function that is called from otherhas state to itake state
    """
    global DEBUG
    if DEBUG:
        print("Theyhave->Itake :->:")
    if observations[tt.fsm_adapter.timesincelastactivity] > 50 and not observations[tt.fsm_adapter.f_other_presenting]:
        if DEBUG:
            print("   -> Nobody is gesturing after 50 ms")
        return True
    if observations[tt.fsm_adapter.timesincelastactivity] > 70 and observations[tt.fsm_adapter.f_utterance_complete]:
        if DEBUG:
            print("   -> Nobody is talking after 70 ms")
        return True
    if observations[tt.fsm_adapter.timesincelastactivity] > 120:
        if DEBUG:
            print("   -> It's been 120ms")
        return True
    return False


def itake_otherhas(observations):
    """
    Function that is called from itake state to otherhas state
    """
    global DEBUG
    if DEBUG:
        print("Itake->Theyhave :->:")
    if observations[tt.fsm_adapter.timesincelastactivity] > 170:
        if DEBUG:
            print("   -> They haven't talked in 170ms")
        if observations[tt.fsm_adapter.f_voice_activity]:
            if DEBUG:
                print("   -> They started talking")
            return True
    if observations[tt.fsm_adapter.f_voice_activity]:
        if DEBUG:
            print("   -> They started talking")
        return True
    return False


def itake_ihave(observations):
    """
    Function that is called from itake state to ihave state
    """
    global DEBUG
    if DEBUG:
        print("Itake->Ihave :->:")
        print("Action queued? : " + str(tt.fsm_adapter.f_action_queued))

    if observations[tt.fsm_adapter.f_action_queued] == 1:
        if DEBUG:
            print("   -> I have an action waiting")
        if observations[tt.fsm_adapter.f_other_lookat]:
            if DEBUG:
                print("   -> Someone is looking at me")
            return True
    return False


class Model(FSM):
    """
    Multi-party (MP)GANDALF finite state machine
    """

    def __init__(self):
        FSM.__init__(self, self.createTree())
        self.isSpeaking = False
        self.action_started_at = timems()
        self.agent = None
        self.actionqueued = False
        self.actionrunning = False
        self.lastactivitystamp = timems()

    def createTree(self):
        """
        Create the state machine
        """
        self.my_turn_node = FSMNode("I have turn", self.startMyTurn, self.endMyTurn)
        other_has_turn_node = FSMNode("Someone else has turn", None, None)
        itake_turn_node = FSMNode("Floor is open", None, None)
        youtake_turn_node = FSMNode("Floor is open", None, None)

        myturn_out = [(ihave_igive, youtake_turn_node)]
        youtake_out = [(igive_ihave, self.my_turn_node),
                       (igive_otherhas, other_has_turn_node)]

        otherhas_out = [(otherhas_itake, itake_turn_node)]
        itake_out = [(itake_ihave, self.my_turn_node),
                     (itake_otherhas, other_has_turn_node)]

        self.my_turn_node.setMap(myturn_out)
        other_has_turn_node.setMap(otherhas_out)

        youtake_turn_node.setMap(youtake_out)
        itake_turn_node.setMap(itake_out)
        return [other_has_turn_node, itake_turn_node,
                self.my_turn_node, youtake_turn_node]

    def queue_action(self):
        """
        Queue an action.. in other words, I WANT TO TAKE A TURN BUT IT'S NOT MY TURN YET
        """
        self.actionqueued = True
        print("Queuing action")

    def update(self, observations):
        """
        Update function
        """
        global DEBUG
        observations[tt.fsm_adapter.f_action_queued] = self.actionqueued  # TODO
        observations[tt.fsm_adapter.f_running_action] = self.actionrunning  # TODO
        observations[tt.fsm_adapter.timesincelastactivity] = timems() - self.lastactivitystamp
        FSM.update(self, observations)
        if DEBUG:
            print("Current state : " + self.cur_state.name)
        return observations

    def startMyTurn(self):
        """
        Yay I can take my turn, trigger my action and utterance
        """
        global DEBUG
        self.action_started_at = timems()
        if DEBUG:
            print("Starting my turn")
        # self.agent.queuedAction = False
        self.actionrunning = True
        self.actionqueued = False

    def endMyTurn(self):
        """
        End my turn, yield to someone else
        """
        global DEBUG

        if DEBUG:
            print("Ending my turn")


if __name__ == "__main__":
    adapter = SimFeatureAdapter()
    agent_estimate = Model()
    simulator = Simulator(agent_estimate, 4)

    simulator.circle.makeRobotLookAtPerson(0)


    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        simulator.running = False
        simulator.quit()


    signal.signal(signal.SIGINT, signal_handler)


    def my_callback():
        time.sleep(0.05)
        while simulator.running:
            fts = simulator.getFeatures()
            fts_trans = adapter.transform_features(fts)
            observations = agent_estimate.update(fts_trans)
            # print(str(observations))
            simulator.vis_features(observations, agent_estimate.cur_state)

            simulator.circle.robot.queuedAction = agent_estimate.actionqueued
            if agent_estimate.actionrunning and timems() - agent_estimate.action_started_at > 2000:
                agent_estimate.actionrunning = False

            simulator.circle.makeRobotLookAtPerson(simulator.circle.turnstate.whospeaking)
            # print("Current state: " + str(agent_estimate.cur_state.name))
            time.sleep(0.05)


    thr = threading.Thread(target=my_callback)
    thr.start()
    simulator.start()
    simulator.startVis()
    print("Started simulator")
    time.sleep(1)

    simulator.join()
