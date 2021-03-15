import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import altair as alt
import datetime
from datetime import time

abbr2state = {
    'al': 'Alabama',
    'ak': 'Alaska',
    'as': 'American Samoa',
    'az': 'Arizona',
    'ar': 'Arkansas',
    'ca': 'California',
    'co': 'Colorado',
    'ct': 'Connecticut',
    'de': 'Delaware',
    'dc': 'District of Columbia',
    'fl': 'Florida',
    'ga': 'Georgia',
    'gu': 'Guam',
    'hi': 'Hawaii',
    'id': 'Idaho',
    'il': 'Illinois',
    'in': 'Indiana',
    'ia': 'Iowa',
    'ks': 'Kansas',
    'ky': 'Kentucky',
    'la': 'Louisiana',
    'me': 'Maine',
    'md': 'Maryland',
    'ma': 'Massachusetts',
    'mi': 'Michigan',
    'mn': 'Minnesota',
    'ms': 'Mississippi',
    'mo': 'Missouri',
    'mt': 'Montana',
    'ne': 'Nebraska',
    'nv': 'Nevada',
    'nh': 'New Hampshire',
    'nj': 'New Jersey',
    'nm': 'New Mexico',
    'ny': 'New York',
    'nc': 'North Carolina',
    'nd': 'North Dakota',
    'mp': 'Northern Mariana Islands',
    'oh': 'Ohio',
    'ok': 'Oklahoma',
    'or': 'Oregon',
    'pa': 'Pennsylvania',
    'pr': 'Puerto Rico',
    'ri': 'Rhode Island',
    'sc': 'South Carolina',
    'sd': 'South Dakota',
    'tn': 'Tennessee',
    'tx': 'Texas',
    'ut': 'Utah',
    'vt': 'Vermont',
    'vi': 'Virgin Islands',
    'va': 'Virginia',
    'wa': 'Washington',
    'wv': 'West Virginia',
    'wi': 'Wisconsin',
    'wy': 'Wyoming'
}

abbr2id = {
    'ak': '02',
    'al': '01',
    'ar': '05',
    'as': '60',
    'az': '04',
    'ca': '06',
    'co': '08',
    'ct': '09',
    'dc': '11',
    'de': '10',
    'fl': '12',
    'ga': '13',
    'gu': '66',
    'hi': '15',
    'ia': '19',
    'id': '16',
    'il': '17',
    'in': '18',
    'ks': '20',
    'ky': '21',
    'la': '22',
    'ma': '25',
    'md': '24',
    'me': '23',
    'mi': '26',
    'mn': '27',
    'mo': '29',
    'ms': '28',
    'mt': '30',
    'nc': '37',
    'nd': '38',
    'ne': '31',
    'nh': '33',
    'nj': '34',
    'nm': '35',
    'nv': '32',
    'ny': '36',
    'oh': '39',
    'ok': '40',
    'or': '41',
    'pa': '42',
    'pr': '72',
    'ri': '44',
    'sc': '45',
    'sd': '46',
    'tn': '47',
    'tx': '48',
    'ut': '49',
    'va': '51',
    'vi': '78',
    'vt': '50',
    'wa': '53',
    'wi': '55',
    'wv': '54',
    'wy': '56'
}


def str2datetime(dd):
    tmp = dd.split('-')
    return datetime.date(int(tmp[0]), int(tmp[1]), int(tmp[2]))


@st.cache
def load_npp_data():
    DATA_PATH = Path(
        'data/covidcast-indicator-combination-confirmed_incidence_prop-2020-02-20-to-2021-02-20.csv'
    )
    df = pd.read_csv(DATA_PATH, sep=',', usecols=['geo_value', 'time_value', 'value'])
    dates = set(df['time_value'].to_numpy())
    min_d = str2datetime(min(dates))
    max_d = str2datetime(max(dates))
    df['datetime_date'] = df['time_value'].apply(str2datetime)
    return df, dates, min_d, max_d


