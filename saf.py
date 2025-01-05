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
# Default MSP is 4.343428601986846.

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