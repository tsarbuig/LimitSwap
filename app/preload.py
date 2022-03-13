import signal
import argparse
from time import sleep, time
from datetime import datetime
from jsmin import jsmin
import json
import os
import logging
import sys
import apprise
import cryptocode, re, pwinput
import requests


# color styles
class style():  # Class of different text colours - default is white
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    INFO = '\033[36m'
    DEBUG = '\033[35m'


"""""""""""""""""""""""""""
//PRE LOADED FUNCTIONS
"""""""""""""""""""""""""""

# Function to cleanly exit on SIGINT
def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def timestamp():
    timestamp = time()
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object

#
# START - COMMAND LINE ARGUMENTS
#
parser = argparse.ArgumentParser()

# USER COMMAND LINE ARGUMENTS
parser.add_argument("--pump", type=int, help="Holds the position as long as the price is going up. Sells when the price has gone down PUMP percent")
parser.add_argument("-p", "--password", type=str, help="Password to decrypt private keys (WARNING: your password could be saved in your command prompt history)")
parser.add_argument("--reject_already_existing_liquidity", action='store_true', help="If liquidity is found on the first check, reject that pair.")
parser.add_argument("-s", "--settings", type=str, help="Specify the file to user for settings (default: settings.json)", default="./settings.json")
parser.add_argument("-t", "--tokens", type=str, help="Specify the file to use for tokens to trade (default: tokens.json)", default="./tokens.json")
parser.add_argument("-v", "--verbose", action='store_true', help="Print detailed messages to stdout")
parser.add_argument("-pc", "--password_on_change", action='store_true', help="Ask user password again if you change tokens.json")
parser.add_argument("-sm", "--slow_mode", action='store_true', help="Bot will only check price 2 times/s. Use it if you're on a RPC with rate limit")

# DEVELOPER COMMAND LINE ARGUMENTS
# --dev - general argument for developer options
# --debug - to display the "printt_debug" lines
# --sim_buy tx - simulates the buying process, you must provide a transaction of a purchase of the token
# --sim_sell tx - simulates the buying process, you must provide a transaction of a purchase of the token
# --benchmark - run benchmark mode
parser.add_argument("--dev", action='store_true', help=argparse.SUPPRESS)
parser.add_argument("--sim_buy", type=str, help=argparse.SUPPRESS)
parser.add_argument("--sim_sell", type=str, help=argparse.SUPPRESS)
parser.add_argument("--debug", action='store_true', help=argparse.SUPPRESS)
parser.add_argument("--benchmark", action='store_true', help=argparse.SUPPRESS)

command_line_args = parser.parse_args()

#
# END - COMMAND LINE ARGUMENTS
#

def printt(*print_args, write_to_log=False):
    # Function: printt
    # ----------------------------
    # provides normal print() functionality but also prints our timestamp
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    print(timestamp(), ' '.join(map(str, print_args)))
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))

def printt_v(*print_args, write_to_log=False):
    # Function: printt
    # ----------------------------
    # provides normal print() functionality but also prints our timestamp and pays attention to user set verbosity.
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    if command_line_args.verbose == True:
        print(timestamp(), ' '.join(map(str, print_args)))
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))

def printt_err(*print_args, write_to_log=True):
    # Function: printt_err
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an error
    #
    # print_args - normal arguments that would be passed to the print() function
    # write_to_log - wether or not to write the same text to the log file
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.RED, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))

def printt_warn(*print_args, write_to_log=False):
    # Function: printt_warn
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display a warning
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.YELLOW, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))

def printt_ok(*print_args, write_to_log=False):
    # Function: printt_ok
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an OK text
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.GREEN, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))

def printt_info(*print_args, write_to_log=False):
    # Function: printt_info
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an INFO text in yellow
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.INFO, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))

def printt_debug(*print_args, write_to_log=False):
    # Function: printt_warn
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display a warning
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    if command_line_args.debug == True:
        print(timestamp(), " ", style.DEBUG, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))

