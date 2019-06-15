# Simple Request Bot
# Made by thegodpixel#3404
#    ____  _           _______       ______                          _____ __            ___
#   / __ \(_)  _____  / / ___/____  / __/ /__      ______ _________ / ___// /___  ______/ (_)___  _____
#  / /_/ / / |/_/ _ \/ /\__ \/ __ \/ /_/ __/ | /| / / __ `/ ___/ _ \\__ \/ __/ / / / __  / / __ \/ ___/
# / ____/ />  </  __/ /___/ / /_/ / __/ /_ | |/ |/ / /_/ / /  /  __/__/ / /_/ /_/ / /_/ / / /_/ (__  )
#/_/   /_/_/|_|\___/_//____/\____/_/  \__/ |__/|__/\__,_/_/   \___/____/\__/\__,_/\__,_/_/\____/____/
#
#Copyright Pixel Software Studios
#Not for use outside of Simple Studios under contract
#Finished 6/15/19

import discord
import datetime
import json
import re

from pymongo import MongoClient
from discord.ext import commands

with open("config.json", "r") as config_file:
	config = json.load(config_file)

prefix = config["prefix"]

mclient = MongoClient("mongodb://{}:{}@{}:{}/requests".format(config["mongousr"], config["mongopwd"], "localhost", "27017"))
reqdb = mclient.requests

bot = commands.Bot(command_prefix=prefix)
bot.remove_command('help')

#//////////////////////////////
requestId = 0
requests = []
moderatorRole = "Moderator"

datefmt = "%I:%M%p on %B %d, %Y"
permissionInformation = {"request": "Permissions: Everyone", "reqedit": "Permissions: Author of edited request or Mod", "approve": "Permissions: Mod Only", "reject": "Permissions: Mod Only", "setapprovedchannel": "Permissions: Mod Only"}
usageInformation = {"request": "Usage: " + prefix + "request \"requestText\"", "reqedit": "Usage: " + prefix + "reqedit requestID \"newRequestText\"", "approve": "Usage: " + prefix + "approve requestID", "reject": "Usage: " + prefix + "reject requestID", "setapprovedchannel": "Usage: " + prefix + "setapprovedchannel channelName [Defaults to current channel]"}

emoji_pattern = re.compile('[^\s!-~]', re.UNICODE)

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

@bot.command()
async def request(ctx, *args):
	global requestId
	if len(args) == 1:
		requestsFromUser = 0
		for req in requests:
			if req["author"] == ctx.author:
				#Get change in time between now and the time of the request for ANTI SPAM
				minutes_diff = (datetime.datetime.now() - datetime.datetime.strptime(req["timestamp"], datefmt)).total_seconds() / 60.0
				if int(minutes_diff) < 5:
					requestsFromUser += 1
					if requestsFromUser > 1:
						return await ctx.send(ctx.author.mention + " you have already made 2 requests in the last 5 minutes! Try again later")

		requests.append({"request": args[0], "author": ctx.author, "timestamp": datetime.datetime.now().strftime(datefmt), "approved": False, "requestId": requestId})
		await ctx.send("```Request Submitted: \"{}\"\n\nSubmitted By: {}\nRequest ID: {}```".format(args[0], ctx.author, requestId))

		reqdb.requests.insert_one(
			{
				"request": args[0],
				"author": str(ctx.author),
				"timestamp": requests[-1]["timestamp"],
				"approved": False,
				"edited": False,
				"requestId": requestId
			}
		)

		requestId += 1
	else:
		return await ctx.send(usageInformation["request"])

@bot.command()
async def reqedit(ctx, *args):
	if len(args) == 2 and args[0].isdigit():
		editedRequest = False
		for req in requests:
			if req["requestId"] == int(args[0]):
				editedRequest = True
				if req["author"] == ctx.author or any([True for role in ctx.author.roles if str(role) == moderatorRole]):
					for reqA in approvedRequests:
						if reqA["requestId"] == req["requestId"]:
							return await ctx.send("Your request has already been approved, you cannot edit an already approved request.")
					req["request"] = args[1]
					reqdb.requests.update_one({"requestId": req["requestId"]}, {"$set": {"request": req["request"], "edited": True}})
					await ctx.send("```Request Resubmitted: \"{}\"\n\nSubmitted By: {}\nEdited By: {}\nRequest ID: {}```".format(req["request"], req["author"], ctx.author, req["requestId"]))
				else:
					return await ctx.send("You do not have the required permissions to edit this request (not the author/not a mod)")
		if not editedRequest:
			await ctx.send("Could not find a request with that ID")
	else:
		await ctx.send(usageInformation["reqedit"])

@bot.command()
async def approve(ctx, *args):
	global approvedChannel
	if any([True for role in ctx.author.roles if str(role) == moderatorRole]) or ctx.author.guild_permissions.administrator:
		if len(args) == 1 and args[0].isdigit():
			approvedRequest = None
			for req in requests:
				if int(req["requestId"]) == int(args[0]):
					approvedRequest = req

			if not approvedRequest:
				return await ctx.send("Could not find request with ID " + args[0])
				
			if approvedRequest["approved"]:
				return await ctx.send("This request has already been approved")
		
			approvedRequest["approved"] = True

			if approvedChannel == None:
				for tc in ctx.guild.text_channels:
					if str(tc) == config["approvedChannel"]:
						approvedChannel = tc
			await ctx.send("Approved request with ID: " + str(approvedRequest["requestId"]))

			if approvedChannel == None:
				await ctx.send("Couldn't find a valid approved-requests channel, please set the approved channel using !setapprovedchannel")
			else:
				await approvedChannel.send("```Approved Request: \"{}\"\n\nSubmitted By: {}\nRequest ID: {}```".format(approvedRequest["request"], approvedRequest["author"], approvedRequest["requestId"]))
			
			reqdb.requests.update_one({"requestId": approvedRequest["requestId"]}, {"$set": {"approved": True}})

		else:
			await ctx.send(usageInformation["approve"])
	else:
		await ctx.send("You do not have the required permissions to use this command")

