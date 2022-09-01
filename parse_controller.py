import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict, namedtuple

from controller_input import ControllerInput

Command = namedtuple('Command', ['number', 'type', 'string'])


def get_command_type_no(command_type):
    if command_type in ['CHANGE_FL']:
        return 1
    elif command_type in ['DIRECT_TO', 'DIRECT_VIA']:
        return 2
    elif command_type in ['HEADING', 'HEADING_RIGHT', 'HEADING_LEFT']:
        return 3
    elif command_type in ['SPEED', 'SPEED_MATCH_POINT', 'SPEED_MAX', 'SPEED_MIN']:
        return 4
    elif command_type in ['CONTROL_ASM', 'CONTROL_XASM']:
        return 5
    else:
        return 6


def get_command_info(cmd_element):
    type = cmd_element.tag
    string = cmd_element.tag

    if cmd_element.tag == 'ControlInput':

        if cmd_element.find('Action') is not None:
            if cmd_element.find('Action').text == 'ASM':

                type = 'CONTROL_ASM'
                string = 'CONTROL_ASM'

            elif cmd_element.find('Action').text == 'XASM':

                type = 'CONTROL_XASM'
                string = 'CONTROL_XASM'

    elif cmd_element.tag == 'CFLInput':

        if cmd_element.find('CFL') is not None:
            type = 'CHANGE_FL'
            string = type + ' ' + cmd_element.find('CFL').text
        else:
            type = 'CHANGE_FL'
            string = type

    elif cmd_element.tag == 'TFLInput':

        if cmd_element.find('TFL') is not None:
            type = 'CHANGE_FL'
            string = type + ' ' + cmd_element.find('TFL').text
        else:
            type = 'CHANGE_FL'
            string = type

    elif cmd_element.tag == 'PFLInput':

        if cmd_element.find('PFL') is not None:
            type = 'CHANGE_FL'
            string = type + ' ' + cmd_element.find('PFL').text
        else:
            type = 'CHANGE_FL'
            string = type

    elif cmd_element.tag == 'ECLInput':

        if cmd_element.find('ECL') is not None:
            type = 'CHANGE_FL'
            string = type + ' ' + cmd_element.find('ECL').text
        else:
            type = 'CHANGE_FL'
            string = type

    elif cmd_element.tag == 'DirectInput':

        type = 'DIRECT_TO'
        string = type

        if cmd_element.find('Type') is not None:
            if cmd_element.find('Type').text == 'TO':
                type = 'DIRECT_TO'
                if cmd_element.find('Name') is not None:
                    string = type + ' ' + cmd_element.find('Name').text
                else:
                    string = type
            elif cmd_element.find('Type').text == 'VIA':
                type = 'DIRECT_VIA'

                if cmd_element.find('Name') is not None:
                    string = type + ' ' + cmd_element.find('Name').text
                else:
                    string = type


    elif cmd_element.tag == 'HeadingInput':

        type = 'HEADING'
        string = type

        heading_obj = cmd_element.find('AssignedHeading')

        if heading_obj is not None:

            if heading_obj.find('Heading') is not None:

                cmd_string_obj = heading_obj.find('Heading')
                type = 'HEADING'
                string = type + ' ' + cmd_string_obj.text

            elif heading_obj.find('RightTurn') is not None:

                cmd_string_obj = heading_obj.find('RightTurn')
                type = 'HEADING_RIGHT'
                string = type + ' ' + cmd_string_obj.text

            elif heading_obj.tag.find('LeftTurn') is not None:
                cmd_string_obj = heading_obj.find('LeftTurn')
                type = 'HEADING_LEFT'
                string = type + ' ' + cmd_string_obj.text


    elif cmd_element.tag == 'SpeedInput':

        if cmd_element.find('Assigned') is not None:

            cmd_string_obj = cmd_element.find('Assigned')
            type = 'SPEED_MATCH_POINT'
            string = type + ' ' + cmd_string_obj.text

        elif cmd_element.find('Max') is not None:
            cmd_string_obj = cmd_element.find('Max')
            type = 'SPEED_MAX'
            string = type + ' ' + cmd_string_obj.text

        elif cmd_element.find('Min') is not None:
            cmd_string_obj = cmd_element.find('Min')
            type = 'SPEED_MIN'
            string = type + ' ' + cmd_string_obj.text
        else:
            type = 'SPEED'
            string = type
    number = get_command_type_no(type)
    cmd = Command(number, type, string)
    return cmd


def get_controller_data(filename, filter_by_hours=None, limit=None):
    coordinates = {'BK': [49.5, 1.5, 52.5, 4.8], 'BN': [49.5, 3, 52, 6], 'BL': [48, 3.3, 51, 7.5],
                   'BO': [49.5, 4.5, 52, 7.7]}
    count = 0
    root = ET.parse(filename).getroot()


    result = []
    for flight in root.findall('FlightRecord'):
        if limit is not None and count >= limit:
            print('Breaking parsing due to limit reached')
            break
        cmd_index = 0
        flight_id = flight.find('FlightIdentification')
        callsign = flight_id.find('Callsign').text
        events = flight.find('Events')
        prev = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        for ci in events.findall('ControllerInput'):
            if limit is not None and count >= limit:
                print('Breaking parsing due to limit reached')
                break

            fl_data = flight.find('FlightData')
            departure = fl_data.findtext('ADEP', ' ')
            destination = fl_data.findtext('ADES', ' ')

            sector = ci.find('Sector').text
            cmd_list = [ci.find('ControlInput'), ci.find('CFLInput'), ci.find('TFLInput'),
                        ci.find('PFLInput'), ci.find('ECLInput'), ci.find('DirectInput'),
                        ci.find('HeadingInput'), ci.find('SpeedInput')]
            cmd_element = next((item for item in cmd_list if item is not None), None)

            if cmd_element is None:
                print('No commands found in ci')
                continue

            cmd = get_command_info(cmd_element)
            if cmd.number == 6:
                print(f'Skipping command(type 6): {cmd}')
                continue

            time = ci.find('Time').text
            timestamp = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f%z')
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            if filter_by_hours:
                if timestamp.hour not in filter_by_hours:
                    continue

            sector_code = sector[:2]
            if sector_code in coordinates:
                if (timestamp - prev) < datetime.timedelta(seconds=30):
                    # Not a new command, add to the previous command
                    print('Appending cmd to previous ci')
                    result[-1].commands.append(cmd)
                else:
                    count += 1
                    cmd_index += 1
                    prev = timestamp
                    controller_input = ControllerInput(departure=departure, command=cmd,
                                                       callsign=callsign, sector_code=sector_code,
                                                       timestamp=timestamp, time_str=time_str, sector=sector,
                                                       destination=destination, cmd_index=cmd_index)
                    result.append(controller_input)
    print(f'Found {len(result)} controller inputs for filename: {filename}, hours: {filter_by_hours}, limit: {limit}')
    return result


if __name__ == '__main__':
    data = get_controller_data('controller-inputs.xml', limit=20)
    print(f'Fetched {len(data)} records')
