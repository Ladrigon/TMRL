"""Import Libraries"""
import time
from stable_baselines3 import SAC
from typing import Callable
from control.tmgamepad import TMGamePad
from env import TM_env
from callback import TMAiCallback, TMAiEpisodeCallback

"""Initializing command input"""
pad = TMGamePad()

"""Initialize environment"""
env = TM_env(pad, reward_scale = 4)
env.close()

"""Set up model saving"""
model_name = f"sac_tmai_{round(time.time())}"

"""Set up callbacks"""
checkpoint_callback = TMAiCallback(save_path=model_name)
episode_callback = TMAiEpisodeCallback(save_path=model_name)

"""Set up model"""
model = SAC("MlpPolicy", env, verbose=2, tensorboard_log="tensorboard_logs", 
            use_sde=False, seed=69, batch_size= 256, gamma= 0.85, buffer_size=8000000)

model.learn(total_timesteps=1000000, tb_log_name=model_name, log_interval=1, progress_bar= True, callback=[episode_callback, checkpoint_callback])
model.save("model")

env.close()