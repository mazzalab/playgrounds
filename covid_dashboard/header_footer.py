import dash_bootstrap_components as dbc
import dash_html_components as html
from typing import List


class HeaderFooter:

    @staticmethod
    def get_header(logo_url: str) -> List[str]:
        header_line = [
            dbc.Col(html.Img(
                src=logo_url,
                alt="Logo IRCCS-CSS",
                width="50",
                className="header_text"
            ), width=1),
            dbc.Col(html.H4(
                children='SPONGE: COVID-19 MD Dashboard at IRCCS Casa Sollievo della Sofferenza',
                className="header_logo"
            ))
        ]

        return header_line
