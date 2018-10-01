import os
import time
import re
import logging
from slackclient import SlackClient
from urllib import urlopen
from dotenv import Dotenv
import json
import signal
# Of course, replace by your correct path
dotenv = Dotenv(os.path.join(os.path.dirname(__file__), ".env"))
os.environ.update(dotenv)
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# kbot's user ID in Slack: value is assigned after the bot starts up
kbot_id = None

logging.basicConfig(filename='log.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
PING_COMMAND = "ping"
HELP_COMMAND = "help"
CHOC_COMMAND = "choc"
BOTS_COMMAND = "bots"
EXIT_COMMAND = "exit"
WEATHER_COMMAND = 'weather'
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
exit_flag = False
start_time = time.time()
logged_in = True

def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals
    can be mapped here as well (SIGHUP?)
    Basically it just sets a global flag, and main() will exit
    it's loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """

    global logged_in
    if sig_num == signal.SIGINT:
        logging.warning(" SIGINT recieved from the os: program interrupted")
        logged_in = False
    elif sig_num == signal.SIGTERM:
        logging.warning(" SIGTERM recieved from the os: program terminated")
        logged_in = False
    elif sig_num == signal.SIGKILL:
        logging.warning(" SIGKILL recieved from the os: program terminated")
        logged_in = False    

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == kbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning)
        in message text and returns the user ID which was mentioned.
        If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(HELP_COMMAND)
    # Finds and executes the given command, filling in response
    response = None
    logging.info('Command: {}'.format(command))
    # This is where you start to implement more commands!
    if command.startswith(HELP_COMMAND):
        response = "choc - displays chocolate emoji\nping - ping kitkat bot" \
                    +"\nbots - displays all the slack bots" \
                    +"\nweather - dispalys todays weather in Indy\nexit - exits" 
    elif command.startswith(CHOC_COMMAND):
        response = ":chocolate_bar:"
    elif command.startswith(BOTS_COMMAND):
        response = ''
        request = slack_client.api_call("users.list")
        if request['ok']:
            for item in request['members']:
                if item['is_bot']:
                    response = response + item['name'] + "\n"
    elif command.startswith(EXIT_COMMAND):
        # slack_client.api_call("channels.leave")
        response = "Bye Bye"
        global exit_flag
        exit_flag = True
    elif command.startswith(PING_COMMAND):
        response = "Uptime {}".format(time.time() - start_time)
    elif command.startswith(WEATHER_COMMAND):
        baseurl = "https://query.yahooapis.com/v1/public/yql?"
        yql_url = baseurl + "q=select* from weather.forecast " \
              "where woeid = 2427032 &format=json"
        result = urlopen(yql_url).read()
        data = json.loads(result)
        response = getWeatherDetails(data)
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def getWeatherDetails(data):
    query = data.get('query')
    if query is None:
        return {}
    result = query.get('results')
    if result is None:
        return {}
    channel = result.get('channel')
    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    condition = item.get('condition')
    link = item.get('link')
    url = link.split('/*')
    res = "Today in " + location.get('city') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature') + \
             ", " + url[-1]

    return res

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    while logged_in:
        try:
            if slack_client.rtm_connect(with_team_state=False):
                logging.info("KitKat Bot connected and running!")
                # Read bot's user ID by calling Web API method `auth.test`
                kbot_id = slack_client.api_call("auth.test")["user_id"]
                while not exit_flag:
                    command, channel = parse_bot_commands(slack_client.rtm_read())
                    if command:
                        handle_command(command, channel)
                    time.sleep(RTM_READ_DELAY)           
            else:
                print("Connection failed. Exception traceback printed above.")
        except Exception as e:
            logging.error(e)
            logging.info("Connection error, will retry in 5 seconds")
            time.sleep(5)
    logging.info("KitKat Bot disconnected!")