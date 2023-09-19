'''
9/19/23, Emily Driano

This script can be run to pull the country data from the UN Data Portal used for calibration. If the 'get' options below
are set to True, this script will utilize the UN Data Portal API to scrape the data - and create files for -
contraceptive prevalence rate (cpr.csv), mortality probability (mortality_prob.csv), mortality trend (mortality_trend.csv),
age-specific fertility rate (asfr.csv), and the population pyramid (which is used in the {country}.py file).

The only setup required is to set the country name (all lower-case) and location ID (which can be found in the file
un_data_country_codes.csv, also located in the data_processing folder). If the country folder already exists, the script
will create the respective files and overwrite or create the files in the existing country folder. If the country folder
does not exist, the script will create a relevant country folder and create/store the newly-created files in this folder.

For more information about the UN Data Portal API, visit this site: https://population.un.org/dataportal/about/dataapi

'''
import os
import pandas as pd
import requests

# COUNTRY CODES FOR REFERENCE
# Senegal ID = 686
# Kenya ID = 404
# Ethiopia ID = 231
# India ID = 356

# Country name and location id(s) (per UN Data Portal); User must update these two variables prior to running.
country = 'ethiopia'
location_id = 686

# Default global variables
startYear = 1960
endYear = 2030

# Set options for web scraping of data; all True by default
get_cpr = True  # Contraceptive prevalence rate
get_mortality_prob = True # Mortality prob
get_mortality_trend = True # Mortality trend
get_asfr = True # Age-specific fertility rate
get_pop_pyramid = True # Population pyramid (5-year age groups for both male/female sex)

# API Base URL
base_url = "https://population.un.org/dataportalapi/api/v1"

# Function that calls a GET request to the UN Data Portal API given the target/uri specified
def get_data(target):
    '''
    Scrapes data from UN data portal using the UN Data Portal API
    https://population.un.org/dataportal/about/dataapi
    '''
    # Get the response, which includes the first page of data as well as information on pagination and number of records
    response = requests.get(target)

    # Converts call into JSON
    j = response.json()

    # Converts JSON into a pandas DataFrame.
    df = pd.json_normalize(
        j['data'])  # pd.json_normalize flattens the JSON to accommodate nested lists within the JSON structure

    # Loop until there are new pages with data
    while j['nextPage'] != None:
        # Reset the target to the next page
        target = j['nextPage']

        # call the API for the next page
        response = requests.get(target)

        # Convert response to JSON format
        j = response.json()

        # Store the next page in a data frame
        df_temp = pd.json_normalize(j['data'])

        # Append next page to the data frame
        df = pd.concat([df, df_temp])
        print("writing file...")

    # If country folder doesn't already exist, create it (location in which created data files will be stored)
    if os.path.exists(f'../{country}') == False:
        os.mkdir(f'../{country}')

    return df

# Called if creating country file cpr.csv
if get_cpr:
    # Set params used in API
    cpr_ind = 1
    mcpr_ind = 2

    # Call API
    target = base_url + f"/data/indicators/{cpr_ind},{mcpr_ind}/locations/{location_id}/start/{startYear}/end/{endYear}"
    df = get_data(target)

    # Reformat data
    df_cpr = df.loc[(df['category'] == 'All women') & (df['variantLabel'] == 'Median') & (df['indicatorId'] == cpr_ind)]
    df_mcpr = df.loc[(df['category'] == 'All women') & (df['variantLabel'] == 'Median') & (df['indicatorId'] == mcpr_ind)]
    df_cpr = df_cpr.filter(['timeLabel', 'value'])
    df_mcpr = df_mcpr.filter(['timeLabel', 'value'])
    df_cpr.rename(columns={'timeLabel': 'year', 'value': 'cpr'}, inplace=True)
    df_mcpr.rename(columns={'timeLabel': 'year', 'value': 'mcpr'}, inplace=True)
    df2 = pd.merge(df_cpr, df_mcpr, on='year')

    # Save file
    df2.to_csv(f'../{country}/cpr.csv', index=False)

# Called if creating country file mortality_prob.csv
if get_mortality_prob: # TODO: Need to confirm this indicator is correct
    # Set params used in API
    ind = 80
    startYear = 2020
    endYear = 2020

    # Call API
    target = base_url + f"/data/indicators/{ind}/locations/{location_id}/start/{startYear}/end/{endYear}"
    df = get_data(target)

    # Reformat data
    df = df.filter(['ageStart', 'sex', 'value'])
    df = df.loc[(df['sex'] == 'Male') | (df['sex'] == 'Female')]
    df['ageStart'] = df['ageStart'].astype('int')
    df = df.rename(columns={'ageStart': 'age'})
    df = df.pivot(index='age', columns='sex', values='value')
    df = df.rename(columns={'Male': 'male', 'Female': 'female'})
    df = df.round(decimals=8)
    df = df[['male', 'female']]

    # Save file
    df.to_csv(f'../{country}/mortality_prob.csv')

# Called if creating country file mortality_trend.csv
if get_mortality_trend:
    # Set params used in API
    ind = 59
    startYear = 1950

    # Call API
    target = base_url + f"/data/indicators/{ind}/locations/{location_id}/start/{startYear}/end/{endYear}"
    df = get_data(target)

    # Reformat data
    df = df.filter(['timeLabel', 'value'])
    df.rename(columns={'timeLabel': 'year', 'value': 'crude_death_rate'}, inplace=True)

    # Save file
    df.to_csv(f'../{country}/mortality_trend.csv', index=False)

# Called if creating country file asfr.csv
if get_asfr:
    # Set params used in API
    ind = 17
    startYear = 1950
    endYear = 2022

    # Call API
    target = base_url + f"/data/indicators/{ind}/locations/{location_id}/start/{startYear}/end/{endYear}"
    df = get_data(target)

    # Reformat data
    df = df.loc[(df['variantLabel'] == 'Median')]
    df.rename(columns={'timeLabel': 'year'}, inplace=True)
    df = df.pivot(index='year', columns='ageLabel', values='value')
    df = df.round(decimals=3).drop('50-54', axis=1)

    # Save file
    df.to_csv(f'../{country}/asfr.csv')

# Called if creating country file pop_pyramid.csv, which is used by the {country}.py file
if get_pop_pyramid: #TODO: this assumes we can take pop values from UN Data Portal API, whereas in country file it says it's taken from WPP. Ok, or should we download data from WPP instead?
    # Set params used in API
    ind = 46
    startYear = 1962
    endYear = 1962

    # Call API
    target = base_url + f"/data/indicators/{ind}/locations/{location_id}/start/{startYear}/end/{endYear}"
    df = get_data(target)

    # Reformat data
    df = df.filter(['ageStart', 'sex', 'value'])
    df = df.loc[(df['sex'] == 'Male') | (df['sex'] == 'Female')]
    df = df.pivot(index='ageStart', columns='sex', values='value')
    df = df[['Male', 'Female']]

    # Save file
    df.to_csv(f'../{country}/pop_pyramid.csv')
