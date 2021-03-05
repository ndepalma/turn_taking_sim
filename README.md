# Multi-party turn-taking simulator

This simple simulator is meant for educational purposes only. There are many reasons why this 
model of human-robot turn-taking should not work. However, as a pedagogical tool, this simple simulator
may help students learn and think about turn taking in a multi-party environment. This simulator was
designed as a pedagogical tool for [our AI-HRI](http://ai-hri.github.io/2018/) workshop at the AAAI Fall Symposium. 

Dependencies:
* Python 3.7
* kivy (python-gui)
* wasy10 truetype font. Accessible [here](https://github.com/byrongibson/fonts/blob/master/truetype/ttf-lyx/wasy10.ttf)
* pygame

To run the app, simply run the entry for each model. For instance:

```bash
$ python GANDALF.py 
```
or 
```bash
$ python MP_GANDALF.py
```

A fun simple project that the students can do is to write their own model. You can do this easily by 
replacing the update in your own simulator loop. Look in MP_GANDALF.py for these lines:

```python
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
```

If you have any questions, don't hesitate to reach out.  