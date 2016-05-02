#!/usr/bin/env python3

# The MIT License (MIT)

# Copyright (c) 2016 RascalTwo @ therealrascaltwo@gmail.com

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Reddit USL Soccer Sidebar Updater.

Updates the sidebar of a subreddit with the current
standings in USL Soccer.

"""
import json
import time
import re
import requests


class HTTPException(Exception):
    """Whenever there is a non-200 response code returned."""


class RedditAPIException(Exception):
    """Reddit itself returned a error based on our POST/GET request."""


def handle_response(function):
    """Decorator to catch errors within request responses."""
    def function_wrapper(*args, **kwargs):
        """Function wrapper."""
        response = function(*args, **kwargs)

        if response.status_code != 200:
            raise HTTPException("'{}' returned a status code of {}"
                                .format(function.__name__,
                                        response.status_code))

        if "errors" in response.json() and len(response.json()["errors"]) != 0:
            raise RedditAPIException("\n".join("'{0}' error {1[0]}: {1[1]}"
                                               .format(function.__name__, error)
                                               for error in response.json()["errors"]))

        if "error" in response.json():
            raise RedditAPIException("'{}' error: {}"
                                     .format(function.__name__,
                                             response.json()["error"]))

        return response.json()
    return function_wrapper


class RedditUSLSoccerStandingsSidebarUpdater(object):
    """Reddit USL Soccer Sidebar Updater.

    Updates the sidebar of a subreddit with the current
    standings in USL Soccer.

    """

    def __init__(self):
        """Create bot and import 'config.json'."""
        with open("config.json", "r") as config_file:
            self.config = json.loads(config_file.read())

        self.token = None

    def _headers(self, auth=True):
        """Header(s) to send to Reddit.

        Keyword Arguments:
        `auth` (bool(true)) -- Should the 'Authorization' header be
                               included. Default is true. Options is provided
                               because '_get_token' must have this false.

        Returns:
        `dict` -- With keys as headers, and values as header contents.

        """
        if auth:
            return {
                "User-Agent": self.config["user_agent"],
                "Authorization": "{} {}".format(self.token["token_type"],
                                                self.token["access_token"])
            }
        return {
            "User-Agent": self.config["user_agent"]
        }

    @handle_response
    def _get_token(self):
        """Return the access_token for this session.

        Returns:
        `dict` -- contains 'access_token', 'refresh_token', and 'token_type'.

        May throw a 'HTTPException' or 'RedditAPIException'.

        """
        client_auth = requests.auth.HTTPBasicAuth(self.config["client_id"],
                                                  self.config["client_secret"])
        post_data = {
            "grant_type": "password",
            "username": self.config["username"],
            "password": self.config["password"]
        }
        return requests.post("https://www.reddit.com/api/v1/access_token",
                             auth=client_auth,
                             data=post_data,
                             headers=self._headers(False))

    def refresh_token(self):
        """Attempt to refresh the access token."""
        try:
            self.token = self._get_token()
        except (HTTPException, RedditAPIException) as token_exception:
            self.token = None
            print("Could not get access token from the Reddit API.\n"
                  "This can be caused by mutiple things, such as:\n"
                  "  Reddit not being accessable\n"
                  "  Username and/or password being incorrect.\n"
                  "  'client_id' and/or 'client_secret' being incorrect.\n"
                  "  Applicaiton on Reddit not created as a 'script'.\n\n"
                  "Raw Error: {}".format(token_exception))

    def run(self):
        """Start the loop for the bot to run in."""
        self.refresh_token()

        uptime = 0

        while True:
            print("Uptime: {}s".format(uptime))

            if self.token["expires_in"] <= 60:
                print("Refreshing access token...", end="")
                self.refresh_token()
                print("Access token refreshed.")

            if uptime % self.config["check_rate"] == 0:
                try:
                    print("Updating...", end="")

                    subreddit_settings = self.get_subreddit_settings()["data"]
                    current_table = (subreddit_settings["description"]
                                     .split("[](/begin_table)")[1]
                                     .split("[](/end_table)")[0])

                    new_table = ("\n\n"
                                 "Team | Pts | GP| Record\n"
                                 "---|---|---|---\n"
                                 "{}"
                                 "\n\n"
                                 "*Updated {} {}*\n\n"
                                 .format("\n".join(get_current_standings()),
                                         time.strftime("%d %b %I:%M %p", time.localtime()),
                                         time.tzname[0]))

                    subreddit_settings["description"] = (subreddit_settings["description"]
                                                         .replace(current_table, new_table))

                    self.change_sidebar_content(subreddit_settings)

                    print("Updated.")
                except(HTTPException, RedditAPIException) as exception:
                    print("There was an error when updating the sidebar.\n"
                          "{}".format(exception))

            uptime += 60
            self.token["expires_in"] -= 60
            time.sleep(60)

    @handle_response
    def get_subreddit_settings(self):
        """Get subreddit settings.

        Returns:
        `dict` -- Settings of subreddit.

        """
        return requests.get("https://oauth.reddit.com/""r/{}/about/edit.json"
                            .format(self.config["subreddit"]),
                            headers=self._headers())

    @handle_response
    def change_sidebar_content(self, post_data):
        """Change subreddit settings to the data provided.

        Keyword Arguments:
        `post_data` (dict) -- All settings to set. Only 'description' actually
                              changes, but the post request requires all
                              fields to be provided.

        """
        post_data["api_type"] = "json"
        post_data["link_type"] = post_data["content_options"]
        post_data["type"] = post_data["subreddit_type"]
        post_data["sr"] = post_data["subreddit_id"]
        return requests.post("https://oauth.reddit.com/api/site_admin",
                             data=post_data,
                             headers=self._headers())


def get_current_standings():
    """Return Reddit-formated current Western Conference standings.

    Returns:
    `list` (str) -- List of rows containing team name and scores.

    """
    html = (requests.get("http://www.uslsoccer.com/usl-standings").text
            .split('class="pageEl"')[1:])

    html = [(part.split('<script type="text/javascript">')[1].split("</script>")[0])
            for part in html if '$j("body").trigger("pageElementAjaxLoad")' in part]

    elements = [part.split('/page_element/ajax/')[1].split("'")[0]
                for part in html]

    node_ids = [part.split("page_node_id=")[1].split("'")[0]
                for part in html]

    url = ("http://www.uslsoccer.com/page_element/ajax/{}?"
           "width_percentage=100&page_node_id={}&subseason="
           .format(elements[1], node_ids[1]))

    headers = {
        "Referer": "http://www.uslsoccer.com/usl-standings",
        "X-Requested-With": "XMLHttpRequest"
    }

    html = requests.get(url, headers=headers).text

    for match in re.findall("<a .*?>", html):
        html = html.replace(match, "")

    replacements = {
        "</a>": "",
        'class="name expandedView"': "",
        'class="name condensedView"': "",
        'class="highlight"': ""
    }

    for replacer in replacements:
        html = html.replace(replacer, replacements[replacer])

    standings = []

    for row in ["".join(part.split(">")[1:])for part in html.split("<tr")][2:]:
        cols = [col.split("</td")[0].strip() for col in row.split("<td")][1:]
        standings.append("{0[0]}|{0[2]}|{0[6]}|{1}"
                         .format(cols, "-".join(cols[3:6])))

    return standings


if __name__ == "__main__":
    RedditUSLSoccerStandingsSidebarUpdater().run()
