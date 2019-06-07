import discord
import datetime
import time
import csv
import os
import json

from discord.ext import commands

with open("config.json", "r") as config_file:
	config = json.load(config_file)

prefix = config["prefix"]

bot = commands.Bot(command_prefix=prefix)
bot.remove_command('help')

requestId = 0
datefmt = "%I:%M%p on %B %d, %Y"
requests = []
approvedRequests = []
approvedChannel = config["approvedChannel"]
moderatorRole = "Moderator"
usageInformation = {"request": "Usage: " + prefix + "request \"requestText\"", "reqedit": "Usage: " + prefix + "reqedit requestID \"text\"", "approve": "Usage: " + prefix + "approve requestID", "reject": "Usage: " + prefix + "reject requestID", "setapprovedchannel": "Usage: " + prefix + "setapprovedchannel channelName [Defaults to current channel]"}

@bot.command()
async def request(ctx, *args):
	global requestId
	if len(args) == 1:
		requestsFromUser = 0
		for req in requests:
			if req["author"] == ctx.author:
				# timeDeltaMinutes = str((time.time() - req["time"]) % 3600 // 60)
				# if timeDeltaMinutes[0] == "0" or timeDeltaMinutes[0] == ".":
				# 	timeDeltaMinutes = timeDeltaMinutes[2:]
				# timeDeltaMinutes.replace(".0", "")
				# if int(timeDeltaMinutes) < 5:
				# 	requestsFromUser += 1
				# 	if requestsFromUser > 1:
				# 		return await ctx.send(ctx.author.mention + " you have already made 2 requests in the last 5 minutes! Try again later")
				minutes_diff = (datetime.datetime.now() - datetime.datetime.strptime(req["timestamp"], datefmt)).total_seconds() / 60.0
				if int(minutes_diff) < 5:
					requestsFromUser += 1
					if requestsFromUser > 1:
						return await ctx.send(ctx.author.mention + " you have already made 2 requests in the last 5 minutes! Try again later")



				# rqDateTime = datetime.datetime.strptime(requests["timestamp"], "%I:%M%p on %B %d, %Y")
				# currentDateTime = datetime.datetime.strptime(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
				# rqDateTimeDelta = rqDateTime, datetime.datetime.strptime(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
				# if rqDateTime.year == 
				# if requests["timestamp"][requests["timestamp"].index("on ") + 3:] == datetime.date.today().strftime("%B %d, %Y"):
				#     if datetime.datetime.strptime(requests["timestamp"], "%I:%M%p on %B %d, %Y") == datetime.datetime.now().strftime("%I:%M%p"):

		requests.append({"request": args[0], "author": ctx.author, "time": time.time(), "timestamp": datetime.datetime.now().strftime(datefmt), "approved": False, "requestId": requestId})
		await ctx.send("```Request Submitted: \"{}\"\n\nSubmitted By: {}\nRequest ID: {}```".format(args[0], ctx.author, requestId))
		requestId += 1

		# with open("requests.csv", "w") as requestsFile:
		# 	fieldnames = ["request", "author", "time", "timestamp", "approved", "requestId"]
		# 	writer = csv.DictWriter(requestsFile, fieldnames=fieldnames)

		# 	writer.writeheader()
		# 	writer.writerow(requests[-1])
	else:
		return await ctx.send(usageInformation["request"])

