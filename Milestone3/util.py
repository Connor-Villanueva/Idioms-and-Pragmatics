def parse_addressee(input_text: str) -> str:
    '''
    Given a msg, return the addressee and the msg

    The addressee is who the msg was addressed to
    '''
    try:
        addressee, specific_msg = input_text.split(":", 2)[1:]
        return addressee, specific_msg
    
    except Exception as e:
        raise e
    
def parse_sender(input_txt: str) -> str:
    '''
    Given a msg, (after parsing the addressee), return the sender of the msg
    '''
    return input_txt.split("!", 1)[0].lstrip(":")

def parse_line(line : str) -> tuple[str, str, str, str | None] | None:
    '''
    Given a line from the IRC response, parse the line
    '''
    if not line:
        return None
    split_text = line.split(" ", 3)

    match len(split_text):
        case 3: 
            sender, msg_type, channel = split_text
            rest = None
        case 4: 
            sender, msg_type, channel, rest = split_text
        case _: 
            return None
        
    return sender, msg_type, channel, rest