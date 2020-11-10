import dash
import plotly.express as px
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate

from . import app

colors = {
    'background': '#FFFFFF',
    'text': '#000000'
}


class Body:
    def __init__(self, df_energy, df, df_distance):
        self.tot_frames = int(df_energy.Energy.size / df_energy.Replica.unique().size)

        import plotly.graph_objects as go
        self.scatter_energy = go.Figure()
        self.scatter_energy.add_trace(go.Scatter(x=df_energy.Frame, y=df_energy.Energy,
                                 mode='markers',
                                 name='markers'))

        # self.scatter_energy = px.scatter(df_energy, x="Frame", y="Energy", color="Replica", opacity=0.2,
        #                                  color_discrete_sequence=px.colors.qualitative.D3[0:2])
        # self.scatter_energy.update_yaxes(nticks=10, gridcolor="lightgray", showline=True, linewidth=2,
        #                                  linecolor='black')
        # self.scatter_energy.update_xaxes(showgrid=True, gridcolor="lightgray", showline=True, linewidth=2,
        #                                  linecolor='black',
        #                                  tickvals=list(range(0, self.tot_frames + 1, 50)))  # nticks=10,
        # self.scatter_energy.update_traces(marker=dict(size=6,
        #                                               opacity=0.2,
        #                                               # color=px.colors.qualitative.Plotly[0]
        #                                               # line=dict(width=2,
        #                                               #           color='DarkSlateGrey')
        #                                               ),
        #                                   selector=dict(mode='markers'))

        self.fig1 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")  #

        size_stylesheet = [
            # Group selectors
            {
                'selector': 'node',
                'style': {
                    'content': 'data(label)',
                    'font-size': '7px'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'width': 2
                }
            },
            {
                'selector': '.small',
                'style': {
                    'width': 10,
                    'height': 10,
                }
            }
        ]
        self.fig_network = cyto.Cytoscape(
            id='fig_network',
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '400px'},
            stylesheet=size_stylesheet,
            elements=[
                {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}, 'classes': 'small'},
                {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}, 'classes': 'small'},
                {'data': {'id': 'three', 'label': 'Node 3'}, 'position': {'x': 250, 'y': 250}, 'classes': 'small'},
                {'data': {'id': 'for', 'label': 'Node 4'}, 'position': {'x': 300, 'y': 300}, 'classes': 'small'},
                {'data': {'id': 'five', 'label': 'Node 5'}, 'position': {'x': 100, 'y': 100}, 'classes': 'small'},
                {'data': {'source': 'one', 'target': 'two'}},
                {'data': {'source': 'one', 'target': 'three'}},
                {'data': {'source': 'one', 'target': 'for'}},
                {'data': {'source': 'two', 'target': 'for'}},
                {'data': {'source': 'five', 'target': 'three'}},
                {'data': {'source': 'five', 'target': 'for'}}
            ]
        )

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
                      dash.dependencies.Output('fig_network', 'style'),
                      dash.dependencies.Output('distance_plot', 'figure')],
                     [dash.dependencies.Input('size', 'children'),
                      dash.dependencies.Input('simtime-slider', 'value')],
                     )(self.update_plot)

        app.callback([dash.dependencies.Output('simtime-slider', 'max'),
                      dash.dependencies.Output('simtime-slider', 'value'),
                      dash.dependencies.Output('simtime-slider', 'marks')],
                     [dash.dependencies.Input('url', 'href')])(self.set_frame_extreme_positions)

    @staticmethod
    def __make_option_box() -> dbc.Col:
        option_box = dbc.Col(
            [
                html.Div(dbc.Container(
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
                ), className='divBorder'),

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

    def update_plot(self, inner_window_height: int, slider_extreme_values: list):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        network_style = {}
        if button_id == "size":
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
                height=300,

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

            network_style = {'height': inner_window_height - 300 - 150, 'background-color': colors['background']}

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
                height=inner_window_height - 300 - 150
            )
        else:
            self.scatter_distance.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )
            self.scatter_energy.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )

        return self.scatter_energy, self.fig1, network_style, self.scatter_distance

    def set_frame_extreme_positions(self, value):
        return self.tot_frames, [0, self.tot_frames], {i: str(i) for i in range(0, self.tot_frames + 1, 300)}

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

    def __make_fig_network(self):
        fig_network = dbc.Col(
            [
                dbc.Row(dbc.Col(
                    self.fig_network
                ))
            ], className="chart"
        )
        return fig_network

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
                        dbc.Col(self.__make_fig_network(), width=8),
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
