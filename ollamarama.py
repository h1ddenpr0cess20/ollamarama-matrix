"""
ollamarama-matrix: An AI chatbot for the Matrix chat protocol with infinite personalities.

Author: Dustin Whyte
Date: December 2023
"""

from nio import AsyncClient, MatrixRoom, RoomMessageText
import json
import datetime
import asyncio
import requests
import markdown

class ollamarama:
    def __init__(self):
        #load config file
        self.config_file = "config.json"
        with open(self.config_file, "r") as f:
            config = json.load(f)
            f.close()

        self.server, self.username, self.password, self.channels, self.admins = config["matrix"].values()

        self.client = AsyncClient(self.server, self.username)

        # time program started and joined channels
        self.join_time = datetime.datetime.now()
        
        # store chat history
        self.messages = {}

        self.api_url = config["ollama"]["api_base"] + "/api/chat"

        self.models = config["ollama"]["models"]
        self.default_model = self.models[config["ollama"]["default_model"]]
        self.model = self.default_model

        self.temperature, self.top_p, self.repeat_penalty = config["ollama"]["options"].values()
        self.defaults = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repeat_penalty": self.repeat_penalty
        }

        self.default_personality = config["ollama"]["personality"]
        self.personality = self.default_personality
        self.prompt = config["ollama"]["prompt"]

    # get the display name for a user
    async def display_name(self, user):
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except Exception as e:
            return user

    # simplifies sending messages to the channel            
    async def send_message(self, channel, message):
        await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={
                "msgtype": "m.text", 
                "body": message,
                "format": "org.matrix.custom.html",
                "formatted_body": markdown.markdown(message, extensions=['fenced_code', 'nl2br'])},
        )

    # add messages to the history dictionary
    async def add_history(self, role, channel, sender, message):
        if channel not in self.messages:
            self.messages[channel] = {}
        if sender not in self.messages[channel]:
            self.messages[channel][sender] = [
                {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}
        ]
        self.messages[channel][sender].append({"role": role, "content": message})

        #trim history
        if len(self.messages[channel][sender]) > 24:
            if self.messages[channel][sender][0]["role"] == "system":
                del self.messages[channel][sender][1:3]
            else:
                del self.messages[channel][sender][0:2]

    #generate Ollama model response
    async def respond(self, channel, sender, message, sender2=None):
        try:
            data = {
                "model": self.model, 
                "messages": message, 
                "stream": False,
                "options": {
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                    "repeat_penalty": self.repeat_penalty
                    }
                }
            response = requests.post(self.api_url, json=data, timeout=300) #may need to increase for larger models, only tested on small models
            response.raise_for_status()
            data = response.json()
            
        except Exception as e:
            await self.send_message(channel, "Something went wrong")
            print(e)
        else:
            response_text = data["message"]["content"]
            await self.add_history("assistant", channel, sender, response_text)

            # .x function was used
            if sender2:
                display_name = await self.display_name(sender2)
            # .ai was used
            else:
                display_name = await self.display_name(sender)

            response_text = f"**{display_name}**:\n{response_text.strip()}"
            
            try:
                await self.send_message(channel, response_text)
            except Exception as e: 
                print(e)
            
    #set personality or custom system prompt
    async def set_prompt(self, channel, sender, persona=None, custom=None, respond=True):
        #clear existing history
        try:
            self.messages[channel][sender].clear()
        except:
            pass
        if persona != None and persona != "":
            # combine personality with prompt parts
            prompt = self.prompt[0] + persona + self.prompt[1]
        if custom != None  and custom != "":
            prompt = custom
        await self.add_history("system", channel, sender, prompt)
        if respond:
            await self.add_history("user", channel, sender, "introduce yourself")
            await self.respond(channel, sender, self.messages[channel][sender])

    async def ai(self, channel, message, sender, x=False):
        try:
            if x:
                if len(message) > 2:
                    name = message[1]
                    if message[2]:
                        message = message[2:]
                        if channel in self.messages:
                            for user in self.messages[channel]:
                                try:
                                    username = await self.display_name(user)
                                    if name == username:
                                        name_id = user
                                except:
                                    name_id = name
                            await self.add_history("user", channel, name_id, ' '.join(message))
                            await self.respond(channel, name_id, self.messages[channel][name_id], sender)
            else:
                await self.add_history("user", channel, sender, ' '.join(message[1:]))
                await self.respond(channel, sender, self.messages[channel][sender])
        except:
            pass
    
    async def reset(self, channel, sender, sender_display, stock=False):
        if channel in self.messages:
            try:
                self.messages[channel][sender].clear()
            except:
                self.messages[channel] = {}
                self.messages[channel][sender] = []
        if not stock:
            await self.send_message(channel, f"{self.bot_id} reset to default for {sender_display}")
            await self.set_prompt(channel, sender, persona=self.personality, respond=False)
        else:
            await self.send_message(channel, f"Stock settings applied for {sender_display}")
    
    async def help_menu(self, channel, sender_display):
        with open("help.txt", "r") as f:
            help_menu, help_admin = f.read().split("~~~")
            f.close()
        await self.send_message(channel, help_menu)
        if sender_display in self.admins:
            await self.send_message(channel, help_admin)

    async def change_model(self, channel, model=False):
        with open(self.config_file, "r") as f:
            config = json.load(f)
            f.close()
        self.models = config["ollama"]["models"]
        if model:
            try:
                if model in self.models:
                    self.model = self.models[model]
                elif model == 'reset':
                    self.model = self.default_model
                await self.send_message(channel, f"Model set to **{self.model}**")
            except:
                pass
        else:
            current_model = f"**Current model**: {self.model}\n**Available models**: {', '.join(sorted(list(self.models)))}"
            await self.send_message(channel, current_model)

    async def clear(self, channel):
        self.messages.clear()
        self.model = self.default_model
        self.personality = self.default_personality
        self.temperature, self.top_p, self.repeat_penalty = self.defaults.values()
        await self.send_message(channel, "Bot has been reset for everyone")
        
    async def handle_message(self, message, sender, sender_display, channel):
        user_commands = {
            ".ai": lambda: self.ai(channel, message, sender),
            f"{self.bot_id}:": lambda: self.ai(channel, message, sender),
            ".x": lambda: self.ai(channel, message, sender, x=True),
            ".persona": lambda: self.set_prompt(channel, sender, persona=' '.join(message[1:])),
            ".custom": lambda: self.set_prompt(channel, sender, custom=' '.join(message[1:])),
            ".reset": lambda: self.reset(channel, sender, sender_display),
            ".stock": lambda: self.reset(channel, sender, sender_display, stock=True),
            ".help": lambda: self.help_menu(channel, sender_display),
        }
        admin_commands = {
            ".model": lambda: self.change_model(channel, model=message[1] if len(message) > 1 else False),
            ".clear": lambda: self.clear(channel),
        }
        #may add back temperature controls later, per user, for now you can just change that in config on the fly

        command = message[0]
        if command in user_commands:
            action = user_commands[command]
        if sender_display in self.admins and command in admin_commands:
            action = admin_commands[command]
        await action()
        
    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        if isinstance(event, RoomMessageText):
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            message = event.body
            message = message.split(" ")
            sender = event.sender
            sender_display = await self.display_name(sender)
            channel = room.room_id
            
            #check if the message was sent after joining and not by the bot
            if message_time > self.join_time and sender != self.username:
                try:
                    await self.handle_message(message, sender, sender_display, channel)
                except:
                    pass

    async def main(self):
        # Login, print "Logged in as @alice:example.org device id: RANDOMDID"
        print(await self.client.login(self.password))

        # get account display name
        self.bot_id = await self.display_name(self.username)
        
        # join channels
        for channel in self.channels:
            try:
                await self.client.join(channel)
                print(f"{self.bot_id} joined {channel}")
                
            except:
                print(f"Couldn't join {channel}")
        
        # start listening for messages
        self.client.add_event_callback(self.message_callback, RoomMessageText)

        await self.client.sync_forever(timeout=30000, full_state=True) 

if __name__ == "__main__":
    ollamarama = ollamarama()
    asyncio.get_event_loop().run_until_complete(ollamarama.main())

