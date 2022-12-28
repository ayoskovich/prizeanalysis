from dash import Dash, html, dcc

import plotly.express as px
import pandas as pd

import plotly.graph_objects as go
from plotly.graph_objs._figure import Figure

import json
import sqlalchemy
import pandas as pd
import boto3

def load_data() -> pd.DataFrame:
    client = boto3.client("secretsmanager", region_name='us-east-1')
    response = client.get_secret_value(
        SecretId="rds!db-b98bc80d-69cd-4918-aa32-f0a33add0630"
    )["SecretString"]

    response = json.loads(response)
    user, password = response["username"], response["password"]
    hostname = "lotto.cvospk6lbhi0.us-east-1.rds.amazonaws.com"
    port = 5432
    databasename = "postgres"

    cstring = f"postgresql://{user}:{password}@{hostname}:{port}/{databasename}"
    eng = sqlalchemy.create_engine(cstring)
    with eng.begin() as conn:
        df = pd.read_sql("""
        select * from soldtickets st
        left join (select game_number as gn, num, den from odds) as o 
        on st.game_number = o.gn
        """, con=conn)

    return df

df = load_data()

def droppy() -> dcc.Dropdown:
    rows = (
        df[['game_title', 'game_number']]
        .drop_duplicates()
        .to_dict(orient='records')
    )

    return dcc.Dropdown(
        options = [
            {'label': row['game_title'], 'value': row['game_number']}
            for row in rows
        ],
        value=rows[0]['game_number'],
        id='my-dropdown'
    )

def topbot(df: pd.DataFrame, n=5) -> pd.DataFrame:
    """ Returns a dataframe with the top and bottom
    stacked. 
    """
    return pd.concat([df.head(n), df.tail(n)])

def topbottable() -> Figure:
    """ This figure shows the top and bottom 5 prizes and the games that 
    have them left. 
    """
    N = 5
    out = (
        df
        .loc[lambda x: x['timestamp'] == x['timestamp'].max()]
        .assign(remaining = lambda x: x.prizes_remaining / x.prizes_start)
        .sort_values(by='remaining')
        .pipe(topbot, n=N)
        [['prize_amount', 'prizes_start', 'game_title', 'price', 'den', 'remaining']]
        .assign(
            price = lambda x: x['price'].apply(lambda x: "${:,.2f}".format(x)),
            prize_amount = lambda x: x['prize_amount'].apply(lambda x: "${:,.0f}".format(x))
        )
        .rename(columns={
            'prize_amount': 'Prize Amount',
            'prizes_start': '# Starting Prizes',
            'price': 'Price',
            'den': 'Odds',
            'game_title': 'Game Title',
            'remaining': '% Prizes Remaining'
        })
    )
    out.style.format({
        "Price": "${:,d}"
    })

    out['Color'] = '#857ff5'
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=[x for x in out.columns if x != 'Color'],
                    line_color='black', fill_color='white'
                ),
                cells=dict(
                    values=out.drop(labels='Color', axis=1).transpose().values.tolist(),
                    line_color='black',
                    fill_color=[out.Color]
                )
            ),
        ])
    fig.update_layout(title="Top and Bottom 5 % Tickets Remaining")
    return fig

def remaininghist() -> Figure:
    """ A histogram showing the distribution """
    out = (
        df
        .loc[lambda x: x['timestamp'] == x['timestamp'].max()]
        .assign(remaining = lambda x: x.prizes_remaining / x.prizes_start)
    )
    fig = px.histogram(out, x="remaining", title="Distribution of % Remaining")
    fig.update_layout(xaxis_title='% Prizes Remaining', yaxis_title="Count")
    return fig

def summarizegame(number: int) -> html.Div:
    samp = df.loc[lambda x: x['game_number'] == int(number)]
    if not samp.shape[0]:
        return html.Div('Hmm, there doesnt seem to be any games for the number {number}')

    row = samp.iloc[0]
    name = row['game_title']
    unique_prizes = map(lambda x: "${:,.0f}".format(x), samp['prize_amount'].unique())
    unique_prizes = ', '.join(unique_prizes)
    odds = f'Odds: 1 in {row["den"]}'
    prizes_remaining = "{:,.0f}".format(samp['prizes_remaining'].sum())

    comp = html.Div(children=[
        html.H1(name),
        html.H2(odds),
        html.P(unique_prizes),
        html.P(prizes_remaining)
    ], style={'border': '1px solid black'})

    return comp