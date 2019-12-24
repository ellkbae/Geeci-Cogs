import traceback

from discord.ext import commands
import asyncio
import discord
import json

def is_mod(ctx): #confirming if person is admin/mod by checking their role ID
    role_id = [x.id for x in ctx.message.author.roles]
    print("mod",role_id)
    return 156219889831510016 in role_id or 357024045839024128 in role_id

def guild_leader(ctx): #has Guild Leader role so that they can create it.
    role_id = [x.id for x in ctx.message.author.roles]
    print(role_id)
    return 658894407742914600 in role_id or is_mod(ctx)

private_channel = 658893955756326922
public_channel = 658894266923483146

class GW2():
    """
    An Gw2 plugins
    """
    def __init__(self, bot):
        self.bot = bot
        self.guild_msg = None
        self.output()
        loop = asyncio.get_event_loop()
        self.loop_timer = loop.create_task(self.bg_guild_update())

    def input(self,json_data):
        """
        Allow to update files for future
        Args:
            json_data: self.data obj
        """
        with open("guild_list.json",'w') as f:
            json.dump(json_data,f,indent = 2)
        print("Updating")

    def output(self):
        """
        Get latest data from json that we stored
        Returns:
            self.data = Json obj
        """
        with open("guild_list.json","r") as f:
            self.data = json.load(f)
        print("reading files")
        return self.data

    def make_embed(self,server,name,**kwargs):
        embed = discord.Embed()
        try:
            author = server.get_member(kwargs["author"])
            embed.set_author(name = author,icon_url=author.avatar_url or author.default_url)
        except: #nothing we can do about this eh?
            print("Unable to get this member for Name, {}".format(kwargs["author"]))
            return #if author not found, we will skip.
        embed.title = name
        embed.set_thumbnail(url = kwargs["pic"])
        embed.description = kwargs["msg"]
        embed.add_field(name = "Requirement",value = kwargs["req"])
        return embed


    async def asking_info(self,ctx,msg):
        """
        This allow to repeat task for 5 time for other
        Args:
            ctx: context objection from pass_context
            msg: A message to ask user for prompt input

        Returns:
            msg obj that user reply to
        """
        def check(m):
            return m.author == ctx.message.author
        await ctx.send(msg)
        try:
            info = await self.bot.wait_for("message",timeout=60,check = check)
        except asyncio.TimeoutError:
            await ctx.send(content = "You didn't say anything, please start over")
            return None
        return info

    @commands.command(pass_context = True)
    @commands.check(guild_leader)
    async def add(self,ctx):
        """
        Allow user add info for guild ad

        """
        #asking for guild name
        guild_name = await self.asking_info(ctx,"Enter the name of your team")
        if guild_name is None: return
        if self.data.get(guild_name): #If it already exists, we will leave
            return await ctx.send(content ="That team already exists or name has been taken!")

        #Getting requirement for joining guilds
        guild_req = await self.asking_info(ctx,"Enter the requirements needed to join this team:")
        if guild_req is None: return

        #A personal message from guild to any user
        guild_msg = await self.asking_info(ctx,"Enter the team description that everyone will see:")
        if guild_msg is None: return

        #Picture such as guild icon
        guild_pic = await self.asking_info(ctx,"Link the URL of your teams logo or picture here, do not add a file:")
        if guild_pic is None: return

        #We are making embed of it here
        embed = discord.Embed()
        embed.set_author(name = ctx.message.author,icon_url=ctx.message.author.avatar_url)
        embed.title = guild_name.clean_content
        embed.set_thumbnail(url = guild_pic.clean_content)
        embed.description = guild_msg.clean_content
        embed.add_field(name = "Requirement",value = guild_req.clean_content)

        #Once we done created embed, we will info user it will take some time to get approval of it then, we will send to private channel allow mod to see to approval or not
        #Once we send to private, we will store them into database and write it down
        msg = await ctx.send(content = "Thank you for your application to create a team, mods will now review the application and decide yes or no to be added.",embed = embed)
        private = await self.bot.get_channel(private_channel).send(embed = embed)
        self.data[guild_name.content] = {"pic":guild_pic.content,"msg":guild_msg.content,"req":guild_req.clean_content,
                                         "author":ctx.message.author.id,"msg_id":msg.id,"private":private.id,
                                         "approval":False}
        self.input(self.data)

    @commands.command(pass_context = True)
    @commands.check(is_mod)
    async def delete(self,ctx,*,name):
        """
        If mod dont like it for some reason , they can delete it
        Args:
            ctx: context object
            name: Str name
        """
        #pop it, which mean wll be gone from database when you do pop, adding second params of None so it dont return error about key missing
        data = self.data.pop(name,None)
        if data: #if it exists, then it is already pop
            public =data.get("public") #checking if it was in channel already
            if public: #if so, find message objection of that within giving id and delete it
                try:
                    public_msg = await self.bot.get_channel(public_channel).get_message(public)
                    print(public_msg)
                    await public_msg.delete()
                    private_msg = await self.bot.get_channel(private_channel).get(data["private"]) #same thing with Private
                    await private_msg.delete()
                except:
                    pass
            self.input(self.data) #updating it
            await ctx.send(content = "I have removed the teams info/app")

        else:
            await ctx.send(content = "Cannot find such a team, please double check the teams name")

    @commands.command(pass_context = True)
    @commands.check(is_mod)
    async def approval(self,ctx,*,name):
        """
        As name state, it is to approval It
        """
        data = self.data.get(name) #check if it exists and it haven't got approval yet
        if data: # if exists
            if data["approval"]: #if already approval
                return await ctx.send("It has already been approved!")

            #since it didnt got approval and just got it, so we will created embed
            embed = self.make_embed(ctx.message.guild,name,**data)
            #now we will send to public channel
            public = await self.bot.get_channel(public_channel).send(embed = embed)
            self.data[name].update({"approval":True,"public":public.id}) #we will add new info of approval and public msg id
            self.input(self.data) #updating it

        else:
            await ctx.send("Cannot find it, please double check team name")

    @commands.command(pass_context = True,brief = "Showing info about a certain team")
    async def info(self,ctx,*,name):
        """
        To show info about its
        """
        data = self.data.get(name)
        if data: #if it  exists
            if data["approval"]: #and it is already approval, if so, we can show it
                embed = self.make_embed(ctx.message.guild,name,**data) # **data mean unpack whole thing
                await ctx.send(embed = embed)
            else:
                return await ctx.send(content = "It hasn't gotten approval yet!")
        else:
            await ctx.send(content = "Cannot find it, please double check")

    @commands.command(name = "list",pass_context = True,brief = "Showing all team list")
    async def _list(self,ctx):
        def check(reaction, user):
            if reaction.message.id == msg.id and user == player:
                if str(reaction.emoji) in [u"\u2B05", u"\u27A1"]:
                    return True
            return False
        player = ctx.message.author

        embed_list = self.make_embed_list()

        current_page = 1
        first_start = True
        max_page = len(embed_list)
        print("starting now", max_page)
        print(embed_list)
        while True:
            if first_start:
                print("first start")
                first_start = False
                msg = await ctx.send(embed=embed_list[current_page-1])
                print(msg)
                await msg.add_reaction(u"\u2B05")
                await msg.add_reaction(u"\u27A1")

            else:
                print(current_page)
                await msg.edit(embed=embed_list[current_page-1])

            try:
                react = await self.bot.wait_for("reaction_add",timeout=60, check=check)
                print("react show" , react)
                if react is None:
                    await msg.clear_reaction()
                else:
                    await msg.remove_reaction(react[0].emoji,react[1])
            except asyncio.TimeoutError:
                return

            if react[0].emoji == "⬅":
                #go back by one
                if current_page - 1 == 0: #if it on first page, don't do any
                    continue
                else:
                    current_page -= 1
            elif react[0].emoji == "➡":
                #go next page by one
                if current_page + 1 > max_page: #if it on last page, don't do any
                    continue
                else:
                    current_page += 1
    def get_guild_list(self):#getting info about channel and message id
        with open("background_message.json","r") as fp:
            return json.load(fp)

    def set_guild_list(self,data): #setting info about channel and message id for guild
        with open("background_message.json","w") as fp:
            json.dump(data,fp)


    @commands.command()
    async def guild_setup(self,ctx,amount = 5):
        chan  = ctx.message.channel
        embed = discord.Embed(title = "temp")
        msg_list = []
        for x in range(amount):
            msg_list.append((await chan.send(embed = embed)).id)
        print(msg_list)
        data = self.get_guild_list()
        print(data)
        data["guild"] = {"channel":chan.id,"message":msg_list}
        print(data)
        self.set_guild_list(data)


    async def guild_update(self):
        print("under guild_update")
        data = self.get_guild_list()
        print(data)
        if data.get("guild"):
            chan = self.bot.get_channel(data["guild"]["channel"])
            print(chan)
            msg = []
            for x in data["guild"]["message"]:
                msg.append(await chan.get_message(x))
            return msg

    def make_embed_list(self):
        embed_list = []
        server = self.bot.get_guild(128591319198072832)
        print(self.data)
        for key,value in self.data.items():
            if value["approval"]:
                data = self.make_embed(server,key,**value)
                if data is not None:
                    embed_list.append(data)
        return embed_list


    async def bg_guild_update(self):
        print("running bg guild update")
        main_msg = await self.guild_update() #getting message object for server.
        if main_msg is None:
            print("Main message is not found.")
            await asyncio.sleep(1800) #wait for 30 min until it is update by owner
        guild_list = []
        print("starting loops")
        while True:
            if guild_list == []: #if it empty list, we will recreate new one
                guild_list = self.make_embed_list()
            for x in range(len(main_msg)):
                content = ""
                if len(guild_list) == 0: #if it empty, stop and break out or else it will have error
                    break
                if x == 0:
                    content = "```fix\nGuild List\n```"
                await main_msg[x].edit(content = content,embed = guild_list.pop(0))
            print("Sleeping guild")
            await asyncio.sleep(10*60) #10 min



def setup(bot):
    bot.add_cog(GW2(bot))

