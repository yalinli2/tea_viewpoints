# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 11:50:57 2025

@author: Yalin
"""

# =============================================================================
# Sustainable Avaiation Fuel from Food Waste (SAF)
# =============================================================================

from exposan import saf
saf.load(configuration='EC')
sys = saf.sys
tea = sys.TEA
table = tea.get_cashflow_table()
product = saf.mixed_fuel
quantity = product.F_mass*sys.operating_hours
price = product.price = tea.solve_price(product)
tax = price*sum(table['Tax [MM$]'])/sum(quantity/tea.sales*table['Sales [MM$]'])