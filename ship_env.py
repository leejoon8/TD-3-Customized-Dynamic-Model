#!/usr/bin/python
#-*- coding: utf-8 -*-

from gym import Env, spaces
import numpy as np
from shapely.geometry import LineString, Point
from viewer import Viewer
from simulator_simple import Simulator


class ShipEnv(Env):
    def __init__(self, type='continuous', action_dim = 1):
        self.type = type
        self.action_dim = action_dim
        self.observation_space = spaces.Box(low=np.array([0, -np.pi / 2, 0, -4, -0.2]), high=np.array([150, np.pi / 2, 5.0, 4.0, 0.2]))
        self.init_space = spaces.Box(low=np.array([0, -np.pi / 15, 1.0, 0.2, -0.01]), high=np.array([30, np.pi / 15, 1.5, 0.3, 0.01]))
        self.ship_data = None
        self.last_pos = np.zeros(3)
        self.last_action = np.zeros(self.action_dim)
        self.simulator = Simulator()
        self.point_a = (0.0, 0.0)
        self.point_b = (2000, 0.0)
        self._max_episode_steps = 5000
        self.max_x_episode = (5000, 0)
        self.guideline = LineString([self.point_a, self.max_x_episode])
        self.start_pos = np.zeros(1)
        self.number_loop = 0  # loops in the screen -> used to plot
        self.borders = [[0, 150], [2000, 150], [2000, -150], [0, -150]]
        self.viewer = None


    def step(self, action):
        side = np.sign(self.last_pos[1])
        angle_action = action[0]*side
        rot_action = 0.2
        state_prime = self.simulator.step(angle_level=angle_action, rot_level=rot_action)
        # convert simulator states into obervable states
        obs = self.convert_state(state_prime)
        # print('Observed state: ', obs)
        dn = self.end(state_prime=state_prime, obs=obs)
        rew = self.calculate_reward(obs=obs)
        self.last_pos = [state_prime[0], state_prime[1], state_prime[2]]
        self.last_action = np.array([angle_action, rot_action])
        info = dict()
        return obs, rew, dn, info

    def convert_state(self, state):
        """
        This method generated the features used to build the reward function
        :param state: Global state of the ship
        """
        ship_point = Point((state[0], state[1]))
        side = np.sign(state[1] - self.point_a[1])
        d = ship_point.distance(self.guideline)  # meters
        theta = side*state[2]  # radians
        vx = state[3]  # m/s
        vy = side*state[4]  # m/s
        thetadot = side * state[5]  # graus/min
        obs = np.array([d, theta, vx, vy, thetadot])
        return obs

    def calculate_reward(self, obs):
        d, theta, vx, vy, thetadot = obs[0], obs[1]*180/np.pi, obs[2], obs[3], obs[4]*180/np.pi
        if not self.observation_space.contains(obs):
            print("\n Action: %f,  State[%f %f %f], Velocidade [%f , %f] , Theta: %f, Distance: %f thetadot: %f \n" % (self.last_action[0], self.last_pos[0], self.last_pos[1], self.last_pos[2], vx, vy, theta, d, thetadot))
            return -1000
        else:
            return 1-8*np.abs(theta/90)-np.abs(thetadot/20)-5*np.abs(d)/150-np.abs(vy/4)-np.abs(vx-2)/2


    def end(self, state_prime, obs):
        if not self.observation_space.contains(obs) or -1 > state_prime[0] or state_prime[0] > self.max_x_episode[0] or 160 < state_prime[1] or state_prime[1]< -160:
            if not self.observation_space.contains(obs):
                print("\n Smashed")
            if self.viewer is not None:
                self.viewer.end_episode()
            if self.ship_data is not None:
                if self.ship_data.iterations > 0:
                    self.ship_data.save_experiment(self.name_experiment)
            return True
        else:
            return False

    def set_init_space(self, low, high):
        self.init_space = spaces.Box(low=np.array(low), high=np.array(high))

    def reset(self):
        init = list(map(float, self.init_space.sample()))
        init_states = np.array([self.start_pos[0], init[0], init[1], init[2] * np.cos(init[1]), init[2] * np.sin(init[1]), 0])
        self.simulator.reset_start_pos(init_states)
        self.last_pos = np.array([self.start_pos[0], init[0],  init[1]])
        print('Reseting position')
        state = self.simulator.get_state()
        if self.viewer is not None:
            self.viewer.end_episode()
        return self.convert_state(state)

    def render(self, mode='human'):
        if self.viewer is None:
            self.viewer = Viewer()
            self.viewer.plot_boundary(self.borders)
            self.viewer.plot_guidance_line(self.point_a, self.point_b)

        img_x_pos = self.last_pos[0] - self.point_b[0] * (self.last_pos[0] // self.point_b[0])
        if self.last_pos[0]//self.point_b[0] > self.number_loop:
            self.viewer.end_episode()
            self.viewer.plot_position(img_x_pos, self.last_pos[1], self.last_pos[2], 20 * self.last_action[0])
            self.viewer.restart_plot()
            self.number_loop += 1
        else:
            self.viewer.plot_position(img_x_pos, self.last_pos[1], self.last_pos[2], 20 * self.last_action[0])

    def close(self, ):
        self.viewer.freeze_scream()

######################################################################################
#######################################################################################
######################################################################################
# if __name__ == '__main__':
#     mode = 'normal'
#     if mode == 'normal':
#         env = ShipEnv()
#         for i_episode in range(10):
#             observation = env.reset()
#             for t in range(10000):
#                 env.render()
#                 action = np.array([1])
#                 observation, reward, done, info = env.step(action)
#                 if done:
#                     print("Episode finished after {} timesteps".format(t + 1))
#                     break
#         env.close()

###########################################################################################
###########################################################################################