# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 11:51:23 2025

@author: Yalin
"""

# =============================================================================
# Modular Encapsulated Two-stage Anaerobic Biological (METAB)
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
gases = [i for i in sys.products if i.price]
mixed_gas = gases[0].copy('mixed_gas')
mixed_gas.mix_from(gases)

tea = sys.TEA
table = tea.get_cashflow_table()
product = mixed_gas
quantity = product.F_mass*sys.operating_hours
price = product.price = tea.solve_price(gases)
tax = price*sum(table['Tax [MM$]'])/sum(quantity/tea.sales*table['Sales [MM$]'])

tea.finance_fraction = 0.6
tea.finance_interest = 0.08
tea.finance_years = 10
price = product.price = tea.solve_price(gases)
