# ollamarama-matrix
Ollamarama is an AI chatbot for the [Matrix](https://matrix.org/) chat protocol using LiteLLM and Ollama. It can roleplay as almost anything you can think of. You can set any default personality you would like. It can be changed at any time, and each user has their own separate chat history with their chosen personality setting. Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated, per channel, per user.

This is based on my earlier project, [infinigpt-matrix](https://github.com/h1ddenpr0cess20/infinigpt-matrix), which uses OpenAI and costs money to use.

IRC version available at [ollamarama-irc](https://github.com/h1ddenpr0cess20/ollamarama-irc)

Terminal-based version at [ollamarama](https://github.com/h1ddenpr0cess20/ollamarama)

## Setup

Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run offline LLMs, etc.

You can install it with this command:
```
curl https://ollama.ai/install.sh | sh
```


Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.  Add those to the self.models dictionary.  If you want to use the ones I've included, just run the commands in the models.md file.  You can skip this part, and they should download when the model is switched, but the response will be delayed until it finishes downloading.


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
    Allows use of a custom system prompt instead of the roleplaying prompt

**.reset**
    Reset to preset personality
    
**.stock**
    Remove personality and reset to standard settings
    
**.help**
    Show the built-in help menu

**.models**
    Show current model and available models (admin only)

**.model _name_**
    Set a model (admin only)

**.model _reset_**
    Reset to default model (admin only)

**.temperature** 
    Set temperature value between 0 and 1.  To reset to default, type reset instead of a number. (bot owner only)
                                                
**.top_p**
    Set top_p value between 0 and 1.  To reset to default, type reset instead of a number. (bot owner only)
                                                
**.repeat_penalty**
    Set repeat_penalty between 0 and 2.  To reset to default, type reset instead of a number. (bot owner only)
                                                
**.clear**
    Resets all bot history and sets default model (bot owner only)

**.auth _user_**
    Add user to admins (bot owner only)

**.deauth _user_**
    Remove user from admins (bot owner only)

**.gpersona _persona_**
    Change global personality (bot owner only)

**.gpersona reset**
    Reset global personality (bot owner only)
