import os
import pandas as pd
import re
import requests

from bs4 import BeautifulSoup as bs
from sportsipy.nhl import player, roster, teams
from datetime import date


def parse_player_code(athletes, return_info = None):
    """
    Converts the player info generated from sportsipy to a first name, last name, or player code.
    
    Parameters
    ----------
    athletes: string or list of sportipy-generated player info

    return_info: string, default None 
        options are: 'fname', 'lname', 'pcode', or None which returns [[fname, lname, pcode]]
    
    Returns
    ----------
    string or list of strings of first name, last name, player code, or a list of all three
    """
    
    if not isinstance(athletes, list):
        fname, *lname, pcode = re.findall(r'\S+', str(athletes))
        pcode = pcode[1:-1]
        player_info = {'fname': fname, 'lname': lname, 'pcode': pcode}
        
        if return_info == None:
            return [fname, ' '.join(lname), pcode]
        
        return player_info[return_info]

    lst = []
    
    if return_info == None:
        for athlete in athletes:
            fname, *lname, pcode = re.findall(r'\S+', str(athlete))
            pcode = pcode[1:-1]
            lst.append([fname, ' '.join(lname), pcode])
        return lst
    
    if return_info == 'fname':
        for athlete in athletes:
            fname = re.findall(r'\S+', str(athlete))[0]
            lst.append(fname)
        return lst
    
    if return_info == 'lname':
        for athlete in athletes:
            lname = re.findall(r'\S+', str(athlete))[1:-1]
            lst.append(' '.join(lname))
        return lst
    
    if return_info == 'pcode':
        for athlete in athletes:
            pcode = re.findall(r'\S+', str(athlete))[-1]
            pcode = pcode[1:-1]
            lst.append(pcode)
        return lst


def mine_player_position(player_code: str) -> str:
    """
    Mines the player's position from sports-reference website.
    
    Parameters
    ----------
    player_code: code generated from sportsipy player info unique to the player.

    Returns
    ----------
    player position, any of [C, RW, LW, D, G]
    """
    try:
        page = requests.get(f'https://www.hockey-reference.com/players/{player_code[0]}/{player_code}.html')
        page.raise_for_status()
    except requests.exceptions.HTTPError:
        player_code = f'{player_code[:-2]}.{player_code[-2:]}'
        page = requests.get(f'https://www.hockey-reference.com/players/{player_code[0]}/{player_code}.html')
    soup = bs(page.content, 'html.parser')
    return re.findall(r':\s+(\w+)', soup.find('p').text)[0]


def create_player_dataframe(player_code: str, position = True, first_name = None, last_name = None):
    """
    Gets the player's yearly stats from sportsipy.
    
    Parameters
    ----------
    player_code: string
        code generated from sportipy player info unique to the player.
        
    position: bool, default True
        calls mine_player_position() and includes it in the dataframe.
    
    first_name: string, default None
        first name of the player
    
    last_name: string, default None
        last name of the player

    Returns
    ----------
    pandas DataFrame of the player's yearly stats with their player_code inserted.
    If last_name or both first_name and last_name are both populated, they are also included in the dataframe. (First name cannot be alone.)
    """
    
    athlete = roster.Player(player_code)
    df = athlete.dataframe.iloc[:-1, :]
    df = df.reset_index()
    df = df.rename(mapper = {'level_0': 'season'}, axis = 1)
    
    if position:
        df.insert(loc = 1, column = 'position', value = mine_player_position(player_code))
    
    df.insert(loc = 1, column = 'player_code', value = player_code)
    
    if first_name and last_name:
        df.insert(loc = 1, column = 'first_name', value = first_name)
    
    if last_name:
        df.insert(loc = 1, column = 'last_name', value = last_name)
    
    return df


def mine_player_salary(first_name: str, last_name: str):
    """
    Compiles a dataframe of the player's seasonal salary across their career,
    as well as whether or not a new contract came into effect.
    
    Parameters
    ----------
    first_name: str
        player's first name
        
    last_name: str
        player's last name
    
    Returns
    ----------
    pandas DataFrame of the season, the player's salary for that season, whether it was a new contract.
    """    
    
    full_name = first_name + '-' + last_name
    full_name = ''.join([char for char in full_name if char != '.'])
    full_name = '-'.join(full_name.split(sep = ' ')).lower()
    
    url = f'https://www.capfriendly.com/players/{full_name}'
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')
    
    lst = []
    for table in soup.find_all('div', class_ = 'table_c contract_cont'):
        try:
            contract_year = 1
            table_body = table.find('tbody', id = 'cont_x')
            for mod in ['odd', 'even']:
                for row in table_body.find_all('tr', class_ = mod):
                    lst.append((row.find('td', class_ = 'left').string, row.find_all('td', class_ = 'center')[2].string, contract_year))
                    contract_year = 0
        except IndexError:
            continue

    df = pd.DataFrame(lst, columns=['season', 'AAV', 'contract_year'])
    return df.sort_values('season').reset_index(drop = True)


