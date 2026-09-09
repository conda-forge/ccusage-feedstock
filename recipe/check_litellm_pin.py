"""Fail the build when the vendored LiteLLM pricing snapshot goes stale.

ccusage embeds a LiteLLM pricing snapshot at build time. Upstream feeds it in
from the `litellm` flake input, so `flake.lock` is the source of truth for which
revision belongs to a given tag. This recipe vendors that revision's snapshot as
a source instead of downloading it during the build, which means a version bump
can silently leave the snapshot behind. Fail loudly with the new revision
instead, so bumping it is mechanical.
"""

import json
import os
import sys

PRICING_JSON = "model_prices_and_context_window.json"


def die(message):
    sys.exit("\nERROR: " + message + "\n")


def main():
    (expected_rev,) = sys.argv[1:]
    lock_path = os.path.join(os.environ["SRC_DIR"], "flake.lock")

    try:
        with open(lock_path, encoding="utf-8") as lock_file:
            locked = json.load(lock_file)["nodes"]["litellm"]["locked"]
        owner, repo, rev = locked["owner"], locked["repo"], locked["rev"]
    except (OSError, KeyError, ValueError) as error:
        die(
            "could not read nodes.litellm.locked from {}: {!r}\n\n"
            "Upstream may have stopped pinning the pricing snapshot through its "
            "flake. Check how this tag obtains the snapshot and update the "
            "recipe accordingly.".format(lock_path, error)
        )

    if rev == expected_rev:
        return

    url = "https://raw.githubusercontent.com/{}/{}/{}/{}".format(
        owner, repo, rev, PRICING_JSON
    )
    die(
        "the vendored LiteLLM pricing snapshot is stale.\n\n"
        "  litellm_rev in recipe.yaml: {}\n"
        "  nodes.litellm.locked.rev:   {}\n\n"
        "Upstream moved its pricing pin, so the snapshot this build would embed "
        "is no longer the one upstream ships. Update recipe/recipe.yaml:\n\n"
        "  litellm_rev: {}\n\n"
        "and refresh the sha256 of the pricing source with:\n\n"
        "  curl -sL {} | sha256sum".format(expected_rev, rev, rev, url)
    )


if __name__ == "__main__":
    main()
