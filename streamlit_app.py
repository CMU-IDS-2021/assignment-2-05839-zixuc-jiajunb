import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import altair as alt
import datetime
from functools import reduce


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
    df = pd.read_csv(covid_case_data, sep=',')
    dates = set(df['date'].to_numpy())
    min_date = str2datetime(min(dates))
    max_date = str2datetime(max(dates))
    df['date'] = df['date'].apply(str2datetime)
    return df, min_date, max_date


@st.cache
def load_social_dist_data(path, factor):
    df = pd.read_csv(path, sep=',')
    df['time_value'] = df['time_value'].apply(str2datetime)
    df['factor'] = factor
    return df


@st.cache
def load_mental_data():
    paths = ['data/covidcast-fb-survey-smoothed_anxious_5d-2020-12-20-to-2021-03-12.csv',
             'data/covidcast-fb-survey-smoothed_depressed_5d-2020-12-20-to-2021-03-12.csv',
             'data/covidcast-fb-survey-smoothed_felt_isolated_5d-2020-12-20-to-2021-03-12.csv']
    keys = ['anxious', 'depressed', 'isolated']
    dfs = []
    for p, k in zip(paths, keys):
        df = pd.read_csv(p, sep=',', usecols=['geo_value', 'time_value',
                         'value']).rename(columns={'value': k})
        dfs.append(df)
    merged_df = reduce(lambda x, y: pd.merge(x, y, how='inner',
                       on=['geo_value', 'time_value']), dfs)
    top_states_by_cases_per_1M = ['nd', 'sd', 'ri', 'ut', 'tn']
    bottom_states_by_cases_per_1M = ['hi', 'vt', 'me', 'or', 'wa']

    def process_df(target_list):
        tsc = set(target_list)
        top_df = merged_df[merged_df['geo_value'].apply(lambda x: x in tsc)].copy()
        top_df['datetime'] = top_df['time_value'].apply(str2datetime)
        top_df = pd.melt(top_df, id_vars=['geo_value', 'datetime'],
                     value_vars=['anxious', 'depressed', 'isolated'])
        top_df['location'] = top_df['geo_value'].apply(lambda x: abbr2state[x])
        return top_df
    top_g_df = process_df(top_states_by_cases_per_1M)
    bottom_g_df = process_df(bottom_states_by_cases_per_1M)
    return top_g_df, bottom_g_df


def plot_mental_graphs():
    st.header("Mental Health in COVID period")
    st.subheader("Q: Does people feel anxious, depressed or isolated during covid periods? Are people's feelings different by the number of cases in their states?")
    "Due to the restriction from the survey data, we can only explore the data starting from 12/20/2020"
    top_df, bottom_df = load_mental_data()
    d  = st.sidebar.slider("Select the date range:", 
                   min_value=datetime.date(2020, 12, 20),
                   max_value=datetime.date(2021, 3, 7),
                   value=datetime.date(2021, 3, 7))
    top_df = top_df[top_df['datetime'] == d]
    bottom_df = bottom_df[bottom_df['datetime'] == d]

    top_chart = alt.Chart(top_df).mark_bar().encode(
        x='value:Q',
        y='location:N',
        color='variable:N'
    ).properties(title='Top 5 States by #covid cases per 100K people')

    bottom_chart = alt.Chart(bottom_df).mark_bar().encode(
        x='value:Q',
        y='location:N',
        color='variable:N',
        tooltip=['location:N', 'value:Q', 'variable:N'],
    ).properties(title='Bottom 5 States by #covid cases per 100K people')

    top_chart
    bottom_chart

    st.subheader("Analysis")
    """In this section, we designed bar plots to see to what extent people felt anxious, depressed or isolated. We found that more people feel isolated than depressed. To see if the number of cases in the state affect the number of people who feel anxious, we collect and plot the data for the states with the top 5 number of cases per 100K people and those with bottom 5 number of cases per 100K people. We found that states with fewer cases felt more isolated but less anxious. It may result from the situation that those states carry out more stick policies which requires social distance and causes the feeling of isolation."""


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
    st.header('A glance of the dataset')

    st.sidebar.write(
        'Note that these are not the only datasets involved in our data analysis. We only show the ones that we think can already well represent the overview of the whole data'
    )

    st.subheader('COVID overall fact dataset in the U.S.A.')
    '''
    This dataset comes from [New York Times](https://github.com/nytimes/covid-19-data), with date ranging from 1/21/2020 to 3/13/2021. The data is collected at the state level, with cumulative number of cases and deaths specified for each group of date and state.
    '''
    covid_df, _, _ = load_covid_data()
    covid_df

    st.subheader(
        'Survey datasets regarding to social distancing, virus protection practices, and mental health'
    )
    '''
    The [CMU Delphi Survey](https://delphi.cmu.edu/covidcast/survey-results/?date=20210221) dataset contains results regarding people's practice of social distancing, how they protect themselves from the virus, and if they have any mental health issues. Since the format of these data files all look similar, we will just show the shop data here as an representative. The earliest start date of the dataset is 12/20/2020, and we selected an end date of 3/12/2021
    '''
    '**Description of the shop data**: Estimated proportion of respondents who went to a “market, grocery store, or pharmacy” in the past 24 hours'
    shop_data = 'data/covidcast-fb-survey-smoothed_shop_1d-2020-12-20-to-2021-03-12.csv'
    shop_df = load_social_dist_data(shop_data, 'Went to shop')
    shop_df


