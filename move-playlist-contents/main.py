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

	
	request = youtube.playlistItems().list(
		part = "snippet",
		maxResults = 50,
		playlistId = origin_playlist
	)

	try:
		response = request.execute()
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
	video_playlist_ids = []
	added_video_ids = []

	print("Authenticated!")
	print("Printing page 1...")

	for item in response["items"]:
		video_ids.append(item["snippet"]['resourceId']['videoId'])
		video_playlist_ids.append(item['id'])

	total_pages = math.ceil(response["pageInfo"]["totalResults"]/response["pageInfo"]["resultsPerPage"])

	if total_pages != 1:

		curr_page = 1

		while curr_page != total_pages:

			curr_page += 1

			print(f"Printing page {curr_page}...")

			request = youtube.playlistItems().list(
				part = "snippet",
				maxResults = 50,
				playlistId = origin_playlist,
				pageToken = response["nextPageToken"]
			)

			response = request.execute()

			for item in response["items"]:
				video_ids.append(item["snippet"]['resourceId']['videoId'])
				video_playlist_ids.append(item['id'])

			if log_debug_files:
				with open(f"response{curr_page}.json", "w") as f:
					f.write(json.dumps(response))

	print(f"Found {len(video_ids)} videos.")

	if log_debug_files:

		with open("videoids.json", "w") as f:
			f.write("\n".join(video_ids))

		with open("videoplaylistids.json", "w") as f:
			f.write("\n".join(video_playlist_ids))

	# input("Press ENTER to continue.")

	print("Adding videos to the destination playlist...")

	for video_id in video_ids:
		
		if video_id in added_video_ids:
			print(f"{video_id} skipped, entry is duplicate.")
					
		else:
			request = youtube.playlistItems().insert(
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
			
			print(f"Adding {video_id}...")
			try:
				request.execute()
				added_video_ids.append(video_id)
			except HttpError as err:
				if err.resp.status in [404]:
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

	if log_debug_files:

		with open("responseinsert.json", "w") as f:
			f.write(json.dumps(response))

	print("All videos have been added on the destination playlist!")

	# input("Press ENTER to continue.")

	if move:

		print("Removing videos from the origin playlist...")

		for video_playlist_id in video_playlist_ids:

			request = youtube.playlistItems().delete(
				id = video_playlist_id
			)
			
			print(f"Removing {video_playlist_id}...")
			
			try:
				request.execute()
			except HttpError as err:
				if err.resp.status in [404]:
					time.sleep(0)

		# delete_batch = youtube.new_batch_http_request()

		# for video_playlist_id in video_playlist_ids:
		# 	delete_batch.add(youtube.playlistItems().delete(
		# 		id = video_playlist_id
		# 	))

		# response = delete_batch.execute()

		if log_debug_files:

			with open("responsedelete.json", "w") as f:
				f.write(json.dumps(response))

		print("All videos on the origin playlist have been removed!")
		
	print("All done!")

scopes = ["https://www.googleapis.com/auth/youtube"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = args.client_secrets_file

flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
	client_secrets_file, scopes)
try:
	credentials = flow.run_console()
except:
	sys.exit("That code does not work! Try again!")
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
