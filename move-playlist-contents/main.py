import os
import json
import math
import argparse

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import BatchHttpRequest

parser = argparse.ArgumentParser(description="Moves videos from a playlist (origin) to a new playlist (destination).")
parser.add_argument("--origin-playlist", type=str, help="the origin playlist ID where the videos listed will be moved to another playlist")
parser.add_argument("--destination-playlist", type=str, help="the destination playlist ID where the videos is going to be")
parser.add_argument("--client-secrets-file", type=str, default="client-secret.json", help="the destination playlist where the videos is going to be")

args = parser.parse_args()

origin_playlist = args.origin_playlist
destination_playlist = args.origin_playlist

assert origin_playlist != None, "You must supply the origin playlist ID."
assert destination_playlist != None, "You must supply the destination playlist ID."

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = args.client_secrets_file

flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
	client_secrets_file, scopes)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(
	api_service_name, api_version, credentials=credentials)

request = youtube.playlistItems().list(
	part = "snippet",
	maxResults = 50,
	playlistId = origin_playlist
)

response = request.execute()

with open("response1.json", "w") as f:
	f.write(json.dumps(response))

# print(response)

video_ids = []
video_playlist_ids = []

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

		with open(f"response{curr_page}.json", "w") as f:
			f.write(json.dumps(response))

print("All videos obtained.")

with open("videoids.json", "w") as f:
	f.write("\n".join(video_ids))

with open("videoplaylistids.json", "w") as f:
	f.write("\n".join(video_playlist_ids))


input("Press any key to continue.")

print("Adding videos to the destination playlist...")

insert_batch = youtube.new_batch_http_request()

for video_id in video_ids:
	insert_batch.add(youtube.playlistItems().insert(
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
	))

	# request = youtube.playlistItems().insert(
	# 	part = "snippet",
	# 	body = {
	# 		"snippet": {
	# 			"playlistId": destination_playlist,
	# 			"resourceId": {
	# 				"kind": "youtube#video",
	# 				"videoId": video_id
	# 			}
	# 	  	}
	# 	}
	# )
	
	# request.execute()

response = insert_batch.execute()

with open("responseinsert.json", "w") as f:
	f.write(json.dumps(response))

print("All videos have been added on the destination playlist!")

input("Press any key to continue.")

print("Removing videos from the origin playlist...")

delete_batch = youtube.new_batch_http_request()

for video_playlist_id in video_playlist_ids:
	delete_batch.add(youtube.playlistItems().delete(
		id = video_playlist_id
	))

	# request = youtube.playlistItems().insert(
	# 	part = "snippet",
	# 	body = {
	# 		"snippet": {
	# 			"playlistId": destination_playlist,
	# 			"resourceId": {
	# 				"kind": "youtube#video",
	# 				"videoId": video_id
	# 			}
	# 	  	}
	# 	}
	# )
	
	# request.execute()


response = delete_batch.execute()

with open("responsedelete.json", "w") as f:
	f.write(json.dumps(response))

print("All videos on the origin playlist have been removed!")
print("All done!")