def printt_repeating(token_dict, message, print_frequency=500):
    #     Function: printt_r
    #     --------------------
    #     Function to manage a generic repeating message
    #
    #     token_dict - one element of the tokens{} dictionary
    #     message - the message to be printed
    #
    #     returns: nothing
    
    global repeated_message_quantity
    
    if message == token_dict['_LAST_MESSAGE'] and settings['VERBOSE_PRICING'] == 'false' and print_frequency >= repeated_message_quantity:
        bot_settings['_NEED_NEW_LINE'] = False
        repeated_message_quantity += 1
    else:
        printt_err(message, write_to_log=False)
        repeated_message_quantity = 0
    
    token_dict['_LAST_MESSAGE'] = message

def printt_sell_price(token_dict, token_price):
    #     Function: printt_sell_price
    #     --------------------
    #     Formatted buying information
    #
    #     token_dict - one element of the tokens{} dictionary
    #     token_price - the current price of the token we want to buy
    #
    #     returns: nothing
    printt_debug("printt_sell_price token_dict:", token_dict)
    printt_debug("token_dict['_TRADING_IS_ON'] 266:", token_dict['_TRADING_IS_ON'], "for token:", token_dict['SYMBOL'])
    printt_debug("_PREVIOUS_QUOTE :", token_dict['_PREVIOUS_QUOTE'], "for token:", token_dict['SYMBOL'])
    
    if token_dict['USECUSTOMBASEPAIR'] == 'false':
        price_message = f'{token_dict["_PAIR_SYMBOL"]} Price: {token_price:.24f} {base_symbol} - Buy: {token_dict["BUYPRICEINBASE"]:.6g}'
    
    else:
        price_message = f'{token_dict["_PAIR_SYMBOL"]} Price: {token_price:.24f} {token_dict["BASESYMBOL"]} - Buy: {token_dict["BUYPRICEINBASE"]:.6g}'
    
    price_message = f'{price_message} Sell: {token_dict["_CALCULATED_SELLPRICEINBASE"]:.6g} Stop: {token_dict["_CALCULATED_STOPLOSSPRICEINBASE"]:.6g}'
    # price_message = price_message + " ATH:" + "{0:.24f}".format(token_dict['_ALL_TIME_HIGH']) + " ATL:" + "{0:.24f}".format(token_dict['_ALL_TIME_LOW'])
    
    if token_dict['TRAILING_STOP_LOSS'] != 0:
        price_message = f'{price_message} TrailingStop: {token_dict["_TRAILING_STOP_LOSS_PRICE"]:.6g}'
    
    if token_dict['USECUSTOMBASEPAIR'] == 'false':
        price_message = f'{price_message} - Token balance: {token_dict["_TOKEN_BALANCE"]:.4f} (= {float(token_price) * float(token_dict["_BASE_PRICE"]) * float(token_dict["_TOKEN_BALANCE"]):.2f} $)'
    else:
        price_message = f'{price_message} - Token balance: {token_dict["_TOKEN_BALANCE"]:.4f} (= {float(token_price) * float(token_dict["_TOKEN_BALANCE"]):.2f} {token_dict["BASESYMBOL"]})'
    
    if token_dict['_REACHED_MAX_TOKENS'] == True:
        price_message = f'{price_message}\033[31m - MAXTOKENS reached \033[0m'
    
    if price_message == token_dict['_LAST_PRICE_MESSAGE'] and settings['VERBOSE_PRICING'] == 'false':
        bot_settings['_NEED_NEW_LINE'] = False
    elif token_price > token_dict['_PREVIOUS_QUOTE']:
        printt_ok(price_message)
        token_dict['_TRADING_IS_ON'] = True
    elif token_price < token_dict['_PREVIOUS_QUOTE']:
        printt_err(price_message)
        token_dict['_TRADING_IS_ON'] = True
    else:
        printt(price_message)
    
    token_dict['_LAST_PRICE_MESSAGE'] = price_message

def printt_buy_price(token_dict, token_price):
    #     Function: printt_buy_price
    #     --------------------
    #     Formatted buying information
    #
    #     token_dict - one element of the tokens{} dictionary
    #     token_price - the current price of the token we want to buy
    #
    #     returns: nothing
    
    printt_sell_price(token_dict, token_price)


