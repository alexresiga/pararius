# how to use
- you need to set the `TOKEN`, `CHAT_ID` and `GROUP_ID` repository secrets (Settings > Secrets > Actions)
- create a new bot on telegram with `@BotFather` and save its token (the `TOKEN` variable)
- `@userinfobot` can tell you its id if you forward a message from the conversation with it
- the way the code currently works:
    - errors get redirected to the chat with the bot (the `CHAT_ID` variable)
    - listings get posted in a group (the `GROUP_ID` variable)

# github action
- currently the action runs `every hour between 8 and 20:59`, to increase the frequency edit `.github/workflows/python-automation.yml` (https://crontab.guru/ is your best friend)
