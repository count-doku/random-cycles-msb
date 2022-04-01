# -*- coding: utf-8 -*-
"""
Created on Fri Mar 25 11:37:01 2022

@author: KDominic
"""

import csv
import numpy as np
import matplotlib.pyplot as plt


class coulombCounter():
    """
    Count charge and take coulombic efficiency and self-discharge current
    into account.
    """
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
        

def roll_dice():
    if np.random.random() <= 0.2:
        # Full cycle
        return 0.5
    else:
        # 20% cycle
        return 0.1


def create_cycle(I, CN, DSoC, ts, verbose=False):
    """
    Create one cycle from SoCx over SoCx to SoCx.
    E.g. for DoD = 1:
        SoC = 0.5 <---------------.
        Charge till SoC = 1       |
        Discharge till SoC = 0    |
        Charge till SoC = 0.5 <---'
    I: Current (A) 
    CN: Capacity (As)
    DSoC: Delta SoC for the first part (1) 
     /\      
    /  \    _____
        \  /    DSoC
         \/______
    ts: Sample time
    """
    t = CN/I*DSoC  # Time (s)
    ns = t/ts  # No. of samples 
    
    # Check if ns is an even number, else raise error
    if ns.is_integer():
        ns = int(ns)  # Convert ns to int 
        cycle = ns*[I] + 2*ns*[-I] + ns*[I]  # Create current
        time = np.arange(0, 4*t, ts)  # Create time
        if verbose:
            fig, ax = plt.subplots()
            ax.plot(time, cycle)
            ax.set(xlabel='time in s', ylabel='current in A')
            plt.tight_layout()
        return cycle
    else:
        raise ValueError(f"ns should be integer;\n ns={ns}\n I={I}\n DSoC={DSoC}\n t={t}\n ts={ts}")
    
    
def plot_profile(time, profile, ts, cc_init=3600, C=7200):
    """
    Plot current profile.
    time: Time array
    profile: Current array
    ts: Sample time for coulomb counter (s)
    """
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
    """
    Create profile.
    ts: Sample time (s)
    n_cycles: No. of cycles
    I_choice: Choice for current (A)
    DSoC: Delta SoC for first part, 2*DSoC=DDoD (s)
    """
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
    """
    Save profile.
    time: Time array
    profile: Current profile
    """
    f = open('alterungszyklen.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(['time (s)', 'current (A)'])
    for t, I in zip(time, profile):
        writer.writerow([t, I])
    f.close()
    
    
if __name__ == '__main__':
    """
    Create profile with 3 segments and different current amplitudes:
        600 full cycles
        600 mixed cycles (20% full cycles, 80% part cycles)
        600 part cycles
    """
    ts = 10  # Sample time (s)
    n_cycles = 600  # 600 Cycles per segment
    profile = []
    
    # 600 full cycles
    profile.append(create_profile(ts, n_cycles, [1, 2, 3, 4], 0.5, verbose=False))
    
    # 600 mixed cycles
    for n in range(n_cycles):
        profile.append(create_cycle(np.random.choice([1, 2, 3, 4]), 7200, roll_dice(), ts, verbose=False))
    
    # 600 part cycles
    profile.append(create_profile(ts, n_cycles, [1, 2, 3, 4], 0.1, verbose=False))
    
    profile = np.concatenate(profile)  # Concat profile
    
    # Create time array
    time = [0]
    [time.append(time[i]+ts) for i in range(len(profile)-1)]
    
    plot_profile(time, profile, ts)  # Plot 
    # save_profile(time, profile)  # Save
    