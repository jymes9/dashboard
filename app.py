import random
from datetime import datetime
from collections import defaultdict
import pyrebase
import dash
import dash_daq as daq
import numpy as np
import pandas as pd
import plotly.express as px
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from openpyxl.workbook import Workbook

DATE_START = '2020-12-30'
DATE_END = '2020-12-31'
current_driver = "Shahmir"
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    }, "https://codepen.io/chriddyp/pen/bWLwgP.css",
]
firebaseConfig = {
    "apiKey": "AIzaSyA9Ziyi_GDpAsLSBfn3WpJVc0XTEPqfXNw",
    "authDomain": "test-8cb90.firebaseapp.com",
    "databaseURL": "https://test-8cb90-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "test-8cb90",
    "storageBucket": "test-8cb90.appspot.com",
    "messagingSenderId": "539040571350",
    "appId": "1:539040571350:web:57e34c7c1e1b5bdcc00e77",
    "measurementId": "G-SQB3QGL4HL"}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()
drivers = [user.key() for user in db.get().each()]  # get all drivers


# random walk function generating probabilistic random time series data using a defined start value, threshold,
# step size, min value, max value, and sensor value
def random_walk(
        df, start_value=0, threshold=0.5,
        step_size=1, min_value=0, max_value=8, sensor_value='sensor_type'):
    previous_value = start_value
    for index, row in df.iterrows():
        if previous_value < min_value:
            previous_value = min_value
        if previous_value > max_value:
            previous_value = max_value
        probability = random.random()
        if probability >= threshold:
            df.loc[index, sensor_value] = previous_value + step_size
        else:
            df.loc[index, sensor_value] = previous_value - step_size
        previous_value = df.loc[index, sensor_value]

    return df


# get data from firebase database
def get_firebase_data(driver):
    test_dict = defaultdict(dict)
    for user in db.child(f"{driver}").get().each():
        for k, v in user.val().items():
            date = datetime.strptime(user.key(), '%b %d, %Y').strftime('%Y-%m-%d')
            if k == "Food Types" or k == "Out of range":
                continue
            time = k
            try:
                values = [float(v["Temperature"]), float(v["Humidity"]), float(v["Alcohol content"]),
                          float(v["Light intensity"])]
            except KeyError:
                continue
            test_dict.update({f"{date} {time}": values})
    fire_data = pd.DataFrame.from_dict(test_dict, orient='index',
                                       columns=['Temperature', 'Humidity', 'Alcohol content', 'Light intensity'])
    fire_data.reset_index(level=0, inplace=True)
    fire_data = fire_data.rename(columns={'index': 'Time'})
    fire_data["Time"] = pd.to_datetime(fire_data["Time"])
    fire_data.sort_values("Time", inplace=True)
    return fire_data


# generate data for the different sensor value columns using the random walk function
def generate_data():
    dates = pd.date_range(DATE_START, DATE_END, freq="5min")
    df = pd.DataFrame({
        'Time': dates,
        'Temperature': np.random.normal(0, 1, dates.size),
        'Humidity': np.random.normal(0, 1, dates.size),
        'Alcohol content': np.random.normal(0, 1, dates.size),
        'Light intensity': np.random.normal(0, 1, dates.size)
    })
    # random walk with start value, threshold, step size, min value, max value, sensor value
    df = random_walk(df, start_value=0, threshold=0.5, step_size=0.3, min_value=4, max_value=8,
                     sensor_value='Temperature')
    df = random_walk(df, start_value=0, threshold=0.5, step_size=1, min_value=80, max_value=100,
                     sensor_value='Humidity')
    df = random_walk(df, start_value=0, threshold=0.6, step_size=1, min_value=0, max_value=20,
                     sensor_value='Alcohol content')
    df = random_walk(df, start_value=0, threshold=0.5, step_size=1, min_value=10, max_value=30,
                     sensor_value='Light intensity')
    df.set_index('Time', inplace=True)
    df.reset_index(level=0, inplace=True)
    df = df.rename(columns={'index': 'Time'})
    df["Time"] = pd.to_datetime(df["Time"])  # convert time to datetime format
    df.sort_values("Time", inplace=True)
    return df


def update_db():
    # fire_data = generate_data()
    fire_data = get_firebase_data()
    return fire_data