def plot_num_covid_by_dates():
    st.header("Number of COVID cases/deaths in different states and dates")
    st.subheader("Q1: How does the number of COVID cases/deaths vary by states?")
    st.subheader("Q2: And how does the number of COVID cases/deaths change by dates?")

    'For newly increased data in the map chart, it is calculated by averaging the newly increased cases/deaths throughout the entire date range'

    'You may use the sliding bar below to adjust the range of date that you want to explore. The charts will interactively update based on the new range. Have fun :)'

    raw_df, min_d, max_d = load_covid_data()
    time_bounds = st.slider("Select the date range:",
                            min_value=min_d,
                            max_value=max_d,
                            value=(min_d, max_d))
    df = raw_df[(raw_df['date'] >= time_bounds[0]) & (raw_df['date'] <= time_bounds[1])]
    df = df[(df['state'] != 'Northern Mariana Islands') & (df['state'] != 'Guam') &
            (df['state'] != 'Virgin Islands')]
    states = alt.topo_feature('https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json',
                              'states')

    st.sidebar.write(
        'You may view the increased number or cumulative number and COVID cases or deaths by selecting the option in the dropdown menu below. Both the map and line charts will react correspondingly.'
    )
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
    '''
    **Analysis**:  
    From the map chart, it's obvious that California and Texas have the highest number of COVID cases, followed by New York and Florida. Regarding deaths, California, Texas, and New York states are the top 3.  
      
    From the line chart, we can see that we reached the peak daily new cases and deaths at around December 2020 and January 2021, and then it starts to decrease, probably due to the wider use of vaccines.  
      
    Another interesting finding is that the newly increased lines for both cases and deaths are zig-zagging. Empirically there should not be a huge difference of cases and deaths between nearby dates.
    '''


