import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from . import app

colors = {
    'background': '#FFFFFF',
    'text': '#000000'
}


class Body:
    def __init__(self, df_energy, df, df_distance):
        self.tot_frames = int(df_energy.Energy.size / df_energy.Replica.unique().size)

        self.scatter_energy = px.scatter(df_energy, x="Frame", y="Energy", color="Replica")
        self.scatter_energy.update_yaxes(nticks=10, gridcolor="lightgray", showline=True, linewidth=2,
                                         linecolor='black')
        self.scatter_energy.update_xaxes(showgrid=True, gridcolor="lightgray", showline=True, linewidth=2,
                                         linecolor='black',
                                         tickvals=list(range(0, self.tot_frames + 1, 50)))  # nticks=10,

        self.fig1 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")  #
        self.fig2 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")  #

        self.scatter_distance = px.scatter(df_distance, x="Frame", y="Distance", color="Replica")  # , height=300

        app.clientside_callback(
            """
            function(value){
                return window.innerHeight;
            }
            """,
            dash.dependencies.Output('size', 'children'),
            [dash.dependencies.Input('url', 'href')]
        )

        app.callback([dash.dependencies.Output('energy_scatter_plot', 'figure'),
                      dash.dependencies.Output('fig1_plot', 'figure'),
                      dash.dependencies.Output('fig2_plot', 'figure'),
                      # dash.dependencies.Output('distance_plot', 'figure')
                      ],
                     [dash.dependencies.Input('size', 'children')])(self.update_plot_height)

        app.callback([dash.dependencies.Output('simtime-slider', 'max'),
                      dash.dependencies.Output('simtime-slider', 'value'),
                      dash.dependencies.Output('simtime-slider', 'marks')],
                     [dash.dependencies.Input('url', 'href')])(self.set_frame_extreme_positions)

        app.callback(dash.dependencies.Output('distance_plot', 'figure'),
                     [dash.dependencies.Input('simtime-slider', 'value')])(self.on_move_slider)

    @staticmethod
    def __make_option_box() -> dbc.Col:
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
                                    max=10,
                                    # step=None,
                                    marks={i: str(i) for i in range(0, 1301, 300)},
                                    value=[0, 10]
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

        return option_box

    # ##### CALLBACKS ######
    @staticmethod
    @app.callback(
        dash.dependencies.Output('output-container-simtime-slider', 'children'),
        [dash.dependencies.Input('simtime-slider', 'value')])
    def update_frame_selection(value):
        return f'Selected frames: {value[0]}-{value[1]}'

    def on_move_slider(self, value):
        # self.scatter_energy.update_xaxes()

        self.scatter_distance.update_layout(
            xaxis=[value[0], value[1]]
        )
        return self.scatter_energy

    def set_frame_extreme_positions(self, value):
        return self.tot_frames, [0, self.tot_frames], {i: str(i) for i in range(0, self.tot_frames, 300)}

    def update_plot_height(self, value):
        self.scatter_energy.update_layout(
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

        self.fig1.update_layout(
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

        self.fig2.update_layout(
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

        self.scatter_distance.update_layout(
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

        return self.scatter_energy, self.fig1, self.fig2, self.scatter_distance

    # #######################

    def __make_energy_plot(self):
        energy_plot = dbc.Col(
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id='energy_scatter_plot',
                        figure=self.scatter_energy,
                    )
                )
            ), className="chart"
        )
        return energy_plot

    def __make_fig1_plot(self):
        fig1_plot = dbc.Col(
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id='fig1_plot',
                        figure=self.fig1,
                    )
                )
            ), className="chart"
        )
        return fig1_plot

    def __make_fig2_plot(self):
        fig2_plot = dbc.Col(
            [
                dbc.Row(dbc.Col(
                    dcc.Graph(
                        id='fig2_plot',
                        figure=self.fig2
                    )
                ))
            ], className="chart"
        )
        return fig2_plot

    def __make_distance_plot(self):
        distance_plot = dbc.Col(
            [
                dbc.Row(dbc.Col(
                    dcc.Graph(
                        id='distance_plot',
                        figure=self.scatter_distance
                    ),
                ))
            ], className="chart"
        )
        return distance_plot

    def __all_plot_layout(self):
        plot_layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(self.__make_energy_plot(), width=6),
                        dbc.Col(self.__make_fig1_plot(), width=6)
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(self.__make_fig2_plot(), width=8),
                        dbc.Col(self.__make_distance_plot(), width=4),
                    ],
                )
            ],
            fluid=True,
        )
        return plot_layout

    def build_layout(self):
        main_layout = dbc.Row(
            [
                dbc.Col(Body.__make_option_box(), width=3),
                dbc.Col(self.__all_plot_layout(), width=9)
            ], no_gutters=True
        )
        return main_layout
