# Thanks very much to https://stackoverflow.com/questions/70634321/how-to-get-membership-badges-for-youtube-live-chat-messages/70660765#70660765
# Also, the live JSON is of a very similar format to .live_chat.json files I get from yt-dlp. I might borrow from this file in future.

import requests
import re
import time
import json
import traceback

import sys


# This function name is self explanatory, but it only works for regular chat messages.
# Superchats and those big green messages that members sometimes send will not be printed.
# If you pass in one of those actions, it will throw an exception.
def actiontomessage(action):
    message=""
    
    runs=action["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["message"]["runs"]

    for run in runs:
        if "text" in run: #check for keys without causing exceptions, hopefully
            message += run["text"]
        elif "emoji" in run:
            if "isCustomEmoji" in run["emoji"]: #check for channel-specific emoji
                message += run["emoji"]["shortcuts"][0]
                continue
            message += run["emoji"]["emojiId"]
    
    return message
    
ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'

if len(sys.argv) == 2:
    arg = sys.argv[1]
    if arg[0] == '@':
        print("Getting live page for "+arg, file=sys.stderr)
        page = requests.get("https://www.youtube.com/"+arg+"/live").text 
        found = re.findall('property="og:url" content="(.+?)v=(.+?)">', page) 
        if len(found) == 0:
            print("No Live Streams available for that channel. Check your spelling, or provide a video ID.", file=sys.stderr)
            exit()
        else: # If you ever get an exception here, that means that the initial live page has changed construction. Let me know about it, and then provide a stream videoid instead.
            videoid=found[0][1] 
            # A channel can have multiple live and waiting streams. The /live page will only show one, so we should say which.
            print("Found videoid: "+videoid, file=sys.stderr)
            found = re.findall('property="og:title" content="(.+?)">', page)
            if len(found) != 0:
                print("Video Title: "+found[0], file=sys.stderr)


    elif len(arg) == 11:
        videoid=arg
    else:
        print("bad argument")
        exit()

url = "https://www.youtube.com/live_chat?v=" + videoid





r = requests.get(url, headers={"user-agent": ua})
initial = r.text

try:
    continuation_token = re.findall('continuation":"(.+?)"', initial)[0]
    continuation_token=continuation_token.replace("%3D","=")
except Exception as e:
    print(e)
    print("BUGGER!")
    print(re.findall('continuation":"(.+?)"', initial))
    with open("bugger.html", "w") as text_file:
        text_file.write(r.text)
    print("I could not find the initial continuation token. Are you sure the video ID is for a current livestream?")
    print("Page dumped to 'bugger.html'. ")
    exit()


#The "key" is the api key that the youtube website uses to talk to the internal YouTube API. It is not an API key for my personal account.
#If it stops working, the new key would be inside the html page we fetch above. It's called INNERTUBE_API_KEY somewhere in the JS.
conturl="https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false"

while True:


    contpayload={"context":{"client":{"clientName":"WEB","clientVersion":"2.9999099"}},"continuation":continuation_token}

    time.sleep(0.2)
    r2 = requests.post(conturl, json=contpayload)

    contResp = r2.json()

    # Get the next token from the payload
    try:
        if "invalidationContinuationData" in contResp["continuationContents"]["liveChatContinuation"]["continuations"][0]: # running stream
            continuation_token = contResp["continuationContents"]["liveChatContinuation"]["continuations"][0]["invalidationContinuationData"]["continuation"]
        else: # waiting stream
            continuation_token = contResp["continuationContents"]["liveChatContinuation"]["continuations"][0]["timedContinuationData"]["continuation"]
    except Exception as e:
        print(e)
        print("DARN!")
        print("I could not find the next continuation token. The stream probably ended.")
        print("Response dumped to 'DARN.json'. ")
        print("Below is what we sent in the request")
        print(contpayload)
        with open("DARN.json", "w") as text_file:
           text_file.write(r2.text)
        exit()
    continuation_token=continuation_token.replace("%3D","=")

    try:
        actions=contResp["continuationContents"]["liveChatContinuation"]["actions"]
    except Exception as e:
        #print("no actions?")
        continue

    for action in actions:
        try:

            if "addChatItemAction" in action:
                if "liveChatPaidMessageRenderer" in action["addChatItemAction"]["item"]: #superchats hava a different JSON message to regular chats. I'll decipher later.
                    cashman_name=action["addChatItemAction"]["item"]["liveChatPaidMessageRenderer"]["authorName"]["simpleText"]
                    print(cashman_name+ " PAID SOME MONEY FOR A MESSAGE.")
                elif "liveChatMembershipItemRenderer" in action["addChatItemAction"]["item"]: #same goes for the big messages that members sometimes send. #2025-09-10 addition: which is the same renderer used for when someone joins the membership.
                    member_name=action["addChatItemAction"]["item"]["liveChatMembershipItemRenderer"]["authorName"]["simpleText"]
                    print("MEMBER "+member_name+" HAS SENT A BIG MESSAGE. I'M NOT SAYING WHAT IT IS.")
                elif "liveChatPlaceholderItemRenderer" in action["addChatItemAction"]["item"]:# found this during a test on 2025-08-22. I'm not sure what it is. The exception meant I couldnt crosscheck the id with later msgs
                    print("PLACEHOLDER!   ID:"+action["addChatItemAction"]["item"]["liveChatPlaceholderItemRenderer"]["id"])
                elif "liveChatSponsorshipsGiftPurchaseAnnouncementRenderer" in action["addChatItemAction"]["item"]: # found this at 00:30 on 2025-08-31. It's for gifted memberships. I can't believe I didn't think of it b4.
                    render=action["addChatItemAction"]["item"]["liveChatSponsorshipsGiftPurchaseAnnouncementRenderer"]
                    print("PERSON "+render["header"]["liveChatSponsorshipsHeaderRenderer"]["authorName"]["simpleText"]+" GIFTED SOME MEMBERSHIPS TO THE AUDIENCE")
                elif "liveChatSponsorshipsGiftRedemptionAnnouncementRenderer" in action["addChatItemAction"]["item"]: # 2025-09-10 00:42 another one for redeeming a gift
                    render=action["addChatItemAction"]["item"]["liveChatSponsorshipsGiftRedemptionAnnouncementRenderer"]
                    print("PERSON "+render["authorName"]["simpleText"]+" RECEIVED A GIFTED MEMBERSHIP")
                else: # regular chat messages
                    txtmsg = action["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]
                    author_name = txtmsg["authorName"]["simpleText"]
                    message_id  = txtmsg["id"]
                    timestamp   = txtmsg["timestampUsec"]
                    print(timestamp+"  "+message_id[0:15]+"  "+author_name.ljust(15, ' ')+":   "+actiontomessage(action)[0:180])
            elif "addBannerToLiveChatCommand" in action: # It's been long enough that I've forgotten what banners are.
                print("BANNER DETECTED! SKIPPING!")
            elif "removeChatItemAction" in action: # These don't appear in replay files. I assume they're for when mods remove stuff. //confirmed 2025-08-22 20:20
                print('removeChatItemAction')
            elif "addLiveChatTickerItemAction" in action: # This is for the "recent things" ticker at the top of the chat. It's a bit redundant because anything that causes a ticker update will also cause an addChatItem.
                print("TICKER UPDATE WEEWOO WEEWOO WEEWOO")
            elif "replaceChatItemAction" in action: # 2025-08-22 oh, so that's what it's for
                print("REPLACEACTION "+action["replaceChatItemAction"]["targetItemId"])
            elif "removeChatItemByAuthorAction" in action: # 2025-09-11 I can only assume this removes all messages from a specific author.
                print ("REMOVE ITEMS BY CHANNEL "+ action["removeChatItemByAuthorAction"]["externalChannelId"])
            #I know there will be other types of action and other types of renderer in the addChatItemAction. I've never captured a poll, for instance. That's why I have the else and the except below. They catch the unknowns.

            else:
                print("UNKNOWN ACTION DETECTED! DUMPING ACTION!")
                print("#######################################")
                print(json.dumps(action))
                print("#######################################")
                exit();
        except Exception as e:
            print("BIG IF FAILED! BAILING!\n")
            print("\n")
            print(json.dumps(action))
            print("#########################")
            print(traceback.format_exc())
            exit()
