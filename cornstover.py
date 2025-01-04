# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 08:29:05 2025

@author: Yalin
"""

# =============================================================================
# Ethanol from Corn Stover (CS)
# =============================================================================

from biorefineries import cornstover as cs
cs.load()
sys = cs.sys
tea = sys.TEA
table = tea.get_cashflow_table()
product = cs.ethanol
quantity = product.F_mass*sys.operating_hours
price = product.price = tea.solve_price(product)
tax = price*sum(table['Tax [MM$]'])/sum(quantity/tea.sales*table['Sales [MM$]'])