def plot_social_dist_data():
    st.header("Social distancing in COVID period")
    st.subheader("Q1: How does social distancing affect number of COVID cases?")
    st.subheader(
        "Q2: And alternatively, how does number of COVID cases affect social distancing practices?")

    st.sidebar.write('Which social distancing factor(s) are you interested in?')

    'Due to the restriction from the survey data, we can only explore the data starting from 12/20/2020'
    'You may **select the range of date** that you want to further explore in the below COVID cases line chart (second chart)'

    shop_data = 'data/covidcast-fb-survey-smoothed_shop_1d-2020-12-20-to-2021-03-12.csv'
    restaurant_data = 'data/covidcast-fb-survey-smoothed_restaurant_1d-2020-12-20-to-2021-03-12.csv'
    work_school_data = 'data/covidcast-fb-survey-smoothed_work_outside_home_1d-2020-12-20-to-2021-03-12.csv'
    pub_trans_data = 'data/covidcast-fb-survey-smoothed_public_transit_1d-2020-12-20-to-2021-03-12.csv'
    large_event_data = 'data/covidcast-fb-survey-smoothed_large_event_1d-2020-12-20-to-2021-03-12.csv'
    travel_data = 'data/covidcast-fb-survey-smoothed_travel_outside_state_5d-2020-12-20-to-2021-03-12.csv'

    covid_case_df, _, _ = load_covid_data()
    covid_case_df = covid_case_df[(covid_case_df['date'] > datetime.date(2020, 12, 19))
                                  & (covid_case_df['date'] < datetime.date(2021, 3, 12))]
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

        st.sidebar.write(
            'Which kind of chart do you like for displaying factors (first chart)? Stacked area chart can show overall factor contribution, while scatter chart can more easily show individual factor trends'
        )

        option = st.sidebar.selectbox('Show stacked area chart or scatter chart',
                                      ('Stacked area chart', 'Scatter chart'))

        if option == 'Scatter chart':
            base_factors_plot = alt.Chart(factors_df).mark_point()
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
    else:
        covid_case_line_plot
    '''
    **Analysis**:  
    For the first question, as far as we can tell from this time period, we don't see that social distancing practices affect COVID cases. This conclusion might change if we have survey data dating back to the start of COVID.  
      
    For the second question, we can see that there's an approximately inverse relationship between COVID cases and amount of non-social-distancing activities. When there were more COVID cases (e.g. at the end of December), people had better social distancing practice. However, when there were less COVID cases in February, people started to go outside.  
      
    Regarding each social distancing factors, we can find that over half of the people still went to shop for essentials, no matter the number of COVID cases. However, the number of people who went to restaurants and went to work/school did depend a lot on the COVID situation.
    '''


def plot_wm_acv_data():
    merged_df, min_d, max_d = load_corr_data()

    picked = alt.selection_interval(encodings=["x"])

    st.header("Does wearing masks somewhat affect the number of COVID cases?")
    target_date = st.sidebar.slider("Select the date range:", min_value=min_d, max_value=max_d, value=max_d)
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
    st.subheader("Analysis:")
    """In this section, we designed two scatter plots to see if there is any correlation between people’s acceptance to masks and vaccine, and the number of COVID case increases. We characterize each state as a single point in the graph. The x axis shows how many people in the survey pool are likely to wale at masks, and the y axis shows the number of COVID case increases in the state. If the points seemed to distribute along certain lines, it means there is some correlation. We found that the relation between the acceptance to masks and the number of COVID case increases fluctuate strongly as we change the day where the data are collected,”. It means based on this portion of data we have, there is not strong correlation between the acceptance to masks and the number of covid case increases. It may result from the fact that the functioning of masks takes time to be reflected as the decrease in the number of COVID cases increases. An interesting observation is that the point cluster is moving toward the right as the time slides to the right, which means more and more people start to take masks. """
    """From the second figure, we can see a weak anti-correlation between the acceptance of vacancies and the number of COVID case increases: as more people accept vaccines, the number of COVID cases increases slower."""



st.sidebar.title('COVID Question Explorer')
page = st.sidebar.selectbox("Choose a question to explore", [
    'Overview of dataset', 'COVID vs state and date', 'Effect of social distancing',
    'COVID, mask, and vaccine', "Mental State"
])

st.title("Let's analyze COVID Data 📊.")

st.text('By Jiajun Bao and Zixu Chen')

if page == 'Overview of dataset':
    plot_dataset_overview()
elif page == 'COVID vs state and date':
    plot_num_covid_by_dates()
elif page == 'Effect of social distancing':
    plot_social_dist_data()
elif page == 'COVID, mask, and vaccine':
    plot_wm_acv_data()
elif page == "Mental State":
    plot_mental_graphs()
