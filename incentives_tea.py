# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 09:14:36 2025

@author: Yalin
"""

import numpy as np
from biorefineries.tea import CellulosicEthanolTEA

class IncentivesTEA(CellulosicEthanolTEA):
    '''
    Allow simple incentives to be included in TEA.
    
    See Also
    --------
    BioSTEAM Location-Specific Evaluation (BLocS) module:
    https://github.com/BioSTEAMDevelopmentGroup/BLocS
    Stewart et al., Implications of Biorefinery Policy Incentives and
    Location-Specific Economic Parameters for the Financial Viability of Biofuels.
    Environ. Sci. Technol. 2023, 57 (6), 2262–2271.
    https://doi.org/10.1021/acs.est.2c07936.
    '''
    
    def __init__(self, *args,
                 product=None,
                 unit_incentive=0., # $/kg
                 incentive_mechanism='non-refundable tax', # 'non-refundable tax', 'refundable tax', 'income'
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.unit_incentive = unit_incentive
        self.incentive_mechanism = incentive_mechanism
    
    @property
    def incentive_mechanism(self):
        return self._incentive_mechanism
    @incentive_mechanism.setter
    def incentive_mechanism(self, i):
        i = i.lower().replace('_', '-')
        if ('non-refundable tax' in i) or ('non refundable tax' in i):
            self._incentive_mechanism = 'non-refundable tax'
        elif 'refundable tax' in i:
            self._incentive_mechanism = 'refundable tax'
        elif 'income' in i:
            self._incentive_mechanism = 'income'
        else:
            raise ValueError('incentive_mechanism can only be "refundable tax", '
                             '"non-refundable tax", or "income", '
                             f'the input {i} is not valid.')

    @property
    def annual_product(self):
        '''Annual product yield, [kg/yr].'''
        product = self.product
        return product.F_mass * self.operating_hours if product else 0.
    
    @property
    def annual_income_incentives(self):
        '''Income incentive, [$/yr].'''
        return self.sales - self.system.sales

    @property
    def sales(self):
        '''Total annual product sales, including income incentives [USD/yr].'''
        if self.incentive_mechanism != 'income':
            return self.system.sales
        return self.system.sales + self.annual_product*self.unit_incentive


    def _fill_tax_and_incentives(self, incentives, taxable_cashflow, nontaxable_cashflow, tax, depreciation):
        taxable_cashflow[taxable_cashflow < 0.] = 0.

        # Calculate tax
        start = self._start
        years = self._years
        plant_years = start + years
        empty_cashflows = np.zeros(plant_years)
        tax[:] = self.income_tax * taxable_cashflow
        # assessed_income_tax = taxable_cashflow * self.income_tax
        # index = taxable_cashflow > 0.
        # tax[index] = assessed_income_tax[index]

        mechanism = self.incentive_mechanism
        # Income incentive calculated through sales
        if mechanism == 'income':
            incentives[:] = 0 # otherwise double-counted
            self.incentives = incentives
            return
        
        # For tax credits
        w0 = self._startup_time
        w1 = 1. - w0
        def yearly_flows(x, startup_frac):
            y = empty_cashflows.copy()
            y[start] = w0 * startup_frac * x + w1 * x
            y[start + 1:] = x
            return y

        construction_schedule = self._construction_schedule
        def construction_flow(x):
            y = empty_cashflows.copy()
            y[:start] = x * construction_schedule
            return y

        annual_product = self.annual_product
        startup_VOCfrac = self.startup_VOCfrac
        incentives[:] = yearly_flows(annual_product, startup_VOCfrac)*self.unit_incentive
        self.incentives = incentives
        # breakpoint()
        if mechanism == 'refundable tax': return

        
        # Non-refundable tax
        index = incentives > tax
        incentives[index] = tax[index]