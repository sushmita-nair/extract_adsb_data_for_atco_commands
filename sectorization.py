import pandas as pd
from datetime import datetime
import numpy as np

from util import timing

coordinates = {'BK': [49.5, 1.5, 52.5, 4.8], 'BN': [49.5, 3, 52, 6], 'BL': [48, 3.3, 51, 7.5],
               'BO': [49.5, 4.5, 52, 7.7]}


@timing
def get_sectorization_data(sector_df, date):
    
    df = sector_df[sector_df['target_date'] == date]

    df = df.drop_duplicates('start_time')
    
    df = df[df['sectorisation_name'].notna()]

    df['sectorisation_name'] = df.sectorisation_name.str.split("+")
    

    sector1 = df.sectorisation_name.str[0].str.extract(r'([BDH][0-9]([_-][0-9]+)?)')  # 'B[0-9](_[0-9])?'
    sector2 = df.sectorisation_name.str[1].str.extract(r'([BDH][0-9]([_-][0-9]+)?)')
    sector3 = df.sectorisation_name.str[2].str.extract(r'([BDH][0-9]([_-][0-9]+)?)')
   
    df['sector_B'] = sector1[0].str.replace('-', '_', regex=True)
    df['sector_D'] = sector2[0].str.replace('-', '_', regex=True)
    df['sector_H'] = sector3[0].str.replace('-', '_', regex=True)

    

    return df

def get_time_interval(time, time_array):
    
    time_array = np.sort(time_array)
    

    index = np.searchsorted(time_array, time, side='right')

    return time_array[index - 1]



def get_sector_config(sector, time, sector_df):
    time_array = sector_df['start_time'].to_numpy()

    time_interval = get_time_interval(time, time_array)
    

    sectorization = sector_df[sector_df['start_time'] == time_interval]

    if sector[0] == 'B':
        sector_config = sectorization['sector_B'].item()
    elif sector[0] == 'D':
        sector_config = sectorization['sector_B'].item()
    elif sector[0] == 'H':
        sector_config = sectorization['sector_B'].item()
    else:
        sector_config = None

    return sector_config


all_sector_df = pd.read_csv('/***path to sectorisation.csv ***/')
date_sector = {}

def get_sector_bounds(seat_position, time, date):
    sectorization_dict = {

        'B1': {'BOL': [48.5, 1.5, 51.7, 7.5]},

        'B2': {'BNL': [49.8, 1.5, 51.6, 5.4], 'BOL': [48.6, 4.1, 51.3, 7.1]},

        'B3_1': {'BNL': [49.8, 1.5, 51.6, 5.4], 'BOL': [50, 5, 51.3, 7.3], 'BLL': [48.5, 4, 50.6, 7]},

        'B3_4': {'BNL': [49.8, 1.5, 51.6, 5.4], 'BLH': [48.6, 4.1, 51.3, 7.1, 'H'], 'BOL': [48.6, 4.1, 51.3, 7.1, 'L']},

        'B4_5': {'BNH': [49.8, 1.5, 51.6, 5.4, 'H'], 'BNL': [49.8, 1.5, 51.6, 5.4, 'L'], 'BOL': [50, 5, 51.3, 7.3],
                 'BLL': [48.5, 4, 50.6, 7]},

        'B4_6': {'BNH': [49.8, 1.5, 51.6, 5.4, 'H'], 'BNL': [49.8, 1.5, 51.6, 5.4, 'L'],
                 'BLH': [48.6, 4.1, 51.3, 7.1, 'H'], 'BOL': [48.6, 4.1, 51.3, 7.1, 'L']},

        'B5_5': {'BNH': [49.8, 1.5, 51.6, 5.4, 'H'], 'BNL': [49.8, 3.5, 51.5, 5.4, 'L'],
                 'BKL': [50.3, 1.5, 51.6, 4.3, 'L'], 'BLH': [48.6, 4.1, 51.3, 7.1, 'H'],
                 'BOL': [48.6, 4.1, 51.3, 7.1, 'L']},

        'B5_8': {'BNH': [49.8, 1.5, 51.6, 5.4, 'H'], 'BNL': [49.8, 1.5, 51.6, 5.4, 'L'],
                 'BLH': [48.6, 4.1, 51.3, 7.1, 'H'], 'BOL': [50, 5, 51.3, 7.3, 'L'], 'BLL': [48.5, 4, 50.6, 7, 'L']},

        'B5_9': {'BNH': [49.8, 1.5, 51.6, 5.4, 'H'], 'BNL': [49.8, 1.5, 51.6, 5.4, 'L'], 'BOL': [50, 5, 51.3, 7.3],
                 'BLH': [48.5, 4, 50.6, 7, 'H'], 'BLL': [48.5, 4, 50.6, 7, 'L']},

        'B6_1': {'BNH': [49.8, 1.5, 51.6, 5.4, 'H'], 'BNL': [49.8, 3.5, 51.5, 5.4, 'L'],
                 'BKL': [50.3, 1.5, 51.6, 4.3, 'L'], 'BLH': [48.6, 4.1, 51.3, 7.1, 'H'], 'BOL': [50, 5, 51.3, 7.3, 'L'],
                 'BLL': [48.5, 4, 50.6, 7, 'L']},

        'B6_2': {'BNH': [49.8, 1.5, 51.6, 5.4, 'H'], 'BNL': [49.8, 3.5, 51.5, 5.4, 'L'],
                 'BKL': [50.3, 1.5, 51.6, 4.3, 'L'], 'BOL': [50, 5, 51.3, 7.3], 'BLH': [48.5, 4, 50.6, 7, 'H'],
                 'BLL': [48.5, 4, 50.6, 7, 'L']}

    }

    if date not in date_sector:
        # Since days are iterated sequentially only a single day data needs to be retained at a time
        date_sector.clear()
        date_sector[date] = get_sectorization_data(all_sector_df, date)

    sector_df = date_sector[date]
    assert not sector_df.empty

    sector_config = get_sector_config(seat_position, time, sector_df)

    if sector_config in sectorization_dict:
        if seat_position in sectorization_dict[sector_config]:
            return sectorization_dict[sector_config][seat_position]
        else:
            return None
    else:
        return None

if __name__ == '__main__':
    bounds = get_sector_bounds('BOL','2019-08-02 09:10:25', '2019-08-02')
    print(bounds)
    print(len(bounds))
