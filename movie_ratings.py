#!/usr/bin/env python3
import pandas as pd
from tabulate import tabulate
from stats import (actor_movies, director_movies, sorted_actors, sorted_genres, sorted_directors, movie_search,
                   genre_movies, all_movies, search_raters_movies, watched_stats, movies_by_year, movies_by_release,
                   sorted_companies, production_search)
import inquirer
import shutil
from inquirer.themes import BlueComposure
from add_edit_ratings_new_users import add_movie_ratings
import json
import numpy as np

filename = 'raters.json'
with open(filename, 'r') as f:
    users = json.load(f)

users.append('Return')
raters_list = users

on_opening = [
    inquirer.List('choice_one',
                  message='Please select an option',
                  choices=['Add/Edit Movie Rating', 'List of All Movies', 'Search by Movie Title', 'Search by Actor',
                           'Search by Director', 'Search by Genre', 'Search by Rater', 'Movies by Watched Date',
                           'Movies by Release Date', 'Movies by Production Company', 'Exit Program'])]

questions = [
  inquirer.List('user_choice',
                message='Select the option to get more information',
                choices=['Actors', 'Directors', 'Genres', 'Raters'])]

raters = [
    inquirer.List('raters', message='Pick a rater to get their stats',
                  choices=raters_list)]

rater_info = [
    inquirer.List('rater_info', message='Select a category to get more information',
                  choices=['All Movie Ratings', 'Genres', 'Actors', 'Directors', 'Ratings', 'Return'])]

morestats = [
    inquirer.List('morestats',
                  message='MORE OPTIONS',
                  choices=['Countries', 'Languages', 'Production Companies',
                           'Add/Edit Raters', 'Return'])]


columns = shutil.get_terminal_size().columns

