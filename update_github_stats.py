
"""
🌟 GitHub Stats Auto-Updater for annsayuri
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automatically updates your GitHub Profile README with
fresh stats every day using GitHub Actions! 🎯

HOW IT WORKS:
  1. Fetches your GitHub stats via GitHub API
  2. Updates your README.md with latest data
  3. Commits and pushes changes automatically

SETUP:
  pip install requests PyGithub python-dotenv
"""

import os
import json
import requests
from datetime import datetime, timezone
from github import Github
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# 🔧 CONFIGURATION — Edit these!
# ─────────────────────────────────────────────
GITHUB_USERNAME  = "annsayuri"                   # 👤 Your GitHub username
GITHUB_TOKEN     = os.getenv("GITHUB_TOKEN")     # 🔑 From .env or GitHub Secrets
README_REPO      = f"{GITHUB_USERNAME}/{GITHUB_USERNAME}"  # 📄 Your profile repo


# ─────────────────────────────────────────────
# 📊 FETCH STATS FROM GITHUB API
# ─────────────────────────────────────────────
def fetch_github_stats():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    base = "https://api.github.com"

    print("🔍 Fetching your GitHub stats...")

    # 👤 User profile info
    user_resp = requests.get(f"{base}/users/{GITHUB_USERNAME}", headers=headers)
    user = user_resp.json()

    # 📦 Public repos
    repos_resp = requests.get(
        f"{base}/users/{GITHUB_USERNAME}/repos?per_page=100&sort=updated",
        headers=headers
    )
    repos = repos_resp.json()

    # 🌐 Count total stars
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    # 💻 Top languages by repo
    lang_count = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            lang_count[lang] = lang_count.get(lang, 0) + 1

    top_languages = sorted(lang_count.items(), key=lambda x: x[1], reverse=True)[:3]

    # 🔥 Contribution streak via GitHub GraphQL
    contributions, streak = fetch_contributions_graphql(headers)

    stats = {
        "username":        user.get("login", GITHUB_USERNAME),
        "name":            user.get("name", GITHUB_USERNAME),
        "public_repos":    user.get("public_repos", 0),
        "followers":       user.get("followers", 0),
        "following":       user.get("following", 0),
        "total_stars":     total_stars,
        "top_languages":   top_languages,
        "contributions":   contributions,
        "current_streak":  streak,
        "last_updated":    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "profile_url":     f"https://github.com/{GITHUB_USERNAME}"
    }

    print(f"✅ Stats fetched! {contributions} contributions | {streak} day streak")
    return stats


def fetch_contributions_graphql(headers):
    """📈 Fetch contribution count via GraphQL API"""
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": GITHUB_USERNAME}},
        headers={**headers, "Content-Type": "application/json"}
    )

    data = resp.json()
    try:
        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        total = calendar["totalContributions"]

        # 🔥 Calculate current streak
        streak = 0
        all_days = [
            day
            for week in reversed(calendar["weeks"])
            for day in reversed(week["contributionDays"])
        ]
        for day in all_days:
            if day["contributionCount"] > 0:
                streak += 1
            else:
                break

        return total, streak
    except (KeyError, TypeError):
        print("⚠️  Could not fetch contribution data")
        return 0, 0


# ─────────────────────────────────────────────
# 📝 BUILD THE README CONTENT
# ─────────────────────────────────────────────
def build_readme(stats):
    """🎨 Generate a beautiful README with updated stats"""

    lang_badges = " ".join([
        f"![{lang}](https://img.shields.io/badge/-{lang.replace(' ', '%20')}-informational?style=flat&logo={lang.lower()})"
        for lang, _ in stats["top_languages"]
    ])

    readme = f"""<!-- AUTO-UPDATED by update_github_stats.py — {stats['last_updated']} -->

<h1 align="center">Hey there, I'm {stats['name']} 👋</h1>

<p align="center">
  <a href="{stats['profile_url']}">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=F72DA2&center=true&width=435&lines=Developer+%F0%9F%92%BB;Open+Source+Enthusiast+%F0%9F%8C%9F;Always+learning+new+things+%F0%9F%9A%80" alt="Typing SVG" />
  </a>
</p>

---

## 🎯 GitHub Stats (Auto-Updated Daily!)

| 📊 Metric | 🔢 Value |
|-----------|---------|
| 🔥 Current Streak | **{stats['current_streak']} days** |
| 📝 Contributions (This Year) | **{stats['contributions']}** |
| 📦 Public Repos | **{stats['public_repos']}** |
| ⭐ Total Stars Earned | **{stats['total_stars']}** |
| 👥 Followers | **{stats['followers']}** |

---

## 💻 Top Languages

{lang_badges}

---

## 📈 Contribution Graph

[![GitHub Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username={stats['username']}&theme=tokyo-night&hide_border=true)](https://github.com/{stats['username']})

---

## 🏆 GitHub Trophies

[![trophy](https://github-profile-trophy.vercel.app/?username={stats['username']}&theme=onedark&no-frame=true&margin-w=4)](https://github.com/{stats['username']})

---

<p align="center">
  🕐 Last updated: <strong>{stats['last_updated']}</strong><br/>
  ⚡ Auto-refreshed daily via <a href=".github/workflows/update-stats.yml">GitHub Actions</a>
</p>
"""
    return readme


# ─────────────────────────────────────────────
# 💾 PUSH CHANGES TO GITHUB
# ─────────────────────────────────────────────
def update_readme(stats):
    """🚀 Commit and push the updated README"""
    print("📤 Connecting to GitHub...")

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(README_REPO)

    new_content = build_readme(stats)
    commit_message = f"🤖 Auto-update stats — {stats['last_updated']}"

    try:
        # Update existing README
        file = repo.get_contents("README.md")
        repo.update_file(
            path="README.md",
            message=commit_message,
            content=new_content,
            sha=file.sha
        )
        print(f"✅ README updated successfully! Commit: {commit_message}")

    except Exception as e:
        # Create README if it doesn't exist
        print(f"📄 Creating new README... ({e})")
        repo.create_file(
            path="README.md",
            message=commit_message,
            content=new_content
        )
        print("✅ README created successfully!")


# ─────────────────────────────────────────────
# 🚀 MAIN RUNNER
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("🌟 GitHub Stats Auto-Updater")
    print("=" * 50)

    if not GITHUB_TOKEN:
        print("❌ ERROR: GITHUB_TOKEN not set!")
        print("   👉 Create a .env file with: GITHUB_TOKEN=your_token_here")
        print("   👉 Or set it as a GitHub Actions Secret")
        return

    stats = fetch_github_stats()
    update_readme(stats)

    print("=" * 50)
    print("🎉 All done! Your profile is fresh and updated!")
    print("=" * 50)


if __name__ == "__main__":
    main()
