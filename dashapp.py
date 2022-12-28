from dash import Dash, html, dcc, Output, Input
import charts

app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Lottery Data Analysis'),
    html.Div(children='Investigating Lottery Amounts In The State of Michigan'),
    charts.droppy(),
    html.Div(id='details-card'),
    dcc.Graph(id='example-graph2', figure=charts.topbottable()),
    dcc.Graph(id='graph1', figure=charts.remaininghist())
])


@app.callback(
    Output(component_id='details-card', component_property='children'),
    Input(component_id='my-dropdown', component_property='value')
)
def update_output_div(input_value):
    return charts.summarizegame(input_value)

if __name__ == '__main__':
    app.run_server(debug=True)