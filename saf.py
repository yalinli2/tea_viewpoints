# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 11:50:57 2025

@author: Yalin
"""

'''
Sustainable Avaiation Fuel from Food Waste (SAF)
'''

# =============================================================================
# Load module
# =============================================================================

from exposan import saf
saf.load(configuration='EC')
sys = saf.sys
tea = sys.TEA

products = [saf.mixed_fuel]
product = products[0].copy('product')
product.mix_from(products)
get_quantity = lambda: product.F_mass*sys.operating_hours

def get_MSP(tea=tea):
    global MSP
    MSP = tea.solve_price(products)
    for i in (*products, product): i.price = MSP
    return MSP

def get_tax(tea=tea):
    table = tea.get_cashflow_table()
    tax = get_MSP(tea)*sum(table['Tax [MM$]'])/sum(get_quantity()/tea.sales*table['Sales [MM$]'])
    return tax

baseline_kwargs = {
    '_years': 30,
    'income_tax': 0.21,
    'finance_fraction': 0.6,
    'IRR': 0.1,
    'finance_interest': 0.08,
    'finance_years': 10,
    }

def reset_tea(tea=tea):
    for k, v in baseline_kwargs.items(): setattr(tea, k, v)
    global baseline_MSP
    baseline_MSP = get_MSP(tea)
    print(f'\nBaseline MSP is {baseline_MSP}.')

reset_tea()
# Baseline MSP is 4.343428601986846.


#%%

# =============================================================================
# Item cost vs. technological parameters
# =============================================================================

# Electricity: EIA  https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_6_a
# Table 5.6.A. Average Price of Electricity to Ultimate Customers by End-Use Sector, Industrial, October 2024
# Tipping: EREF Analysis of MSW Landfill Tipping Fees — 2023
# Table 3. Average MSW Landfill Tip Fees, by Region

baseline_tipping_fee = -0.04226536872736153 # $39.7/wet tonne
baseline_electricity_price = 0.06852856268796911

import qsdsan as qs
feedstock = saf.feedstock

def refresh_electricity():
    for i in sys.units:
        if i.power_utility.rate:
            i.simulate()

feedstock.price = baseline_tipping_fee
qs.PowerUtility.price = baseline_electricity_price
print(f'\nBaseline MSP is {get_MSP()}.')
# 4.343428601986847.

saf.get_MFSP(sys)
# 12.003883977302296
#%%
# National average
feedstock.price = baseline_tipping_fee*56.8/(39.7/0.907185)
qs.PowerUtility.price = 0.0821
refresh_electricity()
print(f'National avg MSP is {get_MSP()}.')
# 4.333086263115636.
saf.get_MFSP(sys)
# 11.975300973587867

# California
feedstock.price = baseline_tipping_fee*(71.73-21.39)/(39.7/0.907185)
# feedstock.price = baseline_tipping_fee*71.73/(39.7/0.907185)
qs.PowerUtility.price = 0.2392
refresh_electricity()
print(f'California least favorable MSP is {get_MSP()}.')
# 5.963252307710632.
# 5.72394654512765.
saf.get_MFSP(sys)
# 16.480572236503264
# 15.819205635972079

# Pennsylvania
feedstock.price = baseline_tipping_fee*(92.08+26.02)/(39.7/0.907185)
# feedstock.price = baseline_tipping_fee*92.08/(39.7/0.907185)
qs.PowerUtility.price = 0.073
refresh_electricity()
print(f'Pennsylvania most favorable MSP is {get_MSP()}.')
# 3.5370378575853088.
# 3.8281428572304317.
saf.get_MFSP(sys)
# 9.7752710715752
# 10.579794654783127


#%%

# Adjusting biocrude yield to change Pennsylvania MSP to California,
# not good that only four fitting points (simulation not failed)

import numpy as np, pandas as pd
HTL_yields = saf.HTL_yields
yields = np.arange(1, 100, 1)

unit = sys.flowsheet.unit
stream = sys.flowsheet.stream
HTL = unit.HTL

CrudeSplitter = unit.CrudeSplitter
non_crudes0 = [HTL_yields['gas'], HTL_yields['aqueous'], HTL_yields['char']]
non_crude0 = sum(non_crudes0)
non_crudes0 = [i/non_crude0 for i in non_crudes0]

def adjust_yield(y_crude):
    non_crude = 1 - y_crude
    return [i*non_crude for i in non_crudes0]

feedstock = stream.feedstock
mixed_fuel = stream.mixed_fuel
dry_feedstock = feedstock.F_mass - feedstock.imass['Water']

crudes = []
MFSPs = []
for y in yields:
    sys.reset_cache()
    crude = y/100 if y>=1 else y
    print(f'yield: {crude:.2%}') 
    gas, aq, char = adjust_yield(crude)

    HTL.dw_yields = {
        'gas': gas,
        'aqueous': aq,
        'biocrude': crude,
        'char': char,
        }

    try: 
        sys.simulate()
        MFSP = saf.get_MFSP(sys, print_msg=False)
        print(f'MFSP: ${MFSP:.2f}/GGE.\n')
    except:
        fuel_yield = MFSP = GWP = None
        print('Simulation failed.\n')
    
    crudes.append(crude)
    MFSPs.append(MFSP)

df = pd.DataFrame({
    'biocrude_yield': crudes,
    'MFSP': MFSPs,
    })


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

IRR_kwargs = {
    'finance_fraction': 0,
    'IRR': interest,
    'finance_interest': 0,
    'finance_years': 0,
    }
for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_financial_results()

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