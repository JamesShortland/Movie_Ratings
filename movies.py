import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')
api_key = os.getenv('api_key')

df = pd.read_csv("movie_ratings.csv")
df['Average Rating'] = df[['Matt Rating', 'James Rating', 'Monica Rating', 'Martin Rating']].mean(axis=1)

def movie_actor_list(movie_title):
    actors = []
    movie_title_search = movie_title.replace(' ', '+')
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
    print(movie_details)
    for actor in cast:
        actors.append(actor['name'])
    return actors


# df['Actors'] = df['Movie Title'].apply(movie_actor_list)
# df.to_csv('movies_with_actors.csv', index=False)
movie_actor_list("La la land")