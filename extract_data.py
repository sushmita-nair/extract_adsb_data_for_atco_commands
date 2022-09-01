import datetime
import itertools
import logging
import os
import pickle
import sys
import traceback
import random
from collections import defaultdict, namedtuple
from concurrent.futures.thread import ThreadPoolExecutor
from timeit import default_timer as timer

import pandas as pd
from pyopensky import OpenskyImpalaWrapper

from parse_controller import get_controller_data
from util import timing

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
root.addHandler(handler)


@timing
def query_opensky_group(opensky, hour, bounds, min_time=None, max_time=None, upper_sky=False):
    cols = 'time, lat, lon, heading, velocity, callsign, baroaltitude, geoaltitude, hour'
    query = f'SELECT {cols} FROM state_vectors_data4 WHERE hour>={hour} AND hour<{hour + 3600} ' \
            f'AND lat>={bounds[0]} AND lat<={bounds[2]} AND lon>={bounds[1]} AND lon<={bounds[3]}'
    if min_time:
        query += f' AND time>={min_time}'
    if max_time:
        query += f' AND time<={max_time}'
    if upper_sky:
        query += f' AND baroaltitude>=7467'   # for upper airspace
    df = opensky.rawquery(query)
    return df

# process_ci funcion populates the dataset(cmd_dict and adsb_dict) with command and adsb information for each CI
def process_ci(ci, df, dataset):

    df_upper = get_upper_air_space(ci, df)
    if ci.callsign in df_upper.callsign.str.strip().unique():
        
        is_success = True

        # group by callsign and order by time
        flights_adsb = {}
        for name, group in df_upper.groupby('callsign'):
            group = group.sort_values(by=['time'])
            flights_adsb[name] = group.loc[:,['time', 'lat', 'lon', 'heading', 'velocity', 'geoaltitude', 'baroaltitude']]

            label_ = [c.number for c in ci.commands] if name == ci.callsign else [0]
            flights_adsb[name].loc[:,'label'] = str(label_)

        ci.cmd_index += 1
        # unique cmd_index for each ci for a given callsign on a given day
        key = ci.timestamp.date(), ci.callsign, ci.cmd_index
        dataset['cmd_dict'][key] = pd.DataFrame(
            {'time': [ci.timestamp], 'callsign': [ci.callsign], 'sector': [ci.sector],
             'command_type': [','.join((c.type for c in ci.commands))],
             'command_full': [' '.join([ci.callsign] + [c.string for c in ci.commands])],
             'departure': [ci.departure], 'destination': [ci.destination]}
        )
        dataset['adsb_dict'][key] = flights_adsb

    else:
        if ci.callsign in df.callsign.str.strip().unique():
            print(f'callsign found, but not in upper space: {ci.callsign}')
        else:
            print(f'failed to find callsign: {ci.callsign}')
        is_success = False
    return is_success


def get_upper_air_space(ci, df):
    if ci.sector_bounds is not None:
        if len(ci.sector_bounds) == 5:
            if ci.sector_bounds[4] == 'H':
                df_upper_air_space = df[df['baroaltitude'] > 10820]
            else:
                df_upper_air_space = df[df['baroaltitude'].between(7467, 10820)]
        else:
            df_upper_air_space = df[df['baroaltitude'] >= 7467]
    else:
        df_upper_air_space = df[df['baroaltitude'] >= 7467]
    return df_upper_air_space


Count = namedtuple('count', ['success', 'failed'])

# process_ci_group funcion queries opensky for each group and slices the adsb dataframe for each CI in group
def process_ci_group(opensky, success_all, failed_all, dataset, item):
    start = timer()
    key, cis = item
    hour, bounds = key
    print(f'Executing group: {key} with {len(cis)} items')

    min_time = int(min(ci.timestamp.timestamp() for ci in cis))
    max_time = int(max(ci.timestamp.timestamp() for ci in cis))
    # for each group make a single query
    df = query_opensky_group(opensky, hour, bounds, min_time, max_time, upper_sky=True)
    if df is None:
        raise Exception(f'Opensky query failed for hour: {hour}, bounds: {bounds}')
    success_count = 0
    failed_count = 0
    for ci in cis:
        ts = int(ci.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp())

        time_window = [ts - 1, ts, ts + 1]
        # Slice df for the timestamp of the ci
        df_slice = df.loc[df['time'].isin(time_window)]
        is_success = process_ci(ci, df_slice, dataset)
        if is_success:
            success_all[ci.callsign].append(ci.timestamp)
            success_count += 1
        else:
            failed_all[ci.callsign].append(ci.timestamp)
            failed_count += 1
    end = timer()
    print(
        f'Processed group: {key} with {len(cis)} items: Success: {success_count}, '
        f'Failed: {failed_count} in {(end - start):.2f}s')
    return Count(success_count, failed_count)

def get_random_hours():

    num = random.randrange(23)
    hour_list= [num, num+1]
    return hour_list

# query_data function groups controller inputs into unique hour+bound groups
# and processes each group using multithreading 
@timing
def query_data(days):
    
    start = timer()
    for day in days:
        try:
            dataset = {'cmd_dict': {}, 'adsb_dict': {}}
            filter_by_hours = get_random_hours()
            
            data_path_controller_inp = "/***controller inputs path***/"
            file = '/controller-inputs.xml'
            filename = data_path_controller_inp + day + file
            
            # The limit is only for testing
            controller_inputs = get_controller_data(filename, filter_by_hours=filter_by_hours) #, limit=100

            # Group controller inputs by (hour, bounds)
            groups = defaultdict(list)
            for ci in controller_inputs:
                key = ci.hour, tuple(ci.bounds)
                groups[key].append(ci)
            print(f'Total groups(hour, bounds) found: {len(groups)}')
            success_all, failed_all = defaultdict(list), defaultdict(list)

            workers = 18
            with ThreadPoolExecutor(max_workers=workers) as executor:
                clients = [OpenskyImpalaWrapper() for _ in range(int(workers * 1.5))]
                iter = itertools.cycle(clients)
                result = list(executor.map(lambda x: process_ci_group(next(iter),
                                                                    success_all, failed_all, dataset, x),
                                        groups.items()))
            success = sum(count.success for count in result)
            failed = sum(count.failed for count in result)
            #assert success_all and failed_all
            

        except Exception as e:
            print(f'Exception occurred for day: {day} Success: {success}, Failed: {failed}, Total: {len(controller_inputs)}')
            traceback.print_exc()

        finally:
            end = timer()
            print(f'Executed for day {day}Success: {success}, Failed: {failed}, Total: {len(controller_inputs)}')
            print(f'Hours are {filter_by_hours}')
            print(f'Total time taken: {(end - start):.2f}s')
            

            data_download_path = "/data/****/****/"
            dirpath = os.path.join(data_download_path, "data", day)
            os.makedirs(dirpath, exist_ok=True)

            pickle.dump(success_all, open(os.path.join(dirpath, "success.pkl"), 'wb'))
            pickle.dump(failed_all, open(os.path.join(dirpath, "failed.pkl"), 'wb'))
            pickle.dump(dataset, open(os.path.join(dirpath, "dataset.pkl"), 'wb'))


if __name__ == '__main__':

    month=["01", "02", "03", "04", "05", "06","07","08","09","10","11","12","13","14","15"
     ,"16","17","18","19","20","21","22","23","24","25","26", "27", "28", "29", "30"]
    query_data(days=month)
