import praw

app_ua = '/u/danstansrevolution/ to find streams and send PM to users'
app_id = 'YOUR APP ID'
app_secret = 'YOUR APP SECRET'
app_uri = 'https://127.0.0.1:65010/authorize_callback'

app_refresh = 'YOUR APP REFRESH TOKEN'

def login():
	r = praw.Reddit(app_ua)
	r.set_oauth_app_info(app_id,app_secret, app_uri)
	r.refresh_access_information(app_refresh)
	return r
