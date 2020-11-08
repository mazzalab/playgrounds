import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import pandas as pd
import random

from covid_dashboard import app
from covid_dashboard.Body import Body
from covid_dashboard.header_footer import HeaderFooter


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


def main():
    logo_url = app.get_asset_url("logocss.png")

    header_line = HeaderFooter.get_header(logo_url)
    body = Body(df_energy, df, df_distance)

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
