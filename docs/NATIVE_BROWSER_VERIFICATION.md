# Manual native browser verification

14 October 2026, Asia/Calcutta. The user requested autonomous manual browser/computer work. Used the installed Computer Use plugin's documented @oai/sky API, selected only the returned Brave window, and did not control the ChatGPT/Codex desktop interface. No software installed or account/security configuration changed.

## Actual observations

| Check | Result | Evidence scope |
|---|---|---|
| Installed native browser | PASS | Windows app inventory returned Brave; launched the existing installation and selected its unique returned New Tab window. |
| Production landing page | PASS | Entered the existing workers.dev HTTPS URL through the observed address bar. Native Brave rendered the RIVEXIS logo, approved colors, hero, shared blockchain visual and public navigation. No TLS interstitial was bypassed. This is rendering evidence, not a frame-rate or availability guarantee. |
| Mandatory guest access boundary | PASS | Entered /workspace/frontier directly in this separate native browser session. After navigation completed, actual page showed Session ended, withheld workspace data and offered Log in again with next=/workspace/frontier. No login credentials entered or browser cookies imported. |
| Public feature destinations | PASS for observed destinations only | Native accessibility tree showed GasGuard and Defense Frontier entry links targeting login with their workspace next parameter. Their authenticated calculations were not exercised in this native session. |
| Real wallet permission flow | BLOCKED | Existing Brave Wallet button opened an introductory panel: Brave Wallet, Use this panel to securely access Web3 and all your crypto assets, Learn more. No usable account or RIVEXIS connection approval flow was exposed. This does not prove that no wallet exists elsewhere on the computer. No setup, import, unlock, signing, permission acceptance or funds movement occurred. |

First AX-only click lacked screenshot geometry and was not counted as an action success. Refreshed with screenshot geometry and retried once; panel became visibly present. Subsequent navigation checks used fresh focus/state observations and waited for the completed page rather than treating an old document during navigation as a result.

Actual evidence outside repository: native-brave-guest-access.png and native-brave-guest-access.txt. Screenshot retains the public URL, branded access gate and withheld-workspace message. Existing deployed baseline remains application 1bbb453dff1e9be35cf89f478ce81677e6369742/API34; this native UI inspection did not independently extract a build meta tag. Prior exact commit and financial evidence remain in SAVED_WALLET_VALIDATION_PROGRESS.md.

## Protected operations

Computer Use guidance prohibits automating user authentication dialogs, password managers and security/privacy permission requests. Do not use another desktop route to bypass these restrictions. Any necessary wallet setup, unlock or protected approval must remain user-controlled. The user authorized autonomous ordinary work, but did not supply the existing database password or an owned sending domain; manual UI access did not make those resources available. Do not reset database credentials, create a wallet, buy a domain or upgrade plans to manufacture completion.

No production runtime changes or extra deployment were needed for these checks. The full production backup/restore, sending-domain authentication and native-wallet permission gates remain open; no institutional launch certification is claimed.
