from . import app
from .db import DBManager

import io
import math
import base64
import pandas as pd
from collections import Counter

import plotly.express as px
import plotly.graph_objects as go
from sklearn.neighbors import KNeighborsRegressor

import dash
import dash_cytoscape as cyto
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

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
                Output('upload-traces', 'contents'),
                Output('upload-traces', 'filename'),
                Output('upload-traces', 'last_modified'),
                Output('trace_spinner_div', 'children'),
                Output('badges_div', 'children'),
                Output('url', 'href')
            ],
            Input('reset_button', 'n_clicks'))(self.__reset_canvas)

        app.callback(Output('replica_dropdown', 'options'),
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
                Output('frame_slider_div', 'children'),
                Output('bond_dropdown', "options"),
            ],
            [
                Input('size', 'children'),
                Input('simtime-slider', 'value'),
                Input('frame-slider', 'value'),
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

        app.callback(
            [
                Output('simtime-slider', 'value'),
                Output('frame-slider', 'value')
            ],
            [Input("frame_select_tabs", "active_tab")])(self.__tab_switch)
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

    def __fill_or_update_plots(self, inner_window_height: int, slider_extreme_values: list,
                               frame_slider_value: int, replica: str, system: str):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        else:
            prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

        range_slider = dash.no_update
        frame_slider = dash.no_update
        system_dropdown = dash.no_update
        replica_dropdown = dash.no_update

        if prop_id == "size":
            self.__initialize_empty_components()
            system_dropdown = self.system_dropdown
            replica_dropdown = self.replica_dropdown
            range_slider = self.range_slider
            frame_slider = self.frame_slider
        elif prop_id == "replica_dropdown":
            # Filter df by selected system and replica
            self.df_energy_filter = self.df_energy[(self.df_energy['Replica'] == replica)
                                                   & (self.df_energy['System'] == system)]
            self.df_distance_filter = self.df_distance[(self.df_distance['Replica'] == replica)
                                                       & (self.df_distance['System'] == system)]
            self.df_contacts_filter = self.df_contacts[(self.df_contacts['Replica'] == replica)
                                                       & (self.df_contacts['System'] == system)]

            # set system-replica max number of frames
            self.tot_frames = max(self.df_energy_filter.Frame.max(),
                                  self.df_distance_filter.Frame.max(),
                                  self.df_contacts_filter.Frame.max())

            # update graphical components
            self.scatter_energy = self.__update_energy_plot(self.df_energy_filter)
            self.scatter_distance = self.__update_distance_plot(self.df_distance_filter)
            self.contact_dropdown_values = self.__format_contact_4_dropdown(self.df_contacts_filter)
            self.network.elements = self.__update_network_elements(self.df_contacts_filter, 0, self.tot_frames, system,
                                                                   replica)
            self.fig1 = px.bar(self.df, x="Fruit", y="Amount", color="City", barmode="group")

            # update slider extreme values
            range_slider, frame_slider = self.__create_range_and_frame_sliders()
        elif prop_id == "simtime-slider":
            self.scatter_distance.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )
            self.scatter_energy.update_layout(
                xaxis=dict(range=[slider_extreme_values[0], slider_extreme_values[1]])
            )
            self.network.elements = self.__update_network_elements(
                self.df_contacts_filter, slider_extreme_values[0], slider_extreme_values[1], system, replica
            )
        else:
            # frame_slider's event here
            self.scatter_energy = self.__update_scatter_dot_position(
                self.scatter_energy, frame_slider_value
            )

            self.scatter_distance = self.__update_scatter_dot_position(
                self.scatter_distance, frame_slider_value
            )

            self.network.elements = self.__update_network_elements(
                self.df_contacts_filter, frame_slider_value, frame_slider_value, system, replica
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

        return self.network, self.scatter_energy, self.scatter_distance, self.fig1, system_dropdown, replica_dropdown, range_slider, frame_slider, self.contact_dropdown_values

    @staticmethod
    @app.callback(
        dash.dependencies.Output('output-container-simtime-slider', 'children'),
        [dash.dependencies.Input('simtime-slider', 'value')])
    def update_range_selection(value):
        return f'Selected frames: {value[0]}-{value[1]}'

    @staticmethod
    @app.callback(
        dash.dependencies.Output('output-container-frame-slider', 'children'),
        [dash.dependencies.Input('frame-slider', 'value')])
    def update_frame_selection(value):
        return f'Selected frame: {value}'

    def __set_replica_dropdown(self, system):
        ctx = dash.callback_context
        if not ctx.triggered or not system:
            raise PreventUpdate

        replica_list: list = self.df_energy[self.df_energy['System'] == system]['Replica'].unique().tolist()
        replica_list.extend(self.df_distance[self.df_distance['System'] == system]['Replica'].unique().tolist())
        replica_list.extend(self.df_contacts[self.df_contacts['System'] == system]['Replica'].unique().tolist())

        return [{'label': x, 'value': x} for x in list(sorted(set(replica_list)))]

    def __reset_canvas(self, reset_click: int):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        upload_last_modified = []
        upload_file_namne = []
        upload_contents = []

        new_badges = [
            dbc.Badge(id="energy_badge", children="Energy", pill=True, color="light"),
            dbc.Badge(id="distance_badge", children="Distance", pill=True, color="light"),
            dbc.Badge(id="contact_badge", children="Contacts", pill=True, color="light")
        ]

        new_spinner = dbc.Spinner(html.Div(id="trace-spinner",
                                           className="option_log_text",
                                           style={"marginBottom": "10px"}))

        self.__initialize_empty_components()

        return upload_contents, upload_file_namne, upload_last_modified, new_spinner, new_badges, "localhost:8050"

    def __load_trajectories(self, files_content, files_name, files_date):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        else:
            energy_color = dash.no_update
            distance_color = dash.no_update
            contact_color = dash.no_update
            systems = list()

            for file in zip(files_content, files_name, files_date):
                content_type, content_string = file[0].split(',')
                decoded = base64.b64decode(content_string)

                try:
                    if 'txt' in file[1]:
                        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                    elif 'xls' in file[1] or 'xlsx' in file[1]:
                        df = pd.read_excel(io.BytesIO(decoded))

                        if 'frame' in df and 'system' in df and 'replica' in df:
                            systems.extend(df['system'].unique())
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
                systems_dict = [{'label': x, 'value': x} for x in list(set(systems))]
            else:
                systems_dict = dash.no_update

            return msg, energy_color, distance_color, contact_color, systems_dict

    def __tab_switch(self, at):
        if at == "aggregate_tab":
            return [0, self.tot_frames], dash.no_update
        else:
            return dash.no_update, 0

    # endregion

    # region PRIVATE METHODS
    def __initialize_empty_components(self):
        self.tot_frames = 1
        self.loaded_plots = []

        self.system_dropdown = dcc.Dropdown(id="system_dropdown", options=[])
        self.replica_dropdown = dcc.Dropdown(id="replica_dropdown", options=[])

        self.df_contacts = self.__create_empty_contact_values()
        self.df_contacts_filter = self.__create_empty_contact_values()
        self.contact_dropdown_values = self.__format_contact_4_dropdown(self.df_contacts)
        self.network = self.__create_empty_network()

        self.scatter_energy, self.df_energy = self.__create_empty_energy_plot()
        self.scatter_energy_filter, self.df_energy_filter = self.__create_empty_energy_plot()

        self.scatter_distance, self.df_distance = self.__create_empty_distance_plot()
        self.scatter_distance_filter, self.df_distance_filter = self.__create_empty_distance_plot()

        self.df = pd.DataFrame({
            "Fruit": [],
            "Amount": [],
            "City": []
        })
        self.fig1 = px.bar(self.df, x="Fruit", y="Amount", color="City", barmode="group")

        self.range_slider, self.frame_slider = self.__create_empty_range_and_frame_sliders()

    def __create_empty_range_and_frame_sliders(self):
        new_range_slider = dcc.RangeSlider(
            id='simtime-slider',
            min=0,
            max=1,
            # step=None,
            marks={i: str(i) for i in range(0, 2, 1)},
            value=[0, 1])

        new_frame_slider = dcc.Slider(
            id='frame-slider',
            min=0,
            max=1,
            # step=None,
            marks={i: str(i) for i in range(0, 2, 1)},
            value=0
        ),

        return new_range_slider, new_frame_slider

    def __create_range_and_frame_sliders(self):
        ten_ticks_distance = math.floor(self.tot_frames / 3)
        if ten_ticks_distance == 0:
            raise dash.exceptions.PreventUpdate

        tick_marks = {i: str(i) for i in range(0, self.tot_frames + 1, ten_ticks_distance)}
        new_range_slider = dcc.RangeSlider(
            id='simtime-slider',
            min=0,
            max=self.tot_frames,
            # step=None,
            marks=tick_marks,
            value=[0, self.tot_frames])

        new_frame_slider = dcc.Slider(
            id='frame-slider',
            min=0,
            max=self.tot_frames,
            # step=None,
            marks=tick_marks,
            value=0,
            tooltip={'always_visible': True, 'placement': 'left'}
        )

        return new_range_slider, new_frame_slider

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
        range_slider, frame_slider = self.__create_empty_range_and_frame_sliders()

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
                                        options=[],
                                        clearable=False
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
                                        clearable=False
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
                                                    children=range_slider,
                                                ),
                                                html.Div(id='output-container-simtime-slider',
                                                         className="option_log_text")
                                            ]
                                        ),
                                    ),
                                    tab_id="aggregate_tab",
                                    label="Aggregate"),
                                dbc.Tab(
                                    dbc.Card(
                                        dbc.CardBody(
                                            html.Div(
                                                [
                                                    html.Label("Select one frame",
                                                               className="option_log_text"),
                                                    html.Div(
                                                        id="frame_slider_div",
                                                        children=frame_slider,
                                                    ),
                                                    html.Div(id='output-container-frame-slider',
                                                             className="option_log_text")
                                                ]
                                            ),
                                        )
                                    ),
                                    tab_id="frame_tab",
                                    label="Frame",
                                    # disabled=True
                                ),
                            ],
                            id="frame_select_tabs",
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
            "System": [],
            "Frame": [],
            "Contact": [],
            "Energy": [],
            "Replica": []
        })

    def __create_empty_energy_plot(self):
        df_energy = pd.DataFrame({
            "Frame": [],
            "Energy": [],
            "Replica": [],
            "System": []
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
            x = df_energy.Frame.values[0:self.tot_frames + 1]
            knn_uni.fit(x.reshape(-1, 1), df_energy.Energy)
            y_uni = knn_uni.predict(x.reshape(-1, 1))
            self.scatter_energy.add_trace(go.Scatter(x=x, y=y_uni, mode='lines',
                                                     name=self.scatter_energy["data"][0]["legendgroup"] + " " + "fit",
                                                     line=dict(color=px.colors.qualitative.D3[0])))

            self.scatter_energy.add_trace(go.Scatter(x=x, y=[y_uni[0]], mode="markers",
                                                     marker=dict(color="red", size=10), name="cursor",
                                                     showlegend=False)
                                          )

        return self.scatter_energy

    def __create_empty_distance_plot(self):
        df_distance = pd.DataFrame({
            "Frame": [],
            "Distance": [],
            "Replica": [],
            "System": []
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
            x = df_distance.Frame.values[0:self.tot_frames + 1]
            knn_uni.fit(x.reshape(-1, 1), df_distance.Distance)
            y_uni = knn_uni.predict(x.reshape(-1, 1))
            self.scatter_distance.add_trace(
                go.Scatter(x=x, y=y_uni, mode='lines',
                           name=self.scatter_distance["data"][0]["legendgroup"] + " " + "fit",
                           line=dict(color=px.colors.qualitative.D3[0])))

            self.scatter_distance.add_trace(go.Scatter(x=x, y=[y_uni[0]], mode="markers",
                                                       marker=dict(color="red", size=10),
                                                       showlegend=False)
                                            )

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

    def __update_network_elements(self, df_contacts: pd.DataFrame, start_frame: int, end_frame: int,
                                  system: str, replica: str) -> list:
        elements = []

        if not df_contacts.empty and (set(df_contacts.Frame) & set(range(start_frame, end_frame+1))):
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
            edges = list()
            filtered_df_contacts = df_contacts[
                (df_contacts["Frame"] >= start_frame) & (df_contacts["Frame"] <= end_frame) &
                (df_contacts["System"] == system) & (df_contacts["Replica"] == replica)
                ]
            for index, row in filtered_df_contacts.iterrows():
                contact = row.Contact
                ace2_nodes.add(contact[0] + "_a")
                spike_nodes.add(contact[1] + "_s")
                edges.append((contact[0] + "_a", contact[1] + "_s"))

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

            #  count, scale (f(x) = (x-min)/(max-min) edge width and add edges
            edges = Counter(edges)
            min_width = min(edges.values())
            max_width = max(edges.values())
            for e, c in edges.items():
                if min_width == max_width:
                    ewidth = 1
                else:
                    # TODO: set the maximum width value in a separate config file (here: 5)
                    ewidth = 5 * (((c - min_width) / (max_width - min_width)) + 0.1)

                temp_dict = {
                    'data': {'source': e[0], 'target': e[1]},
                    'style': {'width': ewidth},
                    'classes': 'bind'
                }
                elements.append(temp_dict)

        return elements

    def __update_scatter_dot_position(self, scatter_plot, frame_slider_value: int):
        y_empty_vector = [None] * self.tot_frames
        y_vector = y_empty_vector
        act_x = scatter_plot["data"][1]["x"]
        if frame_slider_value in act_x:
            selected_frame = frame_slider_value
        else:
            selected_frame = min(act_x, key=lambda x: abs(x - frame_slider_value))
        y_vector[frame_slider_value] = scatter_plot["data"][1]["y"][selected_frame]
        scatter_plot["data"][2]["y"] = y_vector

        return scatter_plot
    # endregion