while True:
    choice_one_answers = inquirer.prompt(on_opening, theme=BlueComposure())
    choice_one = choice_one_answers['choice_one']
    if choice_one == 'Add/Edit Movie Rating':
        add_movie_ratings()
    if choice_one == 'Search by Movie Title':
        movie_search()
    if choice_one == 'List of All Movies':
        (all_movie_count, total_runtime_days, total_runtime_hours, total_runtime_minutes, all_movie_avg,
         all_movies_specific_columns_display, discard) = all_movies()
        print(f'There have been {all_movie_count} movies rated so far (total runtime: {total_runtime_days}d'
              f' {total_runtime_hours}h {total_runtime_minutes}m), with an average rating of {round(all_movie_avg, 2)}.'
              f' All movies sorted by average rating, then count of ratings:')
        print('-' * columns)
        print(tabulate(all_movies_specific_columns_display, headers='keys', tablefmt='fancy_grid', showindex=False))
        goback = input('Press enter to return to menu\n')
        if goback == '':
            continue
    if choice_one == 'Search by Actor':
        print('-' * columns)
        print("The 15 most watched actors on this list by runtime are:")
        runtime, rating = sorted_actors()
        print(tabulate(runtime.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)
        print('The 15 highest rated actors on this list are (minimum 4 movies)')
        print(tabulate(rating.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)
        actor_movies()
    if choice_one == 'Search by Director':
        print('-' * columns)
        print("The 15 most watched directors on this list by runtime are:")
        runtime, rating = sorted_directors()
        print(tabulate(runtime.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)
        print('The 15 highest rated directors on this list are (minimum 2 movies)')
        print(tabulate(rating.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)
        director_movies()
    if choice_one == 'Search by Genre':
        print("Genres sorted by average rating:")
        table = sorted_genres()
        print(tabulate(table.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)
        genre_movies()
        print('-' * columns)
    if choice_one == 'Search by Rater':
        while True:
            rater_answer = inquirer.prompt(raters, theme=BlueComposure())
            rater_answer = rater_answer['raters']
            if rater_answer == 'Return':
                break
            topm, genres, average_rating, count, topa, bada, fav_dir, dif, dict, time = (
                search_raters_movies(rater_answer))
            i = int(time/60)
            d = int(i/24)
            w = int(d/7)
            d = d%7
            h = i%24
            m = time%60
            print('-' * columns)
            if w > 0:
                print(f"{rater_answer} has rated {count} movies (total watch time: {w}w {d}d {h}h {m}m), "
                      f"with an average rating of {round(average_rating, 2)}.")
            else:
                print(f"{rater_answer} has rated {count} movies (total watch time: {d}d {h}h {m}m), "
                      f"with an average rating of {round(average_rating, 2)}.")
            print('-' * columns)
            print(f"Distribution of ratings:")
            print('-' * columns)
            for rating in np.arange(10, 0, -0.5):
                if rating in dict:
                    if rating != 10.0:
                        print(f'{rating}:  {'#'*dict[rating]} —— {dict[rating]} ({round((dict[rating]/count*100),2)}%)')
                    else:
                        print(f'{rating}: {'#'*dict[rating]} —— {dict[rating]} ({round((dict[rating]/count*100),2)}%)')
                elif rating == 10:
                    print(f'{rating}: 0')
                else:
                    print(f'{rating}:  0')
            while True:
                print('-' * columns)
                raters_info_answers = inquirer.prompt(rater_info, theme=BlueComposure())
                raters_info_answers = raters_info_answers['rater_info']
                if raters_info_answers == 'Return':
                    break
                if raters_info_answers == 'All Movie Ratings':
                    print(f"All of {rater_answer}'s movie ratings:")
                    print(tabulate(topm.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
                if raters_info_answers == 'Genres':
                    print('-' * columns)
                    print(f"{rater_answer}'s favorite genres:")
                    print('-' * columns)
                    genres_filled = genres.fillna('-')
                    print(tabulate(genres_filled.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
                if raters_info_answers == 'Actors':
                    print('-' * columns)
                    print(f"{rater_answer}'s favorite (and least favorite) 10 actors "
                          f"(that they've seen more than twice):")
                    print('-' * columns)
                    topa_df = topa.head(10)
                    bada_df = bada.head(10)
                    bada_df.insert(0, ' ', ' ')
                    combined_df = pd.concat([topa_df, bada_df], axis=1)
                    print(tabulate(combined_df.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
                if raters_info_answers == 'Directors':
                    print('-' * columns)
                    print(f"{rater_answer}'s favorite directors (that they've seen more than once):")
                    print('-' * columns)
                    print(tabulate(fav_dir.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
                    print('-' * columns)
                if raters_info_answers == 'Ratings':
                    print(f"{rater_answer}'s disagreed with the average the most with these movies:")
                    print('-' * columns)
                    print(tabulate(dif.head(10).round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
                    print('-' * columns)
    if choice_one == 'Movies by Watched Date':
        print('-' * columns)
        print('The breakdown of movies watched by year is as follows:')
        print('-' * columns)
        watched_stats_df, years, totals, averages = watched_stats()
        print(tabulate(watched_stats_df.round(2), headers='keys', tablefmt='fancy_grid'))
        for year, total, average in zip(years, totals, averages):
            print(f"{year}: {'#' * total} {total} —— ({round(average, 2)})")
        years.append('Return')
        print('-' * columns)
        year_selection = [inquirer.List('years_list',
                                        message='Select a year to see the movies watched',
                                        choices=years)]
        while True:
            year_answers = inquirer.prompt(year_selection, theme=BlueComposure())
            year = year_answers['years_list']
            if year == 'Return':
                break
            year_df = movies_by_year(year)
            print(year_df)
    if choice_one == 'Movies by Release Date':
        print('-' * columns)
        print('Breakdown of movies released by decade (with average rating):')
        print('-' * columns)
        movies_by_release()
    if choice_one == 'Movies by Production Company':
        runtime, rating, bottom_rating = sorted_companies()
        rating = rating.head(15)
        bottom_rating = bottom_rating.head(15)
        bottom_rating.insert(0, ' ', ' ')
        combined_df = pd.concat([rating, bottom_rating], axis=1)
        print('-' * columns)
        print('Top 10 production companies by runtime:')
        print('-' * columns)
        print(tabulate(runtime.head(10).round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)
        print('Top and bottom 15 production companies by average rating (minimum 3 movies):')
        print('-' * columns)
        print(tabulate(combined_df.round(2), headers='keys', tablefmt='fancy_grid', showindex=False))
        print('-' * columns)
        production_search()
    if choice_one == 'More Options':
        while True:
            print('-' * columns)
            morestats_answer = inquirer.prompt(morestats, theme=BlueComposure())
            morestats_answer = morestats_answer['morestats']
            if morestats_answer == 'Return':
                print('-' * columns)
                break
            if morestats_answer == 'Add/Edit Raters':
                print("Sorry, our lazy dev hasn't added this yet :(")
                goback = input('Press enter to return to menu\n')
                if goback == '':
                    continue
            if morestats_answer == 'Countries':
                print("Sorry, our lazy dev hasn't added this yet :(")
                goback = input('Press enter to return to menu\n')
                if goback == '':
                    continue
            if morestats_answer == 'Languages':
                print("Sorry, our lazy dev hasn't added this yet :(")
                goback = input('Press enter to return to menu\n')
                if goback == '':
                    continue
            if morestats_answer == 'Production Companies':
                print("Sorry, our lazy dev hasn't added this yet :(")
                goback = input('Press enter to return to menu\n')
                if goback == '':
                    continue
    if choice_one == 'Exit Program':
        break
