"""
Running the threelink arm with the PyGame display. The path planning will
system will generate a trajectory for the controller to follow, moving the
end-effector in a straight line to the target, which changes every n time
steps.
"""
import numpy as np

from abr_control.arms import threejoint as arm
# from abr_control.arms import twojoint as arm
from abr_control.interfaces import PyGame
from abr_control.controllers import OSC, path_planners


# initialize our robot config
robot_config = arm.Config(use_cython=True)

# create our arm simulation
arm_sim = arm.ArmSim(robot_config)

# create an operational space controller
ctrlr = OSC(robot_config, kp=100, vmax=None)

# create our path planner
n_timesteps = 250  # give .25s to reach target
path_planner = path_planners.Linear(robot_config)

# create our interface
interface = PyGame(robot_config, arm_sim, dt=.001)
interface.connect()

# set up lists for tracking data
ee_path = []
target_path = []


try:
    # run ctrl.generate once to load all functions
    zeros = np.zeros(robot_config.N_JOINTS)
    ctrlr.generate(q=zeros, dq=zeros,
                   target_pos=zeros, target_vel=zeros)
    robot_config.R('EE', q=zeros)

    print('\nSimulation starting...\n')
    print('\nClick to move the target.\n')

    count = 0
    while 1:
        # get arm feedback
        feedback = interface.get_feedback()
        hand_xyz = robot_config.Tx('EE', feedback['q'])

        if count % n_timesteps == 0:
            target_xyz = np.array([
                np.random.random() * 2 - 1,
                np.random.random() * 2 + 1,
                0])
            # update the position of the target
            interface.set_target(target_xyz)
            path_planner.generate_path(
                state=hand_xyz, target=target_xyz,
                n_timesteps=n_timesteps, plot=False)

        # returns desired [position, velocity]
        target = path_planner.next_target()

        # generate an operational space control signal
        u = ctrlr.generate(
            q=feedback['q'],
            dq=feedback['dq'],
            target_pos=target[:3],  # (x, y, z)
            target_vel=target[3:])  # (dx, dy, dz)

        # apply the control signal, step the sim forward
        interface.send_forces(
            u, update_display=True if count % 20 == 0 else False)

        # track data
        ee_path.append(np.copy(hand_xyz))
        target_path.append(np.copy(target_xyz))
        count += 1

finally:
    # stop and reset the simulation
    interface.disconnect()

    print('Simulation terminated...')
