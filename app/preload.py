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

