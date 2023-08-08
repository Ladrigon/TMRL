"""Import libraries"""
import numpy as np
from collections import deque
import gym
from gym import spaces
from matplotlib import pyplot as plt
from tm import TM

class TM_env(gym.Env):
    """Custom Environment that follows gym interface"""

    def __init__(self, pad, reward_scale):
        """Initialization of environment variables"""
        super(TM_env, self).__init__()
        self.tm = TM()
        self.pad = pad
        
        self.speed = deque([0, 0,], maxlen=2)
        self.laptime = deque([0, 0.1], maxlen=2)
        self.steer = deque([0, 0], maxlen=2)
        
        self.observation_buffer = deque([np.concatenate([np.array([0,0.,0,-1.,0.]),
                                                         np.zeros(13, dtype=np.float32),
                                                         np.zeros(10, dtype=np.float32),
                                                         ]),
                                         np.concatenate([np.array([0,0.,0,-1.,0.]),
                                                         np.zeros(13, dtype=np.float32),
                                                         np.zeros(10, dtype=np.float32),
                                                         ]),
                                         np.concatenate([np.array([0,0.,0,-1.,0.]),
                                                         np.zeros(13, dtype=np.float32),
                                                         np.zeros(10, dtype=np.float32),
                                                         ]),
                                         np.concatenate([np.array([0,0.,0,-1.,0.]),
                                                         np.zeros(13, dtype=np.float32),
                                                         np.zeros(10, dtype=np.float32),
                                                         ])], 
                                         maxlen = 4)
        
        self.last_lap = 0
        self.current_lap = 0
        
        self.previous_point = 0
        
        self.ep_telemetry = []
        self.ep = 0
        
        self.score_history = []

        self.first_lap = []
        
        self.score = 0
        
        self.reward_scale = reward_scale
        
        self.time_limit = 2*60
        self.stuck_count = 0

        self.action_space = spaces.Box(low=np.array([-1.0, 0.]),
                                       high=np.array([1.0, 1.0]),
                                       shape=(2, ), dtype=np.float32)
        
        self.observation_space = spaces.Box(
            low=np.array([np.concatenate([np.array([0,0.,0,-1.,0.]),
                                          np.zeros(13, dtype=np.float32),
                                          np.zeros(10, dtype=np.float32),
                                          ]),
                          np.concatenate([np.array([0,0.,0,-1.,0.]),
                                          np.zeros(13, dtype=np.float32),
                                          np.zeros(10, dtype=np.float32),
                                          ]),
                          np.concatenate([np.array([0,0.,0,-1.,0.]),
                                          np.zeros(13, dtype=np.float32),
                                          np.zeros(10, dtype=np.float32),
                                          ]),
                          np.concatenate([np.array([0,0.,0,-1.,0.]),
                                          np.zeros(13, dtype=np.float32),
                                          np.zeros(10, dtype=np.float32),
                                          ])
                          ]), 
            high=np.array([np.concatenate([np.array([400,500.,2*np.pi,1.,1.]),
                                                    np.full(13, 300, dtype=np.float32),
                                                    np.full(10, 100, dtype=np.float32),
                                                    ]),
                           np.concatenate([np.array([400,500.,2*np.pi,1.,1.]),
                                                    np.full(13, 300, dtype=np.float32),
                                                    np.full(10, 100, dtype=np.float32),
                                                    ]),
                           np.concatenate([np.array([400,500.,2*np.pi,1.,1.]),
                                                    np.full(13, 300, dtype=np.float32),
                                                    np.full(10, 100, dtype=np.float32),
                                                    ]),
                           np.concatenate([np.array([400,500.,2*np.pi,1.,1.]),
                                                    np.full(13, 300, dtype=np.float32),
                                                    np.full(10, 100, dtype=np.float32),
                                                    ])
                           ]),
            shape=(4,28), dtype=np.float32
        )
        
    def step(self, action):
        """Function of a single game step"""
        
        self.pad.steer(action[0])                           #steer action
        self.steer.append(action[0])                        #log steering

        self.pad.accelerate(self._discretize(action[1]))    #discretize acceleration and input

        self.pad.update()                                   #execute inputs

        self.tm.update_telemetry()

    
        #reward function
        self.current_point = self.tm.check_gate()
        reward = -1
        if self.current_point != 0:
            reward = self.current_point - self.previous_point
            self.previous_point = self.current_point
        if reward < 0:
            reward = -1
        
        reward = reward  / self.reward_scale


        observation = self._observation()                   #update observation
        
        #check lap completion
        new_current_lap = self.tm.lap()
        self.first_lap_time = 0
        if new_current_lap != self.current_lap:
            self.current_lap = new_current_lap
            if self.current_lap == 1:
                self.first_lap.append(self.tm.time)

        reason = None
        done = False
        self.ep_telemetry.append([self.tm.vehicle_telemetry()[0],self.tm.vehicle_telemetry()[1],self.tm.vehicle_telemetry()[2],action[0],action[1],self.tm.time])
        if reward > 0:
            self.score += reward
          
        #check for episode completion
        if self.current_lap > self.last_lap:
            done = True
            reason = "lap_completed"
            
        elif np.pi < self.tm.vehicle_angle() < 2*np.pi:
            done = True
            reason = "reverse"
            
        elif self.tm.vehicle_telemetry()[2] <= 5:
            self.stuck_count+= 1
            if self.stuck_count > 50:
                done = True
                reason = "stuck"
        
        elif self.tm.laptime() >= self.time_limit: # time limit
            done = True
            reason = "time_limit"

        else:
            done = False
        info = {"lap_time": self.tm.laptime(), 
                "done_reason": reason}
        
        #on episode completion, save results from episode
        if done:
            print(reason)
            self.ep_telemetry =  np.array(self.ep_telemetry)
            np.savetxt(f"eps/{self.ep}.csv", self.ep_telemetry, delimiter=",")
            self.ep +=1

            self.score_history.append(self.score)

            np.savetxt("score.csv", self.score_history, delimiter=",")

            np.savetxt("lap_times.csv", self.first_lap, delimiter=",")

            plt.show(block=False)
            plt.pause(0.1)
        
        return observation, reward, done, info

    def reset(self):
        """Reseting the environment for new episode"""
        self.pad.reset()
        self.pad.accelerate(1.0)
        self.pad.update()
        self.ep_telemetry = []

        self.tm.restart_race()

        observation = self._observation()
        self.curent_lap = 0
        self.prev_lap_time = 0
        self.lap_time = 0
        try:
            self.previous_point = self.tm.p0
        except:
            self.previous_point = 0
        
        self.speed = deque([0, 0,], maxlen=2)
        self.laptime = deque([0, 0.1], maxlen=2)
        self.steer = deque([0, 0], maxlen=2)
        self.observation_buffer = deque([np.concatenate([np.array([0,0.,0,-1.,0.]),
                            np.zeros(13, dtype=np.float32),
                            np.zeros(10, dtype=np.float32),
                            ]),
                      np.concatenate([np.array([0,0.,0,-1.,0.]),
                            np.zeros(13, dtype=np.float32),
                            np.zeros(10, dtype=np.float32),
                            ]),
                      np.concatenate([np.array([0,0.,0,-1.,0.]),
                            np.zeros(13, dtype=np.float32),
                            np.zeros(10, dtype=np.float32),
                            ]),
                      np.concatenate([np.array([0,0.,0,-1.,0.]),
                            np.zeros(13, dtype=np.float32),
                            np.zeros(10, dtype=np.float32),
                            ])], maxlen = 4)
        
        self.score = 0
        self.stuck_count = 0

        return observation

    def close(self):
        # set pad to default state
        self.pad.reset()
        self.pad.update()

    def _observation(self):
        """
        Observation structure:
            - velocity                                              [1]
            - acceleration                                          [1]
            - angle to centerline                                   [1]
            - lidar (every 15 degrees)                              [13]
            - previous steering input                               [1]
            - wall contact                                          [1]
            - curvature measurements (every 0.2s from 1s in front)  [10]
            ============================================================
            Observation size                                        [28]

        """

        self.tm.update_telemetry()
        
        velocity = self.tm.vehicle_telemetry()[2]
        
        self.speed.append(self.tm.vehicle_telemetry()[2])
        self.laptime.append(self.tm.laptime())
        acceleration = (self.speed[1] - self.speed[0]) / (self.laptime[1] - self.laptime[0])
        
        angle = self.tm.vehicle_angle()
        
        lidar = self.tm.vehicle_lidar(15)
        
        steer = self.steer[0]
        
        wall_contact = self.tm.vehicle_collision()
        
        curvature = self.tm.lap_radius()
        
        observation = np.concatenate([np.array([velocity, acceleration, angle, steer, wall_contact]),
                                     lidar, *curvature])
        
        self.observation_buffer.append(observation)
        return np.array([self.observation_buffer[0],self.observation_buffer[1],self.observation_buffer[2],self.observation_buffer[3]])

    def _discretize(self, v):
        """Discretization of throttle input"""
        if 0 < v <= 0.1:
            new_throttle = 0
        elif 0.1 < v <= 0.4:
            new_throttle = 0.5
        else:
            new_throttle = 1
        return(new_throttle)