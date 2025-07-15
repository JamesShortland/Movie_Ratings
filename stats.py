import pandas as pd
import json
import shutil
import inquirer
from tabulate import tabulate
from inquirer.themes import BlueComposure


# on opening, deal with json list within csv
csv_file = 'movies_and_ratings'
movies_df = pd.read_csv(csv_file, index_col=False)
movies_df['Genres'] = movies_df['Genres'].apply(json.loads)
movies_df['Actors'] = movies_df['Actors'].apply(json.loads)
movies_df['Characters'] = movies_df['Characters'].apply(json.loads)
movies_df['Director'] = movies_df['Director'].apply(json.loads)
movies_df['Production Companies'] = movies_df['Production Companies'].apply(json.loads)
movies_df['Production Countries'] = movies_df['Production Countries'].apply(json.loads)
movies_df['Spoken Language'] = movies_df['Spoken Language'].apply(json.loads)

# headers used later for formatting column headers
headers = {'AverageRating': 'Average Rating',
           'MovieCount': 'Movie Count',
           'TotalRuntime': 'Total Runtime',
           'AverageRanking': 'Average Movie Ranking'}

# list of raters saved in json to allow for dynamic users, open here
filename = 'raters.json'
with open(filename, 'r') as f:
    users = json.load(f)

# users contains just the name, iterate through names to add 'Rating' to finish the column header
# average rating added to rating columns for use later
rating_columns = []
user_columns = []
for user in users:
    user_columns.append(f'{user} Rating')
rating_columns = user_columns + ['Average Rating']

# for formatting: allows for lines that span the width of terminal later
columns = shutil.get_terminal_size().columns


# used later for formatting tables, rounds values and gets rid of leading/ending zeros and replaces nan values with '-'
def safe_format(value):
    if pd.isna(value):
        return '-'
    elif isinstance(value, float):
        return f"{value:.2f}".rstrip('0').rstrip('.')
    elif isinstance(value, int):
        return str(value)
    return value


# adds ranking column using all_movie_df, and moves ranking column to left side of df
# used for formatting later
def add_ranking_columns(df):
    new_df = df.merge(all_movie_df[['Movie Title', 'Ranking']], on='Movie Title', how='left')
    final_columns = ['Ranking'] + [col for col in df.columns if col != 'Ranking']
    new_df = new_df[final_columns]
    new_df = new_df.sort_values(by='Ranking', ascending=True).reset_index(drop=True)
    return new_df


# produces table of all movies, and information about movie list as a whole
def all_movies():
    print('-' * columns)
    # specific columns defines columns needed for this specific function, adds rating_columns from earlier to finish
    # off list of all needed columns for dataframe
    specific_columns = ['Movie Title', 'Watched Date', 'Runtime (mins)']
    specific_columns.extend(rating_columns)
    # makes a new columns in the movies_df that counts the number of ratings (user_columns without nan)
    movies_df['Number_of_Ratings'] = movies_df[user_columns].notna().sum(axis=1)
    # adds the new column to the specific columns list to call later
    specific_columns.append('Number_of_Ratings')
    # makes a new df made up of the specific columns, sorts by first average rating and then number of ratings
    all_movies_specific_columns = (
        movies_df[specific_columns]
        .sort_values(by=['Average Rating', 'Number_of_Ratings'], ascending=False)
        .reset_index(drop=True)
    )
    # Creates a new column 'Ranking' that counts up from 1 per row
    all_movies_specific_columns['Ranking'] = range(1, len(movies_df) + 1)

    # movie_ranking takes a df row by row and checks if the row before has the same average rating and same number of
    # ratings. if so, give the movie the same ranking as the movie before it, otherwise keep the ranking it already has
    def movie_ranking(df):
        for i in range(1, len(df)):
            if ((df.loc[i, 'Average Rating'] == df.loc[i - 1, 'Average Rating']) and
                    (df.loc[i, 'Number_of_Ratings'] == df.loc[i - 1, 'Number_of_Ratings'])):
                df.loc[i, 'Ranking'] = df.loc[i - 1, 'Ranking']
        return df

    # makes a new list that puts the ranking in first, keeping the rest of the columns in the same order
    columns_in_order = ['Ranking'] + [col for col in all_movies_specific_columns.columns if col != 'Ranking']
    all_movies_specific_columns = all_movies_specific_columns[columns_in_order]

    # runs the df through the movie_ranking function to get finalized ranking numbers
    all_movies_specific_columns = movie_ranking(all_movies_specific_columns)

    # gets rid of number_of_ratings columns for later printing (we don't want to see number of ratings in final print)
    all_movies_specific_columns = all_movies_specific_columns.drop(columns='Number_of_Ratings').reset_index(drop=True)
    # counts number of movies by titles and average of average ratings
    movie_count = all_movies_specific_columns['Movie Title'].count()
    movie_avg = all_movies_specific_columns['Average Rating'].mean()

    # math to get all total runtime information (days, hours, minutes)
    runtime_hours = int(all_movies_specific_columns['Runtime (mins)'].sum()/60)
    runtime_days = int(runtime_hours/24)
    runtime_hours = int(runtime_hours % 24)
    runtime_minutes = (all_movies_specific_columns['Runtime (mins)'].sum() % 60)

    # creates total row, getting the average of all the rating columns (all users + average rating)
    total_row = all_movies_specific_columns[rating_columns].mean().round(2)
    # saves row (pd.series) as dictionary to make adding values easier
    total_row = total_row.to_dict()
    # adds label 'AVERAGE RATINGS' under Runtime (mins) column
    total_row['Runtime (mins)'] = 'AVERAGE RATINGS'
    # iterates through all other columns in df, and adds a blank entry for each into the dictionary
    for column in all_movies_specific_columns.columns:
        if column not in total_row:
            total_row[column] = ''
    # adds total_row into df with index label 'Average Row'
    all_movies_specific_columns.loc['Average Row'] = total_row
    # rounds all values in df to 2 decimal places
    all_movies_specific_columns_rounded = all_movies_specific_columns.round(2)
    # uses safe_format for nice printing formatting, and drops index
    all_movies_specific_columns_final = all_movies_specific_columns_rounded.map(safe_format).reset_index(drop=True)
    return (movie_count, runtime_days, runtime_hours, runtime_minutes, movie_avg,
            all_movies_specific_columns_final, all_movies_specific_columns)


