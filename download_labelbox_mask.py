#!/usr/bin/env python
# coding: utf-8

#  This is a test of downloading a mask image from Labelbox using an API key rather
#  than the "token" parameter at the end of the instanceURI, and then writing directly
#  to a file based on the response content
#  https://www.kite.com/python/answers/how-to-download-an-image-using-requests-in-python

import requests

url = "https://api.labelbox.com/masks/feature/ckbi4pe6y0xzr0yc9h1601e6z"
with open('api_key.txt') as f:
    api_key = f.read()

headers = {'Authorization':'Bearer '+ api_key.strip()}

# In principle could also pass the token as params to requests.get()
#   if we didn't need the API key (or could still pass that in headers)
# e.g.
# instanceURI = "https://api.labelbox.com/masks/feature/ckbi4pe6y0xzr0yc9h1601e6z?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJja2IxMjNyYXkwbHdkMDc4MWkwcWE4a2VzIiwib3JnYW5pemF0aW9uSWQiOiJjazkzYnYxcndwanZyMDk0MGQ4bmpidXJ3IiwiaWF0IjoxNTkyNTA1MjIyLCJleHAiOjE1OTUwOTcyMjJ9.bMz4CkoTOH_5ALL7dAgYd8ff_lDntxOxVxuqbX9V0IQ"
# payload = {"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJja2IxMjNyYXkwbHdkMDc4MWkwcWE4a2VzIiwib3JnYW5pemF0aW9uSWQiOiJjazkzYnYxcndwanZyMDk0MGQ4bmpidXJ3IiwiaWF0IjoxNTkyNTA1MjIyLCJleHAiOjE1OTUwOTcyMjJ9.bMz4CkoTOH_5ALL7dAgYd8ff_lDntxOxVxuqbX9V0IQ"}
# response = requests.get(url, stream=True, params=payload)

response = requests.get(url, stream=True, headers=headers)
if response.status_code == 200:
    with open('img.png', 'wb') as out_file:
        out_file.write(response.content)

del response
