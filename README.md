# how to use
- create a new bot on telegram with `@BotFather` and save its token (the `TOKEN` variable)
- `@userinfobot` can tell you its id if you forward a message from the conversation with it
- the way the code currently works:
    - errors get redirected to the chat with the bot (the `CHAT_ID` variable)
    - listings get posted in a group (the `GROUP_ID` variable)
