#!/usr/bin/env python3
import inquirer
from add_edit_ratings import add_movie_ratings
questions = [
  inquirer.List('user_choice',
                message='Select the option to get more information',
                choices=['Actors', 'Directors', 'Genres', 'Raters'],
            )
]

raters = [
    inquirer.List('raters',
                    message='Pick a rater to get their stats',
                    choices=['James', 'Martin', 'Monica', 'Matt'],
                )
]

add_movie_ratings()
answers = inquirer.prompt(questions)

if answers['user_choice'] == 'Raters':
    raters = inquirer.prompt(raters)