#!/usr/bin/env python
#
# Turns the simulator into a 'feature observer'
#

import tt.fsm_adapter as fsm_adapter
from sim.util import timems


class SimFeatureAdapter(fsm_adapter.Adapter):
    """
    This adapts the simulators features to the models expected order of observations
    """

    def __init__(self):
        self.lastFeatures = None
        print("WARNING: If you use this, you will still need " +
              "to set action_queued, action_running, and lastactivity features")

    def transform_features(self, features_in):
        """
        Features from the simulator in, observations for the model out
        """
        # break apart the chunks from the simulator features
        (utterancefeatures, gazefeatures, \
         posfeatures, turnfeatures, scenefeatures) = features_in

        print(
            "Utterance: " + str(utterancefeatures) + ", gaze features: " + str(gazefeatures) + ", pos features: " + str(
                posfeatures))
        chosenpartner = 0
        newObservation = []

        # voice activity   (of others)
        newObservation.append(utterancefeatures[1])
        if (utterancefeatures[1]):
            lastactivitystamp = timems()
        # f_action_queued  (for me)
        newObservation.append(-1)  # fill this in
        # newObservation.append(self.actionqueued) #TODO
        # f_utterance_complete
        newObservation.append(not utterancefeatures[1])  # at the moment, this is just voice_activity inverse

        # f_other_lookat (someone looking at me)
        someone_looking_at_me = False
        for p in range(len(gazefeatures)):
            if (gazefeatures[p] == 0):
                someone_looking_at_me = True
        newObservation.append(someone_looking_at_me)

        # f_other_presenting (someone is gesturing at me)
        someone_gesturing_at_me = False
        for p in range(len(scenefeatures)):
            if (scenefeatures[p]):
                someone_gesturing_at_me = True
        newObservation.append(someone_gesturing_at_me)
        # f_who_talking
        newObservation.append(turnfeatures[0])
        # f_running_action
        newObservation.append(-1)  # fill this in
        # newObservation.append(self.actionrunning)
        # f_wants_turn
        newObservation.append(newObservation[fsm_adapter.f_voice_activity] or \
                              newObservation[fsm_adapter.f_other_presenting])
        # f_other_accepts
        newObservation.append(newObservation[fsm_adapter.f_other_lookat] and \
                              newObservation[fsm_adapter.f_other_presenting])
        # timesincelastactivity
        newObservation.append(-1)  # fill this in
        # newObservation.append(timems()-self.lastactivitystamp)

        # print("Observation transformer output: " + str(newObservation))
        self.lastFeatures = newObservation
        return newObservation

    def getFeatures(self):
        """
        Get the current features from the last simulator step
        """
        return self.lastFeatures
