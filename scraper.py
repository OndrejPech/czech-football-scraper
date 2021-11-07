import os
import json
import argparse
from bs4 import BeautifulSoup
import utils

MAIN_LINK = "https://fotbalunas.cz"
path = "/soutez/"

parser = argparse.ArgumentParser(description="""This program creates folder with \
JSON files with all past games of the league. If  you insert league number \
based on league id on 'https://fotbalunas.cz' \
the program will download all info about the league and played games.\
If you don't parse the league number you have to provide valid http link \
inside the program.""")
parser.add_argument("-l", "--league")
args = parser.parse_args()

if args.league:
    league_id = args.league
else:
    league_id = utils.user_input_num_league()

# BASIC CONNECTION
league_link = MAIN_LINK + path + league_id
r = utils.check_response(league_link)
soup = BeautifulSoup(r.content, 'html.parser')
tag_league_navigation = soup.header.find('div',
                                         {'class': 'secondary-menu secondary-menu-soutez'})
if not tag_league_navigation:
    print(f"League with id {league_id} probably doesn't exists. ", end='')
    print("Please make sure you insert a valid league id.")
    quit()

# SCRAPE BASIC DATA OF THE LEAGUE AND CREATE DICTIONARY
tag_league_info = tag_league_navigation.find('a', string="Tabulka")
link_league_info = MAIN_LINK + tag_league_info['href']
basic_info = utils.scrap_basic_info_league(link_league_info)

# SCRAPE ALL THE GAMES IN THE LEAGUE
tag_all_games = tag_league_navigation.find('a', string="Rozlosování")
link_games = MAIN_LINK + tag_all_games['href']
games = utils.scrap_games_in_league(link_games)

# dump to json
if not os.path.exists(league_id):
    os.makedirs(league_id)

with open(league_id + '/basic.json', 'w') as file:
    json.dump(basic_info, file, indent=4)

with open(league_id + '/games.json', 'w') as file:
    json.dump(games, file, indent=4)
