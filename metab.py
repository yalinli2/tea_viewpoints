# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 11:51:23 2025

@author: Yalin
"""

'''
Modular Encapsulated Two-stage Anaerobic Biological (METAB)
'''

# =============================================================================
# Load module
# =============================================================================

from exposan.metab import create_system

sys = create_system(
    n_stages=2,         # number of stages
    reactor_type='PB',  # PB for packed bed, FB for fluidized bed, or UASB
    gas_extraction='M', # M for membrane gas extraction, V for vacuum extraction, P for passive venting
    Q=5,                # influent flowrate in m3/d
    T=22,               # reactor temperature in degree C
    tot_HRT=12,         # total HRT in d
    )

sys.simulate(state_reset_hook='reset_cache', t_span=(0,200), method='BDF')
tea = sys.TEA

products = [i for i in sys.products if i.price]
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
    '_duration': (tea._start, tea._start+30),
    'income_tax': 0,
    'finance_fraction': 0,
    'IRR': 0.05,
    'finance_interest': 0,
    'finance_years': 0,
    }

def reset_tea():
    for k, v in default_kwargs.items(): setattr(tea, k, v)
    print(f'\nDefault MSP is {get_MSP()}.')

reset_tea()
# Default MSP is 9.145709189106421.

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