import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from covid_dashboard import app
from covid_dashboard.Body import Body
from covid_dashboard.header_footer import HeaderFooter


def main():
    logo_url = app.get_asset_url("logocss.png")
    header_line = HeaderFooter.get_header(logo_url)

    # body = Body(df_energy, df, df_distance, df_contacts)
    body = Body()
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
