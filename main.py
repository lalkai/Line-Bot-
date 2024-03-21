# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationSendMessage,
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot import (
    AsyncLineBotApi, WebhookParser
)
from fastapi import Request, FastAPI, HTTPException
from fastapi.responses import FileResponse
import aiohttp
import os
import subprocess
import sys
from bot import ask_2
from fastapi import File, Form, UploadFile
from fastapi.responses import HTMLResponse
from linebot.exceptions import LineBotApiError
import tracemalloc
import random
import time



os.environ['LINE_CHANNEL_SECRET'] = "SECRET"
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = "ACCESS_TOKEN"


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

app = FastAPI()
session = aiohttp.ClientSession()
async_http_client = AiohttpAsyncHttpClient(session)
line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)
parser = WebhookParser(channel_secret)


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        user_text = event.message.text
        
        res = ask_2(user_text)

        await line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=res)
        )

    return 'OK'

@app.get("/")
async def form_get():
    return HTMLResponse("""
        <html>
            <head>
                <title>send Text and Photo</title>
            </head>
            <body>
                <form action="/send" method="post" enctype="multipart/form-data">
                    <label for="text">Text:</label>
                    <textarea id="text" name="text"></textarea>
                    <br><br>
                    <label for="photo">Photo:</label>
                    <input type="file" id="photo" name="photo">
                    <br><br>
                    <input type="submit" value="send">
                </form>
            </body>
        </html>
    """)

@app.get("/image/{rn}", tags=["rn"])
def image(rn: str):
    return FileResponse(f"photo/{rn}.jpg")

def randomName(current_time):
    random.seed(current_time)
    random_ = random.random() 
    return random_ 

@app.post("/send")
async def send( text: str = Form(None), photo: UploadFile = Form(...)):
    tracemalloc.start()
   
    current_time = int(time.time())
    rn = str(randomName(current_time)).replace(".","")
    
    with open(f"photo/P{rn}.jpg", "wb") as f:
        f.write(await photo.read())

    try:
        if photo.size == 0:
            await line_bot_api.broadcast(TextSendMessage(text=text))
        elif text is None:
            await line_bot_api.broadcast(ImageSendMessage(original_content_url=f"url/image/P{rn}",
                                                      preview_image_url=f"url/image/P{rn}"))
        else:
            await line_bot_api.broadcast(TextSendMessage(text=text))
            await line_bot_api.broadcast(ImageSendMessage(original_content_url=f"url/image/P{rn}",
                                                      preview_image_url=f"url/image/P{rn}"))
        
        
    except LineBotApiError as e:
        print(e)
    

    return "successfully"

