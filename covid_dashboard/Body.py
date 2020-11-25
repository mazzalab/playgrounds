from . import app
from .db import DBManager

import io
import base64
import math
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from sklearn.neighbors import KNeighborsRegressor

import dash
from dash.dependencies import Input, Output, State
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
        self.__initialize_empty_components()

        # region Callbacks declaration
        app.clientside_callback(
            """
            function(value){
                return window.innerHeight;
            }
            """,
            Output('size', 'children'),
            [Input('url', 'href')]
        )

        app.callback(
            [
                Output('trace_spinner_div', 'children'),
                Output('badges_div', 'children'),
                Output('url', 'href')
            ],
            Input('reset_button', 'n_clicks'))(self.__reset_canvas)

        app.callback(
            Output('replica_dropdown', 'options'),
            Input('system_dropdown', 'value'))(self.__set_replica_dropdown)

        app.callback(
            [
                Output('network_div', 'children'),
                Output('energy_scatter_plot', 'figure'),
                Output('distance_plot', 'figure'),
                Output('fig1_plot', 'figure'),
                Output('system_dropdown_div', 'children'),
                Output('replica_dropdown_div', 'children'),
                Output('range_slider_div', 'children'),
                Output('select_individual_frame', 'max'),
            ],
            [
                Input('size', 'children'),
                Input('simtime-slider', 'value'),
                Input('replica_dropdown', 'value'),
                State('system_dropdown', 'value')])(self.__fill_or_update_plots)

        app.callback(
            [
                Output('trace-spinner', "children"),
                Output('energy_badge', "color"),
                Output('distance_badge', "color"),
                Output('contact_badge', "color"),
                Output('system_dropdown', 'options')
            ],
            Input('upload-traces', 'contents'),
            State('upload-traces', 'filename'),
            State('upload-traces', 'last_modified'))(self.__load_trajectories)
        # endregion

    def build_layout(self):
        main_layout = dbc.Row(
            [
                dbc.Col(self.__make_option_box(), width=2),
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

        range_slider = dash.no_update
        single_frame_max = dash.no_update
        system_dropdown = dash.no_update
        replica_dropdown = dash.no_update

        if prop_id == "size":
            self.__initialize_empty_components()
            system_dropdown = self.system_dropdown
            replica_dropdown = self.replica_dropdown
        elif prop_id == "replica_dropdown":
            # update slider extreme values
            range_slider = self.__create_range_slider()
            single_frame_max = range_slider.max

            # update graphical components
            filtered_df_energy = self.df_energy[(self.df_energy['Replica'] == replica)
                                                & (self.df_energy['System'] == system)]
            filtered_df_distance = self.df_distance[(self.df_distance['Replica'] == replica)
                                                    & (self.df_distance['System'] == system)]
            filtered_df_contacts = self.df_contacts[(self.df_contacts['Replica'] == replica)
                                                    & (self.df_contacts['System'] == system)]
            self.scatter_energy = self.__update_energy_plot(filtered_df_energy)
            self.scatter_distance = self.__update_distance_plot(filtered_df_distance)
            self.contact_dropdown_values = self.__format_contact_4_dropdown(filtered_df_contacts)
            self.network.elements = self.__update_network_elements(filtered_df_contacts, 0, self.tot_frames)
            self.fig1 = px.bar(self.df, x="Fruit", y="Amount", color="City", barmode="group")
        else:
            self.scatter_distance.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )
            self.scatter_energy.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )

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

        return self.network, self.scatter_energy, self.scatter_distance, self.fig1, system_dropdown, replica_dropdown, range_slider, single_frame_max

    @staticmethod
    @app.callback(
        dash.dependencies.Output('output-container-simtime-slider', 'children'),
        [dash.dependencies.Input('simtime-slider', 'value')])
    def update_frame_selection(value):
        return f'Selected frames: {value[0]}-{value[1]}'

    def __set_replica_dropdown(self, system):
        ctx = dash.callback_context
        if not ctx.triggered or not system:
            raise PreventUpdate

        replica_list: list = self.df_energy[self.df_energy['System'] == system]['Replica'].unique()
        return [{'label': x, 'value': x} for x in replica_list]

    def __reset_canvas(self, reset_click: int):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        new_badges = [
            dbc.Badge(id="energy_badge", children="Energy", pill=True, color="light"),
            dbc.Badge(id="distance_badge", children="Distance", pill=True, color="light"),
            dbc.Badge(id="contact_badge", children="Contacts", pill=True, color="light")
        ]

        new_spinner = dbc.Spinner(html.Div(id="trace-spinner",
                                           className="option_log_text",
                                           style={"marginBottom": "10px"}))

        return new_spinner, new_badges, "localhost:8050"

    def __load_trajectories(self, files_content, files_name, files_date):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        else:
            energy_color = dash.no_update
            distance_color = dash.no_update
            contact_color = dash.no_update
            systems = dash.no_update

            for file in zip(files_content, files_name, files_date):
                content_type, content_string = file[0].split(',')
                decoded = base64.b64decode(content_string)

                try:
                    if 'txt' in file[1]:
                        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                    elif 'xls' in file[1] or 'xlsx' in file[1]:
                        df = pd.read_excel(io.BytesIO(decoded))

                        if 'frame' in df and 'system' in df and 'replica' in df:
                            if 1 < self.tot_frames != df.frame.nunique():
                                raise Exception("Loaded files have different numbers of frames")
                            elif systems != dash.no_update and len(systems) != df['system'].nunique():
                                raise Exception("Loaded files contain different systems")
                            else:
                                self.tot_frames = df.frame.nunique()
                                systems = df['system'].unique()
                        else:
                            raise Exception("Missing critical columns (frame, system, or replica)")

                        if 'Diff_TOTAL_Average' in df:
                            self.df_energy = df[['system', 'frame', 'Diff_TOTAL_Average', 'replica']]
                            self.df_energy.columns = ["System", "Frame", "Energy", "Replica"]

                            self.loaded_plots.append("energy")
                            energy_color = "success"
                        if 'Distance_Interface' in df:
                            self.df_distance = df[['system', 'frame', 'Distance_Interface', 'replica']]
                            self.df_distance.columns = ["System", "Frame", "Distance", "Replica"]

                            self.loaded_plots.append("distance")
                            distance_color = "primary"
                        if 'TOTAL_S_avg' in df:
                            self.df_contacts = df
                            self.df_contacts["Contact"] = list(
                                zip(df["amm_spike"] + df["uniprot_pos_spike"].astype(str),
                                    df["amm_ace2"] + df["uniprot_pos_ace2"].astype(str)))
                            self.df_contacts = self.df_contacts[
                                ['system', 'frame', 'Contact', 'TOTAL_S_avg', 'replica']]
                            self.df_contacts.columns = ["System", "Frame", "Contact", "Energy", "Replica"]

                            self.loaded_plots.append("contact")
                            contact_color = "danger"

                            # TODO: to be handled later
                            self.df = pd.DataFrame({
                                "Fruit": [],
                                "Amount": [],
                                "City": []
                            })
                except Exception as e:
                    print(e)

            msg = f'Missing {3 - len(self.loaded_plots)} plot{"s" if 3 - len(self.loaded_plots) > 1 else ""}' if 3 - len(
                self.loaded_plots) > 0 else "Data ready to be plotted"

            if len(self.loaded_plots) == 3:
                systems_dict = [{'label': x, 'value': x} for x in systems]
            else:
                systems_dict = dash.no_update

            return msg, energy_color, distance_color, contact_color, systems_dict

    # endregion

    # region PRIVATE METHODS
    def __initialize_empty_components(self):
        self.tot_frames = 1
        self.loaded_plots = []

        self.system_dropdown = dcc.Dropdown(id="system_dropdown", options=[])
        self.replica_dropdown = dcc.Dropdown(id="replica_dropdown", options=[])

        self.df_contacts = self.__create_empty_contact_values()
        self.contact_dropdown_values = self.__format_contact_4_dropdown(self.df_contacts)
        self.network = self.__create_empty_network()
        self.scatter_energy, self.df_energy = self.__create_empty_energy_plot()
        self.scatter_distance, self.df_distance = self.__create_empty_distance_plot()
        self.df = pd.DataFrame({
            "Fruit": [],
            "Amount": [],
            "City": []
        })
        self.fig1 = px.bar(self.df, x="Fruit", y="Amount", color="City", barmode="group")

    def __create_range_slider(self):
        ten_ticks_distance = math.floor(self.tot_frames / 3)
        if ten_ticks_distance == 0:
            raise dash.exceptions.PreventUpdate

        tick_range = list(range(0, self.tot_frames+1, ten_ticks_distance))
        if tick_range[-1] != self.tot_frames:
            tick_range[-1] = self.tot_frames
        ticks_dict = {i: str(i) for i in tick_range}

        new_range_slider = dcc.RangeSlider(
            id='simtime-slider',
            min=0,
            max=self.tot_frames,
            # step=None,
            marks=ticks_dict,
            value=[0, self.tot_frames])

        return new_range_slider

    def __all_plot_layout(self):
        plot_layout = dbc.Container(
            dbc.Row(
                [
                    dbc.Col(self.__make_network_fig(), width=4),
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

    def __make_option_box(self) -> dbc.Col:
        option_box = dbc.Col(
            [
                dbc.Row(
                    dbc.Col(
                        dbc.Label("Load trajectories", className="option_section_title")
                    )
                ),
                html.Div(
                    [
                        dcc.Upload(
                            id='upload-traces',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files', style={'color': 'blue', 'borderBottom': '1px solid blue'})
                            ]),
                            style={
                                'width': 'calc(100% - 5px)',
                                'boxSizing': 'borderBox',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'marginBottom': '10px',
                            },
                            # Enable multiple files to be uploaded
                            multiple=True
                        ),
                        html.Div(id="badges_div", children=[
                            dbc.Badge(id="energy_badge", children="Energy", pill=True, color="light"),
                            dbc.Badge(id="distance_badge", children="Distance", pill=True, color="light"),
                            dbc.Badge(id="contact_badge", children="Contacts", pill=True, color="light")
                        ], style={'display': 'inline-block'}),
                        dbc.Button(id="reset_button", children="reset", size="sm", outline=True,
                                   style={"marginLeft": "3px"}),

                        html.Div(id="trace_spinner_div", children=dbc.Spinner(html.Div(id="trace-spinner",
                                                                                       className="option_log_text",
                                                                                       style={"marginBottom": "10px"})
                                                                              )
                                 ),
                    ]
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Label("Select trajectory", className="option_section_title")
                    )
                ),
                html.Div(dbc.Container(
                    [
                        dbc.Row([
                            dbc.Col(
                                className="option_label",
                                children=html.Label(children="Select system"),
                            ),
                            dbc.Col(
                                html.Div(
                                    id="system_dropdown_div",
                                    children=dcc.Dropdown(
                                        id="system_dropdown",
                                        options=[]
                                    )
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
                                html.Div(
                                    id="replica_dropdown_div",
                                    children=dcc.Dropdown(
                                        id="replica_dropdown",
                                        options=[],
                                    )
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

    def __make_network_fig(self):
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

    def __create_empty_contact_values(self):
        return pd.DataFrame({
            "Frame": [],
            "Contact": [],
            "Energy": [],
            "Replica": []
        })

    def __create_empty_energy_plot(self):
        df_energy = pd.DataFrame({
            "Frame": [],
            "Energy": [],
            "Replica": []
        })
        return px.scatter(df_energy, x="Frame", y="Energy",
                          color_discrete_sequence=px.colors.qualitative.D3[0]), df_energy

    def __update_energy_plot(self, df_energy: pd.DataFrame) -> go.Figure:
        if not df_energy.empty:
            self.scatter_energy = px.scatter(df_energy, x="Frame", y="Energy")

            self.scatter_energy.update_yaxes(nticks=10, gridcolor="lightgray", showline=True, linewidth=2,
                                             linecolor='black')
            self.scatter_energy.update_xaxes(showgrid=True, gridcolor="lightgray", showline=True, linewidth=2,
                                             linecolor='black',
                                             tickvals=list(range(0, self.tot_frames + 1,
                                                                 int((self.tot_frames + 1) / 10))))  # nticks=10,
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

        return px.scatter(df_distance, x="Frame", y="Distance", color="Replica"), df_distance

    def __update_distance_plot(self, df_distance: pd.DataFrame):
        if not df_distance.empty:
            self.scatter_distance = px.scatter(df_distance, x="Frame", y="Distance")

            self.scatter_distance.update_yaxes(nticks=10, gridcolor="lightgray", showline=True, linewidth=2,
                                               linecolor='black')
            self.scatter_distance.update_xaxes(showgrid=True, gridcolor="lightgray", showline=True, linewidth=2,
                                               linecolor='black',
                                               tickvals=list(range(0, self.tot_frames + 1,
                                                                   int((self.tot_frames + 1) / 10))))  # nticks=10,
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
            elements=elements)

    def __update_network_elements(self, df_contacts: pd.DataFrame, start_frame: int, end_frame: int) -> list:
        elements = []

        if not df_contacts.empty:
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
