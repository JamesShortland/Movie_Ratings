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

def search_raters_movies(rater):
    rater_avg_rating = movies_df[f'{rater}_Rating'].mean()
    raters_movies = movies_df[['Movie_Title', f'{rater}_Rating']].reset_index(drop=True)
    raters_movies_cleaned = raters_movies.dropna()
    genres = movies_df[['Movie_Title', 'Genres', f'{rater}_Rating']].reset_index(drop=True)
    raters_genres = genres.explode('Genres')
    raters_genres_cleaned = raters_genres.dropna()
    average_rating_by_genre = raters_genres_cleaned.groupby('Genres').agg(
        Rating=(f'{rater}_Rating', 'mean'),
        Count=('Movie_Title', 'count')).reset_index()
    sorted_genres = average_rating_by_genre.sort_values(by='Rating', ascending=False).reset_index(drop=True)
    sorted_movies = raters_movies_cleaned.sort_values(by= f'{rater}_Rating', ascending=False).reset_index(drop=True)
    raters_count = raters_movies_cleaned[f'{rater}_Rating'].count()
    return sorted_movies, sorted_genres, rater_avg_rating, raters_count

sorted_movies, sorted_genres, average_rating, count = search_raters_movies('Monica')


print(sorted_movies.head(10).to_string(index=False))