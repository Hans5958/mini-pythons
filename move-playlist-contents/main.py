import os
import json
import math
import argparse
import sys

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import BatchHttpRequest
from googleapiclient.errors import HttpError

parser = argparse.ArgumentParser(description="Moves videos from a playlist (origin) to a new playlist (destination).")
parser.add_argument("--origin-playlist", type=str, help="the origin playlist ID where the videos listed will be moved to another playlist")
parser.add_argument("--destination-playlist", type=str, help="the destination playlist ID where the videos is going to be"),
parser.add_argument("--batch-file", type=argparse.FileType('r', encoding='utf-8'))
parser.add_argument("--client-secrets-file", type=str, default="client-secret.json", help="the destination playlist where the videos is going to be")
parser.add_argument("--move", action='store_true')
parser.add_argument("--log-debug-files", action='store_true')

args = parser.parse_args()

move = args.move
log_debug_files = args.log_debug_files
if not args.batch_file == None:
	batch_str = args.batch_file.read()
else:
	batch_str = False

queue = []

if args.origin_playlist and args.destination_playlist:
	queue.append([args.origin_playlist, args.destination_playlist])
elif batch_str:
	for line in batch_str.split():
		queue.append(line.split(','))
else:
	exit("You give me nothing to move. What the hell should I do?")

def move_playlist_contents(
	origin_playlist, 
	destination_playlist,
	youtube,
	move=False,
	log_debug_files=False
):

	request_add = youtube.playlistItems().list(
		part = "snippet",
		maxResults = 50,
		playlistId = origin_playlist
	)

	try:
		response = request_add.execute()
	except HttpError as err:
		if err.resp.status in [404]:
			print("Playlist not found. Ending.")
			return
		else:
			print("Something went wrong!")
			raise err
	except Exception as e:
		print("Something went wrong!")
		raise e

	if log_debug_files:
		with open("response1.json", "w") as f:
			f.write(json.dumps(response))

	# print(response)

	video_ids = []
	processed_video_ids = []

	print("Authenticated!")
	print("Printing page 1...")

	for item in response["items"]:
		video_ids.append((item["snippet"]['resourceId']['videoId'], item['id']))

	total_pages = math.ceil(response["pageInfo"]["totalResults"]/response["pageInfo"]["resultsPerPage"])

	if total_pages != 1:

		curr_page = 1

		while curr_page != total_pages:

			curr_page += 1

			print(f"Printing page {curr_page}...")

			request_add = youtube.playlistItems().list(
				part = "snippet",
				maxResults = 50,
				playlistId = origin_playlist,
				pageToken = response["nextPageToken"]
			)

			response = request_add.execute()

			for item in response["items"]:
				video_ids.append((item["snippet"]['resourceId']['videoId'], item['id']))

			if log_debug_files:
				with open(f"response{curr_page}.json", "w") as f:
					f.write(json.dumps(response))

	print(f"Found {len(video_ids)} videos.")

	if log_debug_files:

		with open("videoids.txt", "w") as f:
			f.write("\n".join(video_ids))

	# input("Press ENTER to continue.")
    
	video_ids.reverse()

	print("Adding videos to the destination playlist...")

	for video_id, video_playlist_id in video_ids:
		
		if video_id in processed_video_ids:
			print(f"{video_id} skipped, entry is duplicate.")
					
		else:
			request_add = youtube.playlistItems().insert(
				part = "snippet",
				body = {
					"snippet": {
						"playlistId": destination_playlist,
						"resourceId": {
							"kind": "youtube#video",
							"videoId": video_id
						}
					}
				}
			)
			
			request_remove = youtube.playlistItems().delete(
				id = video_playlist_id
			)
			
			print(f"Moving {video_id}... ", end="")
			try:
				request_add.execute()
				print(f"Added. ", end="")
				if move:
					request_remove.execute()
					print(f"Deleted.")
				processed_video_ids.append(video_id)
			except HttpError as err:
				if err.resp.status in [404]:
					print()
					print(f"{video_id} not found. Skipping.")
		
	# insert_batch = youtube.new_batch_http_request()

	# for video_id in video_ids:
	# 	insert_batch.add(youtube.playlistItems().insert(
	# 		part = "snippet",
	# 		body = {
	# 			"snippet": {
	# 				"playlistId": destination_playlist,
	# 				"resourceId": {
	# 					"kind": "youtube#video",
	# 					"videoId": video_id
	# 				}
	# 		  	}
	# 		}
	# 	))

	# response = insert_batch.execute()

	# if log_debug_files:

	# 	with open("responseinsert.json", "w") as f:
	# 		f.write(json.dumps(response))

	print("All videos have been added on the destination playlist!")
	print("All done!")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = args.client_secrets_file

flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
	client_secrets_file, 
	[
		"https://www.googleapis.com/auth/youtube.force-ssl"
	],
	redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

auth_url, _ = flow.authorization_url(prompt='consent')

print('Please go to this URL: {}'.format(auth_url))
code = input('Enter the authorization code: ')

try:
	flow.fetch_token(code=code)
	credentials = flow.credentials
except:
	print("That code does not work! Try again!")
	exit()
youtube = googleapiclient.discovery.build(
	api_service_name, api_version, credentials=credentials)

for current in queue:

	move_playlist_contents(
		current[0], 
		current[1], 
		youtube,
		move,
		log_debug_files
	)
