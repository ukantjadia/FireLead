import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

class DataSaver:
    def __init__(self, data_folder: str = None):
        self.data_folder = Path(data_folder) if data_folder else Path.cwd()
        self.data_folder.mkdir(parents=True, exist_ok=True)

    def save(self, data: pd.DataFrame, filename: str = None) -> Path:
        df_replaced = data.replace(r'^\s*$', np.nan, regex=True)
        df_filled = df_replaced.fillna("N/A")

        if filename is None:
            now = datetime.now()
            filename = f"{now.strftime('%Y-%m-%d_%H-%M')}_leads.xlsx"

        # Create full file path
        file_path = self.data_folder / filename

        # Save as Excel file
        df_filled.to_excel(file_path, index=False, engine='openpyxl')
        print(f"\n✅ Data saved to: {file_path}")

        return file_path
