import time
import re
import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def user_input_num_league() -> str:
    """ask for user input and return it ts a number"""
    while True:
        print('Please enter valid ID of the league you want to crawl.')
        print('You can find the number  on the end of the URL path ')
        print("For example: 'https://fotbalunas.cz/soutez/438/'")
        print("Use '438' if you want first league")
        id_league = input('league id: ')
        try:
            int(id_league)
        except ValueError:
            print("That's not a number!\n")
        else:
            return id_league


def check_response(link: str):
    """return requests.Response() object, close program if RequestException appeared"""
    try:
        r = requests.get(link)
    except requests.exceptions.RequestException as e:
        print(
            'Problem occurred during http request, please find more info bellow')
        print(str(e))
        quit()
    else:
        return r


def get_level_of_league(league_name: str) -> tuple:
    """
    depends on league name from website this function returns three items tuple
    with level, district and region items. In this order.
    District and region can be None
    """
    words = league_name.split('|')
    level = district = region = None
    if len(words) == 3:
        level = words[2].strip()
        district = words[1].strip()
        region = words[0].strip()
    elif len(words) == 2:
        level = words[1].strip()
        region = words[0].strip()
    elif len(words) == 1:
        level = words[0].strip()

    return level, district, region


def scrap_basic_info_league(link: str) -> dict:
    """scrapes basic data of the league and return a dictionary with league info"""
    r = check_response(link)
    soup = BeautifulSoup(r.content, 'html.parser')
    page_content = soup.find('div',
                             {'id': 'content', 'class': 'inner-container'})

    league_id = int(link.split('/')[-2])
    league_name_string = page_content.h1.text
    level, district, region = get_level_of_league(league_name_string)
    season = page_content.h2.text.replace('-', '/')  # YYYY/YYYY format

    print('Scrapping: ', league_name_string)
    time.sleep(3)

    teams = []  # list of dicts
    tags_all_teams = page_content.table.find_all('a')
    for tag in tags_all_teams:
        team = tag.text
        team_id = tag["href"].split('/')[-2]
        if team not in teams:
            teams.append({"team_id": team_id, "team_name": team})

    basic_info = {
        "competition_id": league_id,
        "competition_name": level,
        "district": district,
        "region": region,
        "season_name": season,
        "teams": teams,
        "updated": datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    return basic_info


def clean_team_name(team_name: str) -> str:
    """remove unnecessary whitespaces from team name."""
    name = team_name.strip()
    if not name[-2].isalpha():
        last_letter = name[-1].strip()
        new_string = name[:-1].strip()
        return new_string + ' ' + last_letter
    return name


def scrap_games_in_league(link: str) -> dict:
    """
    go through all the games in league.
    Get all the basic info and open new link for each game to get more info.
    Scrapes goal, cards, lineups etc.
    return dictionary with these keys
    {
      "match_id",
      "competition_id",
      "round",
      "datetime",
      "home_team",
      "away_team",
      "home_team_id",
      "away_team_id",
      "score",
      "half_time_score",
      "home_score",
      "away_score",
      "result_type",
      "home_lineup",
      "away_lineup",
      "cards",
      "goals",
    }
    """
    games = dict()
    league_id = int(link.split('/')[-2])

    r = check_response(link)
    soup = BeautifulSoup(r.content, 'html.parser')
    parsed = urlparse(link)
    # not hardcoded "https://fotbalunas.cz"
    base_url = f'{parsed.scheme}://{parsed.netloc}'

    page_content = soup.find('div',
                             {'id': 'content', 'class': 'inner-container'})
    rounds = page_content.find_all('div', {'class': 'panel panel-default'})
    game_num = 0  # to give 3 second break after each 30 games
    for round in rounds:
        round_info = round.h3.text
        round_num = int(round_info.split(',')[0].strip().split('.')[0])
        # year variable is important, because date of each match is only DD/MM
        #            main info split | date and time split | date split | year
        year = int(round_info.split(',')[1].strip().split()[0].split('.')[-1])

        for match in round.find_all('li'):
            tag = match.find('td', {'class': 'zapas-item-utkani text-left'})
            teams = tag.a.string.split('-')
            home_team = clean_team_name(teams[0])
            away_team = clean_team_name(teams[1])

            relative_link = tag.a['href']
            match_id = int(relative_link.split('/')[-2])
            link = base_url + relative_link

            result_tag = match.find('td', {'class': 'zapas-item-vysledek'})
            score_date_tags = result_tag.find_all('a')
            score_tag = score_date_tags[0]
            date_tag = score_date_tags[1]

            # get full_time_score and half_time_score and type as nice strings
            ugly_score = score_tag.text.strip()
            if 'kont' in ugly_score:  # game ended with forfeit
                full_time_score = ugly_score.split('kont.')[0].strip()
                half_time_score = '-:-'
                result_type = 'forfeit'
            else:
                full_time_score = ugly_score.split('(')[0].strip()
                half_time_score = ugly_score.split('(')[1].strip().strip(')')
                if 'p.' in full_time_score:  # game decided by penalties
                    result_type = 'penalties'
                    full_time_score = full_time_score.replace('p.', '').strip()
                else:
                    result_type = 'regular'
            home_score = full_time_score.split(':')[0].replace('p.', '').strip()
            away_score = full_time_score.split(':')[1].replace('p.', '').strip()

            # get datetime of match as datetime object
            m_datetime = date_tag.text.strip().split()
            m_month = int(m_datetime[0].split('.')[1])
            m_day = int(m_datetime[0].split('.')[0])
            m_hour = int(m_datetime[1].split(':')[0])
            m_minute = int(m_datetime[1].split(':')[1])
            match_datetime = datetime.datetime(year, m_month, m_day, m_hour,
                                               m_minute).isoformat()

            if full_time_score.split(':')[0] == '-':
                print(f"Match {match_id} between {home_team} and {away_team} "
                      f"takes place {match_datetime}", end=' ')
                print('FUTURE GAME, NOT SAVED')
                continue

            game_num += 1
            if game_num % 30 == 0:
                print('next 30 games:')
                time.sleep(3)

            # ___open http link of this game to get more detailed info ___
            r = check_response(link)
            soup = BeautifulSoup(r.content, 'html.parser')

            # get team names ind team ids
            tag_teams = soup.find_all('h2')[:2]
            tag_home_team = tag_teams[0].a
            tag_away_team = tag_teams[1].a
            home_team = tag_home_team.text
            away_team = tag_away_team.text
            home_id = tag_home_team["href"].split('/')[-2]
            away_id = tag_away_team["href"].split('/')[-2]

            if result_type == 'forfeit':  # no more info needed
                home = away = cards = goals = []
                print('Game bellow forfeited. No extra info needed.')
            else:  # get lineups,goals and cards
                tag_line_ups = soup.find('h4', text="Sestavy").find_parent()
                sections = tag_line_ups.find_all('div')

                # usually sections[0] is home_team lineup,
                # sections[1] is away_team lineup
                # sections[2] is about_cards
                # but sometimes some sections are missing, so following loop
                # connect sections with correct variable
                div_home = div_away = div_cards = None
                for section in sections:
                    tag_strong = section.strong
                    if not tag_strong:  # this part is missing
                        continue
                    if home_team in tag_strong:  # section belongs to home_team
                        div_home = section
                    elif away_team in tag_strong:  # section belongs to away_team
                        div_away = section
                    elif 'ŽK:' in tag_strong or 'ČK:' in tag_strong:  # to cards
                        div_cards = section

                try:
                    home = get_players(home_team, div_home)
                except IndexError:
                    print(f'Unknown error by scraping {home_team} line up.')
                    home = []
                try:
                    away = get_players(away_team, div_away)
                except IndexError:
                    print(f'Unknown error by scraping {away_team} line up.')
                    away = []

                cards = cards_received(div_cards)

                tag_goals = soup.find('h4', text="Branky").find_parent()
                goals = get_goal_scorer(tag_goals)

            match_info = {
                "match_id": match_id,
                "competition_id": league_id,
                "round": round_num,
                "datetime": match_datetime,
                "home_team": home_team,
                "away_team": away_team,
                "home_team_id": home_id,
                "away_team_id": away_id,
                "score": full_time_score,
                "half_time_score": half_time_score,
                "result_type": result_type,
                "home_score": int(home_score),
                "away_score": int(away_score),
                "home_lineup": home,
                "away_lineup": away,
                "cards": cards,
                "goals": goals
            }

            games[match_id] = match_info

            print(match_datetime,
                  f"{home_team} vs {away_team} ended",
                  f"{full_time_score}({half_time_score}). Match id:{match_id}",
                  end='')
            print('.Scrapping OK')

    print(f'Total of {game_num} games scrapped')
    return games


def nice_text(text: str) -> str:
    """remove all tabs and newlines and '[-]' from text and strip it"""
    text = re.sub(r"\s+", " ", text)
    text = text.replace('[-]', '').strip()
    return text


def get_players_ids(tag) -> list:
    """extract all players ids from tag"""
    links = tag.find_all('a')
    ids = [link['href'].split('/')[-2] for link in links]
    return ids


def match_card_info(ids: list, items: list, card_color: str) -> list:
    """
    match list with ids and list with card info,
    and create list of dictionaries with complete card info
    keys(player_id, name, minutes, card)
     """
    cards = []  # list of dict
    for player_id, text in zip(ids, items):  # match each player id with card info

        minute = re.search(r'(\d+)\.', text)
        if not minute:  # on some games this info is missing
            minute = '1'
            name = text.strip()
        else:
            minute = minute.group(0).strip('.')
            name = re.findall(r'\d+\.(.*)', text)[0].strip()
        info = {'player_id': player_id,
                'name': name,
                'minute': minute,
                'card': card_color
                }
        cards.append(info)
    return cards


def cards_received(tag) -> list:
    """
    Separate text into yellow cards and red cards. Get all players ids.
    Use match_card_info() to match cards with ids
    Return list of dicts with info about all cards received in this game.
    If no tag, return empty list.
    """
    if not tag:
        return []

    text = nice_text(tag.text)
    text = re.sub(r" \.", "", text)  # remove dot on the end

    yellow_cards_index = text.find('ŽK:')
    red_cards_index = text.find('ČK:')

    if red_cards_index == -1:  # no red cards in this game,only yellow
        text = text[yellow_cards_index + 3:]
        items_y = re.split('[-,]', text)
        items_r = []
    else:
        if yellow_cards_index != -1:  # yellow and red cards
            text_yellow = text[yellow_cards_index + 3:red_cards_index]
            text_red = text[red_cards_index + 3:]
            items_y = re.split('[-,]', text_yellow)
            items_r = re.split('[,-]', text_red)
        else:  # only red cards in this game
            text = text[red_cards_index + 3:]
            items_y = []
            items_r = re.split('[,-]', text)

    ids = get_players_ids(tag)  # list of ids
    ids_y = ids[:len(items_y)]  # ids which belongs to items_y
    ids_r = ids[len(items_y):]  # ids which belongs to item_r

    yellows = match_card_info(ids_y, items_y, "yellow")
    reds = match_card_info(ids_r, items_r, "red")
    cards = yellows + reds
    return cards


def get_goal_scorer(tag) -> list:
    """
    return list of all goal scorers as list of dicts
    keys(player_id, name, minute, goal_type)
    if no goals, return empty list
    """
    if not tag.div:  # no goals
        return []

    ids = get_players_ids(tag)
    text = nice_text(tag.text).replace("Branky", '')
    items = re.split("[-,]", text)

    goals = []  # list of dicts
    for player_id, text in zip(ids, items):  # match each goal with player id
        # minute = re.findall('(\d+)\.',text)[0]
        minute = re.search(r'(\d+)\.', text)
        if not minute:  # on some games this info is missing
            minute = '1'
            name = text.strip()
        else:
            minute = minute.group(0).strip('.')
            name = re.findall(r'\d+\.(.*)', text)[0].strip()

        goal_type = 'regular'
        if '(' in name:  # behind name is (p.) or (vl.)
            name, goal_info = name.split('(')
            name = name.strip()
            if goal_info[0] == 'p':
                goal_type = 'penalty'
            elif goal_info[0] == 'v':
                goal_type = 'own'
            else:
                goal_type = 'unknown'

        info = {'player_id': player_id,
                'name': name,
                'minute': minute,
                'goal_type': goal_type}

        goals.append(info)

    return goals


def get_players(team: str, tag) -> list:
    """
    Takes team_name and tag of names with lineups.
    If no tag given, return empty list.
    Clean up text of tag, so we got 11 items.
    If item has two players (base + subs),separate them.
    Make new dictionary of each player with keys(id,name,role,minutes)
    return list of dictionaries
    """
    if not tag:
        print(f'Missing line up for {team} in the game bellow.')
        return []

    text = nice_text(tag.text)
    # separate text into 11 items
    items = text.split(',')
    items[0] = items[0].replace(team, "").strip()  # remove team name
    top11 = []
    # sometimes happened that players are not separated with ',' but with '-'
    # this loop flatten the items list and players will remain in same order
    for item in items:
        persons = item.split('- ')
        for person in persons:
            person = person.strip()
            if person:
                top11.append(person)

    if len(top11) < 7:
        print(f'Less than 7 players on {team} side. ',
              'Game supposed to be canceled')
        return []

    ids = get_players_ids(tag)  # list of ids

    # Make new dictionary of each player with keys(id,name,role,minutes)
    lineup = []  # list of dict
    i = 0
    for player in top11:
        if player.find('(') == -1:  # player got not subs, he played all game
            played = 90
            role = 'start'
            info = {'player_id': ids[i], 'name': player,
                    'role': role, 'minutes': played}
            lineup.append(info)
            i += 1

        else:  # player got subs, he played did not played 90 minutes
            players = player.split('(')
            subs_minute = re.findall(r'(\d+)\.', players[1])[0]
            player = players[0].strip()  # base player
            played = int(subs_minute)
            role = 'start'
            info = {'player_id': ids[i], 'name': player, 'role': role,
                    'minutes': played}
            lineup.append(info)
            i += 1

            player = players[1]  # subs player
            player = player.replace(subs_minute, '').replace('.', '', 1)
            player = player.replace(')', '').strip()
            played = 90 - int(subs_minute)
            role = 'subs'
            info = {'player_id': ids[i], 'name': player, 'role': role,
                    'minutes': played}
            lineup.append(info)
            i += 1

    return lineup
