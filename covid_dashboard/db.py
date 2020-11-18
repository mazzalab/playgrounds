import random
import pandas as pd


class DBManager:
    def __init__(self):
        pass

    def connect(self, db_uri: str, db_user: str, db_passw: str) -> bool:
        pass

    def get_energy_values(self, system: str, replica: int) -> pd.DataFrame:
        df_energy = pd.DataFrame({
            "Frame": [str(i) for i in range(0, 10)],
            "Energy": [i + random.uniform(-50, 50) for i in range(0, 10)],
            "Replica": (10 * ["first"])
        })

        return df_energy

    def get_distance_values(self, system: str, replica: int) -> pd.DataFrame:
        df_distance = pd.DataFrame({
            "Frame": [str(i) for i in range(0, 10)],
            "Distance": sorted([random.uniform(0, 20) for i in range(0, 10)], reverse=True),
            "Replica": (10 * ["first"])
        })

        return df_distance

    def get_contacts(self, system, replica):
        df_contact = pd.DataFrame({
            "Frame": [0, 0, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 9],
            "Contact": [
                ("SER11", "GLY109"),
                ("MET21", "TYR34"),
                ("SER11", "GLY109"),
                ("GLY109", "SER11"),
                ("MET21", "GLY10"),
                ("GLU166", "SER11"),
                ("MET21", "GLY10"),
                ("SER11", "GLY109"),
                ('MET2', "GLU99"),
                ('ARG212', "GLY10"),
                ('HIS54', 'SER113'),
                ('HIS54', 'GLY10'),
                ('TRP88', 'VAL77'),
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
                "hb",
                "sb",
                "pc",
                "sb",
                "hb",
            ],
            "Energy": [random.randint(-8, 10)] * 13,
            "Replica": 13 * ["first"]
        })

        return df_contact
