import numpy as np
import pandas as pd
import requests
import os
import json
import inquirer
from dotenv import load_dotenv


def add_movie_ratings():
    csv_file = 'movies_and_ratings'

    load_dotenv(dotenv_path='.env')
    api_key = os.getenv('api_key')

    if os.path.exists(csv_file):
        movies_df = pd.read_csv(csv_file, index_col=False)

        def safe_json_loads(x):
            if isinstance(x, str):
                try:
                    return json.loads(x)
                except ValueError:
                    return x
            return x
        movies_df['Actors'] = movies_df['Actors'].apply(safe_json_loads)
        movies_df['Genres'] = movies_df['Genres'].apply(safe_json_loads)
        movies_df['Characters'] = movies_df['Characters'].apply(safe_json_loads)
        movies_df['Director'] = movies_df['Director'].apply(safe_json_loads)
        movies_df['Production Companies'] = movies_df['Production Companies'].apply(safe_json_loads)
        movies_df['Production Countries'] = movies_df['Production Countries'].apply(safe_json_loads)
        movies_df['Spoken Language'] = movies_df['Spoken Language'].apply(safe_json_loads)

    else:
        columns = ['Movie Title', 'Actors', 'Characters', 'Director', 'Genres', 'Origin Country',
                   'Production Companies', 'Production Countries', 'Release Date', 'Runtime', 'Spoken Language',
                   'Watched Date', 'Matt Rating', 'Martin Rating', 'James Rating', 'Monica Rating', 'Average Rating']
        movies_df = pd.DataFrame(columns=columns)

    filename = 'raters.json'
    with open(filename, 'r') as f:
        users = json.load(f)

    def parse_ratings(input_str):
        pairs = input_str.split(", ")
        ratings_dict = {}
        for pair in pairs:
            username, rating = pair.split(" ")
            ratings_dict[username.title()] = rating
        return ratings_dict

    while True:
        movie_title = input("What movie would you like to rate? Or press return to exit. \n")
        if movie_title == '':
            break
        if movie_title.title() in movies_df['Movie Title'].values:
            edit = input("You've already rated this movie! Would you like to update your ratings? y/n \n")
            if edit.lower() == 'n':
                continue
            elif edit.lower() == 'y':
                ratings = []
                for user in users:
                    rating_column = f'{user} Rating'
                    rating_movie = movies_df.loc[movies_df['Movie Title'] ==
                                                 movie_title.title(), rating_column].values[0]
                    if not pd.isna(rating_movie):
                        while True:
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
                    else:
                        continue
                new_user = input('Please enter new ratings by typing the user and their rating separated with a comma '
                                 '(ie. James 10, Monica 10) or press return to exit\n')
                if new_user != '':
                    new_ratings = parse_ratings(new_user)
                else:
                    average_rating = sum(ratings) / len(ratings)
                    movies_df.loc[movies_df['Movie Title'] == movie_title.title(), 'Average Rating'] = average_rating
                    print(f'All changes updated! The new average rating for {movie_title.title()} is {average_rating}.')
                    break

                for name in new_ratings:
                    rating_column = f'{name.title()} Rating'
                    if name.title() in users:
                        print(f'You already have {name.title()} in your dataframe, updating with their rating...')
                        try:
                            final_new_rating = float(new_ratings[name])
                            movies_df.loc[movies_df['Movie Title'] == movie_title.title(), rating_column] = (
                                    final_new_rating)
                            ratings.append(final_new_rating)
                        except ValueError:
                            print(f"Sorry, I don't recognize {name.title()}'s rating as a rating, try again?")
                    elif name.title() not in users:
                        print(f'Adding {name.title()} to the list of users now...')
                        users.append(name.title())
                        try:
                            final_new_rating = float(new_ratings[name])
                            movies_df.loc[movies_df['Movie Title'] == movie_title.title(), rating_column] = (
                                final_new_rating)
                            ratings.append(final_new_rating)
                        except ValueError:
                            print(f"Sorry, I don't recognize {name.title()}'s rating as a rating, try again?")
                if ratings:
                    average_rating = sum(ratings) / len(ratings)
                    movies_df.loc[movies_df['Movie Title'] == movie_title.title(), 'Average Rating'] = average_rating
                    print(f'All changes updated! The new average rating for {movie_title.title()} is {average_rating}.')
        else:
            movie_title_search = movie_title.replace(' ', '+')
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title_search}"
            search_response = requests.get(search_url)
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data['results']:
                    movies_list = [
                        f"{movie['title']} ({movie.get('release_date', 'Unknown')})"
                        for movie in search_data['results']
                    ]

                    # Use Inquirer to ask the user to select the movie
                    questions = [
                        inquirer.List(
                            'movie',
                            message="Please select the correct movie",
                            choices=movies_list
                        )
                    ]

                    selected_movie_title = inquirer.prompt(questions)['movie']

                    # Find the selected movie in the search results
                    for movie in search_data['results']:
                        if f"{movie['title']} ({movie.get('release_date', 'Unknown')})" == selected_movie_title:
                            selected_movie = movie
                            break

                    movie_id = selected_movie['id']
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
                        movie_data = [title.title(), actors, characters, directors, genres, origin_country,
                                      production_companies, production_countries, release_date,
                                      runtime, spoken_language, watched_date]

                        required_columns = movies_df.shape[1]
                        current_columns = len(movie_data)
                        difference = required_columns - current_columns
                        if difference > 0:
                            movie_data.extend([np.nan] * difference)
                        movies_df.loc[len(movies_df)] = movie_data

                    users_and_ratings = input('Please enter all users and their ratings '
                                              'separated with a comma (ie. James 10, Monica 10)\n')

                    user_ratings = parse_ratings(users_and_ratings)
                    ratings_values = [float(value) for value in user_ratings.values()]
                    average_rating = sum(ratings_values)/len(ratings_values)
                    movies_df.loc[
                        movies_df['Movie Title'] == movie_title.title(), 'Average Rating'] = average_rating

                    for name in user_ratings:
                        rating_column = f'{name.title()} Rating'
                        if name.title() in users:
                            try:
                                final_new_rating = float(user_ratings[name])
                                movies_df.loc[movies_df['Movie Title'] == movie_title.title(), rating_column] = (
                                    final_new_rating)
                            except ValueError:
                                print(f"Sorry, I don't recognize {name.title()}'s rating as a rating, try again?")
                        else:
                            users.append(name.title())
                            try:
                                final_new_rating = float(user_ratings[name])
                                movies_df.loc[movies_df['Movie Title'] == movie_title.title(), rating_column] = (
                                    final_new_rating)
                            except ValueError:
                                print(f"Sorry, I don't recognize {name.title()}'s rating as a rating, try again?")
                    print(f'{movie_title.title()} has been added to the system, '
                          f'with an average rating of {round(average_rating, 2)}')

    with open(filename, 'w') as f:
        json.dump(users, f)
    movies_df['Genres'] = movies_df['Genres'].apply(json.dumps)
    movies_df['Actors'] = movies_df['Actors'].apply(json.dumps)
    movies_df['Characters'] = movies_df['Characters'].apply(json.dumps)
    movies_df['Director'] = movies_df['Director'].apply(json.dumps)
    movies_df['Production Companies'] = movies_df['Production Companies'].apply(json.dumps)
    movies_df['Production Countries'] = movies_df['Production Countries'].apply(json.dumps)
    movies_df['Spoken Language'] = movies_df['Spoken Language'].apply(json.dumps)
    movies_df.to_csv('movies_and_ratings', index=False)
