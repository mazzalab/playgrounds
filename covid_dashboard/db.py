import random
import pandas as pd


class DBManager:
    def __init__(self):
        pass

    def connect(self, db_uri: str, db_user: str, db_passw: str) -> bool:
        pass

    def get_energy_values(self, system: str, replica: int) -> pd.DataFrame:
        df_energy = pd.DataFrame({
            "Frame": [str(i) for i in range(0, 600)],
            "Energy": [i + random.uniform(-50, 50) for i in range(0, 600)],
            "Replica": (600 * ["first"])
        })

        return df_energy

    def get_distance_values(self, system: str, replica: int) -> pd.DataFrame:
        df_distance = pd.DataFrame({
            "Frame": [str(i) for i in range(0, 600)],
            "Distance": sorted([random.uniform(0, 20) for i in range(0, 600)], reverse=True),
            "Replica": (600 * ["first"])
        })

        return df_distance

    def get_network_values(self, system, replica):
        elements = [
            # Parent Nodes
            {
                'data': {'id': 'spike', 'label': 'Spike'}
            },
            {
                'data': {'id': 'ace2', 'label': 'hACE2'}
            },

            # Children Nodes
            {
                'data': {'id': '1', 'label': 'a1', 'parent': 'spike'},
                'position': {'x': -20, 'y': 150}
            },
            {
                'data': {'id': '2', 'label': 'a2', 'parent': 'spike'},
                'position': {'x': 10, 'y': 200}
            },
            {
                'data': {'id': '3', 'label': 'a3', 'parent': 'spike'},
                'position': {'x': 10, 'y': 250}
            },
            {
                'data': {'id': '4', 'label': 'a4', 'parent': 'spike'},
                'position': {'x': -20, 'y': 300}
            },

            {
                'data': {'id': '5', 'label': 'a5', 'parent': 'ace2'},
                'position': {'x': 150, 'y': 150}
            },
            {
                'data': {'id': '6', 'label': 'a6', 'parent': 'ace2'},
                'position': {'x': 120, 'y': 200}
            },
            {
                'data': {'id': '7', 'label': 'a7', 'parent': 'ace2'},
                'position': {'x': 100, 'y': 250}
            },
            {
                'data': {'id': '8', 'label': 'a8', 'parent': 'ace2'},
                'position': {'x': 100, 'y': 300}
            },
            {
                'data': {'id': '9', 'label': 'a9', 'parent': 'ace2'},
                'position': {'x': 120, 'y': 350}
            },
            {
                'data': {'id': '10', 'label': 'a10', 'parent': 'ace2'},
                'position': {'x': 150, 'y': 400}
            },

            # Edges
            {
                'data': {'source': '1', 'target': '2'},
                'classes': 'internal'
            },
            {
                'data': {'source': '1', 'target': '4'},
                'classes': 'internal'
            },
            {
                'data': {'source': '2', 'target': '4'},
                'classes': 'internal'
            },
            {
                'data': {'source': '2', 'target': '3'},
                'classes': 'internal'
            },

            {
                'data': {'source': '1', 'target': '6'},
                'classes': 'bind'
            },
            {
                'data': {'source': '3', 'target': '7'},
                'classes': 'bind'
            },

            {
                'data': {'source': '5', 'target': '10'},
                'classes': 'internal'
            },
            {
                'data': {'source': '10', 'target': '7'},
                'classes': 'internal'
            },
            {
                'data': {'source': '7', 'target': '8'},
                'classes': 'internal'
            },
            {
                'data': {'source': '7', 'target': '9'},
                'classes': 'internal'
            },
        ]

        return elements

    def get_contacts(self, system, replica):
        df_contact = pd.DataFrame({
            "Frame": [0, 0, 1, 2, 2, 3, 3, 4],
            "Contact": [
                ("SER11", "GLY109"),
                ("MET21", "GLY10"),

                ("SER11", "GLY109"),

                ("GLY109", "SER11"),
                ("MET21", "GLY10"),

                ("GLU166", "SER11"),
                ("MET21", "GLY10"),

                ("SER11", "GLY109")
            ],
            "Contact_type": [
                "hb",
                "sb",

                "hb",

                "hb",
                "sb",

                "pc",
                "sb",

                "hb",
            ],
            "Energy": [random.randint(2, 10)] * 8,
            "Replica": 8 * ["first"]
        })

        return df_contact
