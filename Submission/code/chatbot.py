from irc import *
from util import *
from idiom_parser import *

active_users = []
irc : IRC = IRC()
idioms = Idioms()

'''
Helper functions to parse received messages
'''
def handle_users_list(input: str):
    _, users_temp = input.split(":", 2) 
    users_list = users_temp.split()
    for user in users_list:
        if user not in active_users and user != DEFAULT_NICKNAME:
            active_users.append(user)

def handle_join(input: str):
    user = parse_sender(input)
    if user not in active_users and user != DEFAULT_NICKNAME:
        active_users.append(user)

def handle_quit(input: str):
    user = parse_sender(input)
    if user in active_users:
        active_users.remove(user)

def handle_privmsg(sender: str, input: str) -> tuple[str, str]|None:
    global active_users

    try:
        addressee, _ = parse_addressee(input)

        ## If meant for us, continue
        if addressee == DEFAULT_NICKNAME:
            pass
        # If not for us, return None
        else:
            print("Not addressed to this chatbot")
            return
        
        sender = parse_sender(sender)
        return sender, input
    
    except Exception as e:
        print("Improper chatbot command, violates, 'botname-bot: [command]'")
        return

def parse_txt(input_txt : str) -> tuple[str, str] | None:
    '''
    Given a full response from IRC, prase the txt
    '''
    mult_lines = input_txt.splitlines()
    for line in mult_lines:
        parsed = parse_line(line)
        if not parsed:
            continue

        sender, msg_type, chanenl, rest = parsed
            
        match msg_type:
            case "JOIN": 
                handle_join(sender)
            case "QUIT":    
                handle_quit(sender)
            case "PRIVMSG": 
                return sender, rest
            case "353": 
                handle_users_list(rest) 
            case _:
                continue

def handle_specific_msg(sender: str, specific_msg: str):
    global active_users

    ## high potential to revamp handling of finding commands
    _, msg_only = parse_addressee(specific_msg)

    msg_cleaned = msg_only.strip().lower()
    handled = False

    words = nltk.word_tokenize(msg_cleaned)

    if "hi" in words or "hello" in words:
        print("Received proper greeting command")
        irc.send("Hey!", sender)
        handled = True

    if "usage" in words or "who are you?" in words:
        print("Received proper 'usage' command")
        irc.send(f"{WHO_AM_I}", sender)
        
        for line in USAGE_MSG_2:
            irc.send(f"{line}", sender)
        handled = True

    if "users" in words:
        print("Received proper 'users' command")
        irc.send(f"{active_users}", sender)
        handled = True

    # to be updated
    if "forget" in words:
        print("Received proper 'forget' command")
        active_users = []
        irc.send("Forgetting everything...", sender)
        handled = True
    if "die" in words:
        print("Received proper 'die' command")
        irc.send("really? ok", sender)
        irc.command("QUIT")
        handled = True
        sys.exit()
    
    if not handled:
        print(f"Received: '{msg_cleaned}'")
        response = idioms.respond(msg_cleaned)
        print(f"Responding with: '{response}'")
        irc.send(response, sender)

def main(channel: str = None):
    if (channel is None):
        irc.connect()
    else:
        irc.connect(channel=channel)

    print(f"Sucessfully connected to {irc.channels[0]}")
    
    while (True):
        try:
            res = irc.get_response()

            res = parse_txt(res)

            if (res):
                print(res)
                sender, msg = handle_privmsg(*res)

                handle_specific_msg(sender, msg)

        
        except Exception as e:
            print(e)
            continue

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        try:
            _, channelFlag, channel = sys.argv

            if ("--channel" not in channelFlag):
                raise Exception

            if (channel[0] != "#"):
                print("Channel name must start with #")
                sys.exit(1)
            
            main(channel=channel)

        except Exception as e:
            print("Usage: python3 chatbot.py --channel [channel]")
            sys.exit(1)
    else:
        main()