# calls all_movies function for all_movie_df for use later
(all_movie_count, total_runtime_days, total_runtime_hours, total_runtime_minutes, all_movie_avg,
 all_movies_specific_columns_display, all_movie_df) = all_movies()

# uses explode to get actor information out of lists, (each movie repeated as many times as size of cast list)
df_exploded_cast = movies_df.explode('Actors')
# merges exploded cast df with all_movie_df in order to get rankings (matches movie titles across df and adds rankings)
df_exploded_cast = df_exploded_cast.merge(all_movie_df[['Movie Title', 'Ranking']], on='Movie Title', how='left')
# same logic as before to get 'Ranking' column on the far left
sorted_columns = ['Ranking'] + [col for col in df_exploded_cast.columns if col != 'Ranking']
df_exploded_cast = df_exploded_cast[sorted_columns]
# groups exploded df by actor name, and aggregates information from ranking, rating, movie count, and runtime columns
average_rating_by_actor = df_exploded_cast.groupby('Actors').agg(
    AverageRanking=('Ranking', 'mean'),
    AverageRating=('Average Rating', 'mean'),
    MovieCount=('Movie Title', 'count'),
    TotalRuntime=('Runtime (mins)', 'sum')).reset_index()
# needs little extra logic to round the value of average ranking to 2 places
average_rating_by_actor['AverageRanking'] = pd.to_numeric(average_rating_by_actor['AverageRanking'],
                                                          errors='coerce').round(2)

# same logic as actors
df_exploded_genre = movies_df.explode('Genres')
df_exploded_genre = df_exploded_genre.merge(all_movie_df[['Movie Title', 'Ranking']], on='Movie Title', how='left')
sorted_columns = ['Ranking'] + [col for col in df_exploded_genre.columns if col != 'Ranking']
df_exploded_genre = df_exploded_genre[sorted_columns]
average_rating_by_genre = df_exploded_genre.groupby('Genres').agg(
    AverageRanking=('Ranking', 'mean'),
    AverageRating=('Average Rating', 'mean'),
    MovieCount=('Movie Title', 'count'),
    TotalRuntime=('Runtime (mins)', 'sum')).reset_index()
average_rating_by_genre['AverageRanking'] = pd.to_numeric(average_rating_by_genre['AverageRanking'],
                                                          errors='coerce').round(2)

df_exploded_language = movies_df.explode('Spoken Language')
average_rating_by_language = df_exploded_language.groupby('Spoken Language').agg(
    AverageRating=('Average Rating', 'mean'),
    MovieCount=('Movie Title', 'count'),
    TotalRuntime=('Runtime (mins)', 'sum')).reset_index()
df_production_companies = movies_df.explode('Production Companies')
average_rating_by_company = df_production_companies.groupby('Production Companies').agg(
    AverageRating=('Average Rating', 'mean'),
    MovieCount=('Movie Title', 'count'),
    TotalRuntime=('Runtime (mins)', 'sum')).reset_index()

# same logic as genre and actors
df_director = movies_df.explode('Director')
df_director = df_director.merge(all_movie_df[['Movie Title', 'Ranking']], on='Movie Title', how='left')
sorted_columns = ['Ranking'] + [col for col in df_director.columns if col != 'Ranking']
df_director = df_director[sorted_columns]
average_rating_by_director = df_director.groupby('Director').agg(
    AverageRanking=('Ranking', 'mean'),
    AverageRating=('Average Rating', 'mean'),
    MovieCount=('Movie Title', 'count'),
    TotalRuntime=('Runtime (mins)', 'sum')).reset_index()