def save_settings(settings, pwd):
    if len(pwd) > 0:
        encrypted_settings = settings.copy()
        encrypted_settings['LIMITWALLETPRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['LIMITWALLETPRIVATEKEY'], pwd)
        encrypted_settings['PRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY'], pwd)
        if settings['PRIVATEKEY2'] != 'null':
            encrypted_settings['PRIVATEKEY2'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY2'], pwd)
        if settings['PRIVATEKEY3'] != 'null':
            encrypted_settings['PRIVATEKEY3'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY3'], pwd)
        if settings['PRIVATEKEY4'] != 'null':
            encrypted_settings['PRIVATEKEY4'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY4'], pwd)
        if settings['PRIVATEKEY5'] != 'null':
            encrypted_settings['PRIVATEKEY5'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY5'], pwd)
    
    # TODO: MASSAGE OUTPUT - LimitSwap currently loads settings.json as a [0] element, so we need to massage our
    #                  settings.json output so that it's reasable. This should probably be fixed by us importing
    #                  the entire json file, instead of just the [0] element.
    
    print(timestamp(), "Writing settings to file.")
    
    if settings['ENCRYPTPRIVATEKEYS'] == "true":
        output_settings = encrypted_settings
    else:
        output_settings = settings
    
    with open(command_line_args.settings, 'w') as f:
        f.write("[\n")
        f.write(json.dumps(output_settings, indent=4))
        f.write("\n]\n")


def load_settings_file(settings_path, load_message=True):
    # Function: load_settings_file
    # ----------------------------
    # loads the settings file defined by command_line_args.settings, sets sane defaults if variables aren't found in settings file
    # exits with an error message if necessary variables are not found in the settings files
    #
    # settings_path = the path of the file to load settings from
    #
    # returns: a dictionary with the settings from the file loaded
    
    if load_message == True:
        print(timestamp(), "Loading settings from", settings_path)
    
    with open(settings_path, ) as js_file:
        f = jsmin(js_file.read())
    all_settings = json.loads(f)
    
    settings = bot_settings = {}
    
    # Walk all settings and find the first exchange settings. This will keep us backwards compatible
    for settings_set in all_settings:
        if 'EXCHANGE' in settings_set:
            settings = settings_set
        elif 'EXCHANGE' not in settings_set:
            bot_settings = settings_set
    
    #
    # INITIALIZE BOT SETTINGS
    #
    
    if len(bot_settings) > 0:
        print(timestamp(), "Global settings detected in settings.json.")
    
    # There are values that we will set internally. They must all begin with _
    # _NEED_NEW_LINE - set to true when the next printt statement will need to print a new line before data
    
    default_true_settings = [
    ]
    
    program_defined_values = {
        '_NEED_NEW_LINE': False
    }
    
    for default_true in default_true_settings:
        if default_true not in settings:
            print(timestamp(), default_true,
                  "not found in settings.json, settings a default value of false.")
            bot_settings[default_true] = "true"
        else:
            bot_settings[default_true] = bot_settings[default_true].lower()
    for value in program_defined_values:
        if value not in bot_settings: bot_settings[value] = program_defined_values[value]
    
    #
    # INITIALIZE EXCHANGE SETTINGS
    #
    
    if len(settings) == 0:
        print(timestamp(), "No exchange settings found in settings.json. Exiting.")
        exit(11)
    
    default_false_settings = [
        'UNLIMITEDSLIPPAGE',
        'USECUSTOMNODE',
        'PASSWORD_ON_CHANGE',
        'SLOW_MODE',
        'START_BUY_AFTER_TIMESTAMP',
        'START_SELL_AFTER_TIMESTAMP',
        'ENABLE_APPRISE_NOTIFICATIONS'
    ]
    
    default_true_settings = [
        'PREAPPROVE',
        'VERBOSE_PRICING'
    ]
    
    # These settings must be defined by the user and we will lower() them
    required_user_settings = [
        'EXCHANGE'
    ]
    
    for default_false in default_false_settings:
        if default_false not in settings:
            print(timestamp(), default_false, "not found in settings.json, settings a default value of false.")
            settings[default_false] = "false"
        else:
            settings[default_false] = settings[default_false].lower()
    
    for default_true in default_true_settings:
        if default_true not in settings:
            print(timestamp(), default_true, "not found in settings.json, settings a default value of true.")
            settings[default_true] = "true"
        else:
            settings[default_true] = settings[default_true].lower()
    
    # Keys that must be set
    for required_setting in required_user_settings:
        if required_setting not in settings:
            print(timestamp(), "ERROR:", required_setting, "not found in settings.json")
            exit(-1)
        else:
            settings[required_setting] = settings[required_setting].lower()
    
    return bot_settings, settings


def decode_key(client):
    printt_debug("ENTER decode_key")
    private_key = settings['LIMITWALLETPRIVATEKEY']
    acct = client.eth.account.privateKeyToAccount(private_key)
    addr = acct.address
    return addr


def auth(Web3):
    my_provider2 = 'https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161'
    client2 = Web3(Web3.HTTPProvider(my_provider2))
    print(timestamp(), "Connected to ETH to check your LIMIT tokens =", client2.isConnected())
    address = Web3.toChecksumAddress("0x1712aad2c773ee04bdc9114b32163c058321cd85")
    abi = standardAbi
    balanceContract = client2.eth.contract(address=address, abi=abi)
    decimals = balanceContract.functions.decimals().call()
    DECIMALS = 10 ** decimals
    
    # Exception for incorrect Key Input
    try:
        decode = decode_key(client2)
    except Exception:
        printt_err("There is a problem with your private key: please check if it's correct. Don't enter your seed phrase !")
        sleep(10)
        sys.exit()
    
    wallet_address = Web3.toChecksumAddress(decode)
    balance = balanceContract.functions.balanceOf(wallet_address).call()
    true_balance = balance / DECIMALS
    printt("Current Tokens Staked = ", true_balance, write_to_log=False)
    return true_balance


def apprise_notification(token, parameter):
    printt_debug("ENTER pushsafer_notification")
    
    apobj = apprise.Apprise()
    
    if settings['APPRISE_PARAMETERS'] == "":
        printt_err("APPRISE_PARAMETERS setting is missing - please enter it")
        return
    
    apprise_parameter = settings['APPRISE_PARAMETERS']
    printt_debug("apprise_parameter:", apprise_parameter)
    for key in apprise_parameter:
        apobj.add(key)
    
    try:
        if parameter == 'buy_success':
            message = "Your " + token['SYMBOL'] + " buy Tx is confirmed. Price : " + str("{:.10f}".format(token['_QUOTE']))
            title = "BUY Success"
            
            apobj.notify(
                body=message,
                title=title,
            )
        
        elif parameter == 'buy_failure':
            message = "Your " + token['SYMBOL'] + " buy Tx failed"
            title = "BUY Failure"
            
            apobj.notify(
                body=message,
                title=title,
            )
        
        elif parameter == 'sell_success':
            message = "Your " + token['SYMBOL'] + " sell Tx is confirmed. Price : " + str("{:.10f}".format(token['_QUOTE']))
            title = "SELL Success"
            
            apobj.notify(
                body=message,
                title=title,
            )
        
        elif parameter == 'sell_failure':
            message = "Your " + token['SYMBOL'] + " sell Tx failed"
            title = "SELL Failure"
            
            apobj.notify(
                body=message,
                title=title,
            )
    
    
    except Exception as ee:
        printt_err("APPRISE - an Exception occured : check your logs")
        logging.exception(ee)

def get_file_modified_time(file_path, last_known_modification=0):
    modified_time = os.path.getmtime(file_path)
    
    if modified_time != 0 and last_known_modification == modified_time:
        printt_debug(file_path, "has been modified.")
    
    return last_known_modification

def reload_bot_settings(bot_settings_dict):
    # Function: reload_settings_file()
    # ----------------------------
    # Reloads and/or initializes settings that need to be updated when run is re-executed.
    # See load_settings_file for the details of these attributes
    #
    program_defined_values = {
        '_NEED_NEW_LINE': False,
        '_QUERIES_PER_SECOND': 'Unknown'
    }
    
    for value in program_defined_values:
        bot_settings_dict[value] = program_defined_values[value]


def parse_wallet_settings(settings, pwd):
    # Function: load_wallet_settings
    # ----------------------------
    # Handles the process of deciding whether or not the user's private key needs to be decrypted
    # Accepts user input for new private keys and wallet addresses
    #
    # returns: none (exits on incorrect password)
    
    settings_changed = False
    
    # Check for limit wallet information
    if " " in settings['LIMITWALLETADDRESS'] or settings['LIMITWALLETADDRESS'] == "":
        settings_changed = True
        settings['LIMITWALLETADDRESS'] = input("Please provide the wallet address where you have your LIMIT: ")
    
    # Check for limit wallet private key
    if " " in settings['LIMITWALLETPRIVATEKEY'] or settings['LIMITWALLETPRIVATEKEY'] == "":
        settings_changed = True
        settings['LIMITWALLETPRIVATEKEY'] = input("Please provide the private key for the wallet where you have your LIMIT: ")
    
    # If the limit wallet private key is already set and encrypted, decrypt it
    elif settings['LIMITWALLETPRIVATEKEY'].startswith('aes:'):
        printt("Decrypting limit wallet private key.")
        settings['LIMITWALLETPRIVATEKEY'] = settings['LIMITWALLETPRIVATEKEY'].replace('aes:', "", 1)
        settings['LIMITWALLETPRIVATEKEY'] = cryptocode.decrypt(settings['LIMITWALLETPRIVATEKEY'], pwd)
        
        if settings['LIMITWALLETPRIVATEKEY'] == False:
            printt_err("ERROR: Your private key decryption password is incorrect")
            printt_err("Please re-launch the bot and try again")
            sleep(10)
            sys.exit()
    
    # Check for trading wallet information
    if " " in settings['WALLETADDRESS'] or settings['WALLETADDRESS'] == "":
        settings_changed = True
        settings['WALLETADDRESS'] = input("Please provide the wallet address for your trading wallet: ")
    
    # Check for trading wallet private key
    if " " in settings['PRIVATEKEY'] or settings['PRIVATEKEY'] == "":
        settings_changed = True
        settings['PRIVATEKEY'] = input("Please provide the private key for the wallet you want to trade with: ")
    
    # If the trading wallet private key is already set and encrypted, decrypt it
    elif settings['PRIVATEKEY'].startswith('aes:'):
        print(timestamp(), "Decrypting trading wallet private key.")
        settings['PRIVATEKEY'] = settings['PRIVATEKEY'].replace('aes:', "", 1)
        settings['PRIVATEKEY'] = cryptocode.decrypt(settings['PRIVATEKEY'], pwd)
    
    # add of 2nd wallet
    if settings['WALLETADDRESS2'] == 'no_utility' or settings['PRIVATEKEY2'].startswith('aes:'):
        stoptheprocess = 1
    else:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to add a 2nd wallet to use MULTIPLEBUYS feature? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS2'] or settings['WALLETADDRESS2'] == "null":
                settings_changed = True
                settings['WALLETADDRESS2'] = input("Please provide the 2nd trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY2'] or settings['PRIVATEKEY2'] == "null":
                settings_changed = True
                settings['PRIVATEKEY2'] = input("Please provide the 2nd private key for the 2nd trading wallet: ")
            stoptheprocess = 0
        else:
            settings['WALLETADDRESS2'] = "no_utility"
            stoptheprocess = 1
    
    # add of 3nd wallet
    if stoptheprocess != 1:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to a 3rd wallet to use MULTIPLEBUYS feature ? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS3'] or settings['WALLETADDRESS3'] == "null":
                settings_changed = True
                settings['WALLETADDRESS3'] = input("Please provide the 3rd trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY3'] or settings['PRIVATEKEY3'] == "null":
                settings_changed = True
                settings['PRIVATEKEY3'] = input("Please provide the 3rd private key for the 3rd trading wallet: ")
            stoptheprocess = 0
        else:
            stoptheprocess = 1
    
    # add of 4th wallet
    if stoptheprocess != 1:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to a 4th wallet to use MULTIPLEBUYS feature ? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS4'] or settings['WALLETADDRESS4'] == "null":
                settings_changed = True
                settings['WALLETADDRESS4'] = input("Please provide the 4th trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY4'] or settings['PRIVATEKEY4'] == "null":
                settings_changed = True
                settings['PRIVATEKEY4'] = input("Please provide the 4th private key for the 4th trading wallet: ")
            stoptheprocess = 0
        else:
            stoptheprocess = 1
    
    # add of 5th wallet
    if stoptheprocess != 1:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to a 5th wallet to use MULTIPLEBUYS feature ? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS5'] or settings['WALLETADDRESS5'] == "null":
                settings_changed = True
                settings['WALLETADDRESS5'] = input("Please provide the 5th trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY5'] or settings['PRIVATEKEY5'] == "null":
                settings_changed = True
                settings['PRIVATEKEY5'] = input("Please provide the 5th private key for the 5th trading wallet: ")
    
    if settings_changed == True:
        save_settings(settings, pwd)
    print(style.RESET + " ")


def token_list_report(tokens, all_pairs=False):
    # Function: token_list_report
    # ----------------------------
    # takes our tokens and reports on the ones that are still enabled
    #
    # tokens: array of dicts representing the tokens to trade in the format absorbed by load_tokens_file
    # all_pairs: If False (default) reports all enabled pairs - if True reports on all pairs
    #
    # returns: an array of all SYMBOLS we are trading
    
    token_list = ""
    tokens_trading = 0
    
    for token in tokens:
        if all_pairs == True or token["ENABLED"] == 'true':
            tokens_trading += 1
            if token_list != "":
                token_list = token_list + " "
            if token['USECUSTOMBASEPAIR'] == 'false':
                token_list = token_list + token['_PAIR_SYMBOL']
            else:
                token_list = token_list + token['_PAIR_SYMBOL']
    
    if all_pairs == False:
        printt("Quantity of tokens attempting to trade:", tokens_trading, "(", token_list, ")")
    else:
        printt("Quantity of tokens attempting to trade:", len(tokens), "(", token_list, ")")

def check_release():
    try:
        url = 'https://api.github.com/repos/tsarbuig/LimitSwap/releases/latest'
        r = (requests.get(url).json()['tag_name'] + '\n')
        printt("Checking Latest Release Version on Github, Please Make Sure You are Staying Updated = ", r, write_to_log=True)
    except Exception:
        r = "github api down, please ignore"
    
    return r


def get_password():
    # Function: get_password
    # ----------------------------
    # Handles the decision making logic concerning private key encryption and asking the user for their password.
    #
    # returns: the user's password
    
    settings_changed = False
    setnewpassword = False
    
    # Check to see if the user has a version of the settings file before private key encryption existed
    if 'ENCRYPTPRIVATEKEYS' not in settings:
        response = ""
        settings_changed = True
        while response != "y" and response != "n":
            print("\nWould you like to use a password to encrypt your private keys?")
            response = input("You will need to input this password each time LimitSwap is executed (y/n): ")
        
        if response == "y":
            settings['ENCRYPTPRIVATEKEYS'] = "true"
            setnewpassword = True
        else:
            settings['ENCRYPTPRIVATEKEYS'] = "false"
            
            # If the user wants to encrypt their private keys, but we don't have an encrypted private key recorded, we need to ask for a password
    elif settings['ENCRYPTPRIVATEKEYS'] == "true" and not settings['PRIVATEKEY'].startswith('aes:'):
        print("\nPlease create a password to encrypt your private keys.")
        setnewpassword = True
    
    # Set a new password when necessary
    if setnewpassword == True:
        settings_changed = True
        passwords_differ = True
        while passwords_differ:
            pwd = pwinput.pwinput(prompt="\nType your new password: ")
            pwd2 = pwinput.pwinput(prompt="\nType your new password again: ")
            
            if pwd != pwd2:
                print("Error, password mismatch. Try again.")
            else:
                passwords_differ = False
    
    # The user already has encrypted private keys. Accept a password so we can unencrypt them
    elif settings['ENCRYPTPRIVATEKEYS'] == "true":
        
        if command_line_args.password:
            pwd = command_line_args.password
        else:
            pwd = pwinput.pwinput(prompt="\nPlease specify the password to decrypt your keys: ")
    
    else:
        pwd = ""
    
    if not pwd.strip():
        print()
        print("X WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING=-= WARNING X")
        print("X       You are running LimitSwap without encrypting your private keys.          X")
        print("X     Private keys are stored on disk unencrypted and can be accessed by         X")
        print("X anyone with access to the file system, including the Systems/VPS administrator X")
        print("X       and anyone with physical access to the machine or hard drives.           X")
        print("X WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING=-= WARNING X")
        print()
    
    if settings_changed == True:
        save_settings(settings, pwd)
    
    return pwd


# RUGDOC CONTROL IMPLEMENTATION
# Rugdoc's answers interpretations
#

interpretations = {
    "UNKNOWN": (style.RED + 'The status of this token is unknown. '
                            '                           This is usually a system error but could also be a bad sign for the token. Be careful.'),
    "OK": (style.GREEN + 'RUGDOC API RESULT : OK \n'
                         '                           √ Honeypot tests passed. RugDoc program was able to buy and sell it successfully. This however does not guarantee that it is not a honeypot.'),
    "NO_PAIRS": (style.RED + 'RUGDOC API RESULT : NO_PAIRS \n'
                             '                           ⚠ Could not find any trading pair for this token on the default router and could thus not test it.'),
    "SEVERE_FEE": (style.RED + 'RUGDOC API RESULT : SEVERE_FEE \n'
                               '                           /!\ /!\ A severely high trading fee (over 50%) was detected when selling or buying this token.'),
    "HIGH_FEE": (style.YELLOW + 'RUGDOC API RESULT : HIGH_FEE \n'
                                '                           /!\ /!\ A high trading fee (Between 20% and 50%) was detected when selling or buying this token. Our system was however able to sell the token again.'),
    "MEDIUM_FEE": (style.YELLOW + 'RUGDOC API RESULT : MEDIUM_FEE \n'
                                  '                           /!\ A trading fee of over 10% but less then 20% was detected when selling or buying this token. Our system was however able to sell the token again.'),
    "APPROVE_FAILED": (style.RED + 'RUGDOC API RESULT : APPROVE_FAILED \n'
                                   '                           /!\ /!\ /!\ Failed to approve the token.\n This is very likely a honeypot.'),
    "SWAP_FAILED": (style.RED + 'RUGDOC API RESULT : SWAP_FAILED \n'
                                '                           /!\ /!\ /!\ Failed to sell the token. \n This is very likely a honeypot.'),
    "chain not found": (style.RED + 'RUGDOC API RESULT : chain not found \n'
                                    '                           /!\ Sorry, rugdoc API does not work on this chain... (it does not work on ETH, mainly) \n')
}

"""""""""""""""""""""""""""
//PRELOAD
"""""""""""""""""""""""""""
print(timestamp(), "Preloading Data")
bot_settings, settings = load_settings_file(command_line_args.settings)

directory = './abi/'
filename = "standard.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    standardAbi = json.load(json_file)

directory = './abi/'
filename = "lp.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    lpAbi = json.load(json_file)

directory = './abi/'
filename = "router.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    routerAbi = json.load(json_file)

directory = './abi/'
filename = "factory2.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    factoryAbi = json.load(json_file)

directory = './abi/'
filename = "koffee.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    koffeeAbi = json.load(json_file)

directory = './abi/'
filename = "pangolin.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    pangolinAbi = json.load(json_file)

directory = './abi/'
filename = "joeRouter.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    joeRouter = json.load(json_file)

directory = './abi/'
filename = "bakeryRouter.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    bakeryRouter = json.load(json_file)

directory = './abi/'
filename = "protofiabi.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    protofiabi = json.load(json_file)

directory = './abi/'
filename = "protofirouter.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    protofirouter = json.load(json_file)

"""""""""""""""""""""""""""
// LOGGING
"""""""""""""""""""""""""""
os.makedirs('./logs', exist_ok=True)

# define dd/mm/YY date to create  logging files with date of the day
# get current date and time
current_datetime = datetime.today().strftime("%Y-%m-%d")
str_current_datetime = str(current_datetime)
# create an LOGS file object along with extension
file_name = "./logs/logs-" + str_current_datetime + ".log"
if not os.path.exists(file_name):
    open(file_name, 'w').close()

# create an EXCEPTIONS file object along with extension
file_name2 = "./logs/exceptions-" + str_current_datetime + ".log"
if not os.path.exists(file_name2):
    open(file_name2, 'w').close()

log_format = '%(levelname)s: %(asctime)s %(message)s'
logging.basicConfig(filename=file_name,
                    level=logging.INFO,
                    format=log_format)

logger1 = logging.getLogger('1')
logger1.addHandler(logging.FileHandler(file_name2))

printt("**********************************************************************************************************************", write_to_log=True)
printt("For Help & To Learn More About how the bot works please visit our wiki here: https://cryptognome.gitbook.io/limitswap/", write_to_log=False)
printt("**********************************************************************************************************************", write_to_log=False)

