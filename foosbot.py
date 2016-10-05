import os
import time
from slackclient import SlackClient

class SlackUser(object):
    @classmethod
    def get_all_from_api(cls, slack_client):
        api_call = slack_client.api_call('users.list')
        if api_call.get('ok'):
            user_data = api_call.get('members')
            return {user_data["id"]: cls(user_data) for user_data in user_data}
        return {}

    # possible keys at top level
    #['status',  'tz', 'name', 'deleted', 'is_bot', 'tz_label',
    #  'real_name', 'color', 'team_id', 'is_admin', 'is_ultra_restricted',
    #  'is_restricted', 'is_owner', 'tz_offset', 'id', 'is_primary_owner']
    #
    # possible keys nested in profile
    # ['first_name', 'last_name', 'fields', 'real_name', 'real_name_normalized',
    #   'image_{24,32,48,72,192,512}', 'avatar_hash']

    def __init__(self, user_data):
        self.first_name = user_data['profile'].get('first_name', '')
        self.last_name = user_data['profile'].get('last_name', '')

class SlackWrapper(object):
    def __init__(self, api_token):
        self.slack_client = SlackClient(api_token)
        self.cached_slack_users = []

        self.is_connected = self.slack_client.rtm_connect()

    def get_latest_messages(self):
        messages = self.slack_client.rtm_read()
        # it's probably not occasionally [] or None interchangeably
        # this can probably be simplified
        if messages is None or len(messages) == 0:
            return []
        return messages

    def get_filtered_messages(self, text_filter):
        matching_messages = []
        for message in self.get_latest_messages():
            if 'text' in message and text_filter in message['text']:
                matching_messages.append(message)
        return matching_messages

    @property
    def all_users(self):
        if len(self.cached_slack_users) == 0:
            retrieved_users = SlackUser.get_all_from_api(self.slack_client)
            if len(retrieved_users) > 0:
                print("Loaded users from server")
                self.cached_slack_users = retrieved_users
            else:
                print("Problem loading users; reverting to existing cache.")
        return self.cached_slack_users

    def get_user_by_id(self, user_id):
        return self.all_users.get(user_id, None)

    def post_message(self, channel, text):
        self.slack_client.api_call("chat.postMessage",
                                   channel=channel,
                                   text=text,
                                   as_user=True)

class FoosBot(object):
    GAME_COMMAND = 'foos'
    # 1 second delay between reading from firehose
    POLL_DELAY_SECONDS = 1

    def __init__(self, bot_name, slack_proxy):
        self.bot_name = bot_name
        self.slack_proxy = slack_proxy

    @property
    def at_bot(self):
        return '<@{}>'.format(self.bot_name)

    def handle_message(self, user, text, channel):
        print text
        response = "I didn't catch that. Say `{}` to get in a game!".format(self.GAME_COMMAND)
        if text.lower().startswith("{} {}".format(self.bot_name, self.GAME_COMMAND)):
            response = user.first_name + " is in!"
        self.slack_proxy.post_message(channel, response)


    def run(self):
        while True:
            for message in self.slack_proxy.get_filtered_messages(self.bot_name):
                user = self.slack_proxy.get_user_by_id(message['user'])
                self.handle_message(user, message['text'], message['channel'])
            time.sleep(self.POLL_DELAY_SECONDS)

if __name__ == "__main__":
    slack_proxy = SlackWrapper(os.environ.get('SLACK_BOT_TOKEN'))
    if slack_proxy.is_connected:
        bot = FoosBot(os.environ.get('BOT_NAME'), slack_proxy)
        print("Foosbot connected and running!")
        bot.run()
    else:
        print("Connection failed. Invalid Slack token or bot ID!?")
