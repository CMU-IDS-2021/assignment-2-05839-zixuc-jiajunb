import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import altair as alt
import datetime
from datetime import time

st.title("Let's analyze Covid Data 📊.")


abbr2state = {'al': 'Alabama', 'ak': 'Alaska', 'as': 'American Samoa', 'az': 'Arizona', 'ar': 'Arkansas', 'ca': 'California', 'co': 'Colorado', 'ct': 'Connecticut', 'de': 'Delaware', 'dc': 'District of Columbia', 'fl': 'Florida', 'ga': 'Georgia', 'gu': 'Guam', 'hi': 'Hawaii', 'id': 'Idaho', 'il': 'Illinois', 'in': 'Indiana', 'ia': 'Iowa', 'ks': 'Kansas', 'ky': 'Kentucky', 'la': 'Louisiana', 'me': 'Maine', 'md': 'Maryland', 'ma': 'Massachusetts', 'mi': 'Michigan', 'mn': 'Minnesota', 'ms': 'Mississippi', 'mo': 'Missouri', 'mt': 'Montana', 'ne': 'Nebraska', 'nv': 'Nevada', 'nh': 'New Hampshire', 'nj': 'New Jersey', 'nm': 'New Mexico', 'ny': 'New York', 'nc': 'North Carolina', 'nd': 'North Dakota', 'mp': 'Northern Mariana Islands', 'oh': 'Ohio', 'ok': 'Oklahoma', 'or': 'Oregon', 'pa': 'Pennsylvania', 'pr': 'Puerto Rico', 'ri': 'Rhode Island', 'sc': 'South Carolina', 'sd': 'South Dakota', 'tn': 'Tennessee', 'tx': 'Texas', 'ut': 'Utah', 'vt': 'Vermont', 'vi': 'Virgin Islands', 'va': 'Virginia', 'wa': 'Washington', 'wv': 'West Virginia', 'wi': 'Wisconsin', 'wy': 'Wyoming'}

abbr2id = {'ak': '02', 'al': '01', 'ar': '05', 'as': '60', 'az': '04', 'ca': '06', 'co': '08', 'ct': '09', 'dc': '11', 'de': '10', 'fl': '12', 'ga': '13', 'gu': '66', 'hi': '15', 'ia': '19', 'id': '16', 'il': '17', 'in': '18', 'ks': '20', 'ky': '21', 'la': '22', 'ma': '25', 'md': '24', 'me': '23', 'mi': '26', 'mn': '27', 'mo': '29', 'ms': '28', 'mt': '30', 'nc': '37', 'nd': '38', 'ne': '31', 'nh': '33', 'nj': '34', 'nm': '35', 'nv': '32', 'ny': '36', 'oh': '39', 'ok': '40', 'or': '41', 'pa': '42', 'pr': '72', 'ri': '44', 'sc': '45', 'sd': '46', 'tn': '47', 'tx': '48', 'ut': '49', 'va': '51', 'vi': '78', 'vt': '50', 'wa': '53', 'wi': '55', 'wv': '54', 'wy': '56'}

def str2datetime(dd):
    tmp = dd.split('-')
    return datetime.date(int(tmp[0]), int(tmp[1]), int(tmp[2]))

@st.cache
def load_npp_data():
    DATA_PATH = Path('data/covidcast-indicator-combination-confirmed_incidence_prop-2020-02-20-to-2021-02-20.csv')
    df = pd.read_csv(DATA_PATH, sep=',', usecols=['geo_value', 'time_value', 'value'])
    dates = set(df['time_value'].to_numpy())
    
    min_d = str2datetime(min(dates))
    max_d = str2datetime(max(dates))
    df['datetime_date'] = df['time_value'].apply(str2datetime)
    return df, dates, min_d, max_d


def plot_num_covid_by_dates():
    st.header("How does the number of covid cases change by dates?")
    raw_df, _, min_d, max_d = load_npp_data()
    time_bounds = st.slider("Select the date range:", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    df = raw_df[(raw_df['datetime_date'] >= time_bounds[0]) & (raw_df['datetime_date'] <= time_bounds[1])]
    grouped_df = df.groupby(['geo_value'])
    agg_df = grouped_df.agg({'value': np.sum}).reset_index()
    agg_df['state'] = agg_df['geo_value'].apply(lambda x: abbr2state[x])
    agg_df['state_id'] = agg_df['geo_value'].apply(lambda x: int(abbr2id[x]))
    agg_df['log_value'] = agg_df['value'].apply(np.log)
    states = alt.topo_feature('https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json', 'states')
    chart = alt.Chart(agg_df).mark_geoshape().encode(
        shape='geo:G',
        color=alt.Color('log_value:Q'),
        tooltip=['state:N', 'value:Q'],
    ).transform_lookup(
        lookup='state_id',
        from_=alt.LookupData(data=states, key='id'),
        as_='geo'
    ).properties(
        width=550,
    ).project(
        type='albersUsa'
    )

    st.write(chart)

@st.cache
def load_corr_data():
    raw_df, _, _, _ = load_npp_data()
    df1 = pd.read_csv(Path('data/covidcast-fb-survey-smoothed_wearing_mask-2020-12-20-to-2021-03-12.csv'), sep=',', usecols=['geo_value', 'time_value', 'value'])
    df2 = pd.read_csv(Path('data/covidcast-fb-survey-smoothed_accept_covid_vaccine-2020-12-20-to-2021-03-12.csv'), sep=',', usecols=['geo_value', 'time_value', 'value'])

    merged_df = (df1.merge(df2, how='inner', on=['geo_value', 'time_value'])
                    .merge(raw_df, how='inner', on=['geo_value', 'time_value'])
                    .rename(columns={'value_x': 'wear_mask', 'value_y': 'accept_vaccine', 'value': 'covid_cases'}))
    merged_df['datetime'] = merged_df['time_value'].apply(str2datetime)
    merged_df['state'] = merged_df['geo_value'].apply(lambda x: abbr2state[x])
    min_d, max_d = merged_df['datetime'].min(), merged_df['datetime'].max()
    return merged_df, min_d, max_d


def plot_wm_acv_data():
    merged_df, min_d, max_d = load_corr_data()

    picked = alt.selection_interval(encodings=["x"])

    st.header("Does wearing masks somewhat affect the number of covid cases?")
    target_date = st.slider("Select the date range:", min_value=min_d, max_value=max_d, value=max_d)
    target_df = merged_df[merged_df['datetime'] == target_date]

    scatter = alt.Chart(target_df).mark_point().encode(
        alt.X('wear_mask', scale=alt.Scale(zero=False)),
        alt.Y('covid_cases', scale=alt.Scale(zero=False)),
        color=alt.condition(picked, "covid_cases", alt.value("lightgray")),
        tooltip=['state:N', 'wear_mask:Q', 'covid_cases:Q']
    ).add_selection(picked)
    st.write(scatter)

    st.header("Is the corelation between the acceptance of vaccines and  the number of covid cases?")
    scatter2 = alt.Chart(target_df).mark_point().encode(
        alt.X('accept_vaccine', scale=alt.Scale(zero=False)),
        alt.Y('covid_cases', scale=alt.Scale(zero=False)),
        color=alt.condition(picked, "covid_cases", alt.value("lightgray")),
        tooltip=['state:N', 'wear_mask:Q', 'covid_cases:Q']
    ).add_selection(picked)
    st.write(scatter2)
plot_num_covid_by_dates()
plot_wm_acv_data()