import praw
import obotdStans ##change back to obot later
import sqlite3
import time
import datetime
from pprint import pprint

SUBREDDIT = "test"
CONTENT_SUBREDDIT = "nbastreams+mlbstreams+nhlstreams"
MAXPOSTS = 10
MANDATORY_PHRASE_COMMENTS = ["/u/streamFinder", "/u/streamFinder/" ]
MANDATORY_PHRASE_SUBMISSION = "game thread"
SETPHRASES = ["BRAVES", "MARLINS", "METS", "PHILLIES", "NATIONALS", "CUBS", "REDS", "BREWERS", "PIRATES",  "DIAMONDBACKS", "ROCKIES", "DODGERS", "PADRES", "ORIOLES", "RED SOX", "YANKEES", "RAYS", "BLUE JAYS", "WHITE SOX", "INDIANS", "TIGERS", "ROYALS", "TWINS", "ASTROS", "ATHLETICS", "MARINERS", "CELTICS", "NETS", "KNICKS", "76ERS", "RAPTORS", "BULLS", "CAVALIERS", "PISTONS", "PACERS", "BUCKS", "HAWKS", "HORNETS", "HEAT", "MAGIC", "WIZARDS", "NUGGETS", "TIMBERWOLVES", "THUNDER", "TRAIL BLAZER", "JAZZ", "WARRIORS", "CLIPPERS", "LAKERS", "SUNS", "MAVERICKS", "ROCKETS", "GRIZZLIES", "PELICANS", "SPURS", "BILLS", "DOLPHINS", "PATRIOTS", "JETS", "RAVENS", "BENGALS", "BROWNS", "STEELERS", "TEXANS", "COLTS", "JAGUARS", "TITANS", "BRONCOS", "CHIEFS", "RAIDERS", "CHARGERS", "COWBOYS", "EAGLES", "REDSKINS", "BEARS", "LIONS", "PACKERS", "VIKINGS", "FALCONS", "SAINTS", "BUCCANEERS", "RAMS", "49ERS", "SEAHAWKS", "HURRICANES", "BLUE JACKETS", "DEVILS", "ISLANDERS", "FLYERS", "PENGUINS", "CAPITALS", "BRUINS", "SABRES", "RED WINGS", "CANADIENS", "SENATORS", "LIGHTNING", "MAPLE LEAFS", "BLACKHAWKS", "AVALANCHE", "STARS", "WILD", "PREDATORS", "BLUES", "JETS", "DUCKS", "COYOTES", "FLAMES", "OILERS", "SHARKS", "CANUCKS", "ny rangers", "tx rangers", "sl cardinals", "az cardinals", "sf giants", "ny giants", "sac kings", "la kings", "fl panthers", "nc panthers"]

SPECIAL_SETPHRASES = ["RANGERS" , "CARDINALS", "GIANTS", "KINGS", "PANTHERS"]## (MLB/NHL MLB/NFL MLB/NFL NBA/NHL NHL/NFL)

SETRESPONSE_SUCCESS = "You have been subscribed to: "
SETRESPONSE_FAIL = "Your query "
WAITTIME = 20


sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldMessages(message_ID, message_TEXT TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS oldPost(comment_ID TEXT, comment_TEXT TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS userRelationTeam(user_name TEXT, team_name TEXT)')
sql.commit()

r = praw.Reddit("/u/streamFinder program that finds streams to PM users")
print("Logging in to reddit")
r = obotdStans.login() ##change back to obot later

def searchBot():
	print("Fetching subreddit "  + SUBREDDIT + " For Comments")
	subreddit = r.get_subreddit(SUBREDDIT)
	print('Fetching comments')
	comments = subreddit.get_comments(limit=MAXPOSTS)
	for comment in comments:
		realTeams = False
		returnString = ""
		cur.execute('SELECT * FROM oldpost WHERE comment_ID=?', [comment.id])
		if not cur.fetchone():
			try:
				cauthor = comment.author.name
				cbody = comment.body.lower()
				if any(mandKey.lower() in cbody for mandKey in MANDATORY_PHRASE_COMMENTS):
					for key in SETPHRASES:
					 	if (" " + key.lower() in cbody):
					 		realTeams = True
					 		cur.execute('SELECT * FROM userRelationTeam WHERE user_name=? AND team_name=?', [cauthor, key.lower()])
					 		if not cur.fetchone():
					 			cur.execute('INSERT INTO userRelationTeam (user_name, team_name) VALUES(?,?)', [cauthor, key.lower()])
							returnString = returnString + key.lower() + ', '		
				if realTeams:
					print("Making a response to " + cauthor)
					comment.reply(SETRESPONSE_SUCCESS + returnString[:-2])
			except AttributeError:
				pass

			cur.execute('INSERT INTO oldpost (comment_ID, comment_TEXT) VALUES(?,?)', [comment.id, cbody])
			sql.commit()


def responseBot():
	content =[]
	print("Fetching subreddit "  + CONTENT_SUBREDDIT + " For Game Threads")
	content_subreddit = r.get_subreddit(CONTENT_SUBREDDIT)
	content += list(content_subreddit.get_hot(limit=20))

	for post in content:
		teams = []
		pTitle = post.title.lower()
		textBody = ""
		maxUps = 0
		if MANDATORY_PHRASE_SUBMISSION in pTitle:
			gameTime = getTime(post)
			for key in SETPHRASES:
				if (" " + key.lower() in pTitle):
					teams.append(key.lower())
			for key in SPECIAL_SETPHRASES:
				if (" " + key.lower() in pTitle):
					if (post.author.name == "NHLStreamsBot"):
						if (" " + key.lower() == " rangers"):
							teams.append("ny rangers")
						elif (" " + key.lower() == " kings"):
							teams.append("la kings")
						elif (" " + key.lower() == " panthers"):
							teams.append("fl panthers")
					elif (post.author.name == "MLBStreamsBot1"):
						if (" " + key.lower() == " rangers"):
							teams.append("tx rangers")
						elif (" " + key.lower() == " giants"):
							teams.append("sf giants")
						elif (" " + key.lower() == " cardinals"):
							teams.append("sl cardinals")
					elif (post.author.name == "nflstreamsbot"):
						if (" " + key.lower() == " cardinals"):
							teams.append("az cardinals")
						elif (" " + key.lower() == " giants"):
							teams.append("ny giants")
						elif (" " + key.lower() == " panthers"):
							teams.append("nc panthers")
					elif (post.author.name == "NBAstreamsBot"):
						if (" " + key.lower() == " kings"):
							teams.append("sac kings")
				submissionComments = post.comments
				for comment in submissionComments:
					try:
						pauthor = comment.author.name
						if (comment.ups > maxUps):
							textBody = comment.body ## This is the text that we want to PM to the user
							maxUps = comment.ups
					except AttributeError:
						continue
			currentTime = int(getCurrentTime())
			if (currentTime == gameTime +5):
				for t in teams:                          
					cur.execute('SELECT * FROM userRelationTeam WHERE team_name=?', [t])
					for row in cur:
						##try:
						r.send_message(row[0], t, textBody, raise_captcha_exception=True)
						##except praw.errors.InvalidCaptcha as e:
							##captcha_id = e.response['captcha']
							##captcha_response = e.response		

def unsubscribeBot():
	print("Fetching Messages")
	gen = r.get_inbox(limit=1000)
	for thing in gen:
		message_Author = thing.author.name if thing.author else None
		message_content = thing.body.lower()
		message_subject = thing.subject.lower()
		message_id = thing.id
		cur.execute('SELECT * FROM oldMessages WHERE message_ID=?', [message_id])
		if not cur.fetchone():
			try:
				if "unsubscribe" in message_content:
					if message_content == "unsubscribe all":
						##Delete from subscriptions
						print("Found a new message (ALL)")
						cur.execute('DELETE FROM userRelationTeam WHERE user_name=?', [message_Author])
						##print("Removed user from databases")
					elif message_content == "unsubscribe":
						print("Found a new message")
						if "re: " in message_subject:
							cur.execute('DELETE FROM userRelationTeam WHERE user_name=? AND team_name=?', [message_Author,message_subject[4:]])
						else:
							cur.execute('DELETE FROM userRelationTeam WHERE user_name=? AND team_name=?', [message_Author,message_subject])
					else:
						print("could not remove user")
			except AttributeError:
				pass

			cur.execute('INSERT INTO oldMessages (message_ID, message_TEXT) VALUES(?,?)', [message_id, message_content])
			sql.commit()


def getTime(Post):
	title_Post = Post.title.lower()
	comment_Author = Post.author.name
	if (comment_Author == "NHLStreamsBot"):
		position_of_PM = title_Post.find("pm", 0)
		return(return24Time("0" + title_Post[position_of_PM-4:position_of_PM-3] + title_Post[position_of_PM-2:position_of_PM] ))
	elif (comment_Author == "NBAstreamsBot"):
		position_of_PM = title_Post.find("pm", 0)
		return(return24Time(title_Post[position_of_PM-6:position_of_PM-4] + title_Post[position_of_PM-3:position_of_PM]))
	elif (comment_Author == "MLBStreamsBot1"):
		position_of_PM = title_Post.find("pm", 0)
		return(return24Time(title_Post[position_of_PM-5:position_of_PM-4] + title_Post[position_of_PM-3:position_of_PM]))
	else:
		return (-1000)


def return24Time(twelveTime):
	twelveNUM = int(twelveTime[:2])
	twentyFourNUM = twelveNUM+12
	return (int(str(twentyFourNUM) + twelveTime[2:]))

def getCurrentTime():
	stringTime = time.strftime("%H:%M")
	numTime = int(stringTime[:2])
	numTime = numTime + 3
	return(str(numTime) + stringTime[3:])

while True:
	searchBot()
	responseBot()
	unsubscribeBot()
	print("Checking again in 20 seconds...")
	time.sleep(WAITTIME)
