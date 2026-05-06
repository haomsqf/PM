# Portfolio Enumeration Summary

## Client Mandate

- Client age: 57
- Current wealth: $18,000,000
- Annual income for next 5 years: $200,000
- Annual spending before retirement: 2% of wealth
- Retirement age: 62
- Target wealth at retirement: $23,000,000
- Risk constraint: avoid drawdown worse than 15% of initial wealth with 99% confidence
- Current allocation: equal weight across 5 assets

### Required Return

Using the client cash flow assumptions, the required annual return to grow from $18mm to $23mm over 5 years is:

- Required annual return: 6.02%

## Current Portfolio

The client's current portfolio is:

- `(20%, 20%, 20%, 20%, 20%)`

Assessment:

- Annualized return: about 6.40%
- Return goal: met
- Worst historical drawdown: about -36.8% of initial wealth
- Drawdown goal: not met

Conclusion:

- The current portfolio appears strong enough on return.
- It is too risky for the client's stated downside tolerance.

## Asset Interpretation

From the factor analysis in the project workbook:

- `Asset 1` appears to be a bond-heavy / core fixed income sleeve.
- `Asset 3` appears to be the main high-volatility / drawdown-heavy sleeve.
- The safer portfolios consistently overweight `Asset 1`, `Asset 4`, and `Asset 5`, while keeping `Asset 3` near zero.

## Methodology

Portfolio weights were enumerated under long-only constraints with fixed weight increments. Each candidate portfolio was evaluated using:

- Annualized return
- Annualized volatility
- Rolling 5-year target hit rate
- Rolling 5-year drawdown-safe rate

### Meaning of Target Hit Rate

`Target hit rate` is the fraction of rolling 5-year historical windows in which the portfolio finished at or above the client's $23mm target, after applying:

- portfolio returns
- annual income of $200k
- annual spending of 2% of wealth

This is different from full-sample average return. A higher-return portfolio can still have a lower target hit rate if it is much more volatile and experiences large early losses in many 5-year windows.

## 30% Cap Results

Constraints:

- 5 assets
- long only
- 5% weight increments
- max 30% per asset

Results:

- Total feasible portfolios: 826
- Portfolios meeting drawdown goal: 10
- Portfolios meeting 99% target-hit goal: 0
- Portfolios meeting both goals: 0
- Portfolios with average return above 6.02%: 569

Top drawdown-feasible portfolio:

- `(30%, 10%, 5%, 25%, 30%)`
- Annualized return: 5.39%
- Annualized volatility: 4.57%
- Rolling target hit rate: 67.2%
- Rolling drawdown-safe rate: 100%

Conclusion:

- Under the original cap, no portfolio met both the return and risk mandate.

## Neighborhood Search Around the Top 30% Portfolio

Seed portfolio:

- `(30%, 10%, 5%, 25%, 30%)`

Search settings:

- 1% grid
- maximum 5% shift per asset
- 30% cap maintained

Results:

- Nearby portfolios tested: 2,271
- Portfolios meeting both goals: 0
- Portfolios meeting 99% target-hit goal: 0
- Best drawdown-safe nearby portfolio: `(30%, 14%, 4%, 23%, 29%)`
- Best drawdown-safe nearby annualized return: 5.49%
- Best drawdown-safe nearby rolling target hit rate: 68.9%

Conclusion:

- Small tweaks around the top 30% portfolio improved results slightly, but not enough to meet the client's target.

## 35% Cap Results

Constraints:

- 5% weight increments
- max 35% per asset

Results:

- Total feasible portfolios: 2,226
- Portfolios meeting drawdown goal: 78
- Portfolios meeting 99% target-hit goal: 0
- Portfolios meeting both goals: 0
- Best drawdown-safe annualized return: 5.56%
- Best drawdown-safe rolling target hit rate: 68.9%

Conclusion:

- Raising the cap from 30% to 35% expanded the safe opportunity set.
- It still did not produce a portfolio that satisfied both client goals.

## 50% Cap Results

Constraints:

- 5% weight increments
- max 50% per asset

Results:

