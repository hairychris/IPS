"""
Interuptible Power Supply (IPS)
"""
import argparse
import os
import sys
import time

import energenie


def ping(target, number_of_pings):
    """Pings a target n times to see if it is up.

    Helper function used by do_ips in case we switch this out for something
    a little more sophisticated at a later date. This is fairly hacky for
    now as it just calls the local ping command on your computer and checks
    the output. It should work cross platform.

    Arguments:
        target {string} -- Hostname (or IP) to ping
        number_of_pings {integer} -- Number of times we should ping the host

    Returns:
        bool -- True if ping succeeded, False if it did not
    """
    ret = os.system(
        "ping -c {} {} 2>&1 >/dev/null".format(number_of_pings, target))
    return ret == 0


def toggle_plug(house_code, device_index, sleep_for):
    """Toggles a particular plug (shoots node in head)

    Uses the energenie library to toggle a plug off and then on again,
    each plug is associated with one house code, a house code can have
    up to 6 plugs associated with it (manual says 4).

    Arguments:
        house_code {string} -- ID for a group of plugs (think sort code)
        device_index {int} -- ID for a particular plug (think account number)
        sleep_for {int} -- Time to leave device off for in seconds

    Returns:
        bool -- True if toggle event succeeded, False if it did not
    """
    device = energenie.Devices.MIHO008((house_code, device_index))
    print("Turning Device #{} OFF using House Code {}".format(
        device, house_code))
    device.turn_off()
    time.sleep(sleep_for)
    print("Turning Device #{} ON using House Code {}".format(
        device, house_code))
    device.turn_on()
    return True


def do_ips(target, number_of_pings, house_code, device_index, sleep_for):
    """Performs actions expected of an IPS, calls ping and toggle helper functions.
    
    [description]
    
    Arguments:
        target {string} -- Hostname (or IP) to ping
        number_of_pings {integer} -- Number of times we should ping the host
        house_code {string} -- ID for a group of plugs (think sort code)
        device_index {int} -- ID for a particular plug (think account number)
        sleep_for {int} -- Time to leave device off for in seconds
    
    Returns:
        bool -- [description]
    """
    ping_responses = 0
    for i in range(0, number_of_pings):
        if ping(target, number_of_pings):
            print('{} is up {}'.format(target, i))
            ping_responses += 1
        else:
            print('{} is down {}'.format(target, i))
    print('Ping responses: {}'.format(ping_responses))

    if ping_responses == 0:
        print('{} is down for all pings'.format(target))
        # Use the toggle_plug helper function to turn device on then off
        toggle_plug(house_code, device_index, sleep_for)
        return False
    return True


if __name__ == "__main__":
    # Let's setup argparse and add the neccesary arguments with help text.
    parser = argparse.ArgumentParser(
        description='Interuptible Power Supply (IPS)')
    parser.add_argument('target', type=str,
                        default='google.com', help='host to ping')
    parser.add_argument('check_every', type=int, default=10,
                        help='how often to perform ping checks')
    parser.add_argument('number_of_pings', type=int,
                        default=3, help='host to ping')
    parser.add_argument('sleep_for', type=int, default=5,
                        help='time to leave device off for in seconds')
    parser.add_argument('house_code', type=str,
                        default='0001', help='house_code for device')
    parser.add_argument('device_index', type=int,
                        default='0', help='device_id to switch off')
    parser.add_argument('--ass', dest='associate_mode', action='store_const',
                        const=True, default=False,
                        help='use associate mode to add more plugs')
    parser.add_argument('--test', dest='test_mode', action='store_const',
                        const=True, default=False,
                        help='ping known bad target to test IPS config')

    args = parser.parse_args()
    # This line is important, without it you will get a weird unhelpful.
    # error message from the energenie library. TODO: helpful error?
    energenie.init()
    # We must convert the house code into hex.
    house_code = int(args.house_code, 16)
    try:
        while True:
            if args.associate_mode and args.test_mode:
                # Inform the user if they passed bad values.
                raise ValueError('You should never set both test and associate mode arguments')
            elif args.associate_mode:
                # We are in association mode, let's toggle the device. 
                toggle(house_code, args.device_index, args.sleep_for)
            elif args.test_mode:
                # Ping invalid host to trigger IPS system delibrately.
                do_ips(
                    '0.0.0.0', args.number_of_pings, house_code, args.device_index, args.sleep_for
                )
            else:
                # Everything looks good, let's become an IPS.
                do_ips(
                    args.target, args.number_of_pings, house_code, args.device_index, args.sleep_for
                )
            # Sleep until we next need to check
            time.sleep(args.check_every)

    except KeyboardInterrupt:
        print('Exiting')
        pass  # user exit
