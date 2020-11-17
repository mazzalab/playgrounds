import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import pandas as pd

from covid_dashboard import app
from covid_dashboard.Body import Body
from covid_dashboard.db import DBManager
from covid_dashboard.header_footer import HeaderFooter


# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})


def main():
    logo_url = app.get_asset_url("logocss.png")
    header_line = HeaderFooter.get_header(logo_url)

    db_manager = DBManager()
    db_manager.connect(db_uri="file:///", db_user="agatta", db_passw="agatta")
    df_energy = db_manager.get_energy_values(system="WT", replica=1)
    df_distance = db_manager.get_distance_values(system="WT", replica=1)
    df_contacts = db_manager.get_contacts(system="WT", replica=1)

    body = Body(df_energy, df, df_distance, df_contacts)
    app.layout = dbc.Container(
        [
            html.Div(id='size', style={"display": "none"}),
            dcc.Location(id='url'),

            dbc.Row(header_line),
            body.build_layout()
        ],
        fluid=True
    )

    app.run_server(debug=True)


if __name__ == '__main__':
    main()
