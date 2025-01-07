# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 08:29:05 2025

@author: Yalin
"""

'''
Ethanol from Corn Stover (CS)
'''

# =============================================================================
# Load module
# =============================================================================

from biorefineries import cornstover as cs
cs.load()
sys = cs.sys
tea = sys.TEA

products = [cs.ethanol]
product = products[0].copy('product')
product.mix_from(products)
get_quantity = lambda: product.F_mass*sys.operating_hours

def get_MSP():
    global MSP, table
    MSP = tea.solve_price(products)
    for i in (*products, product): i.price = MSP
    table = tea.get_cashflow_table()
    return MSP

def get_tax():
    tax = get_MSP()*sum(table['Tax [MM$]'])/sum(get_quantity()/tea.sales*table['Sales [MM$]'])
    return tax

default_kwargs = {
    '_years': 30,
    '_duration': (2007, 2037),
    'construction_schedule': [0.08, 0.6 , 0.32],
    'startup_months': 3,
    'warehouse': 0.04,
    'site_development': 0.09,
    'additional_piping': 0.045,
    'proratable_costs': 0.1,
    'field_expenses': 0.1,
    'construction': 0.2,
    'contingency': 0.1,
    'other_indirect_costs': 0.1,
    'WC_over_FCI': 0.05,
    'depreciation': 'MACRS7',
    'steam_power_depreciation': 'MACRS20',
    'income_tax': 0.35,
    'finance_fraction': 0.6,
    'IRR': 0.1,
    'finance_interest': 0.08,
    'finance_years': 10,
    }

def reset_tea():
    global default_MSP
    for k, v in default_kwargs.items(): setattr(tea, k, v)
    default_MSP = get_MSP()
    print(f'\nDefault MSP is {default_MSP}.')

reset_tea()
# Default MSP is 0.6842768710140141.


#%%

# =============================================================================
# Item cost vs. technological parameters
# =============================================================================

cornstover, cellulase = cs.cornstover, cs.cellulase
default_cornstover_price = 0.05158816935126135
default_cellulase_price = 0.212
cornstover.price = default_cornstover_price*2
cellulase.price = default_cornstover_price*2
print(f'Double corn stover and cellulase price MSP is {get_MSP()}.')
# 1.0537098171440684.

cornstover.price = default_cornstover_price/2
cellulase.price = default_cornstover_price/2
print(f'Half corn stover and cellulase price MSP is {get_MSP()}.')
# 0.49955993418467054.

cornstover.price = default_cornstover_price
cellulase.price = default_cellulase_price
print(f'Default MSP is {get_MSP()}.')

R201, R303 = cs.R201, cs.R303
default_xylan_to_xylose = 0.9
default_glucan_to_glucose = 0.9
R201.xylan_to_xylose.X = default_xylan_to_xylose/2
R303.saccharification[2].X = default_xylan_to_xylose/2
sys.simulate()
print(f'Half glucan and xylan saccharification MSP is {get_MSP()}.')
# 1.017775410721592.

# Cannot double saccharification as it's already near 100%.

R201.xylan_to_xylose.X = default_xylan_to_xylose
R303.saccharification[2].X = default_glucan_to_glucose

default_glucose_to_ethanol = 0.95
default_xylose_to_ethanol = 0.85
R303.cofermentation[0].X = default_glucose_to_ethanol/2
R303.cofermentation[4].X = default_xylose_to_ethanol/2
sys.simulate()
print(f'Half glucose and xylose ethanol yield MSP is {get_MSP()}.')
# 1.008837960461515.

R303.cofermentation[0].X = default_glucose_to_ethanol
R303.cofermentation[4].X = default_xylose_to_ethanol
sys.simulate()
print(f'Default MSP is {get_MSP()}.')


#%%

# =============================================================================
# System size
# =============================================================================

import numpy as np, pandas as pd

feedstock = cs.cornstover
default_feedstock_flowrate = 104229.16
size_ratios = [round(i, 1) for i in np.arange(0.1, 2.1, 0.1)]

def evaluate_across_size_ratios(size_ratios=size_ratios):    
    size_MSPs = []
    for i in size_ratios:
        feedstock.F_mass = i * default_feedstock_flowrate
        sys.simulate()
        if i==1:
            base_MSP = get_MSP()
            print(f'FCI over AOC is {tea.FCI/tea.AOC}.')
        size_MSPs.append(get_MSP())
    df = pd.DataFrame({
        'size_ratio': size_ratios,
        'MSP_ratios': [i/base_MSP for i in size_MSPs],
        'sizes': [2205*i for i in size_ratios],
        'MSP': size_MSPs,
        })
    return df

df = evaluate_across_size_ratios()
df.to_clipboard()
# FCI over AOC is 4.374748210931889.

default_cornstover_price = 0.05158816935126135
feedstock.price = default_cornstover_price * 0.1
df_lowerOPEX = evaluate_across_size_ratios()
df_lowerOPEX.to_clipboard()
# FCI over AOC is 8.748089645734671.

feedstock.price = default_cornstover_price * 10
df_higherOPEX = evaluate_across_size_ratios()
df_higherOPEX.to_clipboard()
# FCI over AOC is 0.7292224234141249.


#%%

# =============================================================================
# Depreciation comparison
# =============================================================================

reset_tea()
tea.depreciation = 'MACRS7'
get_MSP()
# 0.6842768710140142
macrs7_table = tea.get_cashflow_table()
macrs7_table.to_clipboard()


tea.depreciation = 'SL30'
get_MSP()
# 0.693661784340705
sl30_table = tea.get_cashflow_table()
sl30_table.to_clipboard()


#%%

# =============================================================================
# If FCI = CAPEX = total installed equipment cost
# =============================================================================

reset_tea()
CAPEX_kwargs = {
    'warehouse': 0,
    'site_development': 0,
    'additional_piping': 0,
    'proratable_costs': 0,
    'field_expenses': 0,
    'construction': 0,
    'contingency': 0,
    'other_indirect_costs': 0,
    }

for k, v in CAPEX_kwargs.items(): setattr(tea, k, v)
print(f'\nCAPEX MSP is {get_MSP()}.')


#%%

# =============================================================================
# To compare MSP and amortized price
# =============================================================================

reset_tea()

# Amortization factor
get_AF = lambda r=tea.IRR, n=tea._years: r*(1+r)**n/((1+r)**n-1) # 10%, 30 years

# The minor differences in MSP and amortized price is due to the shorter lifetime
# of BT baghouse, will be the same if changing the lifetime to be the same as the
# system lifetime
# for i in sys.units: i.equipment_lifetime.clear()
BT_bag = sys.flowsheet.unit.BT.installed_costs['Baghouse bags']
get_CAPEX = lambda: (tea.FCI-BT_bag)*get_AF(r=tea.IRR, n=tea._years) + BT_bag*get_AF(r=tea.IRR, n=5)
# get_CAPEX = lambda: tea.FCI*get_AF(r=tea.IRR, n=tea._years)

def get_amortized_price(installed_cost_only=False):
    global price
    capital = get_CAPEX() if not installed_cost_only else tea.installed_equipment_cost*get_AF(r=tea.IRR, n=tea._years)
    price = (capital+tea.AOC)/get_quantity()
    return price

print(f'Amortized price with only installed equipment cost is {get_amortized_price(installed_cost_only=True)}.')

# Try to make MSP and amortized price comparable

amortization_kwargs = {
    'construction_schedule': [1],
    'startup_months': 0, # no need to adjust other startup settings
    'WC_over_FCI': 0, # working capital is depreciated
    'finance_fraction': 0, # no need to adjust other finance settings
    'depreciation': 'SL30', # amortization method uses straight-line depreciation
    'steam_power_depreciation': 'SL30',
    # Capital depreciation is excluded from tax, and earnings will be discounted,
    # will be complicated to include tax in the amortization method
    # see separate example below
    'income_tax': 0,
    }

for k, v in amortization_kwargs.items(): setattr(tea, k, v)

print('\nWhen income tax is 0:')
print(f'Amortization MSP is {get_MSP()}.')
print(f'Amortized price is {get_amortized_price()}.')

# =============================================================================
# To see the impact of income tax on MSP and amortized price
# =============================================================================

tea.income_tax = default_kwargs['income_tax']
print(f'\nWhen income tax is {tea.income_tax}:')
print(f'Amortization MSP is {get_MSP()}.')
print(f'Amortized price is {get_amortized_price()/(1-tea.income_tax)}.')


#%%

# =============================================================================
# Finance interest vs. IRR
# =============================================================================

def print_financial_results():
    print(f'IRR={tea.IRR}, finance_interest={tea.finance_interest}, MSP is {get_MSP()}.')

interest = 0.1

reset_tea()
tea.income_tax = 0.35
print(f'\nWhen income tax is {tea.income_tax}:')

finance_kwargs = {
    'finance_fraction': 1,
    'IRR': 0,
    'finance_interest': interest,
    'finance_years': 30,
    }
for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_financial_results()
all_financing_table = tea.get_cashflow_table()
all_financing_table.to_clipboard()

IRR_kwargs = {
    'finance_fraction': 0,
    'IRR': interest,
    'finance_interest': 0,
    'finance_years': 0,
    }
for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_financial_results()
all_equity_table = tea.get_cashflow_table()
all_equity_table.to_clipboard()

reset_tea()
tea.income_tax = 0
print(f'\nWhen income tax is {tea.income_tax}:')

for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_financial_results()

for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_financial_results()

interest = finance_kwargs['finance_interest'] = IRR_kwargs['IRR'] = 0.2
tea.income_tax = 0.35
print(f'\nWhen income tax is {tea.income_tax}:')
for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_financial_results()
for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_financial_results()

tea.income_tax = 0
print(f'\nWhen income tax is {tea.income_tax}:')
for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_financial_results()
for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_financial_results()

# To make 100% loan and 100% equity having the same MSP
# Ideally shouldn't have construction time, but didn't find a way to do so,
# but the impact is minimal (greater with shorter project lifetime and vice versa)
tea.construction_schedule = [1]
tea.WC_over_FCI = 0
cs.BT.equipment_lifetime.clear()
