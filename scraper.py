import os
import json
import argparse
from bs4 import BeautifulSoup
import utils


def get_league_id(args) -> str:
    """"
    Check if league_id is parsed in program arguments by user.
    If not ask user for league_id and return it
    """
    if args.league:
        id_league = args.league
    else:
        id_league = utils.user_input_num_league()
    return id_league


def basic_connection(id_league):
    """
    Check if league_id is valid. If not program quits.
    Return bs4.element.Tag
    """
    league_link = MAIN_LINK + PATH + id_league
    r = utils.check_response(league_link)
    soup = BeautifulSoup(r.content, 'html.parser')
    league_tag = soup.header.find('div', {
        'class': 'secondary-menu secondary-menu-soutez'})
    if not league_tag:
        print(f"League with id {id_league} probably doesn't exists. ", end='')
        print("Please make sure you insert a valid league id.")
        quit()

    return league_tag


def scrape_base_info(tag) -> dict:
    """Scrape basic info from bs4.element.Tag"""
    tag_league_info = tag.find('a', string="Tabulka")
    link_league_info = MAIN_LINK + tag_league_info['href']
    return utils.scrap_basic_info_league(link_league_info)


def scrape_all_games(tag) -> dict:
    """Scrape all the games in the league from bs4.element.Tag"""
    tag_all_games = tag.find('a', string="Rozlosování")
    link_games = MAIN_LINK + tag_all_games['href']
    return utils.scrap_games_in_league(link_games)


def create_jsons(id_league: str, base_info: dict, all_games: dict) -> None:
    """make/ overwrite two JSON files in folder named by league_id"""
    if not os.path.exists(id_league):
        os.makedirs(id_league)

    with open(id_league + '/basic.json', 'w') as file:
        json.dump(base_info, file, indent=4, ensure_ascii=False)

    with open(id_league + '/games.json', 'w') as file:
        json.dump(all_games, file, indent=4, ensure_ascii=False)


MAIN_LINK = "https://fotbalunas.cz"
PATH = "/soutez/"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""
    This program creates folder \
    with JSON files with all past games of the league. If you insert league \
    number based on league id on 'https://fotbalunas.cz' , the program will\
    download all info about the league and played games.\
    If you don't parse the league number you have to provide valid http link \
    inside the program.""")
    parser.add_argument("-l", "--league")
    arguments = parser.parse_args()

    league_id = get_league_id(arguments)
    league_info_tag = basic_connection(league_id)
    basic_info = scrape_base_info(league_info_tag)
    games = scrape_all_games(league_info_tag)

    create_jsons(league_id, basic_info, games)
