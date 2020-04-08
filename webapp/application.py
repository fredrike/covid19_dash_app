#!/usr/bin/env python3
# coding: utf-8



import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output




## Import Libraries
import numpy as np
import pandas as pd
#%matplotlib inline
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

## Read Data for Cases, Deaths and Recoveries
ConfirmedCases_raw=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
Deaths_raw=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')
Recoveries_raw=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')

### Melt the dateframe into the right shape and set index
def cleandata(df_raw):
    df_cleaned=df_raw.melt(id_vars=['Province/State','Country/Region','Lat','Long'],value_name='Cases',var_name='Date')
    df_cleaned=df_cleaned.set_index(['Country/Region','Province/State','Date'])
    return df_cleaned

# Clean all datasets
ConfirmedCases=cleandata(ConfirmedCases_raw)
Deaths=cleandata(Deaths_raw)
Recoveries=cleandata(Recoveries_raw)


### Get Countrywise Data
def countrydata(df_cleaned,oldname,newname):
    df_country=df_cleaned.groupby(['Country/Region','Date'])['Cases'].sum().reset_index()
    df_country=df_country.set_index(['Country/Region','Date'])
    df_country.index=df_country.index.set_levels([df_country.index.levels[0], pd.to_datetime(df_country.index.levels[1])])
    df_country=df_country.sort_values(['Country/Region','Date'],ascending=True)
    df_country=df_country.rename(columns={oldname:newname})
    return df_country

ConfirmedCasesCountry=countrydata(ConfirmedCases,'Cases','Total Confirmed Cases')
DeathsCountry=countrydata(Deaths,'Cases','Total Deaths')
RecoveriesCountry=countrydata(Recoveries,'Cases','Total Recoveries')

### Get DailyData from Cumulative sum
def dailydata(dfcountry,oldname,newname):
    dfcountrydaily=dfcountry.groupby(level=0).diff().fillna(0)
    dfcountrydaily=dfcountrydaily.rename(columns={oldname:newname})
    return dfcountrydaily

NewCasesCountry=dailydata(ConfirmedCasesCountry,'Total Confirmed Cases','Daily New Cases')
NewDeathsCountry=dailydata(DeathsCountry,'Total Deaths','Daily New Deaths')
NewRecoveriesCountry=dailydata(RecoveriesCountry,'Total Recoveries','Daily New Recoveries')

CountryConsolidated=pd.merge(ConfirmedCasesCountry,NewCasesCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,NewDeathsCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,DeathsCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,RecoveriesCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,NewRecoveriesCountry,how='left',left_index=True,right_index=True)
CountryConsolidated['Active Cases']=CountryConsolidated['Total Confirmed Cases']-CountryConsolidated['Total Deaths']-CountryConsolidated['Total Recoveries']
CountryConsolidated['Share of Recoveries - Closed Cases']=np.round(CountryConsolidated['Total Recoveries']/(CountryConsolidated['Total Recoveries']+CountryConsolidated['Total Deaths']),2)
CountryConsolidated['Death to Cases Ratio']=np.round(CountryConsolidated['Total Deaths']/CountryConsolidated['Total Confirmed Cases'],3)


# In[6]:


