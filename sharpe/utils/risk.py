#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np
import pandas as pd

APPROX_BDAYS_PER_MONTH = 21
APPROX_BDAYS_PER_YEAR = 252

MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52

DAILY = 'daily'
WEEKLY = 'weekly'
MONTHLY = 'monthly'
YEARLY = 'yearly'

ANNUALIZATION_FACTORS = {
    DAILY: APPROX_BDAYS_PER_YEAR,
    WEEKLY: WEEKS_PER_YEAR,
    MONTHLY: MONTHS_PER_YEAR
}


def _annual_factor(period):
    try:
        return ANNUALIZATION_FACTORS[period]
    except KeyError:
        raise ValueError("period cannot be {}, possible values: {}".format(
            period, ", ".join(ANNUALIZATION_FACTORS.keys())))


class Risk(object):
    def __init__(self, bar_returns, benchmark_bar_returns=None, risk_free_rate=0, period=DAILY):
        
        if benchmark_bar_returns is None:
            benchmark_bar_returns = pd.Series(0, index=bar_returns.index)
        assert(len(bar_returns) == len(benchmark_bar_returns))

        self._portfolio = bar_returns
        self._benchmark = benchmark_bar_returns
        self._period_count = len(bar_returns)
        self._risk_free_rate = risk_free_rate
        self._annual_factor = _annual_factor(period)
        self._daily_risk_free_rate = self._risk_free_rate / self._annual_factor
        self._win_rate = len(bar_returns[bar_returns > benchmark_bar_returns]) / self._period_count

        self._alpha = None
        self._beta = None
        self._avg_excess_return = np.mean(bar_returns) - self._daily_risk_free_rate
        self._sharpe = None
        self._return = np.expm1(np.log1p(bar_returns).sum())
        self._annual_return = (1 + self._return) ** (self._annual_factor / self._period_count) - 1
        self._benchmark_return = np.expm1(np.log1p(self._benchmark).sum())
        self._benchmark_annual_return = (1+self._benchmark_return) ** \
                                        (self._annual_factor / self._period_count) - 1
        self._max_drawdown = None
        self._volatility = None
        self._annual_volatility = None
        self._benchmark_volatility = None
        self._benchmark_annual_volatility = None
        self._information_ratio = None
        self._sortino = None
        self._tracking_error = None
        self._annual_tracking_error = None
        self._downside_risk = None
        self._annual_downside_risk = None
        self._calmar = None
        self._avg_excess_benchmark_return = None

        self._excess_portfolio = bar_returns - benchmark_bar_returns
        self._excess_return_rate = None
        self._excess_annual_return = None
        self._excess_volatility = None
        self._excess_annual_volatility = None
        self._excess_sharpe = None
        self._excess_max_drawdown = None
        self._var = None

    @property
    def return_rate(self):
        return self._return

    @property
    def annual_return(self):
        return self._annual_return

    @property
    def benchmark_return(self):
        return self._benchmark_return

    @property
    def benchmark_annual_return(self):
        return self._benchmark_annual_return

    @property
    def alpha(self):
        if self._alpha is not None:
            return self._alpha

        if len(self._portfolio) < 2:
            self._alpha = np.nan
            self._beta = np.nan
            return np.nan

        self._alpha = np.mean(self._portfolio - self._daily_risk_free_rate - self.beta *
                              (self._benchmark - self._daily_risk_free_rate)) * self._annual_factor
        return self._alpha

    @property
    def beta(self):
        if self._beta is not None:
            return self._beta

        if len(self._portfolio) < 2:
            self._beta = np.nan
            return self._beta

        cov = np.cov(np.vstack([
            self._portfolio,
            self._benchmark
        ]), ddof=1)

        if cov[1][1] == 0.0:
            return np.nan

        self._beta = cov[0][1] / cov[1][1]
        return self._beta

    @property
    def avg_excess_benchmark_return(self):
        if self._avg_excess_benchmark_return is not None:
            return self._avg_excess_benchmark_return
        self._avg_excess_benchmark_return = np.mean(self._excess_portfolio)
        return self._avg_excess_benchmark_return

    def _calc_volatility(self):
        if len(self._portfolio) < 2:
            self._volatility = 0.
            self._annual_volatility = 0.
        else:
            # std = self._portfolio.std(ddof=1)
            self._volatility = self._portfolio.std(ddof=1)
            self._annual_volatility = self._volatility * (self._annual_factor ** 0.5)

    @property
    def volatility(self):
        if self._volatility is not None:
            return self._volatility

        self._calc_volatility()
        return self._volatility

    @property
    def annual_volatility(self):
        if self._annual_volatility is not None:
            return self._annual_volatility

        self._calc_volatility()
        return self._annual_volatility

    def _calc_benchmark_volatility(self):
        if len(self._benchmark) < 2:
            self._benchmark_volatility = 0.
            self._benchmark_annual_volatility = 0.
        else:
            # std = self._benchmark.std(ddof=1)
            self._benchmark_volatility = self._benchmark.std(ddof=1)
            self._benchmark_annual_volatility = self._benchmark_volatility * (self._annual_factor ** 0.5)

    @property
    def benchmark_volatility(self):
        if self._benchmark_volatility is not None:
            return self._benchmark_volatility

        self._calc_benchmark_volatility()
        return self._benchmark_volatility

    @property
    def benchmark_annual_volatility(self):
        if self._benchmark_annual_volatility is not None:
            return self._benchmark_annual_volatility

        self._calc_benchmark_volatility()
        return self._benchmark_annual_volatility

    @property
    def max_drawdown(self):
        if self._max_drawdown is not None:
            return self._max_drawdown

        portfolio = [1] + list(self._portfolio)
        df_cum = np.exp(np.log1p(portfolio).cumsum())
        max_return = np.maximum.accumulate(df_cum)
        self._max_drawdown = abs(((df_cum - max_return) / max_return).min())
        return self._max_drawdown

    def _calc_tracking_error(self):
        if len(self._portfolio) < 2:
            self._tracking_error = 0.
            self._annual_tracking_error = 0.
            return 0

        self._avg_tracking_return = np.mean(self._excess_portfolio)
        self._tracking_error = self._excess_portfolio.std(ddof=1)
        self._annual_tracking_error = self._tracking_error * (self._annual_factor ** 0.5)

    @property
    def tracking_error(self):
        if self._tracking_error is not None:
            return self._tracking_error

        self._calc_tracking_error()
        return self._tracking_error

    @property
    def annual_tracking_error(self):
        if self._annual_tracking_error is not None:
            return self._annual_tracking_error

        self._calc_tracking_error()
        return self._annual_tracking_error

    @property
    def information_ratio(self):
        if self._information_ratio is not None:
            return self._information_ratio

        if len(self._portfolio) < 2:
            self._information_ratio = np.nan
            return np.nan

        if self.tracking_error == 0:
            self._information_ratio = np.nan
            return np.nan

        self._information_ratio = np.sqrt(self._annual_factor) * self._avg_tracking_return / self.tracking_error
        return self._information_ratio

    @property
    def sharpe(self):
        if self._sharpe is not None:
            return self._sharpe

        if self.volatility == 0:
            self._sharpe = np.nan
            return np.nan

        std_excess_return = np.sqrt((1 / (len(self._portfolio) - 1)) * np.sum(
            (self._portfolio - self._daily_risk_free_rate - self._avg_excess_return) ** 2
        ))
        self._sharpe = np.sqrt(self._annual_factor) * self._avg_excess_return / std_excess_return
        return self._sharpe

    @property
    def excess_sharpe(self):
        if self._excess_sharpe is not None:
            return self._excess_sharpe

        if self.volatility == 0:
            self._excess_sharpe = np.nan
            return np.nan

        std_excess_return = np.sqrt((1 / (len(self._portfolio) - 1)) * np.sum(
            (self._portfolio - self._daily_risk_free_rate - self.avg_excess_benchmark_return) ** 2
        ))
        self._excess_sharpe = np.sqrt(self._annual_factor) * self.avg_excess_benchmark_return / std_excess_return
        return self._excess_sharpe

    def _calc_downside_risk(self):
        if len(self._portfolio) < 2:
            self._annual_downside_risk = 0.
            self._downside_risk = 0.
            return 0
        diff = self._portfolio - self._daily_risk_free_rate
        diff[diff > 0] = 0.
        sum_mean_squares = np.sum(np.square(diff))
        self._downside_risk = (sum_mean_squares / (len(diff) - 1)) ** 0.5
        self._annual_downside_risk = self._downside_risk * (self._annual_factor ** 0.5)

    @property
    def downside_risk(self):
        if self._downside_risk is not None:
            return self._downside_risk

        self._calc_downside_risk()
        return self._downside_risk

    @property
    def annual_downside_risk(self):
        if self._annual_downside_risk is not None:
            return self._annual_downside_risk

        self._calc_downside_risk()
        return self._annual_downside_risk

    @property
    def sortino(self):
        if self._sortino is not None:
            return self._sortino

        if self.downside_risk == 0:
            self._sortino = np.nan
            return np.nan

        self._sortino = self._annual_factor * self._avg_excess_return / self.annual_downside_risk
        return self._sortino

    @property
    def calmar(self):
        if self._calmar is not None:
            return self._calmar

        if np.isclose(self.max_drawdown, 0):
            self._calmar = np.inf * np.sign(self._annual_return)
        else:
            self._calmar = self._annual_return / -self.max_drawdown

        return self._calmar

    @property
    def excess_return_rate(self):
        if self._excess_return_rate is None:
            self._excess_return_rate = np.expm1(np.log1p(self._excess_portfolio).sum())
        return self._excess_return_rate

    @property
    def excess_annual_return(self):
        if self._excess_annual_return is None:
            self._excess_annual_return = (1 + self._excess_return_rate) ** (self._annual_factor / self._period_count) - 1
        return self._excess_annual_return

    def _calc_excess_volatility(self):
        if len(self._excess_portfolio) > 1:
            self._excess_volatility = self._excess_portfolio.std(ddof=1)
            self._excess_annual_volatility = self._excess_volatility * (self._annual_factor ** 0.5)
        else:
            self._excess_volatility = 0
            self._excess_annual_volatility = 0.

    @property
    def excess_volatility(self):
        if self._excess_volatility is None:
            self._calc_excess_volatility()
        return self._excess_volatility

    @property
    def excess_annual_volatility(self):
        if self._excess_annual_volatility is None:
            self._calc_excess_volatility()
        return self._excess_annual_volatility

    @property
    def excess_max_drawdown(self):
        if self._excess_max_drawdown is not None:
            return self._excess_max_drawdown

        if len(self._excess_portfolio) < 1:
            self._excess_max_drawdown = np.nan
            return np.nan

        df_cum = np.exp(np.log1p(self._excess_portfolio).cumsum())
        max_return = np.maximum.accumulate(df_cum)
        self._excess_max_drawdown = -((df_cum - max_return) / max_return).min()
        return self._excess_max_drawdown

    @property
    def var(self):
        """ default: 95% VaR """
        if self._var is not None:
            return self._var

        self._var = self.param_var(0.05)
        return self._var

    def param_var(self, alpha):
        import scipy.stats as stats
        log_return = np.log1p(self._portfolio)
        mean = np.mean(log_return)
        std = np.std(log_return)
        return np.expm1(-stats.norm(mean, std).ppf(alpha))

    @property
    def win_rate(self):
        return self._win_rate

    def performance(self):
        result = {
            'return': self.return_rate,
            'annual_return': self.annual_return,
            'benchmark_return': self.benchmark_return,
            'benchmark_annual_return': self.benchmark_annual_return,
            'alpha': self.alpha,
            'beta': self.beta,
            'sharpe': self.sharpe,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'annual_volatility': self.annual_volatility,
            'information_ratio': self.information_ratio,
            'downside_risk': self.downside_risk,
            'sortino': self.sortino,
            'tracking_error': self.tracking_error,
            'calmar': self.calmar,
            'VaR': self.var,
            'excess_return': self.excess_return_rate,
            'excess_annual_return': self.excess_annual_return,
            'excess_annual_volatility': self.excess_annual_volatility,
            'excess_sharpe': self.excess_sharpe,
            'excess_max_drawdown': self.excess_max_drawdown,
            'win_rate': self.win_rate,
        }

        # now all are done, _portfolio, _benchmark not needed now
        self._portfolio = None
        self._benchmark = None
        return result