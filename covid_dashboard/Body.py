from . import app
from .db import DBManager

import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.neighbors import KNeighborsRegressor

import dash
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate

colors = {
    'background': '#FFFFFF',
    'text': '#000000'
}


class Body:
    def __init__(self):
        self.db_manager = DBManager()
        self.tot_frames = 1

        self.network = self.__create_empty_network()
        self.scatter_energy = self.__create_empty_energy_plot()
        self.scatter_distance = self.__create_empty_distance_plot()

        df = pd.DataFrame({
            "Fruit": [],
            "Amount": [],
            "City": []
        })
        self.fig1 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

        df_contacts = pd.DataFrame({
            "Frame": [],
            "Contact": [],
            "Contact_type": [],
            "Energy": [],
            "Replica": []
        })
        self.contact_dropdown_values = self.__format_contact_4_dropdown(df_contacts)

        # region Callbacks declaration
        app.clientside_callback(
            """
            function(value){
                return window.innerHeight;
            }
            """,
            dash.dependencies.Output('size', 'children'),
            [dash.dependencies.Input('url', 'href')]
        )

        app.callback(dash.dependencies.Output('replica_dropdown', 'options'),
                     dash.dependencies.Input('system_dropdown', 'value')
                     )(self.__on_system_dropdown_select)

        app.callback(
            [dash.dependencies.Output('network_div', 'children'),
             dash.dependencies.Output('energy_scatter_plot', 'figure'),
             dash.dependencies.Output('distance_plot', 'figure'),
             dash.dependencies.Output('fig1_plot', 'figure'),
             dash.dependencies.Output('range_slider_div', 'children'),
             dash.dependencies.Output('select_individual_frame', 'max')
             ],

            [dash.dependencies.Input('size', 'children'),
             dash.dependencies.Input('simtime-slider', 'value'),
             dash.dependencies.Input('replica_dropdown', 'value'),
             dash.dependencies.State('system_dropdown', 'value')]
        )(self.__fill_or_update_plots)

        # endregion

    def build_layout(self):
        systems: list = self.db_manager.get_systems()

        main_layout = dbc.Row(
            [
                dbc.Col(self.__make_option_box(systems), width=2),
                dbc.Col(self.__all_plot_layout(), width=10)
            ], no_gutters=True
        )
        return main_layout

    # region CALLBACKS
    def __fill_or_update_plots(self, inner_window_height: int, slider_extreme_values: list, replica: int, system: str):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        else:
            prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

        single_frame_max = dash.no_update
        range_slider = dash.no_update

        if prop_id == "replica_dropdown":
            self.db_manager.connect(db_uri="file:///", db_user="agatta", db_passw="agatta")
            df_energy = self.db_manager.get_energy_values(system=system, replica=replica)
            df_distance = self.db_manager.get_distance_values(system=system, replica=replica)
            df_contacts = self.db_manager.get_contacts(system=system, replica=replica)

            self.tot_frames = df_energy.Energy.size

            self.all_contacts = df_contacts
            self.contact_dropdown_values = self.__format_contact_4_dropdown(df_contacts)

            self.network.elements = self.__update_network_elements(df_contacts, 0, self.tot_frames)
            self.scatter_energy = self.__update_energy_plot(df_energy)
            self.scatter_distance = self.__update_distance_plot(df_distance)

            df = pd.DataFrame({
                "Fruit": [],
                "Amount": [],
                "City": []
            })
            self.fig1 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

            # update slider extreme values
            range_slider = self.__create_range_slider()
            single_frame_max = range_slider.max

        if prop_id == "size" or prop_id == "replica_dropdown":
            network_style = {'height': f'{inner_window_height - 120}px', 'backgroundColor': colors['background']}
            self.network.style = {**self.network.style, **network_style}

            # calculate zoom level
            zoom_level = (inner_window_height - 120) / 550  # 550px is the starting canvas height
            self.network.layout = {**self.network.layout, **{'zoom': zoom_level}}

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
                height=inner_window_height / 2 - 65,
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
                height=inner_window_height / 2 - 65
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
                height=inner_window_height / 2 - 65
            )
        else:
            self.scatter_distance.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )
            self.scatter_energy.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )

        return self.network, self.scatter_energy, self.scatter_distance, self.fig1, range_slider, single_frame_max

    @staticmethod
    @app.callback(
        dash.dependencies.Output('output-container-simtime-slider', 'children'),
        [dash.dependencies.Input('simtime-slider', 'value')])
    def update_frame_selection(value):
        return f'Selected frames: {value[0]}-{value[1]}'

    def __on_system_dropdown_select(self, system: str) -> list:
        if system is None:
            raise dash.exceptions.PreventUpdate

        replica: list = [{'label': x, 'value': x} for x in self.db_manager.get_replica(system)]
        return replica

    # endregion

    # region PRIVATE METHODS
    def __create_range_slider(self):
        ten_ticks_distance = math.floor(self.tot_frames / 3)
        if ten_ticks_distance == 0:
            raise dash.exceptions.PreventUpdate

        tick_range = list(range(0, self.tot_frames, ten_ticks_distance))
        if tick_range[-1] != self.tot_frames - 1:
            tick_range[-1] = self.tot_frames - 1
        ticks_dict = {i: str(i) for i in tick_range}

        new_range_slider = dcc.RangeSlider(
            id='simtime-slider',
            min=0,
            max=self.tot_frames - 1,
            # step=None,
            marks=ticks_dict,
            value=[0, self.tot_frames - 1])

        return new_range_slider

    def __all_plot_layout(self):
        plot_layout = dbc.Container(
            dbc.Row(
                [
                    dbc.Col(self.__make_fig_network(), width=4),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(self.__make_energy_plot(), width=6),
                                    dbc.Col(self.__make_distance_plot(), width=6)
                                ]
                            ),
                            dbc.Row(self.__make_fig1_plot())
                        ], width=8)
                ]
            ),
            fluid=True,
        )
        return plot_layout

    def __format_contact_4_dropdown(self, df_contacts: pd.DataFrame) -> list:
        all_contacts_set = set()
        all_contacts = []
        for index, row in df_contacts.iterrows():
            temp_contact: tuple = row.Contact

            if temp_contact in all_contacts_set:
                continue
            else:
                all_contacts_set.add(temp_contact)
                temp_dict = dict()
                temp_dict['label'] = temp_contact[0] + "-" + temp_contact[1]
                temp_dict['value'] = temp_dict['label']
                all_contacts.append(temp_dict)

        return all_contacts

    def __make_option_box(self, systems: list) -> dbc.Col:
        option_box = dbc.Col(
            [
                html.Div(dbc.Container(
                    [
                        dbc.Row([
                            dbc.Col(
                                className="option_label",
                                children=html.Label(children="Select system"),
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="system_dropdown",
                                    options=[{'label': x, 'value': x} for x in systems]
                                ),
                                className="option_component",
                            )], no_gutters=True
                        ),
                        dbc.Row([
                            dbc.Col(
                                className="option_label",
                                children=html.Label(children="Select replica"),
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id="replica_dropdown",
                                    options=[],
                                ),
                                className="option_component",
                            )], no_gutters=True
                        )
                    ]
                ), className='divBorder'),

                dbc.Row(
                    html.Hr(className="rounded")
                ),

                dbc.Container(
                    [
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.Label("Select frames (1 frame=2ps)",
                                                           className="option_log_text"),
                                                html.Div(
                                                    id="range_slider_div",
                                                    children=dcc.RangeSlider(
                                                        id='simtime-slider',
                                                        min=0,
                                                        max=1,
                                                        # step=None,
                                                        marks={i: str(i) for i in range(0, 2, 1)},
                                                        value=[0, 1]
                                                    ),
                                                ),
                                                html.Div(id='output-container-simtime-slider',
                                                         className="option_log_text")
                                            ]
                                        ),
                                    ),
                                    label="Aggregate"),
                                dbc.Tab(
                                    dbc.Card(
                                        dbc.CardBody(
                                            html.Div(
                                                [
                                                    html.Label("Select one frame"),
                                                    dbc.Input(id="select_individual_frame",
                                                              type="number",
                                                              min=0,
                                                              max=1,
                                                              step=1,
                                                              value=0,
                                                              style={'width': '50%', 'display': 'inline-block'}),
                                                    dbc.Button("confirm", outline=True, color="primary",
                                                               style={'width': '43%', 'display': 'inline-block',
                                                                      'marginLeft': "7px"}),

                                                ]
                                            ),
                                        )
                                    ),
                                    label="Frame",
                                    # disabled=True
                                ),
                            ]
                        ),
                    ]
                ),

                # html.Hr(),

                dbc.Row(
                    html.Hr(className="rounded")
                ),

                dbc.Container(
                    [
                        dbc.Row(
                            dbc.Col(
                                dbc.Label("Select contacts", className="option_log_text")
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                dcc.Dropdown(
                                    options=self.contact_dropdown_values,
                                    # value=['SER35'],
                                    multi=True,
                                    id="bond_dropdown",
                                    placeholder="Select a contact",
                                    style={'fontSize': '10px'}
                                )
                            )
                        )
                    ]
                )
            ], className="chart"
        )

        return option_box

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
        spike_nodes = 0
        ace2_nodes = 0
        for i in range(len(self.network.elements)):
            data = self.network.elements[i]["data"]

            if "parent" in data and data["parent"] == "spike":
                spike_nodes = spike_nodes + 1
            elif "parent" in data and data["parent"] == "ace2":
                ace2_nodes = ace2_nodes + 1

        network_compound_figure = dbc.Col(
            [
                dbc.Row(
                    dbc.Col(
                        dbc.Label(f"hACE2 nodes: {ace2_nodes}, Spike nodes: {spike_nodes}", className="network_label")
                    ), className="network_label"
                ),
                dbc.Row(
                    dbc.Col(
                        html.Div(
                            id="network_div",
                            children=self.network
                        )
                    )
                )
            ], className="chart"
        )

        return network_compound_figure

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


    def __create_empty_energy_plot(self):
        df_energy = pd.DataFrame({
            "Frame": [],
            "Energy": [],
        })
        return px.scatter(df_energy, x="Frame", y="Energy", color_discrete_sequence=px.colors.qualitative.D3[0])

    def __update_energy_plot(self, df_energy: pd.DataFrame) -> go.Figure:
        self.scatter_energy = px.scatter(df_energy, x="Frame", y="Energy")

        self.scatter_energy.update_yaxes(nticks=10, gridcolor="lightgray", showline=True, linewidth=2,
                                         linecolor='black')
        self.scatter_energy.update_xaxes(showgrid=True, gridcolor="lightgray", showline=True, linewidth=2,
                                         linecolor='black',
                                         tickvals=list(range(0, self.tot_frames + 1, int((self.tot_frames + 1)/10))))  # nticks=10,
        self.scatter_energy.update_traces(marker=dict(size=5,
                                                      opacity=0.2,
                                                      # color=px.colors.qualitative.Plotly[0]
                                                      # line=dict(width=2,
                                                      #           color='DarkSlateGrey')
                                                      ),
                                          selector=dict(mode='markers'))
        knn_uni = KNeighborsRegressor(10, weights='uniform')
        x = df_energy.Frame.values[0:self.tot_frames]
        knn_uni.fit(x.reshape(-1, 1), df_energy.Energy)
        y_uni = knn_uni.predict(x.reshape(-1, 1))
        self.scatter_energy.add_trace(go.Scatter(x=x, y=y_uni, mode='lines',
                                                 name=self.scatter_energy["data"][0]["legendgroup"] + " " + "fit",
                                                 line=dict(color=px.colors.qualitative.D3[0])))

        return self.scatter_energy

    def __create_empty_distance_plot(self):
        df_distance = pd.DataFrame({
            "Frame": [],
            "Distance": [],
            "Replica": []
        })

        return px.scatter(df_distance, x="Frame", y="Distance", color="Replica")

    def __update_distance_plot(self, df_distance: pd.DataFrame):
        self.scatter_distance = px.scatter(df_distance, x="Frame", y="Distance")

        self.scatter_distance.update_yaxes(nticks=10, gridcolor="lightgray", showline=True, linewidth=2,
                                           linecolor='black')
        self.scatter_distance.update_xaxes(showgrid=True, gridcolor="lightgray", showline=True, linewidth=2,
                                           linecolor='black',
                                           tickvals=list(range(0, self.tot_frames + 1, int((self.tot_frames + 1)/10))))  # nticks=10,
        self.scatter_distance.update_traces(marker=dict(size=5,
                                                        opacity=0.2,
                                                        # color=px.colors.qualitative.Plotly[0]
                                                        # line=dict(width=2,
                                                        #           color='DarkSlateGrey')
                                                        ),
                                            selector=dict(mode='markers'))

        knn_uni = KNeighborsRegressor(10, weights='uniform')
        x = df_distance.Frame.values[0:self.tot_frames]
        knn_uni.fit(x.reshape(-1, 1),
                    df_distance.Distance)
        y_uni = knn_uni.predict(x.reshape(-1, 1))
        self.scatter_distance.add_trace(
            go.Scatter(x=x, y=y_uni, mode='lines', name=self.scatter_distance["data"][0]["legendgroup"] + " " + "fit",
                       line=dict(color=px.colors.qualitative.D3[0])))

        return self.scatter_distance

    def __create_empty_network(self):
        size_stylesheet = [
            # Group selectors
            {
                'selector': 'node',
                'style': {
                    'content': 'data(label)',
                    'fontSize': '10px',
                    'width': "8px",
                    'height': "8px"
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'width': 1
                }
            },
            {
                'selector': '.small',
                'style': {
                    'width': 10,
                    'height': 10,
                }
            },
            {
                'selector': '.bind',
                'style': {'width': 1}
            },
            {
                'selector': '.internal',
                'style': {
                    'line-style': 'dashed'
                }
            }
        ]
        elements = []

        return cyto.Cytoscape(
            id='fig_network',
            layout={'name': 'preset', 'fit': True},
            style={'width': '100%', 'height': '500px', 'textValign': 'center', 'textHalign': 'center'},
            stylesheet=size_stylesheet,
            elements=elements
        )

    def __update_network_elements(self, df_contacts: pd.DataFrame, start_frame: int, end_frame: int) -> list:
        elements = [
            # Parent Nodes
            {
                'data': {'id': 'spike', 'label': 'Spike'}
            },
            {
                'data': {'id': 'ace2', 'label': 'hACE2'}
            },
        ]

        ace2_nodes = set()
        spike_nodes = set()
        edges = set()
        filtered_df_contacts = df_contacts.where(
            (df_contacts["Frame"] >= start_frame) & (df_contacts["Frame"] <= end_frame))
        for index, row in filtered_df_contacts.iterrows():
            contact = row.Contact
            ace2_nodes.add(contact[0] + "_a")
            spike_nodes.add(contact[1] + "_s")
            edges.add((contact[0] + "_a", contact[1] + "_s"))

        #  add nodes
        y_pos = range(10, 490, int(480 / len(ace2_nodes)))
        for idx, a in enumerate(ace2_nodes):
            temp_dict = {'data': {'id': a, 'label': a[:-2], 'parent': 'ace2'},
                         'position': {'x': -60, 'y': y_pos[idx]}
                         }
            elements.append(temp_dict)

        y_pos = range(10, 490, int(480 / len(spike_nodes)))
        for idx, s in enumerate(spike_nodes):
            temp_dict = {'data': {'id': s, 'label': s[:-2], 'parent': 'spike'},
                         'position': {'x': 60, 'y': y_pos[idx]}
                         }
            elements.append(temp_dict)

        #  add edges
        for e in edges:
            temp_dict = {
                'data': {'source': e[0], 'target': e[1]},
                'classes': 'bind'
            }
            elements.append(temp_dict)

        return elements
    # endregion
