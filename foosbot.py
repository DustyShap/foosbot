import os
import time
from slackclient import SlackClient


# foosbot's environment variables
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
BOT_ID = os.environ.get('BOT_ID')

AT_BOT = '<@' + BOT_ID + '>'
EXAMPLE_COMMAND = "foos"


# instantiate Slack client
slack_client = SlackClient(SLACK_BOT_TOKEN)


def parse_slack_output(slack_rtm_output):

    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            print(output) #Testing purposes for now
            if output and 'text' in output and AT_BOT in output['text']:
                first_name = lookup_first_name(output['user'])

                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel'], first_name

    return None, None, None


def handle_command(command, channel, name):

    response = "I didn't catch that. Say `" + EXAMPLE_COMMAND + "` to get in a game!"

    if command.startswith(EXAMPLE_COMMAND):
        response = name + " is in!"

    slack_client.api_call("chat.postMessage",
                          channel=channel,
                          text=response,
                          as_user=True)


def lookup_first_name(user_id):

    api_call = slack_client.api_call('users.list')
    if api_call.get('ok'):
         users = api_call.get('members')
         for user in users:
             if user['id'] == user_id:
                 return user['profile']['first_name']

    return None



if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1  #1 second delay between reading from firehose

    if slack_client.rtm_connect():
         print("Foosbot connected and running!")

         while True:
            command, channel, name = parse_slack_output(slack_client.rtm_read())

            if command and channel and name:
                handle_command(command, channel, name)

            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID!?")