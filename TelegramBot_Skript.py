import json 
import requests
import time
import urllib


TOKEN = "386823692:AAFGIZvCUw7AVXIhxLICHIjeLNetgeO3mfw"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
professors = [164399314]
students = [264043624]
break_requests = []

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def send_message_to_all(text, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    chat_ids = professors + students
    print (chat_ids)
    for i in chat_ids:
        url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, i)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        get_url(url)
    
def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)
    
            
def build_keyboard():
    #keyboard = [[item] for item in items]
    keyboard = ['breakrequest']
    #reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": False}
    return json.dumps(reply_markup)

def handle_updates(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            user = update["message"]["from"]["id"]
            if text == "/break":
                if user in break_requests:
                    send_message("already requested break earlier", chat)
                else:
                    send_message("break requested", chat)
                    break_requests.append(user)
                    print(break_requests)
            elif text == "/start_lecture":
                if user in professors:
                    send_message_to_all("the lecture has started")
                else:
                    send_message("only professors are allowed to use this function", chat)
            elif text == "/stop_lecture":
                if user in professors:
                    send_message_to_all("the lecture has stopped")
                else:
                    send_message("only professors are allowed to use this function", chat)
            else:
                send_message("cannot process this message. please use /break to request a break", chat)
                print()
            #if text == "/done":
            #    keyboard = build_keyboard(items)
            #    send_message("Select an item to delete", chat, keyboard)
            #elif text in items:
            #    db.delete_item(text)
            #    items = db.get_items()
            #    keyboard = build_keyboard(items)
            #    send_message("Select an item to delete", chat, keyboard)
            #else:
            #    db.add_item(text)
            #    items = db.get_items()
            #    message = "\n".join(items)
            #    send_message(message, chat)
        except Exception as e:
                print(e)
    
    
def main():
    last_update_id = None
    keyboard = build_keyboard()
    while True:
        print("getting updates")
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(1.0)

        
if __name__ == '__main__':
    main()