@bot.command()
async def showallrequests(ctx, *args):
	if any([True for role in ctx.author.roles if str(role) == moderatorRole]) or ctx.author.guild_permissions.administrator:
		if requests != []:
			for req in requests:
				await ctx.send("```Request Submitted: \"{}\"\n\nSubmitted By: {}\nRequest ID: {}```".format(req["request"], req["author"], req["requestId"]))
		else:
			await ctx.send("No requests")
	else:
		await ctx.send("You do not have the required permissions to use this command")
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
					await ctx.send("```Request Resubmitted: \"{}\"\n\nSubmitted By: {}\nRequest ID: {}```".format(req["request"], ctx.author, req["requestId"]))
					with open("requests.csv", "w") as requestsFile:
						fieldnames = ["request", "author", "time", "timestamp", "approved", "requestId"]
						writer = csv.DictWriter(requestsFile, fieldnames=fieldnames)

						writer.writeheader()
						writer.writerow(requests[-1])
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
				if req["requestId"] == int(args[0]):
					approvedRequest = req
			if not approvedRequest:
				return await ctx.send("Could not find request with ID " + args[0])
			if approvedRequest["approved"]:
				return await ctx.send("This request has already been approved")
			
			approvedRequests.append(approvedRequest)
			approvedRequest["approved"] = True
			if approvedChannel == None:
				for tc in ctx.guild.text_channels:
					if str(tc) == "approved-requests":
						approvedChannel = tc
			await ctx.send("Approved request with ID: " + str(approvedRequest["requestId"]))

			if approvedChannel == None:
				await ctx.send("Couldn't find a valid approved-requests channel, please set the approved channel using !setapprovedchannel")
			else:
				await approvedChannel.send("```Approved Request: \"{}\"\n\nSubmitted By: {}\nRequest ID: {}```".format(approvedRequest["request"], approvedRequest["author"], approvedRequest["requestId"]))
			with open("requests.csv", "w") as requestsFile:
				fieldnames = ["request", "author", "time", "timestamp", "approved", "requestId"]
				writer = csv.DictWriter(requestsFile, fieldnames=fieldnames)

				writer.writeheader()
				writer.writerow(requests[-1])
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
				if req["requestId"] == int(args[0]):
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
			if requests.index(rejectRequest) == len(requests) - 1:
				requestId = requestId - 1
			requests.remove(rejectRequest)
			await ctx.send("Request rejected and removed")
		else:
			await ctx.send(usageInformation["reject"])
	else:
		await ctx.send("You do not have the required permissions to use this command")

@bot.command()
async def setapprovedchannel(ctx, *args):
	global approvedChannel
	if any([True for role in ctx.author.roles if str(role) == moderatorRole]) or ctx.author.guild_permissions.administrator:
		tc = ""
		if len(args) == 1:
			for tc in ctx.guild.text_channels:
				if args[0] == str(tc):
					tc = args[0]
			if tc == "":
				return await ctx.send("Could not find text channel " + args[0] + " in server")
			else:
				approvedChannel = tc
				await ctx.send("Set approved requests channel to " + str(approvedChannel))
		elif len(args) == 0:
			approvedChannel = ctx.message.channel
			await ctx.send("Set approved requests channel to " + str(approvedChannel))

		else:
			await ctx.send(usageInformation["setapprovedchannel"])
	else:
		await ctx.send("You do not have the required permissions to use this command")

@bot.command()
async def help(ctx, *args):
	response = "```Simple Request Bot by The_G0dPiXeL\nAvailable Commands:"
	for cmd, usage in usageInformation.items():
		response += "\n\t{}{} {}".format(prefix, cmd, usage)
	response += "```"
	await ctx.send(response)

@bot.event
async def on_message(message):
	# do some extra stuff here
	if message.author == bot.user:
		return
	await bot.process_commands(message)

@bot.event
async def on_ready():
	global requestId
	print('We have logged in as {0.user}'.format(bot))
	if os.path.isfile("requests.csv"):
		#load requests
		with open("requests.csv") as requestsFile:
			reader = csv.DictReader(requests)
			for req in reader:
				print(req)
				requests.append({"request": req["request"], "author": req["author"], "time": req["time"], "timestamp": req["timestamp"], "approved": req["approved"], "requestId": req["requestId"]})
			print(requests)
			if requests:
				requestId = requests[len(requests) - 1]["requestId"] + 1
		print("Loaded previous requests")

bot.run(config["token"])