# ollamarama-matrix
Ollamarama is an AI chatbot for the [Matrix](https://matrix.org/) chat protocol using Ollama. It can roleplay as almost anything you can think of. You can set any default personality you would like. It can be changed at any time, and each user has their own separate chat history with their chosen personality setting. Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated, per channel, per user.

This is based on my earlier project, [infinigpt-matrix](https://github.com/h1ddenpr0cess20/infinigpt-matrix), which uses OpenAI and costs money to use.  (Now updated with OpenAI/Ollama model switching)

IRC version available at [ollamarama-irc](https://github.com/h1ddenpr0cess20/ollamarama-irc)

Terminal-based version at [ollamarama](https://github.com/h1ddenpr0cess20/ollamarama)

## Setup

Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run local LLMs, etc.

You can install and update it with this command:
```
curl https://ollama.ai/install.sh | sh
```


Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.  Add those to the config.json file.  If you want to use the ones I've included, just run ollama pull _modelname_ for each.


You'll also need to install matrix-nio
```
pip3 install matrix-nio
```

Set up a [Matrix account](https://app.element.io/) for your bot.  You'll need the server, username and password.

Add those to the config.json file.

```
python3 ollamarama.py
```

## Use


**.ai _message_** or **botname: _message_**
&emsp;Basic usage.
    
**.x _user_ _message_**
&emsp;This allows you to talk to another user's chat history.
&emsp;_user_ is the display name of the user whose history you want to use
    
**.persona _personality_**
&emsp;Changes the personality.  It can be a character, personality type, object, idea, whatever.  Use your imagination.

**.custom _prompt_**
&emsp;Allows use of a custom system prompt instead of the roleplaying prompt

**.reset**
&emsp;Clear history and reset to preset personality
    
**.stock**
&emsp;Clear history and use without a system prompt

**Admin only commands**
                                            
**.model _model_**
&emsp;Omit model name to show current model and available models
&emsp;Include model name to change model
                                                
**.clear**
&emsp;Reset bot for everyone
                                