def build_player_stats_df(year = 2022):
    """
    Compiles a dataframe of yearly stats of all current NHL players from sportsipy and exports to csv.
    
    Parameters
    ----------
    year: int, default 2022
        the season roster for which the csv will be created.
    
    Returns
    ----------
    pandas DataFrame of every current player's yearly stats.
    """
    
    team_list = [
        'ANA', 'ARI', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI',
        'COL', 'DAL', 'DET', 'EDM', 'FLA', 'LAK', 'MIN', 'MTL', 
        'NJD', 'NSH', 'NYI', 'NYR', 'OTT', 'PHI', 'PIT', 'SEA',
        'SJS', 'STL', 'TBL', 'TOR', 'VAN', 'VEG', 'WPG', 'WSH'
                ]
    
    df = pd.DataFrame()
    error_teams = []
    error_players = []
    
    dirname = os.path.dirname(__file__)
    pathway = os.path.join(dirname, '../../data/')
    file_names = [
        f'nhl_player_yearly_stats_{year}',
        f'error_teams_{year}',
        f'error_players_{year}'
        ]
    file_num = ['', '', '']
    
    assert os.path.isdir(pathway), "Folder doesn't exist"
    
    for i, file_name in enumerate(file_names):
        while os.path.isfile(pathway + file_name + str(file_num[i]) + '.csv'):
            try:
                file_num[i] += 1
            except TypeError:
                file_num[i] = 1
    
    for club in team_list:
        try:
            team_roster = teams.Roster(club, year)
            team_roster = set(team_roster.players)
        except:
            error_teams.append(club)
            continue
        
        for athlete in team_roster:
            try:
                player_info = parse_player_code(athlete)
                df = pd.concat([df, create_player_dataframe(player_code = player_info[2],
                                                            first_name = player_info[0],
                                                            last_name = player_info[1]
                                                            )
                                ])
            except:
                error_players.append(athlete)


    
    df = df.reset_index(drop = True)

    df.to_csv(pathway + file_names[0] + str(file_num[0]) + '.csv')
    if error_teams:
        pd.DataFrame(error_teams).to_csv(pathway + file_names[1] + str(file_num[1]) + '.csv')
    if error_players:
        pd.DataFrame(error_players).to_csv(pathway + file_names[2] + str(file_num[2]) + '.csv')


def concatenate_dataframes(start_year, end_year = int(date.today().year) + 1):
    """
    Concatenates all of the dataframes created in the build_player_stats_df function and exports to csv.
    
    Parameters
    ----------
    start_year: int
        the earliest season roster for which player data was collected.

    end_year: int, default current year + 1
        the earliest season roster for which player data was collected.
    
    Returns
    ----------
    pandas DataFrame of the yearly stats of every player within the time range.
    """

    dirname = os.path.dirname(__file__)
    pathway = os.path.join(dirname, '../../data/')
    file_name = 'full_nhl_player_yearly_stats'
    file_num = ''

    while os.path.isfile(pathway + file_name + str(file_num) + '.csv'):
        try:
            file_num += 1
        except TypeError:
            file_num = 1
    
    assert os.path.isdir(pathway), "Folder doesn't exist"

    raw = pd.DataFrame()
    for year in range(2015, 2022):
        raw = pd.concat([raw, pd.read_csv(f'data/nhl_player_yearly_stats_{year}.csv', index_col=0)])
    raw.reset_index(drop = True, inplace = True)
    raw.drop_duplicates(inplace = True)
    raw.to_csv(pathway + file_name + str(file_num) + '.csv')


if __name__ == '__main__':
    start_year = 2015
    end_year = 2022
    for year in range(start_year, end_year + 1):
        build_player_stats_df(year)
    
    concatenate_dataframes(start_year, end_year)