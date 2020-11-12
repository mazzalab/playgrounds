import random
import pandas as pd


class DBManager:
    def __init__(self):
        pass

    def connect(self, db_uri: str, db_user: str, db_passw: str) -> bool:
        pass

    def get_energy_values(self, system: str, replica: int) -> pd.DataFrame:
        df_energy = pd.DataFrame({
            "Frame": [str(i) for i in range(0, 600)] + [str(i) for i in range(0, 600)],
            "Energy": [i+random.uniform(-50, 50) for i in range(0, 600)] +
                      [i*0.5+random.uniform(-50, 50) for i in range(0, 600)],
            "Replica": (600 * ["first"]) + (600 * ["second"])
        })

        return df_energy

    def get_distance_values(self, system: str, replica: int) -> pd.DataFrame:
        df_distance = pd.DataFrame({
            "Frame": [str(i) for i in range(0, 600)] + [str(i) for i in range(0, 600)],
            "Distance": sorted([random.uniform(0, 20) for i in range(0, 600)], reverse=True) + sorted(
                [random.uniform(0, 25) for i in range(0, 600)], reverse=True),
            "Replica": (600 * ["first"]) + (600 * ["second"])
        })

        return df_distance