@st.cache
def load_covid_data():
    covid_case_data = 'data/covid-us-states.csv'
    df = pd.read_csv(covid_case_data, sep=',', usecols=['state', 'date', 'cases', 'deaths', 'fips'])
    dates = set(df['date'].to_numpy())
    min_date = str2datetime(min(dates))
    max_date = str2datetime(max(dates))
    df['date'] = df['date'].apply(str2datetime)
    return df, min_date, max_date


@st.cache
def load_covid_range_data(min_date, max_date):
    covid_case_data = 'data/covid-us-states.csv'
    df = pd.read_csv(covid_case_data, sep=',', usecols=['state', 'date', 'cases', 'deaths'])
    df = df[(df['date'] > min_date) & (df['date'] < max_date)]
    df['date'] = df['date'].apply(str2datetime)
    return df


@st.cache
def load_social_dist_data(path, factor):
    df = pd.read_csv(path, sep=',', usecols=['geo_value', 'time_value', 'value'])
    df['time_value'] = df['time_value'].apply(str2datetime)
    df['factor'] = factor
    return df


@st.cache
def load_corr_data():
    raw_df, _, _, _ = load_npp_data()
    df1 = pd.read_csv(
        Path('data/covidcast-fb-survey-smoothed_wearing_mask-2020-12-20-to-2021-03-12.csv'),
        sep=',',
        usecols=['geo_value', 'time_value', 'value'])
    df2 = pd.read_csv(
        Path('data/covidcast-fb-survey-smoothed_accept_covid_vaccine-2020-12-20-to-2021-03-12.csv'),
        sep=',',
        usecols=['geo_value', 'time_value', 'value'])

    merged_df = (df1.merge(df2, how='inner',
                           on=['geo_value',
                               'time_value']).merge(raw_df,
                                                    how='inner',
                                                    on=['geo_value',
                                                        'time_value']).rename(columns={
                                                            'value_x': 'wear_mask',
                                                            'value_y': 'accept_vaccine',
                                                            'value': 'covid_cases'
                                                        }))
    merged_df['datetime'] = merged_df['time_value'].apply(str2datetime)
    merged_df['state'] = merged_df['geo_value'].apply(lambda x: abbr2state[x])
    min_d, max_d = merged_df['datetime'].min(), merged_df['datetime'].max()
    return merged_df, min_d, max_d


def plot_dataset_overview():
    st.header("Overview of dataset itself")

    'COVID dataset in the U.S.A.'
    covid_df, _, _ = load_covid_data()
    covid_df

    'Estimated proportion of respondents who went to a “market, grocery store, or pharmacy” in the past 24 hours'
    shop_data = 'data/covidcast-fb-survey-smoothed_shop_1d-2020-12-20-to-2021-03-12.csv'
    shop_df = load_social_dist_data(shop_data, 'Went to shop')
    shop_df


