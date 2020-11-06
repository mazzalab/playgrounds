import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import random

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], assets_folder="covid_dashboard/assets")

colors = {
    'background': '#FFFFFF',
    'text': '#000000'
}

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

df_energy = pd.DataFrame({
    "Frame": [str(i) for i in range(0, 100)] + [str(i) for i in range(0, 100)],
    "Energy": [random.uniform(0, 20) for i in range(0, 100)] + [random.uniform(0, 20) for i in range(0, 100)],
    "Replica": (100*["first"]) + (100*["second"])
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group", height=300)
scatter_energy = px.scatter(df_energy, x="Frame", y="Energy", color="Replica", height=300)

fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

scatter_energy.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)


header_line = [
    dbc.Col(html.Img(
        src=app.get_asset_url("logocss.png"),
        alt="Logo IRCCS-CSS",
        width="50",
        className="header_text"
    ), width=1),
    dbc.Col(html.H4(
        children='SPONGE: COVID-19 MD Dashboard at IRCCS Casa Sollievo della Sofferenza',
        className="header_logo"
    ))
]

option_box = dbc.Col(
    [
        dbc.Container(
            [
                dbc.Row([
                    dbc.Col(
                        className="option_label",
                        children=html.Label(children="Select system")
                    ),
                    dbc.Col(
                        dbc.DropdownMenu(
                            label="System",
                            children=[
                                dbc.DropdownMenuItem("WT"),
                                dbc.DropdownMenuItem("4-mut"),
                                dbc.DropdownMenuItem("3-mut"),
                            ],
                        ),
                        className="option_component"
                    )], no_gutters=True
                ),
                dbc.Row([
                    dbc.Col(
                        className="option_label",
                        children=html.Label(children="Select replica")
                    ),
                    dbc.Col(
                        dbc.Input(id="replica_input", placeholder="0-102", type="number", min=0, max=102),
                        className="option_component"
                    )], no_gutters=True
                )
            ]
        ),

        dbc.Row(
            html.Hr(className="rounded")
        ),

        dbc.Container(
            [
                dbc.Row(
                    dbc.Col(
                        html.Label("Select frames (1 frame=2ps)")
                    ), className="option_log_text"
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.RangeSlider(
                            id='simtime-slider',
                            min=0,
                            max=1300,
                            # step=None,
                            marks={i: str(i) for i in range(0, 1301, 300)},
                            value=[0, 1300]
                        )
                    )
                ),
                dbc.Row(
                    dbc.Col(
                        html.Div(id='output-container-simtime-slider')
                    ), className="option_log_text"
                )
            ]),

        dbc.Row(
            html.Hr(className="rounded")
        ),

        dbc.Container(
            [
                dbc.FormGroup(
                    [
                        dbc.Label("Select contacts", className="option_log_text"),
                        dbc.Checklist(
                            options=[
                                {'label': 'hydrogen bond', 'value': 'hb'},
                                {'label': 'salt bridge', 'value': 'sb'},
                                {'label': 'pi-cation', 'value': 'pc'},
                                {'label': 'pi-stacking', 'value': 'ts'},
                                {'label': 'van der Waals', 'value': 'vdw'},
                                {'label': 'all', 'value': 'all'},
                            ],
                            value=['all'],
                            id="checklist-input",
                            inline=True,
                        ),
                    ]
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.Dropdown(
                            options=[
                                {'label': 'SER35', 'value': 'SER35'},
                                {'label': 'MET21', 'value': 'MET21'},
                                {'label': 'GLU166', 'value': 'GLU166'}
                            ],
                            value=['SER35'],
                            multi=True
                        )
                    )
                )
            ]
        )
    ], className="chart"
)


@app.callback(
    dash.dependencies.Output('output-container-simtime-slider', 'children'),
    [dash.dependencies.Input('simtime-slider', 'value')])
def update_frame_selection(value):
    return f'Selected frames: {value[0]}-{value[1]}'


energy_plot = dbc.Col(
    [
        dbc.Row(dbc.Col(
            dcc.Graph(
                id='energy_scatter_plot',
                figure=scatter_energy,
            )
        ))
    ], className="chart"
)

energy_plot2 = dbc.Col(
    [
        dbc.Row(dbc.Col(
            dcc.Graph(
                id='example-graph-3',
                figure=fig
            )
        ))
    ], className="chart"
)

first_line_layout = dbc.Row(
    [
        dbc.Col(option_box, width=3),
        dbc.Col(energy_plot, width=4),
        dbc.Col(energy_plot2, width=5)
    ]
)

app.layout = dbc.Container(
    [
        dbc.Row(header_line),
        first_line_layout
    ],
    # fluid=True,
)

if __name__ == '__main__':
    app.run_server(debug=True)
