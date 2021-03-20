import os
import requests
import argparse
import json
import time
import glob
import numpy as np
import pandas as pd
from lxml import html
from datetime import datetime
from uszipcode import SearchEngine
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

COMPONENT_PATH = os.path.dirname(os.path.abspath(__file__))
CHROMEDRIVER_PATH = "/Users/juexinlin/scripts/zillow_data/chromedriver"

def get_zips_for_city(city, state):
    # get zips that with income greater than median
    search = SearchEngine(simple_zipcode=True)
    res = search.by_city_and_state(city, state,returns=0)
    print('# of zips are found: {}'.format(len(res)))
    df_zip = pd.DataFrame([{'zip': e.zipcode, 'home_value': e.median_home_value, 'income': e.median_household_income} for e in res])
    income_threshold = df_zip['income'].quantile(0.5)
    zips = df_zip.loc[df_zip['income']>=income_threshold, 'zip'].values
    print('# of zips are found with income greater than median: {}'.format(len(zips)))
    return zips

def init_driver(file_path):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(executable_path=file_path, 
                              options=options)
    driver.wait = WebDriverWait(driver, 10)
    return driver

def clean(text):
    if text:
        return ' '.join(' '.join(text).split())
    return None


def get_headers():
    # Creating headers.
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'accept-encoding': 'gzip, deflate, sdch, br',
               'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
               'cache-control': 'max-age=0',
               'upgrade-insecure-requests': '1',
               'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    return headers


def create_url(zipcode, filter):
    # Creating Zillow URL based on the filter.

    if filter == "newest":
        url = "https://www.zillow.com/homes/recently_sold/house_type/{0}_rb/0_singlestory/days_sort/".format(zipcode)
    elif filter == "cheapest":
        url = "https://www.zillow.com/homes/recently_sold/house_type/{0}_rb/0_singlestory/pricea_sort/".format(zipcode)
    else:
        url = "https://www.zillow.com/homes/recently_sold/house_type/{0}_rb/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy".format(zipcode)
    return url


def save_to_file(response):
    # saving response to `response.html`

    with open("response.html", 'w') as fp:
        fp.write(response.text)

def get_response(url):
    # Getting response from zillow.com.

    for i in range(5):
        response = requests.get(url, headers=get_headers())
        print("status code received:", response.status_code)
        if response.status_code != 200:
            # saving response to file for debugging purpose.
            save_to_file(response)
            continue
        else:
            return response
    return None

def get_data_from_json(raw_json_data):
    # getting data from json (type 2 of their A/B testing page)
    cleaned_data = clean(raw_json_data).replace('<!--', "").replace("-->", "")
    properties_list = []

    try:
        json_data = json.loads(cleaned_data)
        search_results = json_data.get('cat1').get('searchResults').get('listResults', [])

        for properties in search_results:
            property_info = properties.get('hdpData', {}).get('homeInfo', {})
            htype = property_info.get('homeType', '')
            address = property_info.get('streetAddress', '')
            city = property_info.get('city', '')
            state = property_info.get('state', '')
            zipcode = property_info.get('zipcode', '')
            price = property_info.get('price', np.nan)
            rent = property_info.get('rentZestimate',np.nan)
            date_sold = property_info.get('dateSold', np.nan)
            doz = property_info.get("daysOnZillow", np.nan)
            bedrooms = properties.get('beds', np.nan)
            bathrooms = properties.get('baths', np.nan)
            area = properties.get('area', np.nan)
            info = f'{bedrooms} bds, {bathrooms} ba ,{area} sqft'
            property_url = properties.get('detailUrl')
            
            data = {
                'home_type': htype,
                'address': address,
                'city': city,
                'state': state,
                'zip': zipcode,
                'price': price,
                'rent': rent,
                'date_sold': date_sold,
                'days_on_zillow': doz,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'area': area,
                'url': property_url
            }
            properties_list.append(data)

        return properties_list

    except ValueError:
        print("Invalid json")
        return []


def parse(driver, zipcode, filter="newest", pages=20):
    base_url = create_url(zipcode, filter)
    url = base_url
    
    driver.get(url)
    
    properties_list = []
    
    for i in range(pages):
        print('scraping: ' + url)
        
#         response = get_response(url)        
#         if not response:
#             print("Failed to fetch the page, please check `response.html` to see the response received from zillow.com.")
#             return None
                
        parser = html.fromstring(driver.page_source)
        print("parsing from json data")
        raw_json_data = parser.xpath('//script[@data-zrr-shared-data-key="mobileSearchPageStore"]//text()')
        properties_list_curr_page = get_data_from_json(raw_json_data)
        properties_list.extend(properties_list_curr_page)
        
        if not properties_list_curr_page and not properties_list:
            break
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        is_last_page = soup.find("a", {"title":"Next page"}).has_attr("tabindex")
        
        if not is_last_page:
            url = base_url + f'{i+2}_p'
            driver.get(url)
        else:
            break
            
    return properties_list

