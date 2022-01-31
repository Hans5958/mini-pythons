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

parser = argparse.ArgumentParser(description="Removes duplicate videos from a YouTube playlist.")
parser.add_argument("--playlist", type=str, help="the targeted playlist")
parser.add_argument("--client-secrets-file", type=str, default="client-secret.json", help="the destination playlist where the videos is going to be")

args = parser.parse_args()

playlist = args.playlist

assert playlist != None, "You must supply the playlist ID."

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

videos = []
added_video_ids = []
curr_page = 1

print("Authenticated!")

print(f"Printing page {curr_page}...")

request = youtube.playlistItems().list(
	part = "snippet",
	maxResults = 50,
	playlistId = playlist,
)

response = request.execute()

for item in response["items"]:

	video_id = item["snippet"]['resourceId']['videoId']
	if video_id in added_video_ids: 
		videos.push({
			"video_id": video_id,
			"playlist_id": item['id']
		})
		print(f"Queued {video_id} to be removed.")
	else:
		print(f"Skipped {video_id}.")


with open(f"response{curr_page}.json", "w") as f:
	f.write(json.dumps(response))

while response.get('nextPageToken'):

	curr_page += 1
	print(f"Printing page {curr_page}...")

	request = youtube.playlistItems().list(
		part = "snippet",
		maxResults = 50,
		playlistId = playlist,
		pageToken = response["nextPageToken"]
	)

	response = request.execute()

	for item in response["items"]:
	
		video_id = item["snippet"]['resourceId']['videoId']
		if video_id in added_video_ids: 
			videos.push({
				"video_id": video_id,
				"playlist_id": item['id']
			})
			print(f"Queued {video_id} to be removed.")
		else:
			print(f"Skipped {video_id}.")


	with open(f"response{curr_page}.json", "w") as f:
		f.write(json.dumps(response))

print(f"{len(videos)} videos queued to be removed.")

if len(videos) == 0:
	print("Oh, wait. No duplicates! How lovely!")
	sys.exit(0)

with open("videos.json", "w") as f:
	f.write("\n".join(videos))

input("Press ENTER to continue.")

print("Removing videos from the origin playlist...")

for video in videos:

	request = youtube.playlistItems().delete(
		id = video["playlist_id"]
	)
	
	print(f"Removing {video['video_id']}...")
	
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

with open("responsedelete.json", "w") as f:
	f.write(json.dumps(response))

print("All videos on the origin playlist have been removed!")
print("All done!")