average_rating_by_director['AverageRanking'] = pd.to_numeric(average_rating_by_director['AverageRanking'],
                                                             errors='coerce').round(2)

# uses header dictionary to change the names of the columns across the board
average_rating_by_actor = average_rating_by_actor.rename(columns=headers)
average_rating_by_genre = average_rating_by_genre.rename(columns=headers)
average_rating_by_language = average_rating_by_language.rename(columns=headers)
average_rating_by_company = average_rating_by_company.rename(columns=headers)
average_rating_by_director = average_rating_by_director.rename(columns=headers)
sorted_languages = average_rating_by_language.sort_values(by='Movie Count', ascending=False).reset_index(drop=True)


# produces list of actors sorted by runtime and rating
def sorted_actors():
    # filters actors average rating by actors with more than 3 movies
    filtered_actors = average_rating_by_actor[average_rating_by_actor['Movie Count'] > 3]
    # sorted by total_runtime and rating
    actors_sorted_runtime = filtered_actors.sort_values(by='Total Runtime', ascending=False).reset_index(drop=True)
    actors_sorted_rating = filtered_actors.sort_values(by='Average Rating', ascending=False).reset_index(drop=True)
    # removes run time from the final rating df
    actors_sorted_final = (actors_sorted_rating[['Actors', 'Average Rating', 'Average Movie Ranking']]
                           .reset_index(drop=True))
    return actors_sorted_runtime.head(15), actors_sorted_final.head(15)


# returns df with genres sorted by average rating
def sorted_genres():
    genres_sorted = average_rating_by_genre.sort_values(by='Average Rating', ascending=False).reset_index(drop=True)
    return genres_sorted


# same as sorted_actors, returns directors sorted by runtime and rating
def sorted_directors():
    # filters directors that have 2+ movies
    filtered_directors = average_rating_by_director[average_rating_by_director['Movie Count'] > 1]
    director_sorted_rating = filtered_directors.sort_values(by='Average Rating', ascending=False).reset_index(drop=True)
    director_sorted_final = director_sorted_rating[['Director', 'Average Rating', 'Average Movie Ranking'
                                                    ]].reset_index(drop=True)
    director_sorted_runtime = filtered_directors.sort_values(by='Total Runtime', ascending=False).reset_index(drop=True)
    return (director_sorted_runtime.head(15),
            director_sorted_final.head(15))


# same as sorted_companies, returns directors sorted by runtime and rating
def sorted_companies():
    filtered_companies = average_rating_by_company[average_rating_by_company['Movie Count'] > 2].reset_index(drop=True)
    sorted_companies = filtered_companies.sort_values(by='Average Rating', ascending=False).reset_index(drop=True)
    director_sorted_bad = filtered_companies.sort_values(by='Average Rating', ascending=True).reset_index(drop=True)
    director_sorted_final = sorted_companies[['Production Companies', 'Average Rating']].reset_index(drop=True)
    director_sorted_bad = director_sorted_bad[['Production Companies', 'Average Rating']].reset_index(drop=True)
    director_sorted_runtime = filtered_companies.sort_values(by='Total Runtime', ascending=False).reset_index(drop=True)
    return (director_sorted_runtime,
            director_sorted_final, director_sorted_bad)


