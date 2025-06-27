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
import logging
import logging.config

class ollamarama:
    """
    An Ollama-based chatbot for the Matrix chat protocol, supporting dynamic personalities, 
    custom prompts, and cross-user interactions.

    Attributes:
        config_file (str): Path to the configuration file.
        server (str): Matrix server URL.
        username (str): Username for the Matrix account.
        password (str): Password for the Matrix account.
        channels (list): List of channel IDs the bot will join.
        admins (list): List of admin user IDs.
        client (AsyncClient): Matrix client instance.
        join_time (datetime): Timestamp when the bot joined.
        messages (dict): Stores message histories by channel and user.
        api_url (str): URL for the Ollama API.
        options (dict): Fine tuning parameters for generated responses.
        models (dict): Available large language models.
        default_model (str): Default large language model.
        prompt (list): Template for the roleplaying system prompt.
        default_personality (str): Default personality for the chatbot.
        model (str): Current large language model.
        personality (str): Current personality for the chatbot.
        history_size (int): Size of the chat history for each user
    """
    def __init__(self):
        """Initialize ollamarama by loading configuration and setting up attributes."""
        
        self.config_file = "config.json"
        with open(self.config_file, "r") as f:
            config = json.load(f)
            f.close()
        
        self.server, self.username, self.password, self.channels, self.admins, self.device_id = config["matrix"].values()
        self.client = AsyncClient(self.server, self.username, device_id=self.device_id)

        self.join_time = datetime.datetime.now()
        
        self.messages = {}

        self.api_url, self.options, self.models, self.default_model, self.prompt, self.default_personality, self.history_size = config["ollama"].values()
        self.model = self.default_model
        self.personality = self.default_personality
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': True,
        })
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.log = logging.getLogger(__name__).info
        self.log(f"Model set to {self.model}")

    async def display_name(self, user):
        """
        Get the display name of a Matrix user.

        Args:
            user (str): User ID.

        Returns:
            str: Display name or user ID if unavailable.
        """
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except:
            return user

    async def send_message(self, channel, message):
        """
        Send a formatted message to a Matrix room.

        Args:
            channel (str): Room ID.
            message (str): Message content.
        """
        await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={
                "msgtype": "m.text", 
                "body": message,
                "format": "org.matrix.custom.html",
                "formatted_body": markdown.markdown(message, extensions=['extra', 'fenced_code', 'nl2br', 'sane_lists', 'tables', 'codehilite'])},
        )

    async def add_history(self, role, channel, sender, message):
        """
        Add a message to the interaction history.

        Args:
            role (str): Role of the message sender (e.g., "user", "assistant").
            channel (str): Room ID.
            sender (str): User ID of the sender.
            message (str): Message content.
        """
        if channel not in self.messages:
            self.messages[channel] = {}
        if sender not in self.messages[channel]:
            self.messages[channel][sender] = [
                {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}
        ]
        self.messages[channel][sender].append({"role": role, "content": message})

        if len(self.messages[channel][sender]) > self.history_size:
            if self.messages[channel][sender][0]["role"] == "system":
                self.messages[channel][sender].pop(1)
            else:
                self.messages[channel][sender].pop(0)

    async def respond(self, channel, sender, message, sender2=None):
        """
        Generate and send a response using the Ollama API.

        Args:
            channel (str): Room ID.
            sender (str): User ID of the message sender.
            message (list): Message history.
            sender2 (str, optional): Additional user ID if .x used.
        """
        try:
            data = {
                "model": self.model, 
                "messages": message, 
                "stream": False,
                "options": self.options,
                "timeout": 180
                }
            response = requests.post(self.api_url, json=data, timeout=180)
            response.raise_for_status()
            data = response.json()
            
        except Exception as e:
            await self.send_message(channel, "Something went wrong")
            self.log(e)
        else:
            response_text = data["message"]["content"]

            # Check for different types of thought/solution delimiters
            if "<think>" in response_text:
                thinking, response_text = response_text.split("</think>")
                thinking = thinking.strip("<think>").strip()
                self.log(f"Model thinking for {sender}: {thinking}")
            if "<|begin_of_thought|>" in response_text:
                parts = response_text.split("<|end_of_thought|>")
                if len(parts) > 1:
                    thinking = parts[0].strip("<|begin_of_thought|>").strip('<|end_of_thought|>')
                    response_text = parts[1]
                    self.log(f"Model thinking for {sender}: {thinking}")

            # Check for solution delimiters and clean them up
            if "<|begin_of_solution|>" in response_text:
                parts = response_text.split("<|end_of_solution|>")
                response_text = parts[0].split("<|begin_of_solution|>")[1].strip()

            await self.add_history("assistant", channel, sender, response_text)

            if sender2:
                display_name = await self.display_name(sender2)
            else:
                display_name = await self.display_name(sender)

            response_text = f"**{display_name}**:\n{response_text.strip()}"
            
            try:
                self.log(f"Sending response to {display_name} in {channel}: {response_text}")
                await self.send_message(channel, response_text)
            except Exception as e: 
                self.log(e)
            
    async def set_prompt(self, channel, sender, persona=None, custom=None, respond=True):
        """
        Set a custom or persona-based prompt for a user.

        Args:
            channel (str): Room ID.
            sender (str): User ID of the sender.
            persona (str, optional): Personality name or description.
            custom (str, optional): Custom prompt.
            respond (bool, optional): Whether to generate a response. Defaults to True.
        """
        try:
            self.messages[channel][sender].clear()
        except:
            pass
        if persona != None and persona != "":
            prompt = self.prompt[0] + persona + self.prompt[1]
        if custom != None  and custom != "":
            prompt = custom
        await self.add_history("system", channel, sender, prompt)
        self.log(f"System prompt for {sender} set to '{prompt}'")
        if respond:
            await self.add_history("user", channel, sender, "introduce yourself")
            await self.respond(channel, sender, self.messages[channel][sender])

    async def ai(self, channel, message, sender, x=False):
        """
        Process AI-related commands and respond accordingly.

        Args:
            channel (str): Room ID.
            message (list): Message content split into parts.
            sender (str): User ID of the sender.
            x (bool, optional): Whether to process cross-user interactions. Defaults to False.
        """
        self.log(f"{sender} sent {" ".join(message)} in {channel}")
        if x and message[2]:
            target = message[1]
            message = ' '.join(message[2:])
            if channel in self.messages:
                for user in self.messages[channel]:
                    try:
                        username = await self.display_name(user)
                        if target == username:
                            target = user
                    except:
                        pass
                if target in self.messages[channel]:
                    await self.add_history("user", channel, target, message)
                    await self.respond(channel, target, self.messages[channel][target], sender)
        else:
            await self.add_history("user", channel, sender, ' '.join(message[1:]))
            await self.respond(channel, sender, self.messages[channel][sender])

    
    async def reset(self, channel, sender, sender_display, stock=False):
        """
        Reset the message history for a specific user in a channel, optionally applying stock settings.

        Args:
            channel (str): Room ID.
            sender (str): User ID whose history is being reset.
            sender_display (str): Display name of the sender.
            stock (bool): Whether to reset without setting a system prompt.  Defaults to False.
        """
        if channel not in self.messages:
            self.messages[channel] = {}
        self.messages[channel][sender] = []
        if not stock:
            await self.send_message(channel, f"{self.bot_id} reset to default for {sender_display}")
            self.log(f"{self.bot_id} reset to default for {sender_display} in {channel}")
            await self.set_prompt(channel, sender, persona=self.personality, respond=False)
        else:
            await self.send_message(channel, f"Stock settings applied for {sender_display}")
            self.log(f"Stock settings applied for {sender_display} in {channel}")
    
    async def help_menu(self, channel, sender_display):
        """
        Display the help menu.

        Args:
            channel (str): Room ID.
            sender_display (str): Display name of the sender.
        """
        with open("help.txt", "r") as f:
            help_menu, help_admin = f.read().split("~~~")
            f.close()
        await self.send_message(channel, help_menu)
        if sender_display in self.admins:
            await self.send_message(channel, help_admin)

    async def change_model(self, channel, model=False):
        """
        Change the large language model or list available models.

        Args:
            channel (str): Room ID.
            model (str): The model to switch to. Defaults to False.
        """
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
                self.log(f"Model set to {self.model}")
                await self.send_message(channel, f"Model set to **{self.model}**")
            except:
                pass
        else:
            current_model = f"**Current model**: {self.model}\n**Available models**: {', '.join(sorted(list(self.models)))}"
            await self.send_message(channel, current_model)

    async def clear(self, channel):
        """
        Reset the chatbot globally.
        
        Args:
            channel (str): Room ID.
        """
        self.messages.clear()
        self.model = self.default_model
        self.personality = self.default_personality
        await self.send_message(channel, "Bot has been reset for everyone")
        
    async def handle_message(self, message, sender, sender_display, channel):
        """
        Handles messages sent in the channels.
        Parses the message to identify commands or content directed at the bot
        and delegates to the appropriate handler.

        Args:
            message (list): Message content split into parts.
            sender (str): User ID of the sender.
            sender_display (str): Display name of the sender.
            channel (str): Room ID.
        """
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

        command = message[0]
        if command in user_commands:
            action = user_commands[command]
            await action()
        if sender_display in self.admins and command in admin_commands:
            action = admin_commands[command]
            await action()
        
    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """
        Handle incoming messages in a Matrix room.

        Args:
            room (MatrixRoom): The room where the message was sent.
            event (RoomMessageText): The event containing the message details.
        """
        if isinstance(event, RoomMessageText):
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            message = event.body.split(" ")
            sender = event.sender
            sender_display = await self.display_name(sender)
            channel = room.room_id
            
            if message_time > self.join_time and sender != self.username:
                try:
                    await self.handle_message(message, sender, sender_display, channel)
                except:
                    pass

    async def main(self):
        """
        Initialize the chatbot, log into Matrix, join rooms, and start syncing.

        """
        login_resp = await self.client.login(self.password, device_name=self.device_id)
        self.log(login_resp)
        if not self.device_id and hasattr(login_resp, 'device_id'):
            self.device_id = login_resp.device_id
            try:
                with open(self.config_file, 'r+') as f:
                    config = json.load(f)
                    config.setdefault('matrix', {})['device_id'] = self.device_id
                    f.seek(0)
                    json.dump(config, f, indent=4)
                    f.truncate()
            except Exception:
                pass

        self.bot_id = await self.display_name(self.username)
        
        for channel in self.channels:
            try:
                await self.client.join(channel)
                self.log(f"{self.bot_id} joined {channel}")
                
            except:
                self.log(f"Couldn't join {channel}")
        
        self.client.add_event_callback(self.message_callback, RoomMessageText)

        await self.client.sync_forever(timeout=30000, full_state=True) 

if __name__ == "__main__":
    ollamarama = ollamarama()
    asyncio.run(ollamarama.main())