def plot_num_covid_by_dates():
    st.header("How does the number of COVID cases change by dates?")
    raw_df, min_d, max_d = load_covid_data()
    time_bounds = st.sidebar.slider("Select the date range:",
                                    min_value=min_d,
                                    max_value=max_d,
                                    value=(min_d, max_d))
    df = raw_df[(raw_df['date'] >= time_bounds[0]) & (raw_df['date'] <= time_bounds[1])]
    df = df[(df['state'] != 'Northern Mariana Islands') & (df['state'] != 'Guam') &
            (df['state'] != 'Virgin Islands')]
    states = alt.topo_feature('https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json',
                              'states')

    num_option = st.sidebar.selectbox('Newly increased or cumulative',
                                      ('Newly increased', 'Cumulative'))

    line_df = df.groupby(['date']).agg({'cases': np.sum, 'deaths': np.sum}).reset_index()
    if num_option == 'Cumulative':
        map_df = df.groupby(['state']).agg({
            'cases': np.max,
            'deaths': np.max,
            'fips': np.max
        }).reset_index()
    else:
        sorted_df = df.sort_values(by=['state', 'date'])
        sorted_df['cases'] = sorted_df.groupby(['state'])['cases'].diff().fillna(0)
        sorted_df['deaths'] = sorted_df.groupby(['state'])['deaths'].diff().fillna(0)
        map_df = sorted_df.groupby(['state']).agg({
            'cases': np.mean,
            'deaths': np.mean,
            'fips': np.max
        }).reset_index()

        line_df['cases'] = line_df['cases'].diff()
        line_df['deaths'] = line_df['deaths'].diff()

    data_option = st.sidebar.selectbox('Cases or deaths', ('Cases', 'Deaths'))

    if data_option == 'Deaths':
        y_data = "deaths:Q"
        y_title = 'Deaths'
    else:
        y_data = "cases:Q"
        y_title = 'Cases'

    select = alt.selection_single(on='mouseover', empty='none')

    map_chart = alt.Chart(map_df).mark_geoshape().encode(
        shape='geo:G',
        color=alt.condition(select, alt.value('red'), y_data),
        tooltip=['state:N', y_data],
    ).transform_lookup(lookup='fips', from_=alt.LookupData(data=states, key='id'),
                       as_='geo').properties(
                           width=650, ).project(type='albersUsa').add_selection(select)

    map_chart

    line_chart = alt.Chart(line_df).mark_line().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y(
            y_data,
            title=y_title,
        ),
        tooltip=[alt.Tooltip(y_data, title=y_title),
                 alt.Tooltip('date:T', title="Date")]).properties(width=650)

    line_chart


def plot_social_dist_data():
    st.header("Zooming into the period of 12/20/2020 - 03/21/2021:")
    st.header("How does social distancing affect number of COVID cases?")
    st.header(
        "And alternatively, how does number of COVID cases affect social distancing practices?")

    shop_data = 'data/covidcast-fb-survey-smoothed_shop_1d-2020-12-20-to-2021-03-12.csv'
    restaurant_data = 'data/covidcast-fb-survey-smoothed_restaurant_1d-2020-12-20-to-2021-03-12.csv'
    work_school_data = 'data/covidcast-fb-survey-smoothed_work_outside_home_1d-2020-12-20-to-2021-03-12.csv'
    pub_trans_data = 'data/covidcast-fb-survey-smoothed_public_transit_1d-2020-12-20-to-2021-03-12.csv'
    large_event_data = 'data/covidcast-fb-survey-smoothed_large_event_1d-2020-12-20-to-2021-03-12.csv'
    travel_data = 'data/covidcast-fb-survey-smoothed_travel_outside_state_5d-2020-12-20-to-2021-03-12.csv'

    covid_case_df = load_covid_range_data('2020-12-19', '2021-03-12')
    covid_case_df = covid_case_df.groupby(['date'])
    covid_case_df = covid_case_df.agg({'cases': np.sum}).reset_index()
    covid_case_df['cases'] = covid_case_df['cases'].diff()

    factors = st.sidebar.multiselect('Social distancing factors to include:', [
        'Went to shop', 'Went to restaurant', 'Went to work/school', 'Used public Transportation',
        'Attended large events', 'Traveled Out of State'
    ], [
        'Went to shop', 'Went to restaurant', 'Went to work/school', 'Used public Transportation',
        'Attended large events', 'Traveled Out of State'
    ])

    factors_list = []
    if 'Went to shop' in factors:
        shop_df = load_social_dist_data(shop_data, 'Went to shop')
        factors_list.append(shop_df)
    if 'Went to restaurant' in factors:
        restaurant_df = load_social_dist_data(restaurant_data, 'Went to restaurant')
        factors_list.append(restaurant_df)
    if 'Went to work/school' in factors:
        work_school_df = load_social_dist_data(work_school_data, 'Went to work/school')
        factors_list.append(work_school_df)
    if 'Used public Transportation' in factors:
        pub_trans_df = load_social_dist_data(pub_trans_data, 'Used public Transportation')
        factors_list.append(pub_trans_df)
    if 'Attended large events' in factors:
        large_event_df = load_social_dist_data(large_event_data, 'Attended large events')
        factors_list.append(large_event_df)
    if 'Traveled Out of State' in factors:
        travel_df = load_social_dist_data(travel_data, 'Traveled Out of State')
        factors_list.append(travel_df)

    date_select = alt.selection_interval(encodings=['x'])

    covid_case_line_plot = alt.Chart(covid_case_df).mark_line(point=True).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y(
            "cases:Q",
            title="New cases",
        ),
        tooltip=[alt.Tooltip('cases:Q', title="New cases"),
                 alt.Tooltip('date:T',
                             title="Date")]).add_selection(date_select).properties(width=550,
                                                                                   height=200)

    if len(factors_list) > 0:
        factors_df = pd.concat(factors_list)
        factors_df = factors_df.groupby(['factor', 'time_value'])
        factors_df = factors_df.agg({'value': np.mean}).reset_index()

        option = st.sidebar.selectbox('Show stacked area chart or line chart',
                                      ('Stacked area chart: show overall factor contribution',
                                       'Line chart: show individual factor trends'))

        if option == 'Line chart: show individual factor trends':
            base_factors_plot = alt.Chart(factors_df).mark_line(point=True)
        else:
            base_factors_plot = alt.Chart(factors_df).mark_area()

        base_factors_plot = base_factors_plot.encode(x=alt.X("time_value:T", title="Date"),
                                                     y=alt.Y(
                                                         "value:Q",
                                                         title="Num of person/100 persons",
                                                     ),
                                                     color=alt.Color(
                                                         "factor:N",
                                                         legend=alt.Legend(title="Factors"),
                                                     ),
                                                     tooltip=[
                                                         alt.Tooltip('factor', title="Factor"),
                                                         alt.Tooltip(
                                                             'value',
                                                             title="Avg persons/100 persons"),
                                                         alt.Tooltip('time_value', title="Date")
                                                     ]).properties(width=550)

        scaled_factors_plot = base_factors_plot.encode(
            alt.X('time_value:T', title="Date", scale=alt.Scale(domain=date_select)))

        scaled_factors_plot & covid_case_line_plot

        'You may **select the range of date** that you want to further explore in the **above COVID cases line plot**'
    else:
        covid_case_line_plot


