# Instructions to Run

1. Install required libraries listed in `environment.txt`

2. For improvements in sentence generation, run an instance of llama3 locally. For installation see the following instructions:

    a. Install Ollama from the following [link](https://ollama.com/download).

    b. Run llama3 from the terminal using the command `ollama run llama3`.

    c. By default this should start a local instance on port `11434`. If not, please change the `DEFAULT_LLM_PORT` in `idiom_parser.py`.

3. Run the `chatbot.py` with `python3 chatbot.py`. This will connect to a chatroom on [libera](https://web.libera.chat/).

    a. By default this will connect to the channel `#TESTJMGDLS`.

    b. To connect to the non-default chanenel use the optional flag `python3 chatbot.py --channel {channel_name}`

# Usages

1. To communicate with the bot, you must address it. To do this, your message must start with `JTC-Idiom-Bot: `.

2. The following are valid commands:

    **usage** - Will display a usage message with instructions on how to use the bot.

    **die** - Will kill the bot.

    **What is/are the idiom(s) in: "{sentence}"** - Will tell identify idioms in the given sentence.

    **What does "{idiom}" mean?** - Will give the literal description of the given idiom.

    **Replace the idioms in this sentence with their definition: "{sentence}"** - Will replace the idioms with a gramatically correct definition if the LLM is available. Otherwise it will replace the idiom with its literal definition.