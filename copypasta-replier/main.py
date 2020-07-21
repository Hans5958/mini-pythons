import argparse
import tweepy

parser = argparse.ArgumentParser(description="")
parser.add_argument("--copypasta-input", type=str, help="the copypasta text file")
parser.add_argument("--reply-id", type=str, help="the id of the tweet to be replied")

args = parser.parse_args()

reply_id = args.reply_id
copypasta_dir = args.copypasta_input
copypasta_file = open(copypasta_dir)
copypasta_lines = copypasta_file.readlines()
copypasta_lines = list(map(lambda string: string.rstrip(), copypasta_lines))
copypasta_file.close()

auth = tweepy.OAuthHandler("CONSUMER_KEY", "CONSUMER_SECRET")
auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")

tweet_api = tweepy(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

last_chain_id = 0

# The lines below are untested.

for copypasta_line in copypasta_lines:
	if (index == 0):
		tweet = tweet_api.update_status(copypasta_line, reply_id, True, True)
		last_chain_id = tweet.id
	else:
		tweet = tweet_api.update_status(copypasta_line, last_chain_id, True, False)
		last_chain_id = tweet.id
	print(copypasta_line)