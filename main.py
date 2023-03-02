import json
import os
from io import BytesIO
from http.client import responses

from PIL import Image
from attd import AttributeDict as AttrDict
import requests

MAX_URL_CHARS = 256

try:
  with open('system.json') as f:
    system = AttrDict(json.load(f))
except FileNotFoundError:
  raise SystemExit("The `system.json` file from PK needs to exist!")

try:
  with open('config.json') as f:
    config = json.load(f)
    os.makedirs(config["output_folder"], exist_ok=True)
    output_folder = config["output_folder"]
    base_url = config["base_url"]
    urls_only = config["urls_only"]
    if base_url.endswith('/'):
      base_url = base_url[:-1]
except FileNotFoundError:
  raise SystemExit("The `config.json` file doesn't exist! Can't set the base URLs so doing nothing!")

try:
  with open(f"{output_folder}/cached_urls.json") as f:
    cached_urls = json.load(f)
except FileNotFoundError:
  cached_urls = {}

if len(f"{base_url}/00000000-0000-0000-0000-000000000000.png") > MAX_URL_CHARS:
  raise SystemExit("The base URL is too long!")

try:
  with open(f"{output_folder}/index.json") as f:
    avatars = json.load(f)
except FileNotFoundError:
  avatars = {}

nextMember = 0

avatar_url = system.avatar_url
if avatar_url and cached_urls.get("system_avatar", None) != avatar_url:
  if not urls_only:
    print("Fetching system avatar...")
    r = requests.get(avatar_url)

    if r.status_code == 200: # The 'okay' status code
      avatar = BytesIO(r.content) # So we can do file operations
      img = Image.open(avatar)

      img.save(f"{output_folder}/{system.uuid}.png")

      img.close()
      avatar.close()
    else:
      print(f"Avatar URL for the system gives status code `{r.status_code}`! Reason: `{responses[r.status_code]}`")

  else:
    print("Caching system avatar..")

  avatars["system_avatar"] = f"{system.uuid}.png"
  system.avatar_url = f"{base_url}/{avatars['system_avatar']}"

  cached_urls["system_avatar"] = system.avatar_url

while nextMember < len(system.members):
  member = system.members[nextMember]
  nextMember += 1

  try:
    avatar_url = member.avatar_url
    if avatar_url == None:
      continue

    if cached_urls.get(member.name, None) == avatar_url:
      continue

  except AttributeError:
    continue

  if not urls_only:
    print(f"Fetching avatar for {member.name}...")
    r = requests.get(avatar_url)

    if r.status_code != 200: # The 'okay' status code
      print(f"Avatar URL for {member.display_name} gives status code `{r.status_code}`! Reason: `{responses[r.status_code]}`")
      continue

    avatar = BytesIO(r.content) # So we can do file operations
    img = Image.open(avatar)

    img.save(f"{output_folder}/{member.uuid}.png")

    img.close()
    avatar.close()
  else:
    print(f"Caching {member.name}'s avatar...")

  avatars[member.name] = f"{member.uuid}.png"
  system.members[nextMember-1].avatar_url = f"{base_url}/{avatars[member.name]}"

  cached_urls[member.name] = system.members[nextMember-1].avatar_url

with open(f"{output_folder}/index.json", 'w+') as f:
  json.dump(avatars, f, indent=2)

with open(f"{output_folder}/cached_urls.json", 'w+') as f:
  json.dump(cached_urls, f, indent=2)

with open('system.json', 'w+') as f:
  json.dump(system, f, indent=2)
