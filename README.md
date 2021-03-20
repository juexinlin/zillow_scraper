# zillow scraper

## Requirement
- python3
- [Chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads), note download the version that fits your Chrome version

## Usage

example

```python
python run.py --c charlotte --s nc -o charlotte-nc_2021-02-15 -z
```
inputs
  -c: city
  -s: state
  -o: (optional) output directory, default is current dir
  -z: (optional) zipcodes, separated by ','

## Outputs
#### {city}-{state}_{YY-MM-DD}_{HMS}.csv

Raw data scraped from Zillow

| home_type | address | city | state | zip | price | rent | date_sold | days_on_zillow | bedrooms | bathrooms | area | url|
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| SINGLE_FAMILY | 5246 Autumn Ridge Dr | Wesley Chapel | FL | 33545 | 290000.0 | 2200.0 | 1614067200000 | -1 | 3.0 | 3.0 | 2145.0 | https://www.zillow.com/homedetails/5246-Autumn-Ridge-Dr-Wesley-Chapel-FL-33545/121060376_zpid/ |
| SINGLE_FAMILY | 5337 Treig Ln | Wesley Chapel | FL | 33545 | 268000.0 | 1865.0 | 1614067200000 | -1 | 4.0 | 3.0 | 2200.0 | https://www.zillow.com/homedetails/5337-Treig-Ln-Wesley-Chapel-FL-33545/61000725_zpid/ |

#### {city}-{state}_3ms.csv

Listings that sold in 3 months

| home_type | address | city | state | zip | price | rent | date_sold | days_on_zillow | bedrooms | bathrooms | area | url | days_of_sold |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| SINGLE_FAMILY | 21656 Pearl Crescent Ct | Land O Lakes | FL | 34637 | 315000.0 |  | 1613548800000 | -1 | 3.0 | 2.0 | 1847.0 | https://www.zillow.com/homedetails/21656-Pearl-Crescent-Ct-Land-O-Lakes-FL-34637/121051248_zpid/ | 6
| SINGLE_FAMILY | 21126 Wistful Yearn Dr | Land O Lakes | FL | 34637 | 51500.0 | 2295.0 | 1612771200000 | -1 | 5.0 | 4.0 | 2492.0 | https://www.zillow.com/homedetails/21126-Wistful-Yearn-Dr-Land-O-Lakes-FL-34637/181975425_zpid/ | 15

#### {city}-{state}_summary.csv

Housing statistics for listings sold in 3 months per (zip, bedroom type)
  - count: the number of houses sold
  - price_mean_k: average sold price in thousand
  - monthly_rent: average of z-estimated rent for all available houses
  - price_to_rent_ratio: average price / average rent
  - price_per_sqft_mean: average of price / area
  - price_3m_change: average price of houses sold in 30 days / average price of houses sold between 60 days to 90 days


| bedrooms | zip | count | price_mean_k | monthly_rent | price_to_rent_ratio | price_per_sqft_mean | price_3m_change |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| 3.0 | 33534 | 33.0 | 228.61 | 1707.77 | 11.16 | 137.23 | 1.02 |
| 3.0 | 33541 | 28.0 | 216.54 | 1590.19 | 11.35 | 134.89 | 1.35 |
| 3.0 | 33573 | 69.0 | 265.27 | 1857.31 | 11.9 | 144.99 | 1.04 |
