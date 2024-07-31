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

class ollamarama:
    def __init__(self):
        #load config file
        self.config_file = "config.json"
        with open(self.config_file, "r") as f:
            config = json.load(f)
            f.close()

        self.server, self.username, self.password, self.channels, self.default_personality, self.admins = config[1].values()
        self.api_url = config[2]['api_base'] + "/api/chat"
        self.personality = self.default_personality

        self.client = AsyncClient(self.server, self.username)

        # time program started and joined channels
        self.join_time = datetime.datetime.now()
        
        # store chat history
        self.messages = {}

        #prompt parts
        self.prompt = ("you are ", ". roleplay and speak in the first person and never break character.  keep your responses brief and to the point.")

        self.models = config[0]['models']
        #set model
        self.default_model = self.models[config[0]['default_model']]
        self.model = self.default_model

        #no idea if optimal, change if necessary
        self.temperature, self.top_p, self.repeat_penalty = config[2]['options'].values()
        self.defaults = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repeat_penalty": self.repeat_penalty
        }
        

        #load help menu
        with open("help.txt", "r") as f:
            self.help, self.help_admin = f.read().split("~~~")
            f.close()

    # get the display name for a user
    async def display_name(self, user):
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except Exception as e:
            print(e)

    # simplifies sending messages to the channel            
    async def send_message(self, channel, message):
        await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )

    # add messages to the history dictionary
    async def add_history(self, role, channel, sender, message):
        #check if channel is in the history yet
        if channel in self.messages:
            #check if user is in channel history
            if sender in self.messages[channel]: 
                self.messages[channel][sender].append({"role": role, "content": message})
                
            else:
                self.messages[channel][sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]
        else:
            #set up channel in history
            self.messages[channel]= {}
            self.messages[channel][sender] = {}
            if role == "system":
                self.messages[channel][sender] = [{"role": role, "content": message}]
            else: 
                #add personality to the new user entry
                self.messages[channel][sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]

    #generate Ollama model response
    async def respond(self, channel, sender, message, sender2=None):
        try:
            # #Generate response
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
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()
            data = response.json()
            
        except Exception as e:
            await self.send_message(channel, "Something went wrong")
            print(e)
        else:
            #Extract response text
            response_text = data["message"]['content']

            #add to history
            await self.add_history("assistant", channel, sender, response_text)
            # .x function was used
            if sender2:
                display_name = await self.display_name(sender2)
            # .ai was used
            else:
                display_name = await self.display_name(sender)
            response_text = display_name + ":\n" + response_text.strip()
            #Send response to channel
            try:
                await self.send_message(channel, response_text)
            except Exception as e: 
                print(e)
            #Shrink history list for token size management 
            if len(self.messages[channel][sender]) > 24:
                if self.messages[channel][sender][0]['role'] == 'system':
                    del self.messages[channel][sender][1:3]  #delete the first set of question and answers
                else:
                    del self.messages[channel][sender][0:2]

    # change the personality of the bot
    async def persona(self, channel, sender, persona):
        #clear existing history
        try:
            await self.messages[channel][sender].clear()
        except:
            pass
        personality = self.prompt[0] + persona + self.prompt[1]
        #set system prompt
        await self.add_history("system", channel, sender, personality)
        
    # use a custom prompt
    async def custom(self, channel, sender, prompt):
        try:
            await self.messages[channel][sender].clear()
        except:
            pass
        await self.add_history("system", channel, sender, prompt)  

    # tracks the messages in channels
    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        # Main bot functionality
        if isinstance(event, RoomMessageText):
            # convert timestamp
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            # assign parts of event to variables
            message = event.body
            sender = event.sender
            sender_display = await self.display_name(sender)
            room_id = room.room_id
            

            #check if the message was sent after joining and not by the bot
            if message_time > self.join_time and sender != self.username:
                user = await self.display_name(event.sender)
                #admin commands
                if message == ".admins":
                    await self.send_message(room_id, f"Bot admins: {', '.join(self.admins)}")
                if sender_display in self.admins:
                    #model switching 
                    if message.startswith(".model"):
                        with open(self.config_file, "r") as f:
                            config = json.load(f)
                            f.close()
                        self.models = config[0]['models']
                        if message == ".models":                           
                            current_model = f"Current model: {self.model.removeprefix('ollama/')}\nAvailable models: {', '.join(sorted(list(self.models)))}"
                            await self.send_message(room_id, current_model)
                            
                        if message.startswith(".model "):
                            m = message.split(" ", 1)[1]
                            if m != None:
                                if m in self.models:
                                    self.model = self.models[m]
                                elif m == 'reset':
                                    self.model = self.default_model
                                await self.send_message(room_id, f"Model set to {self.model.removeprefix('ollama/')}")
                    
                    #bot owner commands
                    if sender_display == self.admins[0]:
                        #add admins
                        if message.startswith(".auth "):
                            nick = message.split(" ", 1)[1].strip()
                            if nick != None:
                                self.admins.append(nick)
                                await self.send_message(room_id, f"{nick} added to admins")
                        
                        #remove admins
                        if message.startswith(".deauth "):
                            nick = message.split(" ", 1)[1].strip()
                            if nick != None:
                                self.admins.remove(nick)
                                await self.send_message(room_id, f"{nick} removed from admins")

                        #set new global personality
                        if message.startswith(".gpersona "):
                            m = message.split(" ", 1)[1]
                            if m != None:
                                if m == 'reset':
                                    self.personality = self.default_personality
                                else:
                                    self.personality = m.strip()
                                await self.send_message(room_id, f"Global personality set to {self.personality}")
                        
                        #remove personality globally
                        if message == ".gstock":
                            pass #i'll figure this out later

                        #reset history for all users                
                        if message == ".clear":
                            self.messages.clear()
                            self.model = self.default_model
                            self.temperature, self.top_p, self.repeat_penalty = self.defaults

                            await self.send_message(room_id, "Bot has been reset for everyone")

                        if message.startswith((".temperature ", ".top_p ", ".repeat_penalty ")):
                            attr_name = message.split()[0][1:]
                            min_val, max_val, default_val = {
                                "temperature": (0, 1, self.defaults['temperature']),
                                "top_p": (0, 1, self.defaults['top_p']),
                                "repeat_penalty": (0, 2, self.defaults['repeat_penalty'])
                            }[attr_name]

                            if message.endswith(" reset"):
                                setattr(self, attr_name, default_val)
                                await self.send_message(room_id, f"{attr_name.capitalize()} set to {default_val}")
                            else:
                                try:
                                    value = float(message.split(" ", 1)[1])
                                    if min_val <= value <= max_val:
                                        setattr(self, attr_name, value)
                                        await self.send_message(room_id, f"{attr_name.capitalize()} set to {value}")
                                    else:
                                        await self.send_message(room_id, f"Invalid input, {attr_name} is still {getattr(self, attr_name)}")
                                except:
                                    await self.send_message(room_id, f"Invalid input, {attr_name} is still {getattr(self, attr_name)}")

                # main AI response functionality
                if message.startswith(".ai ") or message.startswith(self.bot_id):
                    if message != ".ai reset":
                        m = message.split(" ", 1)
                        try:
                            m = m[1]
                            await self.add_history("user", room_id, sender, m)
                            await self.respond(room_id, sender, self.messages[room_id][sender])
                        except:
                            pass
                # collaborative functionality
                if message.startswith(".x "):
                    m = message.split(" ", 2)
                    m.pop(0)
                    if len(m) > 1:
                        disp_name = m[0]
                        name_id = ""
                        m = m[1]
                        if room_id in self.messages:
                            for user in self.messages[room_id]:
                                try:
                                    username = await self.display_name(user)
                                    if disp_name == username:
                                        name_id = user
                                except:
                                    name_id = disp_name
                        
                            await self.add_history("user", room_id, name_id, m)
                            await self.respond(room_id, name_id, self.messages[room_id][name_id], sender)

                #change personality    
                if message.startswith(".persona "):
                    m = message.split(" ", 1)
                    m = m[1]
                
                    await self.persona(room_id, sender, m)
                    await self.respond(room_id, sender, self.messages[room_id][sender])

                #custom prompt use   
                if message.startswith(".custom "):
                    m = message.split(" ", 1)
                    m = m[1]
                    await self.custom(room_id, sender, m)
                    await self.respond(room_id, sender, self.messages[room_id][sender])

                # reset bot to default personality
                if message.startswith(".reset") or message == ".ai reset": #some users keep forgetting the correct command
                    if room_id in self.messages:
                        if sender in self.messages[room_id]:
                            self.messages[room_id][sender].clear()
                            await self.persona(room_id, sender, self.personality)
                            
                    try:
                        await self.send_message(room_id, f"{self.bot_id} reset to default for {sender_display}")
                    except:
                        await self.send_message(room_id, f"{self.bot_id} reset to default for {sender}")

                # Stock settings, no personality        
                if message.startswith(".stock"):
                    if room_id in self.messages:
                        if sender in self.messages[room_id]:
                            self.messages[room_id][sender].clear()
                    else:
                        self.messages[room_id] = {}
                        self.messages[room_id][sender] = []
                    try:
                        await self.send_message(room_id, f"Stock settings applied for {sender_display}")
                    except:
                        await self.send_message(room_id, f"Stock settings applied for {sender}")
                
                # help menu
                if message.startswith(".help"):
                    await self.send_message(room_id, self.help)
                    if sender_display in self.admins:
                        await self.send_message(room_id, self.help_admin)

    # main loop
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

        await self.client.sync_forever(timeout=30000) 

if __name__ == "__main__":
    bot = ollamarama()
    asyncio.get_event_loop().run_until_complete(bot.main())

