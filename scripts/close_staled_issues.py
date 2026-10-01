# -*- coding: utf-8 -*-
"""
Closes stale GitHub issues.

This script fetches all open issues from the project's GitHub repository.
It identifies issues where the last comment is older than 90 days and
the issue is not marked with the "help wanted" label. For each stale issue,
it posts a comment explaining that the issue is being closed due to
inactivity and then closes the issue.

Requires the GITHUB_TOKEN environment variable to be set for API authentication.
"""

import json
import os
from datetime import UTC, datetime, timedelta

import requests
from dateutil.parser import parse

if __name__ == "__main__":
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }

    resp = requests.get(
        "https://api.github.com/repos/chinapandaman/PyPDFForm/issues",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    issues = resp.json()

    to_close = []
    for each in issues:
        raw_labels = each.get("labels", [])
        labels = []
        for label in raw_labels:
            if isinstance(label, dict):
                labels.append(label.get("name"))
            elif isinstance(label, str):
                labels.append(label)

        comments_resp = requests.get(each["comments_url"], headers=headers, timeout=30)
        comments_resp.raise_for_status()
        comments = comments_resp.json()

        if (
            comments
            and (
                datetime.now(tz=UTC)
                - parse(comments[-1]["updated_at"]).replace(tzinfo=UTC)
                > timedelta(days=90)
            )
            and "help wanted" not in labels
        ):
            to_close.append(each["url"])

    for each in to_close:
        requests.post(
            f"{each}/comments",
            headers=headers,
            json={"body": "Closing due to inactivity."},
            timeout=30,
        )
        requests.patch(each, headers=headers, json={"state": "closed"}, timeout=30)
