#!/usr/bin/env python
#
# Simulate the GANDALF model of turn taking for the machine
#

from sim.sim import Simulator, timems
from tt.FSM import FSM, FSMNode
from tt.sim_adapter import SimFeatureAdapter
import tt.fsm_adapter
import time
import signal, threading

DEBUG = False
voice_activity = 0
action_queued = 1
wants_turn = 2
otheraccept = 3
timesincelastactivity = 4
utterance_complete = 5
otherlookatme = 6
otherpresenting = 7
who_talking = 8
running_action = 9

lastactivitystamp = timems()

actionqueued = False


def observation_transformer(observations_in):
    """
    This takes the simulators actions and feeds them into the model we specify below
    """
    global lastactivitystamp, actionqueued
    (utterancefeatures, gazefeatures, posfeatures, turnfeatures, scenefeatures) = \
        observations_in
    chosenpartner = 0
    newObservation = []
    print("Turn features: " + str(turnfeatures))
    # voice activity
    newObservation.append(turnfeatures[0])
    if turnfeatures[0]:
        lastactivitystamp = timems()
    # action_queued
    newObservation.append(actionqueued)  # TODO
    # utterance_complete
    newObservation.append(not utterancefeatures[1])
    # otherlookatme
    newObservation.append(gazefeatures[chosenpartner] == 0)
    # otherpresenting
    newObservation.append(scenefeatures[chosenpartner])
    # who_talking
    newObservation.append(turnfeatures[0])
    # running_action
    newObservation.append(0)
    # wants_turn
    newObservation.append(turnfeatures[0] or scenefeatures[chosenpartner])
    # otheraccept
    newObservation.append(gazefeatures[chosenpartner] == 0 and scenefeatures[chosenpartner])
    # timesincelastactivity
    newObservation.append(timems() - lastactivitystamp)

    # print("Observation transformer output: " + str(newObservation))
    return newObservation


######################################################
## State transition callbacks below
######################################################
def ihave_igive(observations):
    """
    Function that is called from ihave state to igive state
    """
    if (not observations[voice_activity] and not observations[action_queued] \
            and observations[wants_turn]):
        return True
    return False


def igive_ihave(observations):
    """
    Function that is called from igive state to ihave state
    """
    if not observations[otheraccept]:
        return True
    return False


def igive_otherhas(observations):
    """
    Function that is called from igive state to otherhas state
    """
    if observations[otheraccept] and observations[wants_turn] and observations[otherlookatme] and observations[action_queued]:
        return True
    return False


def otherhas_itake(observations):
    """
    Function that is called from otherhas state to itake state
    """
    if (observations[timesincelastactivity] > 50 and observations[giving_turn]) or (observations[timesincelastactivity] > 70 and observations[utterance_complete]) or (observations[timesincelastactivity] > 120):
        return True
    return False


def itake_otherhas(observations):
    """
    Function that is called from itake state to otherhas state
    """
    if observations[timesincelastactivity] > 170 and observations[voice_activity]:
        return True
    return False


def itake_ihave(observations):
    """
    Function that is called from itake state to ihave state
    """
    if observations[otherlookatme] and not observations[otherpresenting] and not observations[wants_turn]:
        return True
    return False


class Model(FSM):
    """
    GANDALF finite state machine
    """
    def __init__(self):
        FSM.__init__(self, self.createTree())
        self.actionqueued = False
        self.actionrunning = False

    def createTree(self):
        """
        Create the state machine
        """
        my_turn_node = FSMNode("I have turn", None, None)
        other_has_turn_node = FSMNode("Someone else has turn", None, None)
        itake_turn_node = FSMNode("I'm taking turn", None, None)
        youtake_turn_node = FSMNode("Someone else is taking turn", None, None)

        myturn_out = [(ihave_igive, youtake_turn_node)]
        youtake_out = [(igive_ihave, my_turn_node),
                       (igive_otherhas, other_has_turn_node)]

        otherhas_out = [(otherhas_itake, itake_turn_node)]
        itake_out = [(itake_ihave, my_turn_node),
                     (itake_otherhas, other_has_turn_node)]

        my_turn_node.setMap(myturn_out)
        other_has_turn_node.setMap(otherhas_out)

        youtake_turn_node.setMap(youtake_out)
        itake_turn_node.setMap(itake_out)
        return [my_turn_node, youtake_turn_node,
                other_has_turn_node, itake_turn_node]

    def queueAction(self):
        """
        Queue an action.. in other words, I WANT TO TAKE A TURN BUT IT'S NOT MY TURN YET
        """
        self.actionqueued = True
        print("Queuing action")

    def update(self, observations):
        """
        Update function
        """
        global DEBUG, lastactivitystamp
        observations[tt.fsm_adapter.f_action_queued] = self.actionqueued  # TODO
        observations[tt.fsm_adapter.f_running_action] = self.actionrunning  # TODO
        # observations[tt.fsm_adapter.timesincelastactivity] = timems()-lastactivitystamp
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
            fts_trans = observation_transformer(fts)
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
