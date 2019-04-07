import helpers.converter as cv
import helpers.parser as ps
import os
import argparse

from consts import SERVER_JSON_DIRECTORY, MODELS_DIRECTORY


def parse_servers(args):
    """
    Parses the server json files given in args, otherwise parses all the server json files in the server_json directory.
    :param args: argparse.Namespace object.
    :return: Nothing.
    """
    server_jsons = [x for x in os.listdir(SERVER_JSON_DIRECTORY) if x.endswith('.json')]
    curr_server_num = 1
    if args.files:
        for server_json in args.files:
            print(f'Parsing file {curr_server_num}/{len(args.files)}: {server_json}')
            if server_json not in server_jsons:
                print(f'file not found.')
            else:
                ps.parse_server(server_json)
            curr_server_num += 1
    else:
        for server_json in server_jsons:
            print(f'Parsing file {curr_server_num}/{len(args.files)}: {server_json}')
            ps.parse_server(server_json)
            curr_server_num += 1


def convert_servers(args):
    """
        Converts the messages of given servers into markov models, saved as json files.
        :param args: argparse.Namespace object.
        :return: Nothing.
    """
    if args.files:
        for server_json in args.files:
            cv.convert_server(filename=server_json)
    else:
        for serverid in [x[0] for x in os.walk(MODELS_DIRECTORY)]:
            cv.convert_server(serverid=serverid)


if __name__ == '__main__':
    # Setting up argparser.
    parser = argparse.ArgumentParser(description='Model generator for MarkovBot.')
    parser.add_argument('--file', '--files', dest='files', type=str, nargs='+',
                        help="a list of files to convert (default: prompt user for a file)")
    parser.add_argument('--messages', '-m', dest='only_messages', action='store_true',
                        help="only parses the messages from the server json and does not convert them to models.")
    parser.add_argument('--models', '-d', dest='only_models', action='store_true',
                        help="only converts the messages from the server and does not parse messages from the file.")
    parser.add_argument('--simmodel', '-s', dest='sim_model', action='store_true',
                        help="creates the simulation user model, which determines which order users post in the simulation.")
    args = parser.parse_args()

    if not args.files:
        args.files = [input("Enter the name of the json you want to convert: ")]
    if args.sim_model:
        if not args.files:
            print("Please specify a from which the sim model will be created.")
        else:
            ps.gen_simmodel(args.files[0])
    else:
        # Parse servers.
        if not os.path.isdir(SERVER_JSON_DIRECTORY):
            os.mkdir(SERVER_JSON_DIRECTORY)
        if not args.only_models:
            try:
                parse_servers(args)
            except NameError:
                print('unable to find server in/automatically add server to servers.txt.\n'
                      'Please manually add the server in the following format:\n'
                      'serverid;serverfilename')

        # Convert messages.
        if not args.only_messages:
            convert_servers(args)

