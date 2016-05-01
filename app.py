#!/usr/bin/env python3

# The MIT License (MIT)

# Copyright (c) 2016 RascalTwo @ therealrascaltwo@gmail.com

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import requests
import json
import time
import re


class RedditUSLSoccerStandingsSidebarUpdater(object):
    def __init__(self):
        with open("config.json", "r") as config_file:
            self.config = json.loads(config_file.read())

        self.token = self._get_token()

    def _headers(self, auth=True):
        if auth:
            return {
                "User-Agent": self.config["user_agent"],
                "Authorization": self.token["token_type"] + " " + self.token["access_token"]
            }
        return {
            "User-Agent": self.config["user_agent"]
        }

    def _get_token(self):
        client_auth = requests.auth.HTTPBasicAuth(self.config["client_id"], self.config["client_secret"])
        post_data = {
            "grant_type": "password",
            "username": self.config["username"],
            "password": self.config["password"]
        }
        return requests.post("https://www.reddit.com/api/v1/access_token",
                             auth=client_auth,
                             data=post_data,
                             headers=self._headers(False)).json()

    def run(self):
        uptime = 0

        while True:
            print("Uptime: {}s".format(uptime))

            if self.token["expires_in"] <= 60:
                self.token = self._get_token()

            if uptime % self.config["check_rate"] == 0:
                print("Updating...", end="")

                subreddit_settings = self.get_subreddit_settings()["data"]
                current_table = subreddit_settings["description"].split("[](/begin_table)")[1].split("[](/end_table)")[0]

                prefix = "\n\nTeam | Pts | GP| Record\n---|---|---|---\n"
                latest_table = "\n".join(self.get_current_standings())
                suffix = "\n\n*Updated {} {}*\n\n".format(
                    time.strftime("%d %b %I:%M %p", time.localtime()),
                    time.tzname[0])

                subreddit_settings["description"] = subreddit_settings["description"].replace(current_table, prefix + latest_table + suffix)

                self.change_sidebar_content(subreddit_settings)

                print("Updated.")

            uptime += 60
            self.token["expires_in"] -= 60
            time.sleep(60)

    def get_current_standings(self):
        html = requests.get("http://www.uslsoccer.com/usl-standings").text.split('class="pageEl"')[1:]
        html = [part.split('<script type="text/javascript">')[1].split("</script>")[0] for part in html if '$j("body").trigger("pageElementAjaxLoad")' in part]
        elements = [part.split('/page_element/ajax/')[1].split("'")[0] for part in html]
        node_ids = [part.split("page_node_id=")[1].split("'")[0] for part in html]

        url = "http://www.uslsoccer.com/page_element/ajax/{}?width_percentage=100&page_node_id={}&subseason=".format(elements[1], node_ids[1])
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

        for row in ["".join(part.split(">")[1:]) for part in html.split("<tr")][2:]:
            cols = [col.split("</td")[0].strip() for col in row.split("<td")][1:]
            standings.append(cols[0] + "|" + cols[2] + "|" + cols[6] + "|" + "-".join(cols[3:6]))

        return standings

    def get_subreddit_settings(self):
        response = requests.get("https://oauth.reddit.com/r/{}/about/edit.json".format(self.config["subreddit"]),
                                headers=self._headers())
        return response.json()

    def change_sidebar_content(self, post_data):
        post_data["api_type"] = "json"
        post_data["link_type"] = post_data["content_options"]
        post_data["type"] = post_data["subreddit_type"]
        post_data["sr"] = post_data["subreddit_id"]
        response = requests.post("https://oauth.reddit.com/api/site_admin",
                                 data=post_data,
                                 headers=self._headers())


if __name__ == "__main__":
    RedditUSLSoccerStandingsSidebarUpdater().run()
