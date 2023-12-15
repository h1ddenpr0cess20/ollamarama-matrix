import asyncio
from ollamarama import ollamarama


server = "https://matrix.org" #change if using different homeserver
username = "@USERNAME:SERVER.TLD" 
password = "PASSWORD"

channels = ["#channel1:SERVER.TLD", 
            "#channel2:SERVER.TLD", 
            "#channel3:SERVER.TLD", 
            "!ExAmPleOfApRivAtErOoM:SERVER.TLD", ] #enter the channels you want it to join here
    

personality = "a helpful and thorough AI assistant who provides accurate and detailed answers without being too verbose"

# create bot instance
bot = ollamarama(server, username, password, channels, personality)

# run main function loop
asyncio.get_event_loop().run_until_complete(bot.main())