def production_search():
    runtime, discard, discard = sorted_companies()
    runtime = runtime.head(10)
    list_of_companies = runtime['Production Companies'].unique().tolist()
    list_of_companies.append('Other: search...')
    list_of_companies.append('Return')

    company_list = [
        inquirer.List('companies',
                      message="Select a company to see the movies produced by them, or select 'Other: search...' "
                              "to search by name (select Return to return to the previous menu)",
                      choices=list_of_companies
                      )
    ]

    # same base/final columns logic
    base_columns = ['Movie Title', 'Production Companies']
    final_columns = base_columns + rating_columns

    def search_production_movies(df, company):
        movie_production = df[df['Production Companies'].str.contains(company, case=False, na=False)]
        movie_production = movie_production[final_columns].drop_duplicates().reset_index(drop=True)
        company_avg = movie_production['Average Rating'].mean()
        count = len(movie_production)
        return movie_production, company_avg, count

    while True:
        company_selected = inquirer.prompt(company_list, theme=BlueComposure())
        company_selected = company_selected['companies']

        if company_selected == 'Return':
            return 'Return'

        if company_selected == 'Other: search...':
            while True:
                company_wanted = input("Search for a production company to see its films (type 'break' to exit): ")
                df, rating, count = search_production_movies(df_production_companies, company_wanted)
                if company_wanted == 'break':
                    print('-' * columns)
                    break
                if count == 0:
                    print('-' * columns)
                    print("Sorry, we have no films by that production company in the database, or you've "
                          "mispelled their name. Try again?")
                    print('-' * columns)
                    continue
                print('-' * columns)
                print(f'There are {count} movies produced by {company_wanted}, '
                      f'with an average rating of {rating:.2f}:')

                # same rounded and formatting for printing, used tabulate
                df = add_ranking_columns(df)
                total_row = df[rating_columns].mean().round(2)
                total_row = total_row.to_dict()
                total_row['Production Companies'] = 'AVERAGE'
                for column in df.columns:
                    if column not in total_row:
                        total_row[column] = ''

                # same remove users logic
                columns_to_remove = []
                for column, value in total_row.items():
                    if pd.isna(value):
                        columns_to_remove.append(column)
                df = df.drop(columns=columns_to_remove)
                df.loc['Total'] = total_row
                selected_company_rounded = df.round(2)
                selected_company_filled = selected_company_rounded.map(safe_format)
                print(tabulate(selected_company_filled, headers='keys', tablefmt='fancy_grid', showindex=False))
                print('-' * columns)

        else:
            selected_company = df_production_companies[df_production_companies['Production Companies'].str.contains(company_selected)]
            selected_company = (selected_company[final_columns].drop_duplicates()).reset_index(drop=True)

            selected_company = add_ranking_columns(selected_company)
            total_row = selected_company[rating_columns].mean().round(2)
            total_row = total_row.to_dict()
            total_row['Production Companies'] = 'AVERAGE'
            for column in selected_company.columns:
                if column not in total_row:
                    total_row[column] = ''

            # same remove users logic
            columns_to_remove = []
            for column, value in total_row.items():
                if pd.isna(value):
                    columns_to_remove.append(column)
            selected_company = selected_company.drop(columns=columns_to_remove)
            selected_company.loc['Total'] = total_row

            # gets average rating and count for selected genre for printing
            company_avg = selected_company['Average Rating'].mean()
            company_count = len(selected_company)
            print('-' * columns)
            print(f'There are {company_count-1} movies produced by {company_selected}, '
                  f'with an average rating of {company_avg:.2f}:')

            # same rounded and formatting for printing, used tabulate
            selected_company_rounded = selected_company.round(2)
            selected_company_filled = selected_company_rounded.map(safe_format)
            print(tabulate(selected_company_filled, headers='keys', tablefmt='fancy_grid', showindex=False))
            print('-' * columns)


