from flask import Flask, jsonify, request
import json
from discord_interactions import verify_key_decorator, InteractionType, InteractionResponseType, InteractionResponseFlags
import cv2
import cvzone
from cvzone.SelfiSegmentationModule import SelfiSegmentation
from requests_toolbelt import MultipartEncoder
from PIL import ImageFont, ImageDraw, Image  
import numpy as np  
import requests
from io import BytesIO
import logging

logger = logging.basicConfig(
    format='[%(asctime)s] %(process)d-%(levelname)s : %(message)s', 
    datefmt='%d-%b-%y %H:%M:%S', 
    filename='logs/weezer.log', 
    level=logging.DEBUG)


application = Flask(__name__)
application.debug = False
CLIENT_PUBLIC_KEY = "PUBLIC_KEY"

@application.route('/interactions', methods=['POST'])
@verify_key_decorator(CLIENT_PUBLIC_KEY)
def application_commands():
    if request.json["type"] == 1:
        return jsonify({
            "type": 1
        })
    if request.json['type'] == InteractionType.APPLICATION_COMMAND:
        if request.json['data']['name'] == 'weezer':
            
            if not (request.json['data']['resolved']['attachments'][list(request.json['data']['resolved']['attachments'])[0]]['proxy_url'].lower().endswith(('.png', '.jpg', '.jpeg'))):
                return jsonify({
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": "Only `PNG`, `JPG` & `JPEG` are accepted.",
                        "ephemeral": True
                    }
                })


            response = requests.get(request.json['data']['resolved']['attachments'][list(request.json['data']['resolved']['attachments'])[0]]['proxy_url'])
            image_stream = BytesIO(response.content)
            image_stream.seek(0)
            file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
            imgOffice = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            segmentor = SelfiSegmentation()

            imgOffice = cv2.resize(imgOffice, (640, 480))
            green = (202, 148, 1)

            imgNoBg = segmentor.removeBG(imgOffice, green, threshold=0.70)

            text = 'weezer'

            cv2_im_rgb = cv2.cvtColor(imgNoBg, cv2.COLOR_BGR2RGB)  
            pil_im = Image.fromarray(cv2_im_rgb)  
            draw = ImageDraw.Draw(pil_im)  
            font = ImageFont.truetype("CenturyGothic.ttf", 50)  
            draw.text((450, -10), text, font=font, fill='black')  
            img_byte_arr = BytesIO()
            pil_im.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            url = f"https://discord.com/api/v10/interactions/{request.json['id']}/{request.json['token']}/callback"

            files = {
                'files[0]': ('image.jpeg', img_byte_arr, 'image/jpeg')
            }
            r = requests.post(
                url,
                files = files, 
                data = {
                    "payload_json": json.dumps({
                        "type": 4,
                        "data": {
                            "tts": False,
                            "embeds": [
                                {
                                    "title": "Your weezed image!",
                                    "color": 0x0194CA,
                                    "image": {
                                        "url": "attachment://image.jpeg"
                                    }
                                }
                            ],
                            "components": [{
                                "type": 1,
                                "components": [
                                    {
                                        "type": 2,
                                        "label": "Invite me",
                                        "style": 5,
                                        "url": "https://discord.com/oauth2/authorize?client_id=1064191884546801774&scope=bot%20applications.commands&permissions=0"
                                    },
                                    {
                                        "type": 2,
                                        "label": "Donate",
                                        "style": 5,
                                        "url": "https://uwu.gal/r/kofi"
                                    },
                                ]
                            }],
                            "attachments": [
                                {
                                    "id": 0,
                                    "description": "verification image",
                                    "filename": "image.jpeg"
                                }
                            ]
                        }
                    })
                },
                headers = {}
            )
            return {}