Implementation of the bot will run on your local development machine, and should be able to perform these basic functions:

Connect your app to the KenzieBot (Links to an external site.)Links to an external site. workspace as a bot user
Send a message to a channel announcing that it is online
Wait for and process events/messages in an infinite while-loop
Ignore any messages that don't contain a direct `@mention` of your bot name
Exit your bot program if you receive an exit message.  For example, if your bot is named `example-bot` then your program should exit gracefully when it receives a slack message such as `@example-bot exit`