def plot_wm_acv_data():
    merged_df, min_d, max_d = load_corr_data()

    picked = alt.selection_interval(encodings=["x"])

    st.header("Does wearing masks somewhat affect the number of COVID cases?")
    target_date = st.slider("Select the date range:", min_value=min_d, max_value=max_d, value=max_d)
    target_df = merged_df[merged_df['datetime'] == target_date]

    scatter = alt.Chart(target_df).mark_point().encode(
        alt.X('wear_mask', scale=alt.Scale(zero=False)),
        alt.Y('covid_cases', scale=alt.Scale(zero=False)),
        color=alt.condition(picked, "covid_cases", alt.value("lightgray")),
        tooltip=['state:N', 'wear_mask:Q', 'covid_cases:Q']).add_selection(picked)
    st.write(scatter)

    st.header(
        "Is the corelation between the acceptance of vaccines and  the number of COVID cases?")
    scatter2 = alt.Chart(target_df).mark_point().encode(
        alt.X('accept_vaccine', scale=alt.Scale(zero=False)),
        alt.Y('covid_cases', scale=alt.Scale(zero=False)),
        color=alt.condition(picked, "covid_cases", alt.value("lightgray")),
        tooltip=['state:N', 'wear_mask:Q', 'covid_cases:Q']).add_selection(picked)
    st.write(scatter2)


st.sidebar.title('COVID Question Explorer')
page = st.sidebar.selectbox("Choose a question to explore", [
    'Overview of dataset', 'COVID cases vs date and state', 'Effect of social distancing',
    'COVID, mask, and vaccine'
])

st.title("Let's analyze COVID Data 📊.")

if page == 'Overview of dataset':
    plot_dataset_overview()
elif page == 'COVID cases vs date and state':
    plot_num_covid_by_dates()
elif page == 'Effect of social distancing':
    plot_social_dist_data()
elif page == 'COVID, mask, and vaccine':
    plot_wm_acv_data()
