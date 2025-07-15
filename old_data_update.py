import numpy as np
import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')
api_key = os.getenv('api_key')

csv_file = 'movies_and_ratings_test'
old_data_file = 'old_movies_data.csv'  # Your old data file with titles, ratings, and watched dates

# Load current movies data
if os.path.exists(csv_file):
    movies_df = pd.read_csv(csv_file)
else:
    columns = ['Movie Title', 'Actors', 'Characters', 'Director', 'Genres', 'Origin Country', 'Production Companies',
               'Production Countries', 'Release Date', 'Runtime (mins)', 'Spoken Language', 'Watched Date',
               'Matt Rating', 'Martin Rating', 'James Rating', 'Monica Rating', 'Average Rating']
    movies_df = pd.DataFrame(columns=columns)

# Load old data
if os.path.exists(old_data_file):
    old_movies_df = pd.read_csv(old_data_file)

    for _, row in old_movies_df.iterrows():
        title = row['Movie_Title']
        watched_date = row['Watched_Date']

        # Use the API to fetch new details
        movie_title_search = title.replace(' ', '+')
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title_search}"
        search_response = requests.get(search_url)

        if search_response.status_code == 200:
            search_data = search_response.json()
            if search_data['results']:
                movie_id = search_data['results'][0]['id']
                movie_details_url = (f'https://api.themoviedb.org/3/movie/{movie_id}?'
                                     f'api_key={api_key}&append_to_response=credits')
                details_response = requests.get(movie_details_url)

                if details_response.status_code == 200:
                    movie_details = details_response.json()
                    cast = movie_details['credits']['cast']
                    crew = movie_details['credits']['crew']

                    actors = [actor['name'] for actor in cast]
                    characters = [actor['character'] for actor in cast]
                    directors = [person['name'] for person in crew if person.get('job') == 'Director']
                    genres = [genre['name'] for genre in movie_details['genres']]
                    origin_country = movie_details['origin_country']
                    production_companies = [company['name'] for company in movie_details['production_companies']]
                    production_countries = [country['name'] for country in movie_details['production_countries']]
                    release_date = movie_details['release_date']
                    runtime = movie_details['runtime']
                    spoken_language = [language['english_name'] for language in movie_details['spoken_languages']]

                    # Extract ratings from old data
                    matt_rating = row.get('Matt_Rating', np.nan)
                    martin_rating = row.get('Martin_Rating', np.nan)
                    james_rating = row.get('James_Rating', np.nan)
                    monica_rating = row.get('Monica_Rating', np.nan)

                    # Calculate average rating if there are valid ratings
                    ratings = [r for r in [matt_rating, martin_rating, james_rating, monica_rating] if pd.notna(r)]
                    average_rating = sum(ratings) / len(ratings) if ratings else np.nan

                    # Prepare movie data
                    movie_data = [title.title(), json.dumps(actors), json.dumps(characters), json.dumps(directors), json.dumps(genres), origin_country,
                                  json.dumps(production_companies), json.dumps(production_countries), release_date,
                                  runtime, json.dumps(spoken_language), watched_date, matt_rating, martin_rating,
                                  james_rating, monica_rating, average_rating]
                    movies_df.loc[len(movies_df)] = movie_data

# Save the updated DataFrame
movies_df.to_csv(csv_file, index=False)
