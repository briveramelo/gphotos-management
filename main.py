import os, pickle
from collections import defaultdict
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def run():
    # 1. Auth & service setup
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
    cred_file = 'credentials.json'
    token_file = 'token.pickle'
    if os.path.exists(token_file):
        creds = pickle.load(open(token_file, 'rb'))
    else:
        flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
        creds = flow.run_local_server(port=0)
        pickle.dump(creds, open(token_file, 'wb'))
    service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

    # 2. Page through ALL media items
    def list_all_media():
        next_token = None
        while True:
            resp = service.mediaItems().list(
                pageSize=100,
                pageToken=next_token
            ).execute()
            for item in resp.get('mediaItems', []):
                yield item
            next_token = resp.get('nextPageToken')
            if not next_token:
                break

    # 3. Group by (filename + creationTime)
    groups = defaultdict(list)
    for m in list_all_media():
        key = (m['filename'], m['mediaMetadata']['creationTime'])
        groups[key].append(m['id'])

    # 4. For each group with >1, delete all but the first
    to_delete = []
    for ids in groups.values():
        if len(ids) > 1:
            # preserve the first copy, trash the rest
            to_delete.extend(ids[1:])

    if not to_delete:
        print("No duplicates found.")
    else:
        print(f"Deleting {len(to_delete)} duplicate items…")
        # chunk in batches of 50
        for i in range(0, len(to_delete), 50):
            batch = to_delete[i:i+50]
            service.mediaItems().batchDelete(body={'mediaItemIds': batch}).execute()
        print("Done.")

if __name__ == '__main__':
    run()
