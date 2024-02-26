# ynab-sankey

## Overview
This repository provides functionality to create a sankey chart. This outputs a text file that is designed to be copy and pasted into [SankeyMatic](https://sankeymatic.com/) or a similar tool.

## Requirements
In order to use this you need your [YNAB API key](https://api.ynab.com/) as well as the budget id of the budget you want to work with.

To get the budget id run the following command and grab the corresponding id.
```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://api.ynab.com/v1/budgets
```

Then open `ynab_sankey.py` and update the following two lines at the top:
```python
# User inputs
api_key = 'yourapikeyhere'
budget_id = 'yourbudgetidhere'
```

## Run the script

To run the script:
```bash
python ynab_sankey.py
```
