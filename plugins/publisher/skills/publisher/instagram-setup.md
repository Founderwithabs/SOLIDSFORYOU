# Connect your Instagram to the Publisher

A one-time setup, about 30 minutes, that lets Claude post your finished Reels
to your own Instagram account and read their numbers. It uses Instagram's
official API, so Claude never sees your password and your account stays
within Instagram's rules.

You need: an Instagram account, a Facebook account, and a phone or computer
with a browser. A computer is easier for the developer website; on a phone,
switch the browser to "Desktop site".

Meta renames these screens from time to time. If something doesn't match,
ask Claude and send it a screenshot.

## 1. Make your Instagram a professional account

Instagram app: Settings, then Account type and tools, then Switch to
professional account. Choose **Creator** (or Business) and pick a category.

## 2. Create a Facebook Page and connect it

1. In the Facebook app: Menu, then Pages, then Create. Give it your brand's
   name and a category. Nobody has to follow or use it.
2. In Instagram: Edit profile, then Page (under public business
   information), then Connect existing Page, and choose it. If there's no
   Page option, first add your Facebook account under Settings, then Accounts
   Center.

## 3. Create a free Meta developer app

1. Go to developers.facebook.com, log in with Facebook, and register as a
   developer if asked (accept the terms, verify your phone).
2. My Apps, then Create App.
3. App name: anything, for example "<Your brand> Publisher". Your email.
4. Use case: **Manage messaging & content on Instagram**.
5. Business portfolio: "I don't want to connect a business portfolio yet".
6. Create the app. You land on its dashboard.

## 4. Choose Instagram login and add the permissions

1. On the dashboard, open "Customize the Manage messaging & content on
   Instagram use case".
2. Choose **API setup with Instagram login**.
3. Tap **Add all required permissions**.
4. Open **Permissions and features** and add:
   - `instagram_business_content_publish` (posting Reels)
   - `instagram_business_manage_insights` (views, reach, audience countries)
5. Skip webhooks, business login and app review. Your app only ever posts to
   your own account, so it can stay unpublished.

## 5. Add your account as a tester and accept the invite

1. In the developer site: App roles, then Roles, then Add People, choose
   **Instagram Tester**, and enter your Instagram username.
2. Accept the invite in a browser, logged in to that Instagram account:
   **instagram.com/accounts/manage_access**, then the **Tester invites** tab,
   then Accept. (The invite is often hidden in the Instagram app.)

## 6. Generate your access token, and keep it secret

1. Back in Use cases, Customize: under **Generate access tokens**, find your
   account (tap Add account and log in if it isn't there) and tap **Generate
   token**. Allow the permissions.
2. Copy the token. Treat it like a password: never paste it into a chat with
   Claude or anyone else, never put it in a file you commit, never post it.

## 7. Give the token to Claude Code safely

Store it as an environment variable named **`IG_ACCESS_TOKEN`**:

- **Claude Code on the web (cloud sessions):** open the environment's
  settings (the environment menu in the session's title bar, then Edit). Add
  the token under Network secrets (or API credentials, or as an environment
  variable), named `IG_ACCESS_TOKEN`. Under Allowed domains add
  `graph.instagram.com`. Start a new session so it's picked up.
- **Claude Code on your computer:** set `IG_ACCESS_TOKEN` in your shell
  before starting Claude Code (for example in your shell's startup file or a
  password manager's environment feature). Keep it out of any project folder.

## 8. Check it works

Install the plugin and ask Claude:

```
/plugin install publisher@solidsforyou
```

> Run the publisher's whoami.

It should show your username, account type and how many posts Instagram
still allows today.

## 9. Posting a Reel

Instagram downloads the video itself, so it needs a public link:

1. Upload the finished video to Google Drive and share it as **Anyone with
   the link**.
2. Give Claude the link and the caption. Claude checks the caption against
   Instagram's limits, shows you what it will post, and posts only after you
   say yes. It sends back the Reel's link straight away.
3. Want it at a set time? Tell Claude the time; it posts then. (New accounts
   often can't schedule inside the Instagram app, which this gets around.)

## Troubleshooting

- **No tester invite:** check App roles shows your username as Pending, and
  use the browser link in step 5, not the app.
- **"Invalid OAuth access token":** the token was mistyped or has expired.
  Generate a new one (step 6) and replace `IG_ACCESS_TOKEN`.
- **The token stops working after about 60 days:** ask Claude to run the
  publisher's refresh every few weeks; if it says Instagram issued a new
  token, generate one again.
- **The video fails to process:** the link must open the video file for
  anyone (test it in a private browser window); vertical 9:16 MP4 works best.
- **Paid partnership label:** the API can't switch it on. For paid campaign
  clips, put the required tags and #ad in the caption, or post those by hand
  with the label.
- **Audience countries are empty:** Instagram shows them only once the
  account has enough followers (about 100).
