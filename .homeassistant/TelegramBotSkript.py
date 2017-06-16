#import of all needed packages
import json
import requests
import time
import urllib
import logging

#token and url for telegram access
TOKEN = "386823692:AAFGIZvCUw7AVXIhxLICHIjeLNetgeO3mfw"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

#declaration of variables for authorization and notification handling
global professors
global students
global break_requests
professors = [164399314, 264043624]
students = []
break_requests = []
al1, al2, al3 = 0

#logger setup
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('/home/homeassistant/.homeassistant/logs/TelegramBot.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

#returns content of a url response
def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

#formats url response as json
def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

#gets updates from telegram every 10 seconds
def get_updates(offset=None):
    url = URL + "getUpdates?timeout=10"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

#returns the id of the last update received from telegram
def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

#registers a new student by appending their user id to the students list
#student will now receive notifications and be able to request a break
def register(user_id):
    global students
    students.append(user_id)

#unregisters a specific student by removing their user id from the students list
#student will no longer receive notifications and be able to request a break
def unregister(user_id):
    global students
    students.remove(user_id)

#send a telegram message to a specific chat id
def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

#sends a telegram message to all user ids currently registered as professor or student
def send_message_to_all(text, reply_markup=None):
    global professors, students
    text = urllib.parse.quote_plus(text)
    chat_ids = professors + students
    for i in chat_ids:
        url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, i)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        get_url(url)
        
#sets the state of an entity in home assistant (unfortunately only temporary as sensor values cannot be overwritten)
def set_state(entityID, value):
    url = "http://192.168.1.135:8123/api/states/" + entityID
    r = requests.post(url, json=value)
    
#toggles the button in the home assistant interface
#used to request breaks and turn lecture on and off
def toggle_button(info):
    r = requests.post("http://192.168.1.135:8123/api/services/input_boolean/toggle", json=info)
    
#checks if lecture button is currently set to on or to off and sends the respective message to all registered user ids
def lectureButtontoggled():
    resp = requests.get("http://192.168.1.135:8123/api/states/input_boolean.stopwatch")
    response = json.loads(resp.text)
    if response['state'] == "on":
        send_message_to_all("the lecture has been stopped")
        break_requests.clear()
    else:
        send_message_to_all("the lecture has started")

#builds a custom inline keyboard
#idea was to enable break requests via a button as well as the /break command in telegram
#not yet fully implemented
def build_keyboard():
    keyboard = ['breakrequest']
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": False}
    return json.dumps(reply_markup)

