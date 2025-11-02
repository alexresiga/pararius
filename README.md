# how to use
- you need to set the `TOKEN`, `CHAT_ID` and `GROUP_ID` repository secrets (Settings > Secrets > Actions)
- create a new bot on telegram with `@BotFather` and save its token (the `TOKEN` variable)
- `@userinfobot` can tell you its id if you forward a message from the conversation with it
- the way the code currently works:
    - errors/skipped listings get redirected to the chat with the bot (the `CHAT_ID` variable) (can be disabled (by commenting out/deleting that part of the code (lol)))
    - listings get posted in a group (the `GROUP_ID` variable)

# github action
- currently the action runs `every hour between 8 and 20:59`, to increase the frequency edit `.github/workflows/python-automation.yml` (https://crontab.guru/ is your best friend)
- all seen apartments are written to the `seen.txt` file and the updated file is committed after every script run
