# Release pipeline runtime stability — 17 October 2026

The successful main run 39043521772 reported that checkout v4 and setup-python v5 target deprecated Node 20 and are forced onto Node 24. It also warned that ubuntu-latest starts migrating from Ubuntu 24.04 to 26.04 on October 19. No application failure was inferred from those warnings; this maintenance removes the implicit Action-runtime fallback and avoids an unreviewed OS transition during launch.

All seven jobs in the three existing workflows now explicitly use ubuntu-24.04. The checkout, Node setup and Python setup Actions are pinned to verified commits of current official stable releases, each declaring node24 in its action.yml:

| Official Action | Release | Immutable commit |
|---|---|---|
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 |
| actions/setup-node | v7.1.0 | 949feb2413d6458794dcd2491c4babbbce0c15c1 |
| actions/setup-python | v7.0.0 | 5fda3b95a4ea91299a34e894583c3862153e4b97 |

Node application version 24, Python 3.13, test commands, database fixtures, Cloudflare project/Worker configuration and production URL are retained. Checkout no longer persists a Git credential; CI explicitly requests contents:read, matching the other workflows. No new secret, paid runner or security-sensitive grant is introduced. Normal OS package/security updates still occur within the Ubuntu 24.04 hosted image; this is not a fully hermetic build claim. Action updates now require reviewing and changing the pinned commit.

Validation for this change is the actual existing branch/PR/main GitHub Actions suites and both Worker build paths, rather than a test that only restates workflow text. The manually dispatched deploy workflow is not dispatched merely to duplicate the existing native Cloudflare deployment. Exact checks and deployment results must be read from the release commit's Actions status and production build marker.

Remaining access gates are separate: the installed Brave Wallet was inspected again on October 17 and still exposes its introductory Learn more panel, not a configured account/permission flow. Guest Defense Planner access still withholds workspace data. No wallet was created/imported/unlocked or granted permissions. Off-device encrypted backup verification is complete; independent key custody/second-machine recovery and an owned sending domain remain unresolved. No design or financial-model change is part of this maintenance.

Sources: [GitHub's Ubuntu rollout notice](https://github.com/actions/runner-images/issues/14748), [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1), [setup-node v7.1.0](https://github.com/actions/setup-node/releases/tag/v7.1.0), [setup-python v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0).