firebase_data = get_firebase_data("Shahmir")
last_index = len(firebase_data)
# create the dash web application and define the layout
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Food Analytics: Understand Your Food in transit!"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="🚚", className="header-emoji"),
                html.H1(
                    children="Sensorlytics", className="header-title"
                ),
                html.P(
                    children="Bringing data analytics to food in transit.",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Driver name", className="menu-title"),
                        dcc.Dropdown(
                            id="ticker2",
                            options=[{"label": driver, "value": driver}
                                     for driver in drivers],
                            value="Shahmir",
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Sensor Data", className="menu-title"),
                        dcc.Dropdown(
                            id="ticker",
                            options=[{"label": x, "value": x}
                                     for x in firebase_data.columns[1:]],
                            value=firebase_data.columns[1],
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range", className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=firebase_data.Time.min().date(),
                            max_date_allowed=firebase_data.Time.max().date(),
                            start_date=firebase_data.Time.min().date(),
                            end_date=firebase_data.Time.max().date(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div([
                    html.Button("Download Excel", id="btn_xlsx"),
                    dcc.Download(id="download-dataframe-xlsx"),
                ]),
                html.Div(
                    children=dcc.Graph(
                        id="time-series-chart",
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                daq.Gauge(
                    showCurrentValue=True,
                    id="temperature-gauge",
                    color={"gradient": True, "ranges": {"green": [0, 10], "yellow": [10, 20], "red": [20, 30]}},
                    value=14,
                    label='Temperature',
                    units="Celsius",
                    max=30,
                    min=0,
                ),
                daq.Gauge(
                    showCurrentValue=True,
                    id="humidity-gauge",
                    color={"gradient": True, "ranges": {"red": [0, 30], "yellow": [60, 100], "green": [30, 60]}},
                    value=50,
                    label='Relative Humidity',
                    units="%",
                    max=100,
                    min=0,
                ),
                daq.Gauge(
                    showCurrentValue=True,
                    id="Alcohol-gauge",
                    color={"gradient": True, "ranges": {"green": [0, 20], "yellow": [20, 80], "red": [80, 100]}},
                    value=20,
                    label='Alcohol content',
                    units="%",
                    max=100,
                    min=0,
                ),
                daq.Gauge(
                    showCurrentValue=True,
                    id="light-gauge",
                    color={"gradient": True, "ranges": {"green": [0, 20], "yellow": [20, 80], "red": [80, 100]}},
                    value=10,
                    label='Light intensity',
                    units="lux",
                    max=100,
                    min=0,
                ),
                dcc.Interval(id="timing", interval=2000, n_intervals=0),
            ],
            className="gauge-container",
        ),
    ])


@app.callback(
    Output("temperature-gauge", "value"),
    Output("humidity-gauge", "value"),
    Output("Alcohol-gauge", "value"),
    Output("light-gauge", "value"),
    Input("timing", "n_intervals"),
)
def update_g(n_intervals):
    global last_index
    temp = firebase_data.iloc[last_index - 1]["Temperature"]  # mimics data pulled from live database
    humidity = firebase_data.iloc[last_index - 1]["Humidity"]  # mimics data pulled from live database
    alcohol = firebase_data.iloc[last_index - 1]["Alcohol content"]  # mimics data pulled from live database
    light = firebase_data.iloc[last_index - 1]["Light intensity"]  # mimics data pulled from live database
    if (last_index - 1) == 0:
        last_index = len(firebase_data)
    else:
        last_index -= 1
    return temp, humidity, alcohol, light


@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn_xlsx", "n_clicks"),
    prevent_initial_call=True,
)
def download_xls(n_clicks):
    print(current_driver)
    return dcc.send_data_frame(firebase_data.to_excel, f"{current_driver}'s data.xlsx", sheet_name=f"{current_driver}")


@app.callback(
    Output("time-series-chart", "figure"),
    Output("date-range", "min_date_allowed"),
    Output("date-range", "max_date_allowed"),
    Input("ticker", "value"),
    Input("ticker2", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def display_time_series(ticker, ticker2, start_date, end_date):
    global firebase_data
    global current_driver
    current_driver = ticker2
    firebase_data = get_firebase_data(ticker2)
    min_date_allowed = firebase_data.Time.min().date()
    max_date_allowed = firebase_data.Time.max().date()
    mask = ((firebase_data.Time >= start_date) & (firebase_data.Time <= end_date))
    filtered_data = firebase_data.loc[mask, :]
    fig = px.line(filtered_data, x='Time', y=ticker)
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1h", step="hour", stepmode="backward"),
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    return fig, min_date_allowed, max_date_allowed


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=False, port=8080)