# searches for movie by title
def movie_search():

    # given df and movie title, return df of movies that match and count of movies
    def search_movies(df, movie):
        # same base/final column logic as all_movies
        base_columns = ['Movie Title', 'Watched Date', 'Runtime (mins)', 'Director']
        movie_columns = base_columns + rating_columns
        # searches df under 'Movie Title' to see if contains movie (will return partial matches)
        movie = df[df['Movie Title'].str.contains(movie, case=False, na=False)]
        # removes all duplicate entries
        movie = movie[movie_columns].drop_duplicates().reset_index(drop=True)
        # sorts by average rating
        movie = movie.sort_values(by='Average Rating', ascending=False).reset_index(drop=True)
        moviecount = len(movie)
        return movie, moviecount

    # in while loop for allow searching multiple movies until user breaks out
    while True:
        movie_name = input("Enter a movie title to search the database. You can search for parts of titles. ie. "
                           "'Star Wars' will contain all movies with 'Star Wars' in the title (type 'break' to exit): ")
        if movie_name == 'break':
            break
        # searches df_director in order to have accurate director columns in movie results df
        movie_results, movie_count = search_movies(df_director, movie_name)

        movie_results = add_ranking_columns(movie_results)

        # if movie_count is greater than one, add an average row to summarize results
        if movie_count > 1:
            # same total_row logic as before
            total_row = movie_results[rating_columns].mean().round(2)
            total_row = total_row.to_dict()
            total_row['Director'] = 'AVERAGE'
            for column in movie_results.columns:
                if column not in total_row:
                    total_row[column] = ''
            # checks to see if any user has not rating any movies returned
            columns_to_remove = []
            for column, value in total_row.items():
                if pd.isna(value):
                    # checks if any column in total_row is nan (no ratings by that user), appends column to remove list
                    columns_to_remove.append(column)
            # drops columns that don't have average ratings (on remove list)
            movie_results = movie_results.drop(columns=columns_to_remove)
            movie_results.loc['Total'] = total_row

        # if only one movie is returned, don't need average row, but remove all users that didn't rate it
        else:
            columns_to_remove = movie_results.columns[movie_results.isna().any()].tolist()
            movie_results = movie_results.drop(columns=columns_to_remove)
        if movie_count == 0:
            print('-' * columns)
            print("Sorry, either this movie hasn't been rated or you've misspelled it. Try again?")
            print('-' * columns)
            continue
        print('-' * columns)
        # round final table values, and put through safe formatting. print using tabulate for fancy tables
        movie_results_rounded = movie_results.round(2)
        movie_results_filled = movie_results_rounded.map(safe_format)
        print(tabulate(movie_results_filled, headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)


# searches for movies by genre
def genre_movies():
    list_of_genres = sorted_genres()
    # produces list of genres in ranked order, adds 'Return' to end of the list for menu choices
    list_of_genres = (list_of_genres['Genres'].unique().tolist())
    list_of_genres.append('Return')

    # inquirer used with list_of_genres to allow user to pick one of the genres from set list
    genre_list = [
        inquirer.List('genres',
                      message='Select a genre to see the movies in it (select Return to return to the previous menu)',
                      choices=list_of_genres)
    ]

    # same base/final columns logic
    base_columns = ['Movie Title']
    final_columns = base_columns + rating_columns

    # in while loop, unless user selects 'Return'
    while True:
        genre_selected = inquirer.prompt(genre_list, theme=BlueComposure())
        genre_selected = genre_selected['genres']
        if genre_selected == 'Return':
            return 'Return'

        # searches exploded genre df for selected genre
        selected_genre = df_exploded_genre[df_exploded_genre['Genres'].str.contains(genre_selected)]
        selected_genre = (selected_genre[final_columns].drop_duplicates()).reset_index(drop=True)

        selected_genre = add_ranking_columns(selected_genre)
        # same total row logic
        total_row = selected_genre[rating_columns].mean().round(2)
        total_row = total_row.to_dict()
        total_row['Movie Title'] = 'AVERAGE'
        for column in selected_genre.columns:
            if column not in total_row:
                total_row[column] = ''

        # same remove users logic
        columns_to_remove = []
        for column, value in total_row.items():
            if pd.isna(value):
                columns_to_remove.append(column)
        selected_genre = selected_genre.drop(columns=columns_to_remove)
        selected_genre.loc['Total'] = total_row

        # gets average rating and count for selected genre for printing
        genre_avg = selected_genre['Average Rating'].mean()
        genre_count = len(selected_genre)
        print('-' * columns)
        print(f'There are {genre_count-1} {genre_selected} movies, with an average rating of {genre_avg:.2f}:')

        # same rounded and formatting for printing, used tabulate
        selected_genres_rounded = selected_genre.round(2)
        selected_genres_filled = selected_genres_rounded.map(safe_format)
        print(tabulate(selected_genres_filled, headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)


# searches for movies by actor
def actor_movies():
    # same column logic
    base_columns = ['Movie Title']
    final_columns = base_columns + rating_columns
    # uses 2 dfs in order to get actors characters as well
    base_columns_characters = ['Movie Title', 'Actor Name', 'Character']
    final_columns_characters = base_columns_characters+rating_columns

    def search_actor_movies(df, actor):
        # explodes given df by Actors
        df_exploded = df.explode('Actors')
        # filters for lines where Actors matches given actor
        movie_actors_cast = df_exploded[df_exploded['Actors'].apply(
            lambda x: actor.title() in x.title() if isinstance(x, str) else False)]
        # sums up actors runtime column to get total runtime
        actor_runtime = movie_actors_cast[['Runtime (mins)']].reset_index(drop=True)
        actor_runtime_total = actor_runtime['Runtime (mins)'].sum()

        # creates a df of all movies that actor has been in, dropping all duplicates -- leaving unique movie list
        # important because the search allows for any match; i.e. multiple people with the same name in the same movie
        # stops duplicates from getting added to the list later
        movie_actors = movie_actors_cast[final_columns].drop_duplicates().reset_index(drop=True)

        # keeps a list that does not drop duplicates, allowing for character matching later
        movie_actors_expanded = movie_actors_cast[final_columns].reset_index(drop=True)

        # saves a list of movies for reference later
        movie_list = movie_actors['Movie Title'].to_list()
        list_of_characters = []
        list_of_actors = []

        # iterates through movies in movie_list
        for movies in movie_list:
            # extracts the matching row in the original movies_df
            row = movies_df.loc[movies_df['Movie Title'] == movies]
            if not row.empty:
                # extracts both the lists that contains the cast and the characters
                cast_list = row['Actors'].values[0]
                character_list = row['Characters'].values[0]
                # makes a list of actors that match the name of the actor searched
                matching_actors = [actors for actors in cast_list if actor.title() in actors.title()]
                if matching_actors:
                    list_of_actors.extend(matching_actors)

                    # iterates though the matching actors and extracts their index in the cast list
                    for matching_actor in matching_actors:
                        indexes = [i for i, name in enumerate(cast_list) if name == matching_actor]

                        # uses index to find the actor's characters in the list of characters, save it
                        for index in indexes:
                            actor_character = character_list[index]
                            list_of_characters.append(actor_character)

        # adds columns that contain both the actors name and the characters name to the df3
        movie_actors_expanded['Character'] = list_of_characters
        movie_actors_expanded['Actor Name'] = list_of_actors

        # adds the rating column back onto the df
        movie_actors_final = movie_actors_expanded[final_columns_characters].drop_duplicates().reset_index(drop=True)

        # gets average and watched stats for printing
        actor_avg = movie_actors_expanded['Average Rating'].mean()
        actor_runtime_hours = int(actor_runtime_total/60)
        actor_runtime_minutes = actor_runtime_total % 60
        count = len(movie_actors)
        return actor_runtime_hours, actor_runtime_minutes, movie_actors_final, actor_avg, count

    # operating within a while loop
    while True:
        actor_name = input("Enter the actor's name to get a list of movies (type 'break' to exit): ")
        if actor_name == 'break':
            break

        # called the function, using the exploded_cast df
        hours, minutes, actor_movies_df, actor_avg_rating, actor_count = (
            search_actor_movies(df_exploded_cast, actor_name))

        # add ranking to df
        actor_movies_df = add_ranking_columns(actor_movies_df)

        # if more than one movie, add the average row and remove all rating columns that don't have any ratings
        if len(actor_movies_df) > 1:
            total_row = actor_movies_df[rating_columns].mean().round(2)
            total_row = total_row.to_dict()
            total_row['Character'] = 'AVERAGE'
            columns_to_remove = []
            for column in actor_movies_df.columns:
                if column not in total_row:
                    total_row[column] = ''
            for column, value in total_row.items():
                if pd.isna(value):
                    columns_to_remove.append(column)
            actor_movies_df = actor_movies_df.drop(columns=columns_to_remove)
            actor_movies_df.loc['Total'] = total_row
        else:
            columns_to_remove = actor_movies_df.columns[actor_movies_df.isna().any()].tolist()
            actor_movies_df = actor_movies_df.drop(columns=columns_to_remove)

        # if no movies are returned, print message, and let user try a different name
        if actor_count == 0:
            print('-' * columns)
            print("Sorry, we either don't have this actor, or you've misspelled their name. Try again?")
            print('-' * columns)
            continue
        print('-' * columns)
        print(f"{actor_name.title()} has featured in {actor_count} movies on this list (total runtime {hours}h "
              f"{minutes}m), with an average rating of {actor_avg_rating:.2f}.")
        print('-' * columns)
        actor_movies_df_rounded = actor_movies_df.round(2)
        actor_movies_df_filled = actor_movies_df_rounded.map(safe_format)
        print(f"Movies featuring {actor_name.title()}:")
        print(tabulate(actor_movies_df_filled, headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)


# searches for movies by director
def director_movies():
    base_columns = ['Movie Title', 'Director']
    final_columns = base_columns + rating_columns

    def search_director_movies(df, director):
        movie_director = df[df['Director'].str.contains(director, case=False, na=False)]
        director_runtime = movie_director[['Runtime (mins)']].drop_duplicates().reset_index(drop=True)
        director_runtime_total = director_runtime['Runtime (mins)'].sum()
        movie_director = movie_director[final_columns].drop_duplicates().reset_index(drop=True)
        director_avg = movie_director['Average Rating'].mean()
        runtime_hours = int(director_runtime_total / 60)
        runtime_minutes = director_runtime_total % 60
        count = len(movie_director)
        return runtime_hours, runtime_minutes, movie_director, director_avg, count
    while True:
        director_name = input("Enter the director's name to get a list of movies (type 'break' to exit): ")
        if director_name == 'break':
            break
        hours, minutes, director_movies_df, director_avg_rating, director_count = (
            search_director_movies(df_director, director_name))

        director_movies_df = add_ranking_columns(director_movies_df)

        if len(director_movies_df) > 1:
            total_row = director_movies_df[rating_columns].mean().round(2)
            total_row = total_row.to_dict()
            total_row['Director'] = 'AVERAGE'
            columns_to_remove = []
            for column in director_movies_df.columns:
                if column not in total_row:
                    total_row[column] = ''
            for column, value in total_row.items():
                if pd.isna(value):
                    columns_to_remove.append(column)
            director_movies_df = director_movies_df.drop(columns=columns_to_remove)
            director_movies_df.loc['Total'] = total_row
        else:
            columns_to_remove = director_movies_df.columns[director_movies_df.isna().any()].tolist()
            director_movies_df = director_movies_df.drop(columns=columns_to_remove)
        if director_count == 0:
            print('-' * columns)
            print("Sorry, we either don't have this director, or you've misspelled their name. Try again?")
            print('-' * columns)
            continue
        print('-' * columns)
        print(f'{director_name.title()} has directed {director_count} movies on this list (total runtime {hours}h '
              f'{minutes}m), with an average rating of {director_avg_rating:.2f}.')
        print('-' * columns)
        director_movies_rounded = director_movies_df.round(2)
        director_movies_df_filled = director_movies_rounded.map(safe_format)
        print(f"Movies directed by {director_name.title()}:")
        print(tabulate(director_movies_df_filled, headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)


def search_raters_movies(rater):
    avg_rating = movies_df[f'{rater} Rating'].mean()
    raters_movies = movies_df[['Movie Title', f'{rater} Rating', 'Average Rating',
                               'Runtime (mins)']].reset_index(drop=True)
    raters_movies_cleaned = raters_movies.dropna()
    total_runtime = raters_movies_cleaned['Runtime (mins)'].sum()
    differential = raters_movies_cleaned.assign(
        RatingDifferential=lambda df: abs(df[f'{rater} Rating'] - df['Average Rating']))
    raters_movies_final = raters_movies_cleaned[['Movie Title', f'{rater} Rating']].reset_index(drop=True)
    sorted_differential = differential.sort_values(by='RatingDifferential',
                                                   ascending=False).reset_index(drop=True)
    headers_new = {'RatingDifferential': 'Rating Differential'}
    sorted_differential = sorted_differential.rename(columns=headers_new)
    genres = movies_df[['Movie Title', 'Genres', f'{rater} Rating']].reset_index(drop=True)
    raters_genres = genres.explode('Genres')
    actors = movies_df[['Movie Title', 'Actors', f'{rater} Rating']].reset_index(drop=True)
    raters_actors = actors.explode('Actors')
    directors = movies_df[['Movie Title', 'Director', f'{rater} Rating']].reset_index(drop=True)
    raters_directors = directors.explode('Director')
    raters_directors_cleaned = raters_directors.dropna()
    raters_genres_cleaned = raters_genres.dropna()
    raters_actors_cleaned = raters_actors.dropna()
    avg_rating_by_genre = raters_genres_cleaned.groupby('Genres').agg(
        Rating=(f'{rater} Rating', 'mean'),
        Count=('Movie Title', 'count')).reset_index()
    avg_rating_by_actor = raters_actors_cleaned.groupby('Actors').agg(
        Rating=(f'{rater} Rating', 'mean'),
        Count=('Movie Title', 'count')).reset_index()
    avg_rating_by_director = raters_directors_cleaned.groupby('Director').agg(
        Rating=(f'{rater} Rating', 'mean'),
        Count=('Movie Title', 'count')).reset_index()
    filtered_directors = avg_rating_by_director[avg_rating_by_director['Count'] > 1]
    directors_sorted = filtered_directors.sort_values(by='Rating', ascending=False).reset_index(drop=True)
    filtered_actors = avg_rating_by_actor[avg_rating_by_actor['Count'] > 2]
    top_actors = filtered_actors.sort_values(by='Rating', ascending=False).reset_index(drop=True)
    bad_actors = filtered_actors.sort_values(by='Rating', ascending=True).reset_index(drop=True)
    genre_sorted = avg_rating_by_genre.sort_values(by='Rating', ascending=False).reset_index(drop=True)
    top_movies = raters_movies_final.sort_values(by=f'{rater} Rating', ascending=False).reset_index(drop=True)
    top_movies['Ranking'] = range(1, len(top_movies) + 1)
    final_columns = ['Ranking'] + [col for col in top_movies.columns if col != 'Ranking']
    top_movies = top_movies[final_columns]

    rating_values = {}
    raters_ratings = top_movies[f'{rater} Rating'].tolist()
    for rating in raters_ratings:
        if rating not in rating_values:
            rating_values[rating] = 1
        else:
            rating_values[rating] += 1

    raters_count = raters_movies_final[f'{rater} Rating'].count()

    def movie_ranking(df):
        for i in range(1, len(df)):
            if df.loc[i, f'{rater} Rating'] == df.loc[i - 1, f'{rater} Rating']:
                df.loc[i, 'Ranking'] = df.loc[i - 1, 'Ranking']
        return df
    top_movies = movie_ranking(top_movies)
    return (top_movies, genre_sorted, avg_rating, raters_count, top_actors, bad_actors, directors_sorted,
            sorted_differential, rating_values, total_runtime)


def watched_stats():
    movies_df['Watched Date'] = movies_df['Watched Date'].str.strip()
    year_and_months_dict = {}
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December']
    years = []
    totals = []
    averages = []
    for year in range(2000, 2100):
        year_watched = movies_df[movies_df['Watched Date'].str.contains(str(year), case=False, na=False)]
        year_count = year_watched['Watched Date'].count()
        year_average = year_watched['Average Rating'].mean()
        if year_count > 0:
            years.append(year)
            totals.append(year_count)
            averages.append(year_average)
            months_and_movies_dict = {}
            for month in range(1, 13):
                month_watched = year_watched[year_watched['Watched Date'].str.startswith(f'{month}/')]
                month_count = month_watched['Watched Date'].count()
                months_and_movies_dict[month_names[month-1]] = int(month_count)
            months_and_movies_dict['Total'] = int(year_count)
            months_and_movies_dict['Average Rating'] = year_average.round(2)
            year_and_months_dict[str(year)] = months_and_movies_dict
    month_year_df = pd.DataFrame.from_dict(year_and_months_dict, orient='index')
    total_row = month_year_df[month_names].sum().round(2).to_dict()
    total_row['Total'] = month_year_df['Total'].sum()
    total_row['Average Rating'] = ' '
    month_year_df.loc['Total'] = total_row
    return month_year_df, years, totals, averages


def movies_by_year(year):
    movies_df_time = movies_df.copy()
    movies_df_time['Watched Date'] = pd.to_datetime(movies_df_time['Watched Date'], format='%m/%d/%Y', errors='coerce')
    year_watched = movies_df_time[movies_df_time['Watched Date'].dt.year == year]
    wanted_columns = ['Movie Title', 'Watched Date', 'Runtime (mins)']
    wanted_columns = wanted_columns + rating_columns
    year_watched_clean = year_watched[wanted_columns].sort_values(by='Watched Date')
    year_watched_clean['Watched Date'] = year_watched_clean['Watched Date'].dt.strftime('%-m/%-d/%Y')
    year_watched_clean = year_watched_clean.map(safe_format).reset_index(drop=True)

    rows_with_months = []
    current_month = None

    for _, row in year_watched_clean.iterrows():
        row_month = pd.to_datetime(row['Watched Date']).strftime('%B')

        if row_month != current_month and current_month is not None:
            rows_with_months.append(pd.Series({col: '' for col in year_watched_clean.columns}))

        if row_month != current_month:
            rows_with_months.append(
                pd.Series({'Movie Title': f"{row_month.upper()}", 'Watched Date': '', 'Runtime (mins)': ''}))
            current_month = row_month
        rows_with_months.append(row)

    year_watched_clean_with_months = pd.DataFrame(rows_with_months, columns=year_watched_clean.columns)

    year_watched_clean_with_months = year_watched_clean_with_months.merge(all_movie_df[['Movie Title', 'Ranking']],
                                                                          on='Movie Title', how='left')

    final_columns = ['Ranking'] + [col for col in year_watched_clean_with_months.columns if col != 'Ranking']
    year_watched_clean_with_months = year_watched_clean_with_months[final_columns]

    year_watched_clean_with_months = year_watched_clean_with_months.fillna(' ')
    return tabulate(year_watched_clean_with_months, headers='keys', tablefmt='fancy_grid', showindex=False)


def movies_by_release():
    movies_df['Release Date'] = movies_df['Release Date'].str.strip()
    decades = []
    totals = []
    averages = []

    for decade in range(194, 210):
        decade_watched = movies_df[movies_df['Release Date'].str.contains(str(decade), case=False, na=False)]
        decade_count = decade_watched['Release Date'].count()
        decade_average = decade_watched['Average Rating'].mean()
        if decade_count > 0:
            decades.append(str(decade*10)+'s')
            totals.append(decade_count)
            averages.append(decade_average)

    for decade, total, average in zip(decades, totals, averages):
        print(f'{decade}: {'#' * total} {total} —— ({round(average, 2)})')

    decades.append('Return')
    print('-' * columns)
    decade_selection = [inquirer.List('decades_list',
                                      message='Select a decade to see the movies made in it',
                                      choices=decades)]
    while True:
        decade_answers = inquirer.prompt(decade_selection, theme=BlueComposure())
        decade = decade_answers['decades_list']
        wanted_columns = ['Movie Title', 'Release Date', 'Runtime (mins)']
        wanted_columns = wanted_columns + rating_columns
        if decade == 'Return':
            break
        decade_search = decade.replace('0s', '')
        decade_watched = movies_df[movies_df['Release Date'].str.contains(str(decade_search), case=False, na=False)]
        decade_watched = decade_watched[wanted_columns]
        decade_count = decade_watched['Release Date'].count()
        if decade_count > 0:
            decade_watched = decade_watched.map(safe_format)
            decade_watched['Release Date'] = pd.to_datetime(decade_watched['Release Date'], format='%Y-%m-%d',
                                                            errors='coerce')
            decade_watched = decade_watched.sort_values(by='Release Date')
            rows_with_months = []
            current_year = None
            for _, row in decade_watched.iterrows():
                row_year = pd.to_datetime(row['Release Date']).strftime('%Y')
                if row_year != current_year and current_year is not None:
                    rows_with_months.append(pd.Series({col: '' for col in decade_watched.columns}))
                if row_year != current_year:
                    rows_with_months.append(
                        pd.Series({'Movie Title': f"{row_year}", 'Release Date': '', 'Runtime (mins)': ''}))
                    current_year = row_year
                rows_with_months.append(row)

            decade_watched_with_years = pd.DataFrame(rows_with_months, columns=decade_watched.columns)
            decade_watched_with_years['Release Date'] = decade_watched_with_years['Release Date'].apply(
                lambda x: x.strftime('%-m/%-d/%Y') if pd.notna(x) and isinstance(x, pd.Timestamp) else x)

            decade_watched_with_years = decade_watched_with_years.merge(
                all_movie_df[['Movie Title', 'Ranking']],
                on='Movie Title', how='left')

            final_columns = ['Ranking'] + [col for col in decade_watched_with_years.columns if col != 'Ranking']
            decade_watched_with_years = decade_watched_with_years[final_columns]
            decade_watched_with_years = decade_watched_with_years.fillna(' ')
            print(tabulate(decade_watched_with_years.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