@bot.command()
async def reject(ctx, *args):
	global requestId
	if any([True for role in ctx.author.roles if str(role) == moderatorRole]) or ctx.author.guild_permissions.administrator:
		if len(args) == 1 and args[0].isdigit():
			rejectRequest = None
			for req in requests:
				if int(req["requestId"]) == int(args[0]):
					rejectRequest = req

			if not rejectRequest:
				return await ctx.send("Could not find request with ID " + args[0])

			if rejectRequest["approved"]:
				await ctx.send("This request was already approved, removing from approved list")

				for reqA in approvedRequests:
					if reqA["requestId"] == rejectRequest["requestId"]:
						approvedRequests.remove(reqA)
						async for message in approvedChannel.history(limit=200):
							if message.author == bot.user:
								if "Request ID: " + str(rejectRequest["requestId"]) in message.content:
									await message.delete()
									break

			if requests[-1] == rejectRequest:
				if requestId != 0:
					requestId = requestId - 1

			requests.remove(rejectRequest)
			reqdb.requests.delete_one({"requestId": rejectRequest["requestId"]})

			await ctx.send("Request rejected and removed")
		else:
			await ctx.send(usageInformation["reject"])
	else:
		await ctx.send("You do not have the required permissions to use this command")

@bot.command()
async def setapprovedchannel(ctx, *args):
	global approvedChannel
	if any([True for role in ctx.author.roles if str(role) == moderatorRole]) or ctx.author.guild_permissions.administrator:
		tc = None

		#If the sender has specified a channel
		if len(args) == 1:
			targettcname = emoji_pattern.sub(r'', str(args[0]).replace("#", ""))
			for guildtc in ctx.guild.text_channels:
				#Remove emojis from text channel name
				guildtcname = emoji_pattern.sub(r'', str(guildtc))
				#If the input was a text channel id given by #channelname
				if targettcname.replace("<", "").replace(">", "").isdigit():
					if int(targettcname.replace("<", "").replace(">", "")) == guildtc.id:
						tc = guildtc
				#If the input was a text channel name
				elif guildtcname == targettcname:
					tc = guildtc

			if tc == None:
				return await ctx.send("Could not find text channel " + args[0] + " in server")
			else:
				approvedChannel = tc
				await ctx.send("Set approved requests channel to " + str(approvedChannel))
				config["approvedChannel"] = str(approvedChannel)
				with open("config.json", "w") as f:
					json.dump(config, f)
		#If the user hasn't specified a channel
		elif len(args) == 0:
			approvedChannel = ctx.message.channel
			await ctx.send("Set approved requests channel to " + str(approvedChannel))

			#Change the approvedChannel and write that change to the config file
			config["approvedChannel"] = str(approvedChannel)
			with open("config.json", "w") as f:
				json.dump(config, f)
		else:
			await ctx.send(usageInformation["setapprovedchannel"])
	else:
		await ctx.send("You do not have the required permissions to use this command")

@bot.command()
async def clearallrequests(ctx, *args):
	global requestId
	if any([True for role in ctx.author.roles if str(role) == moderatorRole]) or ctx.author.guild_permissions.administrator:
		reqdb.requests.delete_many({})
		requests.clear()
		requestId = 0
		await ctx.send("Cleared requests")
	else:
		await ctx.send("You do not have the required permissions to use this command")

@bot.command()
async def showallrequests(ctx, *args):
	if any([True for role in ctx.author.roles if str(role) == moderatorRole]) or ctx.author.guild_permissions.administrator:
		if requests != []:
			for req in requests:
				await ctx.send("```Request Submitted: \"{}\"\n\nSubmitted By: {}\nApproved: {}\nRequest ID: {}```".format(req["request"], req["author"], req["approved"], req["requestId"]))
		else:
			await ctx.send("No requests")
	else:
		await ctx.send("You do not have the required permissions to use this command")

@bot.command()
async def help(ctx, *args):
	response = "```Simple Request Bot by The_G0dPiXeL\nAvailable Commands:"
	for cmd, usage in usageInformation.items():
		response += "\n\t{}{}\n\t\t{}\n\t\t{}".format(prefix, cmd, usage, permissionInformation[cmd])
	response += "```"
	await ctx.send(response)

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	await bot.process_commands(message)

@bot.event
async def on_ready():
	global requestId
	print('We have logged in as {0.user}'.format(bot))

	#Populate requests list with requests from database
	for req in reqdb.requests.find({}):
		requests.append({"request": req["request"], "author": req["author"], "timestamp": req["timestamp"], "approved": req["approved"], "edited": req["edited"], "requestId": req["requestId"]})
	
	#Sets requestId to the previous requestId + 1
	requestId = int(requests[-1]["requestId"]) + 1
	print("Loaded requests")
	await bot.change_presence(activity=discord.Game("Simple Requests. Prefix: " + config["prefix"]))

bot.run(config["token"])

