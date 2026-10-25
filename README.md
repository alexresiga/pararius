# how to use
- you need to set the `TOKEN`, `CHAT_ID` and `GROUP_ID` repository secrets (Settings > Secrets > Actions)
- create a new bot on telegram with `@BotFather` and save its token (the `TOKEN` variable)
- `@userinfobot` can tell you its id if you forward a message from the conversation with it
- the way the code currently works:
    - errors/skipped listings get redirected to the chat with the bot (the `CHAT_ID` variable) (can be disabled (by commenting out/deleting that part of the code (lol)))
    - listings get posted in a group (the `GROUP_ID` variable)

# favourite neighbourhoods
- open the map at https://alexresiga.github.io/pararius/ (served by GitHub Pages from `index.html`), pick zip codes, click `Save to GitHub` and commit the pasted JSON
- the picks are stored in `favourites.json` (zip code -> neighbourhood names)
- every listing is posted, starting with a ★ 0-5 closeness score (`closeness.py`): 5 inside a favourite zip code, then by distance from the listing's zip code area centre to the nearest favourite area: 4 up to 0.75 km, 3 up to 1.5 km, 2 up to 2.5 km, 1 up to 4 km, 0 further
- zip code boundaries are in `amsterdam_pc4.geojson` (Gemeente Amsterdam open data, also embedded in `index.html`)
- an empty `favourites.json` (`{}`) means listings are posted without a score

# github action
- currently the action runs `every hour between 8 and 20:59`, to increase the frequency edit `.github/workflows/python-automation.yml` (https://crontab.guru/ is your best friend)
- all seen apartments are written to the `seen.txt` file and the updated file is committed after every script run
