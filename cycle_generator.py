# -*- coding: utf-8 -*-
"""
Created on Fri Mar 25 11:37:01 2022

@author: KDominic
"""

import csv
import numpy as np
import matplotlib.pyplot as plt


class coulombCounter():
    def __init__(self, init_value=0, eta=1, i_sd=0.000, C=3600):
        self.charge = init_value  # Initial charge in As
        self.eta = eta  # Efficiency
        self.C = C  # Capacity
        self.i_sd = i_sd  # Self discharge current
        
    def step(self, I, ts):
        if I >= 0:    
            self.charge += self.eta*ts*I  # Charging direction
        else:
            self.charge += ts*I  # Discharging direction
        
        self.charge -= self.i_sd*ts
        
        return self.charge, self.getSOC()
    
    def getSOC(self):
        soc = self.charge/self.C  # SOC
        
        return soc
    

# def get_cycle(DoD=100, CN=2*3600, ts=1, verbose=False):
#     """

#     """
#     cycle = []
#     current = np.random.choice([0.5, 1, 1.5, 2, 2.5, 3, 4])
#     _time = int(CN/current*DoD/100)
   
#     [cycle.append(current) for i in range(_time)]
#     [cycle.append(-current) for i in range(_time)]
#     time = np.arange(0, 2*_time, ts)
    
#     if verbose:
#         fig, ax = plt.subplots()
#         ax.plot(time, cycle)
#         ax.set(xlabel='time in s', ylabel='current in A')
#         print(f'|\tDoD: {DoD}\t\t\t\t|')
#         print(f'|\tCurrent: {current} A\t\t|')
#         print(f'|\tCharge: {_time*current} As\t|')
#     return cycle, time


# def get_current_profile(cycles=100, verbose=False):
#     current_profile = []
#     for n in range(cycles):
#         DoD = roll_dice()
#         cycle, time = get_cycle(DoD=DoD, verbose=False)
#         current_profile.append(cycle)
    
#     current_profile = np.concatenate(current_profile)
#     if verbose:
#         fig, ax = plt.subplots()
#         ax.plot(current_profile)
#         ax.set(xlabel='time in s', ylabel='current in A')
        

def roll_dice():
    if np.random.random() <= 0.5:
        return 0.5
    else:
        return 0.1


def create_cycle(I, CN, DSoC, ts, verbose=False):
    t = CN/I*DSoC
    ns = t/ts
    if ns.is_integer():
        ns = int(ns)
        cycle = ns*[I] + 2*ns*[-I] + ns*[I]
        time = np.arange(0, 4*t, ts)
        if verbose:
            fig, ax = plt.subplots()
            ax.plot(time, cycle)
            ax.set(xlabel='time in s', ylabel='current in A')
            plt.tight_layout()
        return cycle
    else:
        raise ValueError(f"ns should be integer;\n ns={ns}\n I={I}\n DSoC={DSoC}\n t={t}\n ts={ts}")
    
    
def plot_profile(time, profile, ts, cc_init=3600, C=7200):
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.plot(time, profile, marker=None, drawstyle='steps-post', linewidth=0.1)
    ax.set(xlabel='time in s', ylabel='current in A', title=f'mean(I): {np.mean(profile)}')
    plt.tight_layout()
    plt.savefig('current.png')
    
    cc = coulombCounter(init_value=cc_init, C=C)
    SoC = []
    for i in profile:
        SoC.append(cc.getSOC())
        cc.step(i, ts)
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.plot(time, SoC, marker=None, linewidth=0.1)
    ax.set(xlabel='time in s', ylabel='SoC', title=f'mean(SoC): {np.mean(SoC)}')
    plt.tight_layout()
    plt.savefig('SoC.png')
    
    
def create_profile(ts, n_cycles, I_choice=[1, 2, 3, 4], DSoC=0.5, verbose=False):
    profile = []
    for n in range(n_cycles):
        I = np.random.choice(I_choice)
        cycle = create_cycle(I, 7200, DSoC, ts, verbose=False)
        profile.append(cycle)
    profile = np.concatenate(profile)
    time = [0]
    [time.append(time[i]+ts) for i in range(len(profile)-1)]
    if verbose:
        plot_profile(time, profile, ts)
    return profile
    

def save_profile(time, profile):
    f = open('alterungszyklen.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(['time (s)', 'current (A)'])
    for t, I in zip(time, profile):
        writer.writerow([t, I])
    f.close()
    
    
if __name__ == '__main__':
    ts = 10
    n_cycles = 600
    # create_profile(ts, n_cycles, [1,2,3,4], 0.5, verbose=True)
    profile = []
    profile.append(create_profile(ts, n_cycles, [1, 2, 3, 4], 0.5, verbose=False))
    for n in range(n_cycles):
        profile.append(create_cycle(np.random.choice([1, 2, 3, 4]), 7200, roll_dice(), ts, verbose=False))
    profile.append(create_profile(ts, n_cycles, [1, 2, 3, 4], 0.1, verbose=False))
    profile = np.concatenate(profile)
    time = [0]
    [time.append(time[i]+ts) for i in range(len(profile)-1)]
    
    plot_profile(time, profile, ts)
    save_profile(time, profile)
    