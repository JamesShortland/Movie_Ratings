import os
import pandas as pd
csv_file = 'movies_and_ratings'
if os.path.exists(csv_file):
    movies_df = pd.read_csv(csv_file, index_col=False)

print(movies_df)

