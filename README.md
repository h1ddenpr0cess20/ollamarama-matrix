# ollamarama-matrix
Ollamarama is an AI chatbot for the [Matrix](https://matrix.org/) chat protocol using LiteLLM and Ollama. It can roleplay as almost anything you can think of. You can set any default personality you would like. It can be changed at any time, and each user has their own separate chat history with their chosen personality setting. Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated, per channel, per user.  

Coming soon for IRC 

## Setup

Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run offline LLMs, etc.

You can install it with this command:
```
curl https://ollama.ai/install.sh | sh
```

Once it's all set up, you'll need to download the model.  You can play with the available ones and see what works best for you, but for this bot, zephyr:7b-beta-q8_0 seems to work best of the ones I've tested.  To install:
```
ollama pull zephyr:7b-beta-q8_0
```

You'll also need to install matrix-nio and litellm
```
pip3 install matrix-nio litellm
```

Set up a [Matrix account](https://app.element.io/) for your bot.  You'll need the server, username and password.

Plug those into the appropriate variables in the launcher.py file.

```
python3 launcher.py
```

## Use

**.ai _message_ or botname: _message_**
    Basic usage.
    Personality is preset by bot operator.
  
**.x _user message_**
    This allows you to talk to another user's chat history.
    _user_ is the display name of the user whose history you want to use
      
**.persona _personality_**
    Changes the personality.  It can be a character, personality type, object, idea.
    Don't use a custom prompt here.

**.custom _prompt_**
    Allows use of a custom prompt instead of the built-in one

**.reset**
    Reset to preset personality
    
**.stock**
    Remove personality and reset to standard settings
    
**.help**
    Show the built-in help menu

