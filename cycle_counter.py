# -*- coding: utf-8 -*-
"""
Created on Fri Apr  1 12:57:26 2022

@author: KDominic
"""

import numpy as np
import csv
import matplotlib.pyplot as plt


class cycle_counter():
    def __init__(self, CN):
        self.CN = CN
        self.n_cycles = 0
        self.idx = 0
    
    
    def count_cycle(self, Q_init, current_profile, ts):
        # Initial charge
        Q = Q_init
        
        # Initial negative charge
        Q_dch = 0
        
        # Current- and (Q-Q_init)-signs
        current_sign = np.sign(current_profile[0])
        charge_sign = np.copy(current_sign)
        
        # Sign change counters
        current_sign_changes = 0
        charge_sign_changes = 0
        
        for idx, I in enumerate(current_profile[self.idx:]):
            # print(idx, I, Q)
            
            # Count DoD
            if np.sign(I) == -1:
                Q_dch += I*ts
                
            # Count charge
            Q += I*ts
            
            # Count current sign changes
            if np.sign(I) != current_sign:
                current_sign = np.sign(I)
                current_sign_changes += 1
                # print('Current sign changed')
                
            # Count charge breakpoints
            if np.sign(Q-Q_init) != charge_sign:
                charge_sign = np.sign(Q-Q_init)
                charge_sign_changes += 1
                # print('Charge sign changed')

            if current_sign_changes >= 2 and charge_sign_changes >= 3:
                current_sign_changes = 0
                charge_sign_changes = 0
                self.n_cycles += 1
                self.idx += idx+1
                DoD = np.abs(Q_dch/self.CN)
                
                return self.n_cycles, DoD, Q
            

def reduce_capacity(CN, cycle, n_cycles, CN_init):
    if cycle == 'full':
        # CN = 7200 - CN*0.2/2000*n_cycles
        CN = CN - CN_init*0.2/2000
        return CN
    elif cycle == 'twenty':
        # CN = 7200 - CN*0.05/1400*n_cycles
        CN = CN - CN_init*0.05/1400
        return CN
    else:
        raise ValueError('Unknown cycle name')
    
    
if __name__ == '__main__':
    f = open('alterungszyklen.csv', 'r')
    reader = csv.reader(f)
    current = []
    time = []
    for idx, line in enumerate(reader):
        if idx == 0:
            continue
        current.append(np.double(line[1]))
        time.append(np.double(line[0]))
    
    counter = cycle_counter(7200)
    full_cycles = 0
    twenty_cycles = 0
    eq_full_cycles = 0
    Q = 3600
    CN = 7200
    CN_log = []
    
    while counter.idx < len(current):
        n_cycles, DoD, Q = counter.count_cycle(Q, current, 10)
        if DoD == 1.0:
            full_cycles += 1
            eq_full_cycles += 1
            CN = reduce_capacity(CN, 'full', eq_full_cycles, 7200)
            CN_log.append(CN)
        elif DoD == 0.2:
            twenty_cycles += 1
            if np.mod(twenty_cycles, 5) == 0:
                eq_full_cycles += 1
                CN = reduce_capacity(CN, 'twenty', eq_full_cycles, 7200)
                CN_log.append(CN)
        else:
            raise ValueError('Undefined cycle depth')
            
    fig, ax = plt.subplots(figsize=(6,6))
    ax.plot(CN_log, label='capacity')
    a = []
    [a.append((-0.2/2000*x+1)*7200) for x in range(len(CN_log))]
    ax.plot(a, '--', linewidth=0.5, label='compare-line')
    ax.set(xlabel='Equivalent full cycles', ylabel='Capacity (As)', title='Capacity Evolution')
    ax.text(400, 7000, f'full cycles: {full_cycles}\n 20% cycles: {twenty_cycles}\n equivalent full cycles: {eq_full_cycles}')
    ax.legend()
    plt.tight_layout()
    plt.savefig('CN_evolution.png')
    
    print(counter.idx)
    print('Counted full cycles: ', full_cycles)
    print('Counted twenty cycles: ', twenty_cycles)
    print('Equivalent full cycles: ', eq_full_cycles)