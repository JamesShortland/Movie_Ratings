import pandas as pd
import json
csv_file = 'movies_and_ratings'
movies_df = pd.read_csv(csv_file)
movies_df['Genres'] = movies_df['Genres'].apply(json.loads)
movies_df['Cast'] = movies_df['Cast'].apply(json.loads)
movies_df['Director'] = movies_df['Director'].apply(json.loads)
movies_df['Production_Companies'] = movies_df['Production_Companies'].apply(json.loads)
movies_df['Production_Countries'] = movies_df['Production_Countries'].apply(json.loads)
movies_df['Spoken_Language'] = movies_df['Spoken_Language'].apply(json.loads)
def watched_stats():
    year_and_months_dict = {}
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December']
    for year in range(2000, 2100):
        year_watched = movies_df[movies_df['Watched_Date'].str.contains(str(year), case=False, na=False)]
        year_count = year_watched['Watched_Date'].count()
        if year_count > 0:
            months_and_movies_dict = {}
            for month in range(1, 13):
                month_watched = year_watched[year_watched['Watched_Date'].str.startswith(f'{month}/')]
                month_count = month_watched['Watched_Date'].count()
                months_and_movies_dict[month_names[month-1]] = int(month_count)
            months_and_movies_dict['Total'] = int(year_count)
            year_and_months_dict[str(year)] = months_and_movies_dict
    month_year_df = pd.DataFrame.from_dict(year_and_months_dict, orient='index')
    return month_year_df

month_year = watched_stats()

print(month_year)