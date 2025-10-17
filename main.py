# Thanks very much to https://stackoverflow.com/questions/70634321/how-to-get-membership-badges-for-youtube-live-chat-messages/70660765#70660765
# Also, the live JSON is of a very similar format to .live_chat.json files I get from yt-dlp. I might borrow from this file in future.

import requests
import re
import time
import json

def actiontomessage(action):
    message=""
    
    runs=action["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["message"]["runs"]

    for run in runs:
        if "text" in run: #check for keys without causing exceptions, hopefully
            message += run["text"]
        elif "emoji" in run:
            if "isCustomEmoji" in run["emoji"]: #check for channel-specific emoji
                message += "CustEmoji"
                message += run["emoji"]["shortcuts"][0]
                continue
            message += run["emoji"]["emojiId"]
    
    return message
    






#videoid = '_uMuuHk_KkQ' #Lofi-Girl Live stream 
videoid = '6pqGVd4xhrY' #Kanata Elden Ring
ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'
#ua= 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

url = "https://www.youtube.com/live_chat?v=" + videoid

r = requests.get(url, headers={"user-agent": ua})

initial = r.text

try:
    continuation = re.findall('continuation":"(.+?)"', initial)[0]
    #continuation=continuation[16:-1]
    continuation=continuation.replace("%3D","=")
    ##print(continuation)
except Exception as e:
    print(e)
    print("BUGGER!")
    print(re.findall('continuation":"(.+?)"', initial))
    with open("bugger.html", "w") as text_file:
        text_file.write(r.text)

    exit()

#The "key" is the api key that the youtube website uses to talk to the internal YouTube API. It is not an API key for my personal account.
#If it stops working, the new key would be inside the html page we fetch above. It's called INNERTUBE_API_KEY somewhere in the JS.
conturl="https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"  #parsing prettyprinted might have a performance impact, but it's easier to debug.
#conturl="https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false"

while True:
    #print("loopBegins")


    contpayload={"context":{"client":{"clientName":"WEB","clientVersion":"2.9999099"}},"continuation":continuation}

    time.sleep(0.2)
    r2 = requests.post(conturl, json=contpayload)

    contResp = r2.json()
    ##print(contResp["continuationContents"]["liveChatContinuation"]["continuations"][0]["invalidationContinuationData"]["continuation"])
    try:
        continuation = contResp["continuationContents"]["liveChatContinuation"]["continuations"][0]["invalidationContinuationData"]["continuation"]
    except Exception as e:
        print(e)
        print("DARN!")
        print(contpayload)
        with open("DARN.json", "w") as text_file:
           text_file.write(r2.text)
        exit()
    continuation=continuation.replace("%3D","=")

    try:
        actions=contResp["continuationContents"]["liveChatContinuation"]["actions"]
    except Exception as e:
        #print("no actions?")
        continue

    for action in actions:
        if "addChatItemAction" in action:
            author_name=action["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["authorName"]["simpleText"]
            print(author_name+": "+actiontomessage(action))
        elif "addBannerToLiveChatCommand" in action:
            print("BANNER DETECTED! SKIPPING!")
        elif "removeChatItemAction" in action:
            print('{"removeChatItemAction": {"targetItemId": "SomeItemID"}}')
        else:
            print("UNKNOWN ACTION DETECTED! DUMPING ACTION!")
            print("#######################################")
            print(json.dumps(action)[0:150])
            print("#######################################")
        continue
        
        
        try:
            if action["addBannerToLiveChatCommand"]:
                print("BANNER DETECTED! SKIPPING!")
                continue
        except KeyError:
            try:
                author_name=action["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["authorName"]["simpleText"]
                print(author_name+": "+actiontomessage(action))
            except Exception as e:
                print('{"removeChatItemAction": {"targetItemId": "SomeItemID"}}')
        
        #try:
        #    #if action["addBannerToLiveChatCommand"]:
        #  #      print("BANNER DETECTED! SKIPPING!")
        #  #      continue
        #    author_name=action["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["authorName"]["simpleText"]
       #    print(author_name)
        #except Exception as e:
       #     print("FOR FAILED! NOT BAILING!\n")
       #     print(json.dumps(action)[0:100])
        #    print("\n")
            #print(json.dumps(action))
        #    exit()
