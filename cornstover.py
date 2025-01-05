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
    for i in products: i.price = MSP
    table = tea.get_cashflow_table()
    return MSP

def get_tax():
    tax = get_MSP()*sum(table['Tax [MM$]'])/sum(get_quantity()/tea.sales*table['Sales [MM$]'])
    return tax

default_kwargs = {
    'construction_schedule': tea.construction_schedule, # [0.08, 0.6 , 0.32]
    'startup_months': tea.startup_months, # 3
    'warehouse': tea.warehouse, # 0.04
    'site_development': tea.site_development, # 0.09
    'additional_piping': tea.additional_piping, # 0.045
    'proratable_costs': tea.proratable_costs, # 0.1
    'field_expenses': tea.field_expenses, # 0.1
    'construction': tea.construction, # 0.2
    'contingency': tea.contingency, # 0.1
    'other_indirect_costs': tea.other_indirect_costs, # 0.1
    'WC_over_FCI': tea.WC_over_FCI, # 0.05
    'depreciation': tea.depreciation, # MACRS7
    'steam_power_depreciation': tea.steam_power_depreciation, # MACRS20
    'income_tax': tea.income_tax, # 0.35
    'finance_fraction': tea.finance_fraction, # 0.6
    'IRR': tea.IRR, # 0.1
    'finance_interest': tea.finance_interest, # 0.08
    'finance_years': tea.finance_years, # 10
    }

def reset_tea():
    for k, v in default_kwargs.items(): setattr(tea, k, v)
    print(f'\nDefault MSP is {get_MSP()}.')

reset_tea()
# Default MSP is 0.6842768710140141.


# %%

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


# %%

# =============================================================================
# To make MSP and amortized price comparable
# =============================================================================

reset_tea()
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


# Amortization factor
get_AF = lambda r=tea.IRR, n=tea._years: r*(1+r)**n/((1+r)**n-1) # 10%, 30 years

# The minor differences in MSP and amortized price is due to the shorter lifetime
# of BT baghouse, will be the same if changing the lifetime to be the same as the
# system lifetime
# for i in sys.units: i.equipment_lifetime.clear()
BT_bag = sys.flowsheet.unit.BT.installed_costs['Baghouse bags']
get_CAPEX = lambda: (tea.FCI-BT_bag)*get_AF(r=tea.IRR, n=tea._years) + BT_bag*get_AF(r=tea.IRR, n=5)
# get_CAPEX = lambda: tea.FCI*get_AF(r=tea.IRR, n=tea._years)

def get_amortized_price():
    global price
    price = (get_CAPEX()+tea.AOC)/get_quantity()
    return price

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


# %%

# =============================================================================
# Finance interest vs. IRR
# =============================================================================

def print_results():
    print(f'IRR={tea.IRR}, finance_interest={tea.finance_interest}, MSP is {get_MSP()}.')

interest = 0.1

reset_tea()
tea.income_tax = 0
print(f'\nWhen income tax is {tea.income_tax}:')

finance_kwargs = {
    'finance_fraction': 1,
    'IRR': 0,
    'finance_interest': interest,
    'finance_years': 30,
    }
for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_results()

IRR_kwargs = {
    'finance_fraction': 0,
    'IRR': interest,
    'finance_interest': 0,
    'finance_years': 0,
    }
for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_results()

reset_tea()
tea.income_tax = 0.35
print(f'\nWhen income tax is {tea.income_tax}:')

for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_results()

for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_results()

interest = finance_kwargs['finance_interest'] = IRR_kwargs['IRR'] = 0.2
tea.income_tax = 0
print(f'\nWhen income tax is {tea.income_tax}:')
for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_results()
for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_results()

tea.income_tax = 0.35
print(f'\nWhen income tax is {tea.income_tax}:')
for k, v in finance_kwargs.items(): setattr(tea, k, v)
print_results()
for k, v in IRR_kwargs.items(): setattr(tea, k, v)
print_results()