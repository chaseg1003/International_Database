import pandas as pd
from sqlalchemy import create_engine
from dynaconf import Dynaconf

country_columns = ['GEO_ID', '#YR', 'E0', 'IMR', 'POP_DENS', 'SEXRATIO', 'DEPND', 'TFR']

fertility_columns = ['GEO_ID', '#YR', 'ASFR15_19', 'ASFR20_24', 'ASFR25_29', 'ASFR30_34', 'ASFR35_39', 'ASFR40_44', 'ASFR45_49']

country_df = pd.read_csv('International_Database_Midterm/idbzip/idb5yr.txt', 
                         sep='|', 
                         encoding='utf-8', 
                         usecols=country_columns)

fertility_df = pd.read_csv('International_Database_Midterm/idbzip/idb5yr.txt', 
                            sep='|', 
                            encoding='utf-8', 
                            usecols=fertility_columns)

def build_engine():
    settings = Dynaconf(envvar_prefix="DB", load_dotenv=True)
    return create_engine(settings.ENGINE_URL, echo=False)

engine = build_engine()
print(country_df.head())
country_df = country_df[country_df['GEO_ID'].str.len() == 11]
fertility_df = fertility_df[fertility_df['GEO_ID'].str.len() == 11]

country_df = country_df.dropna(subset=['TFR'])
fertility_df = fertility_df.dropna()

country_df = country_df.rename(columns = {'GEO_ID': 'geo_id', 
                                          '#YR': 'year', 
                                          'E0': 'life_expectancy', 
                                          'IMR': 'infant_mortality', 
                                          'POP_DENS': 'population_density', 
                                          'SEXRATIO': 'sex_ratio', 
                                          'DEPND': 'dependency_ratio', 
                                          'TFR': 'fertility_rate'})

fertility_df = fertility_df.rename(columns = {'GEO_ID': 'geo_id', 
                                              '#YR': 'year', 
                                              'ASFR15_19': 'age_specific_fertility_15_19',
                                              'ASFR20_24': 'age_specific_fertility_20_24',
                                              'ASFR25_29': 'age_specific_fertility_25_29',
                                              'ASFR30_34': 'age_specific_fertility_30_34',
                                              'ASFR35_39': 'age_specific_fertility_35_39',
                                              'ASFR40_44': 'age_specific_fertility_40_44',
                                              'ASFR45_49': 'age_specific_fertility_45_49'})

fertility_age_cols = [
    'age_specific_fertility_15_19',
    'age_specific_fertility_20_24',
    'age_specific_fertility_25_29',
    'age_specific_fertility_30_34',
    'age_specific_fertility_35_39',
    'age_specific_fertility_40_44',
    'age_specific_fertility_45_49'
]

# Match the separate age groups to my database schema
fertility_long_df = fertility_df.melt(
    id_vars=['geo_id', 'year'],
    value_vars=fertility_age_cols,
    var_name='age_group',
    value_name='fertility_rate'
)

fertility_long_df['age_group'] = fertility_long_df['age_group'].str.replace(
    'age_specific_fertility_', ''
)

# Make the country codes more readable
fertility_long_df['geo_id'] = fertility_long_df['geo_id'].str[-2:]
country_df['geo_id'] = country_df['geo_id'].str[-2:]

print(country_df.head())
print(country_df.tail())
print(fertility_df.head())
print(fertility_df.tail())
print(fertility_long_df.head())
print(fertility_long_df.tail())


# Check if the number of rows in the long format matches the expected number
expected_rows = len(fertility_df) * 7
actual_rows = len(fertility_long_df)

print(len(fertility_df))
print(f"Expected rows: {expected_rows}, Actual rows: {actual_rows}")

# Save the DataFrames to SQL tables
fertility_long_df.to_sql('fertility_rates', engine, if_exists='replace', index=False)
country_df.to_sql('country_stats', engine, if_exists='replace', index=False)
