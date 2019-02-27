import threading
import time
import random

import requests


class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self.chats = []
        self.messages = []
        self.updates = []
        self.first_unread_message = 0

    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        try:
            resp = requests.get(self.api_url + method, params)
        except requests.exceptions.ConnectionError:
            print("could not connect to telegram!")
            return []
        result_json = resp.json()['result']
        for key in result_json:
            kl = key.keys()
            if key['update_id'] not in self.updates and 'message' in kl:
                self.updates.append(key['update_id'])
                self.messages.append(key['message'])
                if key['message']['chat']['id'] not in self.chats:
                    self.chats.append(key['message']['chat'])
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_unread_messages(self):
        self.get_updates()
        new_messages = []

        while self.messages and self.first_unread_message < len(self.messages):
            new_messages.append(self.messages[self.first_unread_message])
            self.first_unread_message += 1

        return new_messages


my_bot = BotHandler("<YOUR BOT TOKEN>")


class Printer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            messages = my_bot.get_unread_messages()
            for message in messages:
                last_chat_text = message['text']
                last_chat_name = message['chat']['first_name']
                print(last_chat_name + ": " + last_chat_text)


class Assigner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    @staticmethod
    def random_derangement(n):
        while True:
            v = list(range(n))
            for j in range(n - 1, -1, -1):
                p = random.randint(0, j)
                if v[p] == j:
                    break
                else:
                    v[j], v[p] = v[p], v[j]
            else:
                if v[0] != 0:
                    return tuple(v)

    def run(self):
        while True:
            while not my_bot.chats:
                print("No chat found! check your connection or maybe your bot has no members!")
                time.sleep(2)

            print("You have these members for secret santa:")
            chats = []
            for chat in my_bot.chats:
                if chat not in chats:
                    chats.append(chat)
                    print(chat['first_name'] + ": " + str(chat['id']))
            assign = input("Assign people?(type 'yes' for assign or sth else otherwise)")
            if assign != "yes":
                continue
            indexes = list(Assigner.random_derangement(len(chats)))
            for i in range(len(chats)):
                message = str("You will be " + chats[indexes[i]]['first_name']) + \
                          "'s secret santa (@" + chats[indexes[i]]['username'] + ")"
                my_bot.send_message(chats[i]['id'], message)


def main():
    Assigner().start()
    Printer().start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
