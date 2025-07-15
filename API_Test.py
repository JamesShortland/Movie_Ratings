import requests
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='.env')
api_key = os.getenv('api_key')

# Step 1: Search movie by title
movie_title = 'A+Different+Man'
search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title}"
search_response = requests.get(search_url)

# Step 2: Get the movie ID from the search results
if search_response.status_code == 200:
    search_data = search_response.json()
    if search_data['results']:
        movie_id = search_data['results'][0]['id']  # Get the ID of the first result

        # Step 3: Use the movie ID to get detailed info (including cast)
        movie_details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&append_to_response=credits"
        details_response = requests.get(movie_details_url)

        if details_response.status_code == 200:
            movie_details = details_response.json()
            cast = movie_details['credits']['cast']  # Access the cast data
actors = []
for actor in cast:
    actors.append(actor['name'])

print(actors)