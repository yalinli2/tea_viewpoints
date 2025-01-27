# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 09:50:41 2025

@author: Yalin
"""

import os, warnings, pandas as pd
warnings.filterwarnings('ignore')

from chaospy import distributions as dist
from biosteam.evaluation import Model, Metric
from biorefineries import cornstover as cs
from qsdsan.utils import time_printer

folder = os.path.join(os.path.dirname(__file__), 'results')

#%%

cs.load()
cs_sys = cs.cornstover_sys
cs_tea = cs.cornstover_tea
ethanol = cs.ethanol
cornstover = cs.cornstover
R303 = cs.R303

get_MSP = lambda: cs_tea.solve_price(ethanol)
# If want $/gallon ethanol
# ethanol_density_kggal = cs.ethanol_density_kggal
# get_MESP = lambda: cs_tea.solve_price(ethanol) * ethanol_density_kggal

metrics = [
    Metric('Minimum selling price', get_MSP, '$/kg')
    ]

# Predefined distribution
def default_wide_dist(mid):
    lb = (1.-0.25)*mid - 0
    ub = (1.+0.25)*mid + 0
    if lb > ub:
        ub, lb = lb, ub
    return dist.Uniform(lb, ub)

def default_narrow_dist(mid):
    lb = (1.-0.05)*mid - 0
    ub = (1.+0.05)*mid + 0
    if lb > ub:
        ub, lb = lb, ub
    return dist.Triangle(lb, mid, ub)

def bound_wide_dist(mid):
    lb = (1.-0)*mid - 0.25
    ub = (1.+0)*mid + 0.25
    if lb > ub:
        ub, lb = lb, ub
    lb = max(0, lb)
    ub = min(1, ub)
    return dist.Uniform(lb, ub)

def bound_narrow_dist(mid):
    lb = (1.-0)*mid - 0.05
    ub = (1.+0)*mid + 0.05
    if lb > ub:
        ub, lb = lb, ub
    lb = max(0, lb)
    ub = min(1, ub)
    return dist.Triangle(lb, mid, ub)


# Add model parameters
def add_parameters(model, wide=True):
    if wide is True:
        default_dist = default_wide_dist
        bound_dist = bound_wide_dist
    else:
        default_dist = default_narrow_dist
        bound_dist = bound_narrow_dist
        
    # Default parameters including:
    # equipment cost (cost basis and scaling exponent) and electricity usage
    # stream prices, electricity price, heat utility prices, feedstock flowrate,
    # income tax, and startup months
    # all distri
    model.load_default_parameters(
        feedstock=cornstover,
        shape=default_dist,
        bounded_shape=bound_dist,
        operating_days=False,
        include_feedstock_price=True,
        )
    
    # More important parameters
    param = model.parameter
    
    # Glucan-to-glucose
    saccharification_reaction = R303.saccharification[2]
    X = bound_dist(saccharification_reaction.X)
    @param(element=R303, kind='coupled', distribution=X, baseline=saccharification_reaction.X)
    def set_saccharification_conversion(saccharification_conversion):
        saccharification_reaction.X = saccharification_conversion
    
    # Glucose-to-ethanol
    ethanol_reaction = R303.cofermentation[0]
    X = bound_dist(saccharification_reaction.X)
    @param(element=R303, kind='coupled', distribution=X, baseline=ethanol_reaction.X)
    def set_ethanol_conversion(ethanol_conversion):
        ethanol_reaction.X = ethanol_conversion
        
    # Add saccharification time as a parameter
    X = default_dist(R303.tau_saccharification)
    @param(element=R303, kind='isolated', distribution=X, baseline=R303.tau_saccharification)
    def set_saccharification_time(saccharification_time):
        R303.tau_saccharification= saccharification_time
        
    # Add fermentation time as a parameter
    X = default_dist(R303.tau_cofermentation)
    @param(element=R303, kind='isolated',  distribution=X, baseline=R303.tau_cofermentation)
    def set_fermentation_time(fermentation_time):
        R303.tau_cofermentation = fermentation_time

#%%

# Set up model
cs_model_wide = Model(cs_sys, metrics=metrics)
add_parameters(cs_model_wide, wide=True)

cs_model_narrow = Model(cs_sys, metrics=metrics)
add_parameters(cs_model_narrow, wide=False)

n_param = len(cs_model_wide.parameters)
# sample_size = [n_param*1, n_param*10, n_param*100]
sample_sizes = [10, 100, 1000, 2000]

@time_printer
def run(model, **kwargs):
    model.evaluate(**kwargs)


columns = []
MSPs = []
rhos = []
ps = []

def evaluate_sample_size(model, prefix, sizes, methods=('R', 'L')): # random, Latin hypercube
    for n_sample in sizes:
        for method in methods:
            samples = model.sample(N=n_sample, rule=method, seed=328)
            samples[0] = model.get_baseline_sample().values # make sure the first sample is the baseline
            model.load_samples(samples)
            run(model, notify=100)
            affix = f'{method}_{n_sample}'
            model.table.to_csv(os.path.join(folder, f'{prefix}_{affix}.csv'))
            columns.append(prefix.split('_')[-1][0]+'_'+affix)
            MSPs.append(model.table[model.table.columns[-1]].copy())
            rho, p = model.spearman_r(filter='omit nan')
            rhos.append(rho[rho.columns[-1]].copy())
            ps.append(p[p.columns[-1]].copy())
            print('\n')

evaluate_sample_size(cs_model_wide, prefix='cs_model_wide', sizes=sample_sizes)
evaluate_sample_size(cs_model_narrow, prefix='cs_model_narrow', sizes=sample_sizes)

df_MSP = pd.DataFrame(index=range(sample_sizes[-1]), columns=columns)
for col, MSP in zip(columns, MSPs): df_MSP[col] = MSP
df_MSP.to_csv(os.path.join('summary_MSP.csv'))

df_rho = pd.DataFrame(index=rhos[0].index, columns=columns)
for col, rho in zip(columns, rhos): df_rho[col] = rho
df_rho.to_csv(os.path.join('summary_rho.csv'))

df_p = pd.DataFrame(index=ps[0].index, columns=columns)
for col, p in zip(columns, ps): df_p[col] = p
df_p.to_csv(os.path.join('summary_p.csv'))


#%%

# Models with all of the more important parameters
cs_model_wide_lean = Model(cs_sys, metrics=metrics)
cs_model_wide_lean.parameters = [
    *[i for i in cs_model_wide.parameters if 'cornstover' in str(i.element)],
    *[i for i in cs_model_wide.parameters if 'cellulase' in str(i.element)],
    *[i for i in cs_model_wide.parameters if 'Electricity' in str(i.element)],
    *[i for i in cs_model_wide.parameters if 'R303' in str(i.element)],
    ]

evaluate_sample_size(cs_model_wide_lean, prefix='cs_model_wide_lean', sizes=[2000])

# Models with only some of the more important parameters
cs_model_wide_lean2 = Model(cs_sys, metrics=metrics)
cs_model_wide_lean2.parameters = [
    *[i for i in cs_model_wide.parameters if 'cornstover' in str(i.element)],
    *[i for i in cs_model_wide.parameters if 'cellulase' in str(i.element)],
    *[i for i in cs_model_wide.parameters if 'Electricity' in str(i.element)],
    ]

evaluate_sample_size(cs_model_wide_lean2, prefix='cs_model_wide_lean2', sizes=[2000])


# %%

# Save as a reference, read exported results
model = cs_model_wide_lean2.copy()
df = pd.read_csv(os.path.join(folder, 'cs_model_wide_lean2_L_2000.csv'), header=[0, 1], index_col=0)
model.table = df
rho, p = model.spearman_r(filter='omit nan')
rho.to_clipboard()
p.to_clipboard()
