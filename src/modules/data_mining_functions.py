import os
import pandas as pd
import re
import requests

from bs4 import BeautifulSoup as bs
from sportsipy.nhl import player, roster, teams


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


def build_player_stats_df(to_csv = False):
    """
    Compiles a dataframe of yearly stats of all current NHL players from sportsipy.
    
    Parameters
    ----------
    to_csv: bool, if True create a csv in the data folder
    
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
    pathway = 'C:\\Users\\dfeld\\Documents\\Data Sci Course\\Course Work\\Final Project repo\\data\\'
    file_names = [
        'nhl_player_yearly_stats',
        'error_teams',
        'error_players'
        ]
    file_num = ['', '', '']
    
    assert os.path.isdir(pathway), "Folder doesn't exist"
    
    for i, file_name in enumerate(file_names):
        while os.path.isfile(pathway + file_name + str(file_num[i]) + '.csv'):
            try:
                file_num[i] += 1
            except TypeError:
                file_num[i] = 1
        print(file_num[i])
    
    for club in team_list:
        try:
            team_roster = teams.Roster(club, 2022)
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


if __name__ == '__main__':
    build_player_stats_df()