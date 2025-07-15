import numpy as np
import pandas as pd
import requests
import os
import json
from dotenv import load_dotenv


def add_movie_ratings():
    load_dotenv(dotenv_path='.env')
    api_key = os.getenv('api_key')

    csv_file = 'movies_and_ratings'
    if os.path.exists(csv_file):
        movies_df = pd.read_csv(csv_file, index_col=False)
        movies_df['Actors'] = movies_df['Actors'].apply(json.loads)
        movies_df['Genres'] = movies_df['Genres'].apply(json.loads)
        movies_df['Characters'] = movies_df['Characters'].apply(json.loads)
        movies_df['Director'] = movies_df['Director'].apply(json.loads)
        movies_df['Production Companies'] = movies_df['Production Companies'].apply(json.loads)
        movies_df['Production Countries'] = movies_df['Production Countries'].apply(json.loads)
        movies_df['Spoken Language'] = movies_df['Spoken Language'].apply(json.loads)
    else:
        columns = ['Movie Title', 'Actors', 'Characters', 'Director', 'Genres', 'Origin Country',
                   'Production Companies', 'Production Countries', 'Release Date', 'Runtime', 'Spoken Language',
                   'Watched Date', 'Matt Rating', 'Martin Rating', 'James Rating', 'Monica Rating', 'Average Rating']
        movies_df = pd.DataFrame(columns=columns)

    while True:
        movie_title = input("What movie would you like to rate? Or press return to exit. \n")
        if movie_title == '':
            break
        if movie_title.title() in movies_df['Movie Title'].values:
            edit = input("You've already rated this movie! Would you like to update your ratings? y/n \n")
            if edit.lower() == 'n':
                continue
            elif edit.lower() == 'y':
                users = ['James', 'Monica', 'Matt', 'Martin']
                ratings = []
                for user in users:
                    rating_column = f'{user} Rating'
                    while True:
                        rating_movie = movies_df.loc[movies_df['Movie Title'] ==
                                                     movie_title.title(), rating_column].values[0]
                        if pd.isna(rating_movie):
                            new_rating = input(f"{user} hasn't rated this film yet. "
                                               f"Add a rating or press enter to skip. \n")
                        else:
                            new_rating = input(f'{user} rated {movie_title.title()} '
                                               f'{rating_movie}. Add a new rating or press enter to skip. \n')
                        if new_rating == '':
                            if not pd.isna(rating_movie):
                                ratings.append(float(rating_movie))
                            break
                        try:
                            final_new_rating = float(new_rating)
                            movies_df.loc[movies_df['Movie Title'] == movie_title.title(), rating_column] = (
                                final_new_rating)
                            ratings.append(final_new_rating)
                            break
                        except ValueError:
                            print("Sorry, I don't recognize that as a rating, try again?")
                            continue
                if ratings:
                    average_rating = sum(ratings)/len(ratings)
                    movies_df.loc[movies_df['Movie Title'] == movie_title.title(), 'Average Rating'] = average_rating
                    print(f'All changes updated! The new average rating for {movie_title.title()} is {average_rating}.')
        else:
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

                        title = movie_title.title()
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
                        watched_date = input('What date did you watch this (mm/dd/yyyy)?\n')

                        ratings = []

                        james_rating = input(f"What did James rate {title.title()}? Return if he didn't rate it.\n")
                        if james_rating != '':
                            james_rating = float(james_rating)
                            ratings.append(james_rating)
                        else:
                            james_rating = np.nan

                        monica_rating = input(f"What did Monica rate {title.title()}? Return if she didn't rate it.\n")
                        if monica_rating != '':
                            monica_rating = float(monica_rating)
                            ratings.append(monica_rating)
                        else:
                            monica_rating = np.nan

                        matt_rating = input(f"What did Matt rate {title.title()}? Return if he didn't rate it.\n")
                        if matt_rating != '':
                            matt_rating = float(matt_rating)
                            ratings.append(matt_rating)
                        else:
                            matt_rating = np.nan

                        martin_rating = input(f"What did Martin rate {title.title()}? Return if he didn't rate it.\n")
                        if martin_rating != '':
                            martin_rating = float(martin_rating)
                            ratings.append(martin_rating)
                        else:
                            martin_rating = np.nan
                        if not ratings:
                            print("You didn't add any ratings! Try again?")
                            continue
                        else:
                            average_rating = sum(ratings)/len(ratings)
                            print(f"{movie_title.title()} has been added to the database with an average rating of "
                                  f"{round(average_rating, 2)}")
                else:
                    print("Sorry, I couldn't find the movie. Try another title.")
                    continue
            movie_data = [title.title(), actors, characters, directors, genres, origin_country,
                          production_companies, production_countries, release_date,
                          runtime, spoken_language, watched_date, matt_rating, martin_rating,
                          james_rating, monica_rating, average_rating]
            movies_df.loc[len(movies_df)] = movie_data

    movies_df['Genres'] = movies_df['Genres'].apply(json.dumps)
    movies_df['Actors'] = movies_df['Actors'].apply(json.dumps)
    movies_df['Characters'] = movies_df['Characters'].apply(json.dumps)
    movies_df['Director'] = movies_df['Director'].apply(json.dumps)
    movies_df['Production Companies'] = movies_df['Production Companies'].apply(json.dumps)
    movies_df['Production Countries'] = movies_df['Production Countries'].apply(json.dumps)
    movies_df['Spoken Language'] = movies_df['Spoken Language'].apply(json.dumps)
    movies_df.to_csv('movies_and_ratings_test', index=False)