#handle updates received by the telegram bot
def handle_updates(updates):
    global professors, students, break_requests
    for update in updates["result"]:
        try:
            #extract the input text, chat id and user id from the telegram update
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            user = update["message"]["from"]["id"]
            chat_ids = professors + students
            #handle break requests
            if text == "/break":
                #users that have previously requested a break cannot do so again
                if user in break_requests:
                    send_message("already requested break earlier", chat)
                    logger.info("A user tried to request a break. Request was denied due to existing request.")
                #users have to be registered (either as a student or a professor) to request a break
                elif user in chat_ids:
                    info = {"entity_id": "input_boolean.breakrequest"}
                    toggle_button(info)
                    send_message("break requested", chat)
                    break_requests.append(user)
                    logger.info("A user tried to request a break.")
                #unknown users are asked to register before they can request a break
                else:
                    send_message("please register as a student via /register in order to be able to request a break", chat)
            #handle lecture start request
            elif text == "/start_lecture":
                #user needs to be a professor in order to successfully start the lecture
                if user in professors:
                    value = {"attributes": {"friendly_name": "Lecture"}, "state": "on"}
                    set_state("input_boolean.stopwatch", value)
                    #send_message_to_all("the lecture has started")
                    #logger.info("A professor started the lecture.")
                else:
                    send_message("only professors are allowed to use this function", chat)
                    logger.info("A student tried to start the lecture. Request was denied.")
            #handle lecture stop request
            elif text == "/stop_lecture":
                #user needs to be a professor in order to successfully stop the lecture
                if user in professors:
                    value = {"attributes": {"friendly_name": "Lecture"}, "state": "off"}
                    set_state("input_boolean.stopwatch", value)
                    break_requests.clear()
                    al1, al2, al3 = 0
                    #send_message_to_all("the lecture has stopped")
                    #logger.info("A professor stopped the lecture.")
                else:
                    send_message("only professors are allowed to use this function", chat)
                    logger.info("A student tried to stop the lecture. Request was denied.")
            #handle request to register as a student
            elif text == "/register":
                #a user can only be register as a student once (unless they unregistered in the meantime)
                if user in students:
                    send_message("you are already registered as a student", chat)
                    logger.info("A student tried to register a second time. Request was denied.")
                #professors cannot register as a student
                elif user in professors:
                    send_message("you are already registered as a professor", chat)
                    logger.info("A professor tried to register as a student. Request was denied.")
                #if a user is neither previously registered as a student or professor, they are added as a student
                else:
                    send_message("you are now registered as a student", chat)
                    logger.info("A new student registered.")
                    register(user)
            #handle request to unregister as a student
            elif text == "/unregister":
                #a user registered as a student will be removed from the student list
                if user in students:
                    unregister(user)
                    send_message("you are no longer registered as a student. you will not receive further notifications", chat)
                    logger.info("A student unregistered.")
                #professors cannot unregister via this function
                elif user in professors:
                    send_message("you are registered as a professor. you cannot unregister via this button", chat)
                    logger.info("A professor tried to unregister as a student. Request was denied.")
                #anyone not in the student list cannot unregister from student status
                else:
                    send_message("you were not registered in the first place", chat)
                    logger.info("Someone not registered tried to unregister. Request was denied.")
            #handle info that button was toggled in home assistant
            elif text == "/buttontoggled":
                resp = requests.get("http://192.168.1.135:8123/api/states/input_boolean.stopwatch")
                response = json.loads(resp.text)
                #check whether lecture was started or stopped via home assistant, send out corresponding message
                if response['state'] == "on":
                    send_message_to_all("the lecture was started")
                    logger.info("the lecture button was started")
                if response['state'] == "off":
                    send_message_to_all("the lecture was ended")
                    logger.info("the lecture button was ended")
            #handle alert that breakscore has exceeded limit, send message to users
            elif text == "/breakalert":
                send_message_to_all("you should take a break. conditions in the room are no longer optimal.")
                logger.info("alert to take break sent.")
            #handle alert that light is too dim, send message to users
            elif text == "/lightalert":
                send_message_to_all("you should turn on the lights. it is too dark in the room.")
                logger.info("alert to turn on light sent.)
            #handle alert that air quality is too low, send message to users
            elif text == "/airalert":
                send_message_to_all("you should open the window. there is too much CO2 in the room.")
                logger.info("alert to open window sent."
            #handle input not recognized as one of the above cases
            else:
                send_message("invalid input. please use one of the commands found under /", chat)
                logger.info("Invalid input.")
        #catch exceptions - avoid script disruption due to temporary unavailability of home assistant (such as reboot)
        except Exception as e:
                print(e)
    

#main function - contains an infinite loop
#gets all new updates from telegram since the last update processed by this script
#calls the function handle updates to react to telegram updates
#then handles any possible status changes in home assistant (lecture turned on/off, limits for break/air quality/brightness crossed)
def main():
    last_update_id = None
    response1 = None
    keyboard = build_keyboard()
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
            time.sleep(1)
        try:
            #check if lecture status has changed, send update to telegram bot so it can react accordingly
            resp = requests.get("http://192.168.1.135:8123/api/states/input_boolean.stopwatch")
            response = json.loads(resp.text)
            if response['state'] == response1: 
                pass
            else:
                response1 = response['state']
                update = {'ok': True, 'result': [{'update_id': 0, 'message': {'message_id': 765, 'from': {'id': 0, 'first_name': 'J', 'language_code': 'de-DE'}, 'text': '/buttontoggled', 'chat': {'type': 'private', 'id': 0, 'first_name': 'J'}, 'date': 1497357549, 'entities': [{'offset': 0, 'type': 'bot_command', 'length': 6}]}}]}
                handle_updates(update)
            #check if break score has exceeded limit, send update to telegram bot so it can notify users
            resp = requests.get("http://192.168.1.135:8123/api/states/sensor.breakscore")
            response = json.loads(resp.text)
            if response['state'] < 100:
                pass
            else:
                if al1 = 0:
                    al1 = 1
                    update = {'ok': True, 'result': [{'update_id': 0, 'message': {'message_id': 765, 'from': {'id': 0, 'first_name': 'J', 'language_code': 'de-DE'}, 'text': '/breakalert', 'chat': {'type': 'private', 'id': 0, 'first_name': 'J'}, 'date': 1497357549, 'entities': [{'offset': 0, 'type': 'bot_command', 'length': 6}]}}]}
                    handle_updates(update)
                else:
                    pass
            #check if brightness has fallen below limit, send update to telegram bot so it can notify users
            resp = requests.get("http://192.168.1.135:8123/api/states/isensor.hhz_eg125_light_b_10_0")
            response = json.loads(resp.text)
            if response['state'] > 200: 
                pass
            else:
                if al2 = 0:
                    al2 = 1
                    update = {'ok': True, 'result': [{'update_id': 0, 'message': {'message_id': 765, 'from': {'id': 0, 'first_name': 'J', 'language_code': 'de-DE'}, 'text': '/lightalert', 'chat': {'type': 'private', 'id': 0, 'first_name': 'J'}, 'date': 1497357549, 'entities': [{'offset': 0, 'type': 'bot_command', 'length': 6}]}}]}
                    handle_updates(update)
                else:
                    pass
            #check if air quality has fallen below limit, send update to telegram bot so it can notify users
            resp = requests.get("http://192.168.1.135:8123/api/states/sensor.hhz_eg125_airquality_a_9_1")
            response = json.loads(resp.text)
            if response['state'] < 900: 
                pass
            else:
                if al3 = 0:
                    al3 = 1
                    update = {'ok': True, 'result': [{'update_id': 0, 'message': {'message_id': 765, 'from': {'id': 0, 'first_name': 'J', 'language_code': 'de-DE'}, 'text': '/airalert', 'chat': {'type': 'private', 'id': 0, 'first_name': 'J'}, 'date': 1497357549, 'entities': [{'offset': 0, 'type': 'bot_command', 'length': 6}]}}]}
                    handle_updates(update)
                else:
                    pass
        except:
            pass

#executes main function upon start of python script
if __name__ == '__main__':
        main()