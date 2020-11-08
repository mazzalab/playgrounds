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
    "Energy": sorted([random.uniform(0, 20) for i in range(0, 100)]) + sorted(
        [random.uniform(0, 25) for i in range(0, 100)]),
    "Replica": (100 * ["first"]) + (100 * ["second"])
})

df_distance = pd.DataFrame({
    "Frame": [str(i) for i in range(0, 100)] + [str(i) for i in range(0, 100)],
    "Distance": sorted([random.uniform(0, 20) for i in range(0, 100)], reverse=True) + sorted(
        [random.uniform(0, 25) for i in range(0, 100)], reverse=True),
    "Replica": (100 * ["first"]) + (100 * ["second"])
})

scatter_energy = px.scatter(df_energy, x="Frame", y="Energy", color="Replica")
scatter_energy.update_yaxes(nticks=10, gridcolor="lightgray", showline=True, linewidth=2, linecolor='black')
scatter_energy.update_xaxes(showgrid=True, gridcolor="lightgray", showline=True, linewidth=2, linecolor='black',
                            tickvals=list(range(0, 101, 10)))  # nticks=10,

fig1 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")  #
fig2 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")  #

scatter_distance = px.scatter(df_distance, x="Frame", y="Distance", color="Replica")  # , height=300

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
    dbc.Row(
        dbc.Col(
            dcc.Graph(
                id='energy_scatter_plot',
                figure=scatter_energy,
            )
        )
    ), className="chart"
)

fig1_plot = dbc.Col(
    dbc.Row(
        dbc.Col(
            dcc.Graph(
                id='fig1_plot',
                figure=fig1,
            )
        )
    ), className="chart"
)

fig2_plot = dbc.Col(
    [
        dbc.Row(dbc.Col(
            dcc.Graph(
                id='fig2_plot',
                figure=fig2
            )
        ))
    ], className="chart"
)

distance_plot = dbc.Col(
    [
        dbc.Row(dbc.Col(
            dcc.Graph(
                id='distance_plot',
                figure=scatter_distance
            ),
        ))
    ], className="chart"
)

plot_layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(energy_plot, width=6),
                dbc.Col(fig1_plot, width=6)
            ],
        ),
        dbc.Row(
            [
                dbc.Col(fig2_plot, width=8),
                dbc.Col(distance_plot, width=4),
            ],
        )
    ],
    fluid=True,
)

main_layout = dbc.Row(
    [
        dbc.Col(option_box, width=3),
        dbc.Col(plot_layout, width=9)
    ], no_gutters=True
)

app.layout = dbc.Container(
    [
        html.Div(id='size', style={"display": "none"}),
        dcc.Location(id='url'),

        dbc.Row(header_line),
        main_layout
    ],
    fluid=True
)

app.clientside_callback(
    """
    function(value){
        return window.innerHeight;
    }
    """,
    dash.dependencies.Output('size', 'children'),
    [dash.dependencies.Input('url', 'href')]
)


@app.callback(
    [dash.dependencies.Output('energy_scatter_plot', 'figure'),
     dash.dependencies.Output('fig1_plot', 'figure'),
     dash.dependencies.Output('fig2_plot', 'figure'),
     dash.dependencies.Output('distance_plot', 'figure')],
    [dash.dependencies.Input('size', 'children')])
def update_plot_height(value):
    scatter_energy.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=20, r=10, t=20, b=20),
        height=300
    )

    fig1.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        height=300
    )

    fig2.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        height=value - 300 - 150
    )

    scatter_distance.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=20, r=10, t=20, b=20),
        height=value - 300 - 150
    )

    return scatter_energy, fig1, fig2, scatter_distance


if __name__ == '__main__':
    app.run_server(debug=True)
