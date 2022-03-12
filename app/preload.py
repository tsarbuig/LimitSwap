import signal
import argparse
from time import sleep, time
from datetime import datetime
from jsmin import jsmin
import json
import os
import logging
import sys

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

def load_tokens_file(tokens_path, load_message=True):
    # Function: load_tokens_File
    # ----------------------------
    # loads the token definition file defined by command_line_args.settings, sets sane defaults if variables aren't found in settings file
    # exits with an error message if necessary variables are not found in the settings files
    #
    # IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE
    # Any additional options added to this function must also be considered for change in reload_tokens_file()
    #
    # tokens_path: the path of the file to load tokens from
    # load_message: if true we print to stdout that we're loading settings from the file
    # last_modified: perform this function only if he file has been modified since this date
    #
    # returns: 1. a dictionary of dictionaries in json format containing details of the tokens we're rading
    #          2. the timestamp for the last modification of the file
    
    # Any new token configurations that are added due to "WATCH_STABLES_PAIRS" configuration will be added to this array. After we are done
    # loading all settings from tokens.json, we'll append this list to the token list
    
    printt_debug("ENTER load_tokens_file")
    
    global set_of_new_tokens
    
    if load_message == True:
        print(timestamp(), "Loading tokens from", tokens_path)
    
    with open(tokens_path, ) as js_file:
        t = jsmin(js_file.read())
    tokens = json.loads(t)
    
    required_user_settings = [
        'ADDRESS',
        'BUYAMOUNTINBASE',
        'BUYPRICEINBASE',
        'SELLPRICEINBASE'
    ]
    
    default_true_settings = [
        'LIQUIDITYINNATIVETOKEN'
    ]
    
    default_false_settings = [
        'ENABLED',
        'USECUSTOMBASEPAIR',
        'HASFEES',
        'RUGDOC_CHECK',
        'MULTIPLEBUYS',
        'KIND_OF_SWAP',
        'ALWAYS_CHECK_BALANCE',
        'WAIT_FOR_OPEN_TRADE',
        'WATCH_STABLES_PAIRS'
    ]
    
    default_value_settings = {
        'SLIPPAGE': 49,
        'BUYAMOUNTINTOKEN': 0,
        'MAXTOKENS': 0,
        'MOONBAG': 0,
        'MINIMUM_LIQUIDITY_IN_DOLLARS': 10000,
        'MAX_BASE_AMOUNT_PER_EXACT_TOKENS_TRANSACTION': 0.5,
        'SELLAMOUNTINTOKENS': 'all',
        'GAS': 8,
        'MAX_GAS': 99999,
        'BOOSTPERCENT': 50,
        'GASLIMIT': 1000000,
        'BUYAFTER_XXX_SECONDS': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX': 0,
        'MAX_FAILED_TRANSACTIONS_IN_A_ROW': 2,
        'MAX_SUCCESS_TRANSACTIONS_IN_A_ROW': 2,
        'GASPRIORITY_FOR_ETH_ONLY': 1.5,
        'STOPLOSSPRICEINBASE': 0,
        'BUYCOUNT': 0,
        'TRAILING_STOP_LOSS': 0,
        'ANTI_DUMP_PRICE': 0,
        'PINKSALE_PRESALE_ADDRESS': "",
        '_STABLE_BASES': {}
    }
    
    # There are values that we will set internally. They must all begin with _
    # _LIQUIDITY_CHECKED    - false if we have yet to check liquidity for this token
    # _INFORMED_SELL        - set to true when we've already informed the user that we're selling this position
    # _LIQUIDITY_READY      - a flag to test if we've found liquidity for this pair
    # _LIQUIDITY_CHECKED    - a flag to test if we've check for the amount of liquidity for this pair
    # _INFORMED_SELL        - a flag to store that we've printed to console that we are going to be selling the position
    # _REACHED_MAX_TOKENS   - flag to look at to determine if the user's wallet has reached the maximum number of flags
    #                         this flag is used for conditionals throughout the run of this bot. Be sure to set this
    #                         flag after enough tokens that brings the number of token up to the MAXTOKENS. In other words
    #                         done depend on (if MAXTOKENS < _TOKEN_BALANCE) conditionals
    # _NOT_ENOUGH_TO_BUY    - if user does not have enough base pair in his wallet to buy
    # _GAS_TO_USE           - the amount of gas the bot has estimated it should use for the purchase of a token
    #                         this number is calculated every bot start up
    # _FAILED_TRANSACTIONS  - the number of times a transaction has failed for this token
    # _SUCCESS_TRANSACTIONS - the number of times a transaction has succeeded for this token
    # _REACHED_MAX_SUCCESS_TX  - flag to look at to determine if the user's wallet has reached the maximum number of flags
    #                         this flag is used for conditionals throughout the run of this bot. Be sure to set this
    #                         flag after enough tokens that brings the number of token up to the MAX_SUCCESS_TRANSACTIONS_IN_A_ROW. In other words
    #                         done depend on (if MAX_SUCCESS_TRANSACTIONS_IN_A_ROW < _REACHED_MAX_SUCCESS_TX) conditionals
    # _TRADING_IS_ON        - defines if trading is ON of OFF on a token. Used with WAIT_FOR_OPEN_TRADE parameter
    # _RUGDOC_DECISION      - decision of the user after RugDoc API check
    # _TOKEN_BALANCE        - the number of traded tokens the user has in his wallet
    # _PREVIOUS_TOKEN_BALANCE - the number of traded tokens the user has in his wallet before BUY order
    # _IN_TOKEN             - _IN_TOKEN is the token you want to BUY (example : CAKE)
    # _OUT_TOKEN            - _OUT_TOKEN is the token you want to TRADE WITH (example : ETH or USDT)
    # _BASE_BALANCE         - balance of Base token, calculated at bot launch and after a BUY/SELL
    # _BASE_PRICE           - price of Base token, calculated at bot launch with calculate_base_price
    # _BASE_USED_FOR_TX     - amount of base balance used to make the Tx transaction
    # _PAIR_TO_DISPLAY      - token symbol / base symbol
    # _CUSTOM_BASE_BALANCE  - balance of Custom Base token, calculated at bot launch and after a BUY/SELL
    # _QUOTE                - holds the token's quote
    # _PREVIOUS_QUOTE       - holds the ask price for a token the last time a price was queried, this is used
    #                         to determine the direction the market is going
    # _LISTING_QUOTE        - Listing price of a token
    # _BUY_THE_DIP_ACTIVE   - Price has reached 50% of listing price and we're ready to buy the dip
    # _COST_PER_TOKEN       - the calculated/estimated price the bot paid for the number of tokens it traded
    # _CALCULATED_SELLPRICEINBASE           - the calculated sell price created with build_sell_conditions()
    # _CALCULATED_STOPLOSSPRICEINBASE       - the calculated stoploss price created with build_sell_conditions()
    # _ALL_TIME_HIGH        - the highest price a token has had since the bot was started
    # _ALL_TIME_LOW         - the lowest price a token has had since the bot was started
    # _CONTRACT_DECIMALS    - the number of decimals a contract uses. Used to speed up some of our processes
    #                         instead of querying the contract for the same information repeatedly.
    # _BASE_DECIMALS        - the number of decimals of custom base pair. Used to speed up some of our processes
    #                         instead of querying the contract for the same information repeatedly.
    # _WETH_DECIMALS        - the number of decimals of weth.
    # _LIQUIDITY_DECIMALS   - the number of decimals of liquidity.
    # _LAST_PRICE_MESSAGE   - a copy of the last pricing message printed to console, used to determine the price
    #                         should be printed again, or just a dot
    # _LAST_MESSAGE         - a place to store a copy of the last message printed to conside, use to avoid
    #                         repeated liquidity messages
    # _GAS_IS_CALCULATED    - if gas needs to be calculated by wait_for_open_trade, this parameter is set to true
    # _EXCHANGE_BASE_SYMBOL - this is the symbol for the base that is used by the exchange the token is trading on
    # _PAIR_SYMBOL          - the symbol for this TOKEN/BASE pair
    
    program_defined_values = {
        '_LIQUIDITY_READY': False,
        '_LIQUIDITY_CHECKED': False,
        '_INFORMED_SELL': False,
        '_REACHED_MAX_TOKENS': False,
        '_TRADING_IS_ON': False,
        '_NOT_ENOUGH_TO_BUY': False,
        '_IN_TOKEN': "",
        '_OUT_TOKEN': "",
        '_RUGDOC_DECISION': "",
        '_GAS_TO_USE': 0,
        '_GAS_IS_CALCULATED': False,
        '_FAILED_TRANSACTIONS': 0,
        '_SUCCESS_TRANSACTIONS': 0,
        '_REACHED_MAX_SUCCESS_TX': False,
        '_TOKEN_BALANCE': 0,
        '_PREVIOUS_TOKEN_BALANCE': 0,
        '_BASE_BALANCE': 0,
        '_BASE_PRICE': calculate_base_price(),
        '_BASE_USED_FOR_TX': 0,
        '_PAIR_TO_DISPLAY': "Pair",
        '_CUSTOM_BASE_BALANCE': 0,
        '_QUOTE': 0,
        '_PREVIOUS_QUOTE': 0,
        '_LISTING_QUOTE': 0,
        '_BUY_THE_DIP_ACTIVE': False,
        '_ALL_TIME_HIGH': 0,
        '_COST_PER_TOKEN': 0,
        '_CALCULATED_SELLPRICEINBASE': 99999,
        '_CALCULATED_STOPLOSSPRICEINBASE': 0,
        '_ALL_TIME_LOW': 0,
        '_CONTRACT_DECIMALS': 0,
        '_BASE_DECIMALS': 0,
        '_WETH_DECIMALS': 0,
        '_LAST_PRICE_MESSAGE': 0,
        '_LAST_MESSAGE': 0,
        '_FIRST_SELL_QUOTE': 0,
        '_BUILT_BY_BOT': False,
        '_TRAILING_STOP_LOSS_PRICE': 0,
        '_TRAILING_STOP_LOSS_WITHOUT_PERCENT': 0,
        '_EXCHANGE_BASE_SYMBOL': settings['_EXCHANGE_BASE_SYMBOL'],
        '_PAIR_SYMBOL': ''
    }
    
    for token in tokens:
        
        # Keys that must be set
        for required_key in required_user_settings:
            if required_key not in token:
                printt_err(required_key, "not found in configuration file in configuration for to token", token['SYMBOL'])
                printt_err("Be careful, sometimes new parameter are added : please check default tokens.json file")
                sleep(20)
                exit(-1)
        
        for default_false in default_false_settings:
            if default_false not in token:
                printt_v(default_false, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of false")
                token[default_false] = "false"
            else:
                token[default_false] = token[default_false].lower()
        
        for default_true in default_true_settings:
            if default_true not in token:
                printt_v(default_true, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of true")
                token[default_true] = "true"
            else:
                token[default_true] = token[default_true].lower()
        
        for default_key in default_value_settings:
            if default_key not in token:
                printt_v(default_key, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a value of", default_value_settings[default_key])
                token[default_key] = default_value_settings[default_key]
            elif default_key == 'SELLAMOUNTINTOKENS':
                default_value_settings[default_key] = default_value_settings[default_key].lower()
        
        # Set program values only if they haven't been set already
        if '_LIQUIDITY_READY' not in token:
            for value in program_defined_values:
                token[value] = program_defined_values[value]
        
        for key in token:
            if (isinstance(token[key], str)):
                if re.search(r'^\d*\.\d+$', str(token[key])):
                    token[key] = float(token[key])
                elif re.search(r'^\d+$', token[key]):
                    token[key] = int(token[key])
        
        if token['WATCH_STABLES_PAIRS'] == 'true' and token['USECUSTOMBASEPAIR'] == 'false':
            if token['_COST_PER_TOKEN'] == 0:
                build_sell_conditions(token, 'before_buy', 'hide_message')
            else:
                build_sell_conditions(token, 'after_buy', 'hide_message')
            
            for new_token_dict in build_extended_base_configuration(token):
                set_of_new_tokens.append(new_token_dict)
        elif token['WATCH_STABLES_PAIRS'] == 'true':
            printt("")
            printt_warn("Ignoring WATCH_STABLES_PAIRS", "for", token['SYMBOL'], ": WATCH_STABLES_PAIRS = true and USECUSTOMBASEPAIR = true is unsupported.")
            printt("")
        
        if token['USECUSTOMBASEPAIR'] == 'true' and token['LIQUIDITYINNATIVETOKEN'] == 'false':
            token['_PAIR_SYMBOL'] = token['SYMBOL'] + '/' + token['BASESYMBOL']
        else:
            token['_PAIR_SYMBOL'] = token['SYMBOL'] + '/' + token['_EXCHANGE_BASE_SYMBOL']
    
    # Add any tokens generated by "WATCH_STABLES_PAIRS" to the tokens list.
    for token_dict in set_of_new_tokens:
        tokens.append(token_dict)
    return tokens

def reload_tokens_file(tokens_path, load_message=True):
    # Function: reload_tokens_File
    # ----------------------------
    # loads the token definition file defined by command_line_args.settings, sets sane defaults if variables aren't found in settings file
    # exits with an error message if necessary variables are not found in the settings files
    #
    # IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE
    # Any additional options added to this function must also be considered for change in reload_tokens_file()
    #
    # tokens_path: the path of the file to load tokens from
    # load_message: if true we print to stdout that we're loading settings from the file
    # last_modified: perform this function only if he file has been modified since this date
    #
    # returns: 1. a dictionary of dictionaries in json format containing details of the tokens we're rading
    #          2. the timestamp for the last modification of the file
    
    # Any new token configurations that are added due to "WATCH_STABLES_PAIRS" configuration will be added to this array. After we are done
    # loading all settings from tokens.json, we'll append this list to the token list
    
    printt_debug("ENTER reload_tokens_file")
    
    global _TOKENS_saved
    global set_of_new_tokens
    
    printt_debug("reload_tokens_file _TOKENS_saved:", _TOKENS_saved)
    set_of_new_tokens = []
    
    if load_message == True:
        printt("")
        printt("Reloading tokens from", tokens_path, '\033[31m', "- do NOT change token SYMBOL in real time", '\033[0m', write_to_log=True)
        printt("")
    
    with open(tokens_path, ) as js_file:
        t = jsmin(js_file.read())
    tokens = json.loads(t)
    
    required_user_settings = [
        'ADDRESS',
        'BUYAMOUNTINBASE',
        'BUYPRICEINBASE',
        'SELLPRICEINBASE'
    ]
    
    default_true_settings = [
        'LIQUIDITYINNATIVETOKEN'
    ]
    
    default_false_settings = [
        'ENABLED',
        'USECUSTOMBASEPAIR',
        'HASFEES',
        'RUGDOC_CHECK',
        'MULTIPLEBUYS',
        'KIND_OF_SWAP',
        'ALWAYS_CHECK_BALANCE',
        'WAIT_FOR_OPEN_TRADE',
        'WATCH_STABLES_PAIRS'
    ]
    
    default_value_settings = {
        'SLIPPAGE': 49,
        'BUYAMOUNTINTOKEN': 0,
        'MAXTOKENS': 0,
        'MOONBAG': 0,
        'MINIMUM_LIQUIDITY_IN_DOLLARS': 10000,
        'MAX_BASE_AMOUNT_PER_EXACT_TOKENS_TRANSACTION': 0.5,
        'SELLAMOUNTINTOKENS': 'all',
        'GAS': 8,
        'MAX_GAS': 99999,
        'BOOSTPERCENT': 50,
        'GASLIMIT': 1000000,
        'BUYAFTER_XXX_SECONDS': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX': 0,
        'MAX_FAILED_TRANSACTIONS_IN_A_ROW': 2,
        'MAX_SUCCESS_TRANSACTIONS_IN_A_ROW': 2,
        'GASPRIORITY_FOR_ETH_ONLY': 1.5,
        'STOPLOSSPRICEINBASE': 0,
        'BUYCOUNT': 0,
        'TRAILING_STOP_LOSS': 0,
        'ANTI_DUMP_PRICE': 0,
        'PINKSALE_PRESALE_ADDRESS': "",
        '_STABLE_BASES': {}
    }
    
    program_defined_values = {
        '_LIQUIDITY_READY': False,
        '_LIQUIDITY_CHECKED': False,
        '_INFORMED_SELL': False,
        '_REACHED_MAX_TOKENS': False,
        '_TRADING_IS_ON': False,
        '_RUGDOC_DECISION': "",
        '_GAS_TO_USE': 0,
        '_GAS_IS_CALCULATED': False,
        '_FAILED_TRANSACTIONS': 0,
        '_SUCCESS_TRANSACTIONS': 0,
        '_REACHED_MAX_SUCCESS_TX': False,
        '_TOKEN_BALANCE': 0,
        '_PREVIOUS_TOKEN_BALANCE': 0,
        '_BASE_BALANCE': 0,
        '_BASE_PRICE': 0,
        '_BASE_USED_FOR_TX': 0,
        '_PAIR_TO_DISPLAY': "Pair",
        '_CUSTOM_BASE_BALANCE': 0,
        '_QUOTE': 0,
        '_PREVIOUS_QUOTE': 0,
        '_LISTING_QUOTE': 0,
        '_BUY_THE_DIP_ACTIVE': False,
        '_ALL_TIME_HIGH': 0,
        '_COST_PER_TOKEN': 0,
        '_CALCULATED_SELLPRICEINBASE': 99999,
        '_CALCULATED_STOPLOSSPRICEINBASE': 0,
        '_ALL_TIME_LOW': 0,
        '_CONTRACT_DECIMALS': 0,
        '_BASE_DECIMALS': 0,
        '_WETH_DECIMALS': 0,
        '_LIQUIDITY_DECIMALS': 0,
        '_LAST_PRICE_MESSAGE': 0,
        '_LAST_MESSAGE': 0,
        '_FIRST_SELL_QUOTE': 0,
        '_BUILT_BY_BOT': False,
        '_TRAILING_STOP_LOSS_PRICE': 0,
        '_TRAILING_STOP_LOSS_WITHOUT_PERCENT': 0,
        '_EXCHANGE_BASE_SYMBOL': settings['_EXCHANGE_BASE_SYMBOL'],
        '_PAIR_SYMBOL': '',
        '_NOT_ENOUGH_TO_BUY': False,
        '_IN_TOKEN': '',
        '_OUT_TOKEN': ''
    }
    
    for token in tokens:
        
        # Keys that must be set
        for required_key in required_user_settings:
            if required_key not in token:
                printt_err(required_key, "not found in configuration file in configuration for to token", token['SYMBOL'])
                printt_err("Be careful, sometimes new parameter are added : please check default tokens.json file")
                sleep(20)
                exit(-1)
        
        for default_false in default_false_settings:
            if default_false not in token:
                printt_v(default_false, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of false")
                token[default_false] = "false"
            else:
                token[default_false] = token[default_false].lower()
        
        for default_true in default_true_settings:
            if default_true not in token:
                printt_v(default_true, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of true")
                token[default_true] = "true"
            else:
                token[default_true] = token[default_true].lower()
        
        for default_key in default_value_settings:
            if default_key not in token:
                printt_v(default_key, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a value of", default_value_settings[default_key])
                token[default_key] = default_value_settings[default_key]
            elif default_key == 'SELLAMOUNTINTOKENS':
                default_value_settings[default_key] = default_value_settings[default_key].lower()
        
        # Set program values only if they haven't been set already
        if '_LIQUIDITY_READY' not in token:
            for value in program_defined_values:
                token[value] = program_defined_values[value]
        
        for key in token:
            if (isinstance(token[key], str)):
                if re.search(r'^\d*\.\d+$', str(token[key])):
                    token[key] = float(token[key])
                elif re.search(r'^\d+$', token[key]):
                    token[key] = int(token[key])
        
        if token['WATCH_STABLES_PAIRS'] == 'true' and token['USECUSTOMBASEPAIR'] == 'false':
            if token['_COST_PER_TOKEN'] == 0:
                build_sell_conditions(token, 'before_buy', 'hide_message')
            else:
                build_sell_conditions(token, 'after_buy', 'hide_message')
            
            for new_token_dict in build_extended_base_configuration(token):
                set_of_new_tokens.append(new_token_dict)
        
        elif token['WATCH_STABLES_PAIRS'] == 'true':
            printt_warn("Ignoring WATCH_STABLES_PAIRS", "for", token['SYMBOL'], ": WATCH_STABLES_PAIRS = true and USECUSTOMBASEPAIR = true is unsupported.")
        
        if token['BUYPRICEINBASE'] == 'BUY_THE_DIP':
            token.update({
                'BUYPRICEINBASE': _TOKENS_saved[token['SYMBOL']]['BUYPRICEINBASE'],
            })
        
        token.update({
            '_LIQUIDITY_READY': _TOKENS_saved[token['SYMBOL']]['_LIQUIDITY_READY'],
            '_LIQUIDITY_CHECKED': _TOKENS_saved[token['SYMBOL']]['_LIQUIDITY_CHECKED'],
            '_INFORMED_SELL': _TOKENS_saved[token['SYMBOL']]['_INFORMED_SELL'],
            '_REACHED_MAX_TOKENS': _TOKENS_saved[token['SYMBOL']]['_REACHED_MAX_TOKENS'],
            '_TRADING_IS_ON': _TOKENS_saved[token['SYMBOL']]['_TRADING_IS_ON'],
            '_RUGDOC_DECISION': _TOKENS_saved[token['SYMBOL']]['_RUGDOC_DECISION'],
            '_GAS_TO_USE': _TOKENS_saved[token['SYMBOL']]['_GAS_TO_USE'],
            '_GAS_IS_CALCULATED': _TOKENS_saved[token['SYMBOL']]['_GAS_IS_CALCULATED'],
            '_FAILED_TRANSACTIONS': _TOKENS_saved[token['SYMBOL']]['_FAILED_TRANSACTIONS'],
            '_SUCCESS_TRANSACTIONS': _TOKENS_saved[token['SYMBOL']]['_SUCCESS_TRANSACTIONS'],
            '_REACHED_MAX_SUCCESS_TX': _TOKENS_saved[token['SYMBOL']]['_REACHED_MAX_SUCCESS_TX'],
            '_TOKEN_BALANCE': _TOKENS_saved[token['SYMBOL']]['_TOKEN_BALANCE'],
            '_PREVIOUS_TOKEN_BALANCE': _TOKENS_saved[token['SYMBOL']]['_PREVIOUS_TOKEN_BALANCE'],
            '_BASE_BALANCE': _TOKENS_saved[token['SYMBOL']]['_BASE_BALANCE'],
            '_BASE_PRICE': _TOKENS_saved[token['SYMBOL']]['_BASE_PRICE'],
            '_TRAILING_STOP_LOSS_PRICE': _TOKENS_saved[token['SYMBOL']]['_TRAILING_STOP_LOSS_PRICE'],
            '_TRAILING_STOP_LOSS_WITHOUT_PERCENT': _TOKENS_saved[token['SYMBOL']]['_TRAILING_STOP_LOSS_WITHOUT_PERCENT'],
            '_BASE_USED_FOR_TX': _TOKENS_saved[token['SYMBOL']]['_BASE_USED_FOR_TX'],
            '_PAIR_TO_DISPLAY': _TOKENS_saved[token['SYMBOL']]['_PAIR_TO_DISPLAY'],
            '_CUSTOM_BASE_BALANCE': _TOKENS_saved[token['SYMBOL']]['_CUSTOM_BASE_BALANCE'],
            '_QUOTE': _TOKENS_saved[token['SYMBOL']]['_QUOTE'],
            '_PREVIOUS_QUOTE': _TOKENS_saved[token['SYMBOL']]['_PREVIOUS_QUOTE'],
            '_LISTING_QUOTE': _TOKENS_saved[token['SYMBOL']]['_LISTING_QUOTE'],
            '_BUY_THE_DIP_ACTIVE': _TOKENS_saved[token['SYMBOL']]['_BUY_THE_DIP_ACTIVE'],
            '_ALL_TIME_HIGH': _TOKENS_saved[token['SYMBOL']]['_ALL_TIME_HIGH'],
            '_COST_PER_TOKEN': _TOKENS_saved[token['SYMBOL']]['_COST_PER_TOKEN'],
            '_CALCULATED_SELLPRICEINBASE': _TOKENS_saved[token['SYMBOL']]['_CALCULATED_SELLPRICEINBASE'],
            '_CALCULATED_STOPLOSSPRICEINBASE': _TOKENS_saved[token['SYMBOL']]['_CALCULATED_STOPLOSSPRICEINBASE'],
            '_ALL_TIME_LOW': _TOKENS_saved[token['SYMBOL']]['_ALL_TIME_LOW'],
            '_CONTRACT_DECIMALS': _TOKENS_saved[token['SYMBOL']]['_CONTRACT_DECIMALS'],
            '_BASE_DECIMALS': _TOKENS_saved[token['SYMBOL']]['_BASE_DECIMALS'],
            '_WETH_DECIMALS': _TOKENS_saved[token['SYMBOL']]['_WETH_DECIMALS'],
            '_LIQUIDITY_DECIMALS': _TOKENS_saved[token['SYMBOL']]['_LIQUIDITY_DECIMALS'],
            '_LAST_PRICE_MESSAGE': _TOKENS_saved[token['SYMBOL']]['_LAST_PRICE_MESSAGE'],
            '_LAST_MESSAGE': _TOKENS_saved[token['SYMBOL']]['_LAST_MESSAGE'],
            '_FIRST_SELL_QUOTE': _TOKENS_saved[token['SYMBOL']]['_FIRST_SELL_QUOTE'],
            '_BUILT_BY_BOT': _TOKENS_saved[token['SYMBOL']]['_BUILT_BY_BOT'],
            '_EXCHANGE_BASE_SYMBOL': _TOKENS_saved[token['SYMBOL']]['_EXCHANGE_BASE_SYMBOL'],
            '_PAIR_SYMBOL': _TOKENS_saved[token['SYMBOL']]['_PAIR_SYMBOL'],
            '_IN_TOKEN': _TOKENS_saved[token['SYMBOL']]['_IN_TOKEN'],
            '_OUT_TOKEN': _TOKENS_saved[token['SYMBOL']]['_OUT_TOKEN'],
            '_NOT_ENOUGH_TO_BUY': _TOKENS_saved[token['SYMBOL']]['_NOT_ENOUGH_TO_BUY']
        })
    
    # Add any tokens generated by "WATCH_STABLES_PAIRS" to the tokens list.
    for token_dict in set_of_new_tokens:
        tokens.append(token_dict)
    
    printt_debug("tokens after reload:", tokens)
    printt_debug("EXIT reload_tokens_file")
    return tokens

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

