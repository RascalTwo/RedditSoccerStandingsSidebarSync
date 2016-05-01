# Reddit USL Soccer Standings Sidebar Updater

Made for /u/Totschlag to update the sidebar of /r/SaintLouisFC with the Western Conference standings from [uslsoccer.com](http://www.uslsoccer.com/usl-standings).

Requires `username`, `password`, `client_id`, and `client_secret` for the Reddit account the bot will run under.

Also requires the account to have moderator status in the subreddit of which the sidebar will be updated.

# Dependencies

- [Python 3](https://www.python.org/download/releases/3.0/)
- [Requests](http://docs.python-requests.org/en/master/)

You can have the dependencies automatically installed by executing `pip install -r requirements.txt`, although there is only one dependency. You will obviously have to obtain Python and pip manually.

# Setup

## Reddit Account

> Coming soon.

## Configuration

The configuration file - `config.json` looks like this:

```json
{
    "client_id": "",
    "client_secret": "",
    "user_agent": "SomethingUnique/1.0 by /u/Rascal_Two for /u/Totschlag running under /u/El_Chubacabot at /r/SaintLouisFC",
    "username": "",
    "password": "",
    "subreddit": "SaintLouisFC",
    "check_rate": 600
}
```

- `client_id` is the client ID of the reddit application setup above.
- `client_secret` is the cllicne secret of the reddit application setup above.
- `user_agent` is what reddit identifies the bot as. The more unique this is the better, as common user agents have their rates limited.
- `username` is the username of the Reddit account the bot will run under.
- `password` is the password of the Reddit account the bot will run under.
- `subreddit` is the name of the subreddit sidebar that's being updated.
- `check_rate` is the rate - in seconds - that the bot will update the sidebar.

# Sidebar Requirements

The sidebar must have these two tags(?) in this order. They must be as shown, seperated from the rest of the sidebar by a blank newline. Everything within these two tags will be replaced and set to the table.

```markdown

[](/begin_table)

[](/end_table)

```

# Screenshots and GIFS

> Coming soon

# Explanation

When the bot is first created it loads the configuration data from the `config.json` file. It then sends the `username`, `password`, `client_id`, and `client_secret` to the Reddit API to get a access token. This access token lasts 60 minutes, and is used to do actions as the reddit account.

This access token is automatically refreshed, and I have personaly been able to run the bot for 5 hours without any errors.

Every minute it outputs a message stating it's uptime. It also checks if it's time to update the table. If it it, then it scrapes [this](http://www.uslsoccer.com/usl-standings) site.

*****

The site requires some more client interaction the most, so the scraper must make the AJAX request that is usually made by the browser manually. It obtains both Eastern and Western standings, although the eastern standings are ignored.

The HTML tags are then scraped away and the data is extracted. All values are extracted, although only some are returned.

The data is lastly formated for reddit before finally being returned.

*****

The text within the above mentoned tags on the sidebar is then replaced with the new table data, along with the current time at the bottom of the table.

The last thing needed is to send the new subreddit settings to reddit.

# TODO

> I may do some of these, I may do none of these. Depends on how worth-it said features would be

Convert to [PRAW](https://praw.readthedocs.io/en/stable/)
Exceptions and error messages for if things go wrong.
Logging to file.