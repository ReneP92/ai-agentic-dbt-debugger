"""Lightweight Linear GraphQL API client.

Provides typed helpers for creating issues, reading issues, searching
by content, and adding comments.  Uses ``requests`` for HTTP transport
— no third-party Linear SDK required.

Authentication is via a personal API key passed in the ``Authorization``
header (not Bearer).
"""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from typing import Any

import requests

LINEAR_API = "https://api.linear.app/graphql"

# T-shirt size → Linear numeric estimate (Fibonacci)
ESTIMATE_MAP: dict[str, int] = {
    "XS": 1,
    "S": 2,
    "M": 3,
    "L": 5,
    "XL": 8,
}

# Agent severity → Linear priority (1=Urgent … 4=Low)
PRIORITY_MAP: dict[str, int] = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
}


class LinearClientError(Exception):
    """Raised when the Linear API returns an error."""


class LinearClient:
    """Thin wrapper around the Linear GraphQL API.

    Resolves team and project IDs lazily on first use and caches them
    for the lifetime of the process.
    """

    def __init__(
        self,
        api_key: str | None = None,
        team_key: str = "REN",
        project_name: str = "Data Alerts",
    ) -> None:
        self._api_key = api_key or os.environ.get("LINEAR_AUTH_TOKEN", "")
        self._team_key = team_key
        self._project_name = project_name
        self._team_id: str | None = None
        self._project_id: str | None = None

        if not self._api_key:
            print("[linear] LINEAR_AUTH_TOKEN not set — Linear integration disabled", file=sys.stderr)

    # ── Low-level transport ───────────────────────────────────────────

    def _request(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query/mutation and return the ``data`` dict."""
        if not self._api_key:
            raise LinearClientError("LINEAR_AUTH_TOKEN not configured")

        resp = requests.post(
            LINEAR_API,
            headers={
                "Content-Type": "application/json",
                "Authorization": self._api_key,
            },
            json={"query": query, "variables": variables or {}},
            timeout=30,
        )
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            # Extract response body for debugging context
            detail = ""
            try:
                detail = resp.text[:500]
            except Exception:
                pass
            raise LinearClientError(
                f"HTTP {resp.status_code} from Linear API: {detail}"
            ) from exc

        body = resp.json()

        if "errors" in body:
            msgs = "; ".join(e.get("message", str(e)) for e in body["errors"])
            raise LinearClientError(f"Linear API error: {msgs}")

        return body.get("data", {})

    # ── ID resolution (cached) ────────────────────────────────────────

    @property
    def team_id(self) -> str:
        if self._team_id is None:
            self._resolve_team()
        return self._team_id  # type: ignore[return-value]

    @property
    def project_id(self) -> str:
        if self._project_id is None:
            self._resolve_project()
        return self._project_id  # type: ignore[return-value]

    def _resolve_team(self) -> None:
        data = self._request(
            """
            query Teams {
              teams {
                nodes { id name key }
              }
            }
            """
        )
        for team in data.get("teams", {}).get("nodes", []):
            if team.get("key") == self._team_key:
                self._team_id = team["id"]
                print(f"[linear] Resolved team {self._team_key} → {self._team_id}", file=sys.stderr)
                return
        raise LinearClientError(f"Team with key '{self._team_key}' not found in Linear")

    def _resolve_project(self) -> None:
        data = self._request(
            """
            query Projects($name: String!) {
              projects(filter: { name: { eq: $name } }) {
                nodes { id name }
              }
            }
            """,
            {"name": self._project_name},
        )
        nodes = data.get("projects", {}).get("nodes", [])
        if nodes:
            self._project_id = nodes[0]["id"]
            print(f"[linear] Resolved project '{self._project_name}' → {self._project_id}", file=sys.stderr)
            return
        raise LinearClientError(f"Project '{self._project_name}' not found in Linear")

    # ── Issue operations ──────────────────────────────────────────────

    def create_issue(
        self,
        title: str,
        description: str,
        priority: int | None = None,
        estimate: int | None = None,
    ) -> dict[str, Any]:
        """Create an issue in the configured team and project.

        Returns:
            Dict with ``id`` (UUID), ``identifier`` (e.g. REN-42), ``url``.
        """
        input_fields = {
            "title": title,
            "description": description,
            "teamId": self.team_id,
            "projectId": self.project_id,
        }
        if priority is not None:
            input_fields["priority"] = priority
        if estimate is not None:
            input_fields["estimate"] = estimate

        data = self._request(
            """
            mutation IssueCreate($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success
                issue {
                  id
                  identifier
                  url
                }
              }
            }
            """,
            {"input": input_fields},
        )
        result = data.get("issueCreate", {})
        if not result.get("success"):
            raise LinearClientError("issueCreate returned success=false")

        issue = result.get("issue", {})
        print(f"[linear] Created issue {issue.get('identifier')} → {issue.get('url')}", file=sys.stderr)
        return issue

    def get_issue(self, issue_id: str) -> dict[str, Any]:
        """Fetch a single issue by UUID or identifier (e.g. REN-42).

        Returns:
            Dict with ``id``, ``identifier``, ``title``, ``description``,
            ``priority``, ``estimate``, ``url``, ``state``.
        """
        data = self._request(
            """
            query Issue($id: String!) {
              issue(id: $id) {
                id
                identifier
                title
                description
                priority
                estimate
                url
                state { name }
              }
            }
            """,
            {"id": issue_id},
        )
        issue = data.get("issue")
        if not issue:
            raise LinearClientError(f"Issue '{issue_id}' not found")
        return issue

    def search_issues(self, query: str, first: int = 5) -> list[dict[str, Any]]:
        """Search issues by text content (title + description).

        Returns:
            List of issue dicts with ``id``, ``identifier``, ``title``,
            ``description``, ``priority``, ``url``, ``state``.
        """
        data = self._request(
            """
            query SearchIssues($query: String!, $first: Int) {
              searchIssues(query: $query, first: $first) {
                nodes {
                  id
                  identifier
                  title
                  description
                  priority
                  url
                  state { name }
                }
              }
            }
            """,
            {"query": query, "first": first},
        )
        return data.get("searchIssues", {}).get("nodes", [])

    def add_comment(self, issue_id: str, body: str) -> dict[str, Any]:
        """Add a comment to an issue.

        Args:
            issue_id: The issue UUID (not the identifier like REN-42).
            body: Markdown-formatted comment body.

        Returns:
            Dict with ``id`` of the created comment.
        """
        data = self._request(
            """
            mutation CommentCreate($input: CommentCreateInput!) {
              commentCreate(input: $input) {
                success
                comment { id }
              }
            }
            """,
            {"input": {"issueId": issue_id, "body": body}},
        )
        result = data.get("commentCreate", {})
        if not result.get("success"):
            raise LinearClientError("commentCreate returned success=false")
        return result.get("comment", {})


# ── Module-level singleton ────────────────────────────────────────────

_client: LinearClient | None = None


def get_linear_client() -> LinearClient:
    """Get or create the module-level LinearClient singleton."""
    global _client
    if _client is None:
        _client = LinearClient()
    return _client