- Total feasible portfolios: 7,051
- Portfolios meeting drawdown goal: 627
- Portfolios meeting 99% target-hit goal: 0
- Portfolios meeting both goals: 0
- Portfolios with average return above 6.02%: 4,241
- Best drawdown-safe annualized return: 5.65%
- Best drawdown-safe rolling target hit rate: 75.4%

### Strong Drawdown-Safe Portfolios

- `(50%, 0%, 5%, 5%, 40%)`
  - Return: 5.16%
  - Volatility: 4.29%
  - Target hit rate: 75.4%
  - Drawdown-safe rate: 100%

- `(35%, 0%, 5%, 10%, 50%)`
  - Return: 5.21%
  - Volatility: 4.76%
  - Target hit rate: 73.8%
  - Drawdown-safe rate: 100%

- `(45%, 0%, 5%, 5%, 45%)`
  - Return: 5.19%
  - Volatility: 4.53%
  - Target hit rate: 73.8%
  - Drawdown-safe rate: 100%

- `(40%, 0%, 5%, 10%, 45%)`
  - Return: 5.18%
  - Volatility: 4.51%
  - Target hit rate: 73.8%
  - Drawdown-safe rate: 100%

### Highest-Return but Client-Inappropriate Portfolios

- `(0%, 50%, 45%, 0%, 5%)`
  - Return: 7.29%
  - Volatility: 17.82%
  - Target hit rate: 39.3%
  - Drawdown-safe rate: 0%

- `(0%, 50%, 50%, 0%, 0%)`
  - Return: 7.29%
  - Volatility: 18.86%
  - Target hit rate: 39.3%
  - Drawdown-safe rate: 0%

Conclusion:

- Even with a 50% cap, no portfolio met both the return and risk goals.
- Wider caps improved the risk-feasible set materially.
- The structural tradeoff remained: the safe portfolios did not generate enough return consistency, and the high-return portfolios were too risky.

## Interpretation

The portfolio analysis suggests:

- The current asset menu may be too limited to achieve both client goals simultaneously.
- Risk control pushes the solution toward heavy allocations to the more defensive sleeves.
- Return-seeking pushes the solution toward `Asset 2` and `Asset 3`, but those allocations fail the drawdown mandate.

## Recommended Baseline Portfolio

A reasonable baseline portfolio is:

- `(50%, 0%, 5%, 5%, 40%)`

Why it is a strong baseline:

- It aligns much better with the client's downside preferences than the current equal-weight allocation.
- It achieved the highest rolling target hit rate among the drawdown-safe portfolios tested.
- It maintained a 100% rolling drawdown-safe rate in the historical test.

Why it is not sufficient on its own:

- Its annualized return is only 5.16%, below the 6.02% required return.
- Its rolling target hit rate is 75.4%, well below the 99% requirement.

## Practical Recommendation

The best framing is:

- Use `(50%, 0%, 5%, 5%, 40%)` as the strategic core or baseline portfolio.
- Treat it as the drawdown-control anchor.
- Consider modest opportunistic active management or tactical tilts toward higher-return sleeves when conviction is high.

Important caveat:

- Active tilts should operate inside a clear risk budget.
- The recommendation should not assume that active management automatically solves the shortfall.
- Instead, it should be presented as a controlled attempt to improve return outcomes while preserving the baseline portfolio's stronger risk profile.

## Files

Key files produced during the analysis:

- [portfolio_enumerator.py](/Users/aryanchatterjee/Dev/PM/portfolio_enumerator.py)
- [portfolio_neighborhood_search.py](/Users/aryanchatterjee/Dev/PM/portfolio_neighborhood_search.py)
- [portfolio_enumeration_results.csv](/Users/aryanchatterjee/Dev/PM/portfolio_enumeration_results.csv)
- [portfolio_enumeration_results_cap35.csv](/Users/aryanchatterjee/Dev/PM/portfolio_enumeration_results_cap35.csv)
- [portfolio_enumeration_results_cap50.csv](/Users/aryanchatterjee/Dev/PM/portfolio_enumeration_results_cap50.csv)
- [neighbor_results_cap30_small.csv](/Users/aryanchatterjee/Dev/PM/neighbor_results_cap30_small.csv)
