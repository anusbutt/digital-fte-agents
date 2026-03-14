"""social_post.py — Thin wrapper that re-exports social posting functions.

The orchestrator imports from this module to dispatch Facebook, Instagram,
and Twitter posts after HITL approval.

Usage (from orchestrator):
    from scripts.social_post import post_facebook, post_instagram, post_twitter
"""

from scripts.facebook_post import post_facebook
from scripts.instagram_post import post_instagram
from scripts.twitter_post import post_twitter

__all__ = ["post_facebook", "post_instagram", "post_twitter"]