def plotcountry(Country, limit=100, chartcol=px.colors.qualitative.Plotly[0]):
    CountryConsolidated_new = CountryConsolidated[CountryConsolidated['Total Confirmed Cases'] >= limit]
    fig = make_subplots(rows=3, cols=2,shared_xaxes=True, shared_yaxes=True, horizontal_spacing=0.05,
                    specs=[[{}, {}],[{},{}],
                       [{"colspan": 2}, None]],
                    subplot_titles=(f'Total Confirmed Cases in {Country}','Active Cases','Deaths','Recoveries','Death to Cases Ratio'))
    fig.add_trace(go.Scatter(x=CountryConsolidated_new.loc[Country].index,y=CountryConsolidated_new.loc[Country,'Total Confirmed Cases'],
                         mode='lines+markers',
                         name='Confirmed Cases',
                         line=dict(color=chartcol,width=2)),
                         row=1,col=1)
    fig.add_trace(go.Scatter(x=CountryConsolidated_new.loc[Country].index,y=CountryConsolidated_new.loc[Country,'Active Cases'],
                         mode='lines+markers',
                         name='Active Cases',
                         line=dict(color=chartcol,width=2)),
                         row=1,col=2)
    fig.add_trace(go.Scatter(x=CountryConsolidated_new.loc[Country].index,y=CountryConsolidated_new.loc[Country,'Total Deaths'],
                         mode='lines+markers',
                         name='Total Deaths',
                         line=dict(color=chartcol,width=2)),
                         row=2,col=1)
    fig.add_trace(go.Scatter(x=CountryConsolidated_new.loc[Country].index,y=CountryConsolidated_new.loc[Country,'Total Recoveries'],
                         mode='lines+markers',
                         name='Total Recoveries',
                         line=dict(color=chartcol,width=2)),
                         row=2,col=2)
    fig.add_trace(go.Scatter(x=CountryConsolidated_new.loc[Country].index,y=CountryConsolidated_new.loc[Country,'Death to Cases Ratio'],
                         mode='lines+markers',
                         name='Death to Cases Ratio',
                         line=dict(color=chartcol,width=2)),
                         row=3,col=1)
    #fig.update_layout(showlegend=False)
    fig.update_layout(
        autosize=False,
        height=600,
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def plotcountries(Country_L, Country_R, limit=100):
    CC = CountryConsolidated.reset_index()
    CC_L = CC[
        (CC['Total Confirmed Cases'] >= limit) & (CC['Country/Region'] == Country_L)
        ].reset_index(drop=True)
    CC_R = CC[
        (CC['Total Confirmed Cases'] >= limit) & (CC['Country/Region'] == Country_R)
        ].reset_index(drop=True)
    Countries = CC_L.append(CC_R).reset_index()

    plots = ('Total Confirmed Cases','Active Cases','Total Deaths','Total Recoveries','Death to Cases Ratio')
    #fig = make_subplots(rows=3, cols=2,shared_xaxes=True,
    fig = make_subplots(rows=3, cols=2,shared_xaxes=True, shared_yaxes=True, horizontal_spacing=0.03, vertical_spacing=0.06,
                    specs=[[{}, {}],[{},{}],
                       [{"colspan": 2}, None]],
                    subplot_titles=plots)
    for i, sl in enumerate(plots):
        for j, country in enumerate([Country_L, Country_R]):
            fig.add_trace(
                go.Scatter(
                    x=Countries[Countries['Country/Region'] == country]['index'],
                    y=Countries[Countries['Country/Region'] == country][sl],
                    mode='lines+markers',
                    name=country,
                    #name='Confirmed Cases',
                    line=dict(color=px.colors.qualitative.Plotly[j],width=2),
                    legendgroup="group",
                    #color='Country/Region'
                    showlegend = True if (i == 0) else False
                ),
                row=(int)(i/2)+1,
                col=(i%2)+1
            )
    fig.update_layout(
        autosize=False,
        height=800,
        showlegend=False,
    )

    return fig


CountriesList=['Sweden','Norway', 'Denmark', 'Spain', 'Italy', 'Germany','US','France','South Korea','Japan','Singapore']


import dash_core_components as dcc
# import flask

# server = flask.Flask(__name__)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = html.Div([
    html.Label("Filter by first case."),
    dcc.Slider(id='filter-limit',
        min=0,
        max=1000,
        value=100,
        marks={i: str(i) for i in range(0, 1000, 100)},
        step=10,
    ),
    html.Div([
        dcc.Dropdown(
            id='l_country',
            options=[{'label': c, 'value': c}
                     for c in CountriesList],
            value=CountriesList[0]
        ),
        dcc.Graph(
            id='l_graph',
            # hoverData={'points': [{'customdata': 'Japan'}]}
        ),
    ], style={'width': '49%', 'display': 'inline-block'}),
    html.Div([
        dcc.Dropdown(
            id='r_country',
            options=[{'label': c, 'value': c}
                     for c in CountriesList],
            value=CountriesList[1]
        ),
        dcc.Graph(
            id='r_graph',
            # hoverData={'points': [{'customdata': 'Japan'}]}
        ),
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([
        dcc.Graph(
            id='big_graph',
            # hoverData={'points': [{'customdata': 'Japan'}]}
            )]),
])

@app.callback(
    dash.dependencies.Output('l_graph', 'figure'),
    [dash.dependencies.Input('l_country', 'value'),
    dash.dependencies.Input('filter-limit', 'value'),])
def callback_left(country, limit):
    return plotcountry(country, limit, chartcol=px.colors.qualitative.Plotly[0])

@app.callback(
    dash.dependencies.Output('r_graph', 'figure'),
    [dash.dependencies.Input('r_country', 'value'),
    dash.dependencies.Input('filter-limit', 'value'),])
def callback_right(country, limit):
    return plotcountry(country, limit, chartcol=px.colors.qualitative.Plotly[1])

@app.callback(
    dash.dependencies.Output('big_graph', 'figure'),
    [dash.dependencies.Input('l_country', 'value'),
     dash.dependencies.Input('r_country', 'value'),
    dash.dependencies.Input('filter-limit', 'value'),])
def callback_big(country_l, country_r, limit):
    return plotcountries(country_l, country_r, limit)

application = app.server


if __name__ == '__main__':
    app.run_server(debug=True)

