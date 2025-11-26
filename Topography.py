import pandas as pd
import numpy as np

# Läs in kalkylarket som beskriver topografin
df = pd.read_excel("Topografi karta.xlsx", header=None)

# Konvertera direkt till en NumPy matrix
matrix = df.to_numpy()