def execute(output_dir, city, state, zips=[], max_num_retries=2):
    output_data = []
    if not zips:
        zips = get_zips_for_city(city, state)
        
    driver = init_driver(CHROMEDRIVER_PATH)
    
    for i in range(len(zips)):
        num_tries = 0
        while True:
            print("Entering search zip %s of %s" % (str(i + 1), str(len(zips))))
            try:
                out_zip = parse(driver, zips[i], filter="newest", pages=20)
                output_data.extend(out_zip)
                break
            except (ValueError, AttributeError):
                os.system('say "break"')
                if num_tries >= max_num_retries:
                    print('skipping:', zips[i])
                    break
                print('retrying:', zips[i])
                time.sleep(300)
                num_tries += 1
        time.sleep(np.random.lognormal(0,1))

    driver.quit()
    
    file_name = "%s-%s_%s_%s.csv" % (city, state, str(time.strftime("%Y-%m-%d")), str(time.strftime("%H%M%S")))
    df_res = pd.DataFrame(output_data).drop_duplicates()
    df_res.to_csv(os.path.join(output_dir, file_name), index = False, encoding = "UTF-8")

    generate_summary_stat(output_dir, city, state)
    
def generate_summary_stat(output_dir, city, state):
    city_state = '-'.join([city, state])
    date = os.path.basename(output_dir).split('_')[-1]
    files = glob.glob(os.path.join(output_dir,'{0}_{1}*.csv'.format(city_state, date)))
    # read output files
    df = pd.DataFrame()
    for f in files:
        df = pd.concat([df, pd.read_csv(f)], axis = 0)
    df.drop_duplicates(inplace=True)
    df = df.reset_index(drop=True)
    # compute the days of sold
    df['days_of_sold'] = df['date_sold'].apply(lambda x: (datetime.today() - datetime.utcfromtimestamp(x/1000)).days)
    # export 3month data
    df_3ms = df[df.days_of_sold<=90]
    df_3ms.to_csv(os.path.join(output_dir, '{0}_3ms.csv'.format(city_state)), index=False)
    # generate summaries
    df_target = df_3ms[(df_3ms.area>1000) & (df_3ms.bedrooms.isin([3,4,5])) & df_3ms.price]
    df_target['months_of_sold'] = 1*(df_target['days_of_sold']>30) + 1*(df_target['days_of_sold']>60) + 1
    def f(x):
        return pd.Series({
            'count': x.shape[0],
            'price_mean_k': x['price'].mean()/1000,
            'monthly_rent': x['rent'].mean(),
            'price_to_rent_ratio': x['price'].mean()/(x['rent'].mean()*12),
            'price_per_sqft_mean': (x['price']/x['area']).mean(),
            'price_3m_change': (x.loc[x['months_of_sold']==1,'price'].mean()/x.loc[x['months_of_sold']==3,'price'].mean()),
            'rent_3m_change': (x.loc[x['months_of_sold']==1,'rent'].mean()/x.loc[x['months_of_sold']==3,'rent'].mean()),
            'price_per_sqft_median': (x['price']/x['area']).median(),
            'price_per_sqft_q1': (x['price']/x['area']).quantile(0.25),
            'price_sold_1m': x.loc[x['months_of_sold']==1,'price'].mean(),
            'count_sold_1m': x.loc[x['months_of_sold']==1,'price'].count(),
            'price_sold_2m': x.loc[x['months_of_sold']==2,'price'].mean(),
            'price_sold_3m': x.loc[x['months_of_sold']==3,'price'].mean(),
            'count_sold_3m': x.loc[x['months_of_sold']==3,'price'].count()
        })
    df_summary = df_target.groupby(['bedrooms', 'zip', 'city']).apply(f).reset_index().sort_values(['bedrooms', 'price_to_rent_ratio'], ascending=[True,True]).round(2)
    # export summary table
    columns = ['city','bedrooms','zip','count','price_mean_k','monthly_rent','price_to_rent_ratio','price_per_sqft_mean','price_3m_change']
    df_summary[columns].to_csv(os.path.join(output_dir,'{}_summary.csv'.format(city_state)), index=False)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--city', type=str, help='city name')
    argparser.add_argument('-s', '--state', type=str, help='state name')
    argparser.add_argument('-o', '--output_dir', type=str, default=COMPONENT_PATH)
    argparser.add_argument('-z', '--zips', type=str, default='')
    args = argparser.parse_args()
    
    if args.zips:
        zips = args.zips.split(',')
    else:
        zips = []
        
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
            
    execute(args.output_dir, args.city, args.state, zips)