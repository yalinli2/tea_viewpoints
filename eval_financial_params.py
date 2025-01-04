# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 11:27:59 2025

@author: Yalin
"""

# =============================================================================
# Evaluate across finance parameters
# =============================================================================

import numpy as np, pandas as pd
def reset_financial_parameters(tea, income_tax=0.35, finance_interest=0.08, IRR=0.1, finance_fraction=0.6):
    tea.income_tax = income_tax
    tea.finance_interest = finance_interest
    tea.IRR = IRR
    tea.finance_fraction = finance_fraction
reset_financial_parameters()

income_taxes = [0.35, 0.21, 0]
finance_fractions = [round(i, 1) for i in np.arange(0, 1.1, 0.1)]

def price_across_finance_fractions(
        tea,
        product,
        income_tax,
        finance_interest,
        IRR,
        finance_fractions,
        ):
    default_tax = tea.income_tax
    default_interest = tea.finance_interest
    default_IRR = tea.IRR
    default_fraction = tea.finance_fraction
    
    tea.income_tax = income_tax
    tea.finance_interest = finance_interest
    tea.IRR = IRR
    print(f'Tax: {income_tax}, interest: {finance_interest}; IRR: {IRR}.')
    print('___')
    prices = []
    for finance_fraction in finance_fractions:
        tea.finance_fraction = finance_fraction
        price = tea.solve_price(product)
        print(f'Finance fraction: {finance_fraction}, price at ${price:.2f}/kg.')
        prices.append(price)
        
    tea.income_tax = default_tax
    tea.finance_interest = default_interest
    tea.IRR = default_IRR
    tea.finance_fraction = default_fraction
    
    return prices


# %%

# High interest loan, high IRR
s1_kwargs = {
    'finance_interest': 0.2,
    'IRR': 0.2,
    }
# Zero-interest loan, high IRR
s2_kwargs = {
    'finance_interest': 0,
    'IRR': 0.2,
    }
# Very high loan, zero IRR (no discount)
s3_kwargs = {
    'finance_interest': 0.2,
    'IRR': 0,
    }
# Zero-interest loan, zero IRR (no discount)
s4_kwargs = {
    'finance_interest': 0,
    'IRR': 0,
    }

def evalute(tea, product, income_taxes=income_taxes, finance_fractions=finance_fractions):
    dct = {'finance_fractions': finance_fractions,}
    
    for tax in income_taxes:
        for s, kwargs in zip((
                ['s1', 's2', 's3', 's4'],
                [s1_kwargs, s2_kwargs, s3_kwargs, s4_kwargs],
                )):
            dct.update({
                s: price_across_finance_fractions(income_tax=tax, **kwargs),
                })
    df = pd.DataFrame(dct)
    return df