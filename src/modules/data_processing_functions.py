import pandas as pd

def filter_position(df, position):
    """
    Distills the dataframe down to only the hockey positions selected.
    
    Parameters
    ----------
    df: pandas DataFrame
        the dataframe to filter.
        
    position: iterable, string
        the list of hockey positions to be selected. Can be any combination of:
        ['C', 'RW', 'LW', 'F', 'W', 'D', 'G'], which represent respectively:
        [Center, Right Wing, Left Wing, Forward, Winger, Defense, Goalie]

    Returns
    ----------
    pandas DataFrame of only the players at the positions selected.
    """
    
    position = list(set(position))
    return df[df['position'].isin(position)].reset_index(drop = True)


def adjust_season_format(date):
    """
    Changes the format of the date to the season's end year.
    
    Parameters
    ----------
    date: string
        the season's date

    Returns
    ----------
    string of the season's end year, format 20XX.
    """
    
    return int(''.join('20' + date[-2:]))


def split_teams(df_copy):
    """
    Changes 'TOT' (total) team abbreviation to a combination of the player's teams from the year before and the year after.
    (An assumption is being made that the player didn't play for more than 2 teams across 2 season, like Taylor Hall did.)
    
    Parameters
    ----------
    df: pandas DataFrame
        the dataframe to filter.
        
    Returns
    ----------
    pandas DataFrame where 'TOT' team abbreviation is removed.
    """
    
    df = df_copy.copy()    
    team_list = df['team_abbreviation'].to_list()
    error_list = []
    
    for i, team in enumerate(team_list):
        try:
            if team != 'TOT':
                continue
            
            if (
                df.loc[i, 'player_code'] == df.loc[i-1, 'player_code']
                and not isinstance(team_list[i-1], list)
                and team_list[i-1] != 'TOT' 
                and team_list[i+1] != 'TOT'
            ):
                team_list[i] = [team_list[i-1], team_list[i+1]]
        
        except KeyError:
            error_list.append(df.loc[i, 'player_code'])
            continue
    
    df['team_abbreviation'] = team_list
    further_list = [(i) for i in range(len(team_list)) if team_list[i] == 'TOT']
    print('rows that still need addressing:\n')
    print(further_list)
    print('error list: ')
    print(error_list)
    return df_copy, further_list


def stats_per_60_minutes(df_copy):
    """
    Standardizes the player data per 60 minutes of ice time.
    
    Parameters
    ----------
    df: pandas DataFrame
        the dataframe to standardize.
        
    Returns
    ----------
    pandas DataFrame where additional, standardized columns are created based on existing numeric columns.
    """
    
    df = df_copy.copy()
    numeric_categories = [df.columns[i] for i in range(len(df.columns)) if df[df.columns[i]].dtype.kind in ['i' ,'f']]
    for category in ['season', 'age', 'games_played', 'time_on_ice']:
        try:
            numeric_categories.remove(category)
        except:
            continue
            
    for category in numeric_categories:
        df[f'{category}_per_60_minutes'] = df[category]/df['time_on_ice']*60
    
    return df


def add_shifted_years(df_copy, n_years = 1):
    """
    Adds a set of columns for each player's previous years' performances.
    
    Parameters
    ----------
    df: pandas DataFrame
        the dataframe to process.
        
    n_year: int, default = 1
        the number of previous years for which columns should be added.
        
    Returns
    ----------
    pandas DataFrame where additional columns are created based on previous years' numeric columns.
    """
    
    df = df_copy.copy()
    numeric_categories = [df.columns[i] for i in range(len(df.columns)) if df[df.columns[i]].dtype.kind in ['i' ,'f']]
    for category in ['season', 'age', 'games_played', 'time_on_ice']:
        try:
            numeric_categories.remove(category)
        except:
            continue
    
    for year in range(1, n_years+1):
        for category in numeric_categories:
            df[f'{category}_{year}_seasons_ago'] = df.groupby('player_code').shift(year)[category]
    
    return df


def preprocessing_pipeline(df_copy):
    """
    Performs all the preprocessing on the data to prepare for entry in the machine learning model.
    
    Parameters
    ----------
    df: pandas DataFrame
        the dataframe to filter.

    Returns
    ----------
    pandas DataFrame with a reduced column set and adjusted values.
    """
    
    df = df_copy.copy()    
    df = filter_position(df, ['C', 'RW', 'LW', 'F', 'W'])
    df.season = df.season.apply(adjust_season_format)
    df = df[[
        'season','first_name', 'last_name', 'player_code', 'age', 'team_abbreviation',
        'games_played', 'time_on_ice', 'points', 'goals', 'goals_created', 'assists',
        'giveaways', 'takeaways', 'hits_at_even_strength'
    ]]
    
    df = stats_per_60_minutes(df)
    df = df.drop(
        ['points', 'goals', 'goals_created', 'assists', 'giveaways', 'takeaways', 'hits_at_even_strength'],
        axis = 1
    )
    
    df = add_shifted_years(df, 2)
    df = df.dropna().reset_index(drop = True)
#     df = split_teams(df)
    
    return df