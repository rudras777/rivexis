# Saved wallet identity validation

14 October 2026, Asia/Calcutta. Baseline main 437a656554f2ca2f79c06f9bc761fe2f41a8bf19, API33. Previous merged recovery CI 38479161913 passed; production root served that exact commit.

Account preference writes previously accepted any 40-digit hexadecimal wallet, including the zero address and malformed mixed-case checksum. This disagreed with the inspection, provider and Settings UI validators. Shared server/client preference validation now applies strict checksums and rejects zero addresses before normalization. Lowercase public addresses and correct checksums remain supported; five-address bound and deduplication remain.

For legacy reads, only invalid saved wallet entries are filtered from the returned preferences. Other valid appearance, financial and contract settings remain. Original metadata is not modified; an explicit owner save is still required for persistence. No migration, deletion, authentication, signing, financial-kernel or design changes.

New backend regressions cover valid checksum/lowercase/numeric addresses; zero/bad checksum/whitespace/non-string/non-hex inputs; no provider write on invalid input; legacy reads preserving unrelated preferences and original metadata. The first run exposed an old test's unchecked uppercase fixture; replaced with an actual EIP-55-valid identity. All 221 financial/API/account tests then passed, as did web typechecking. New browser regression covers invalid addresses before writes, valid identity save/reload and duplicate rejection. Final CI and deployment verification pending.

Rollback: retain existing full API33 artifact fdb58f92ddcdb8461ed5ec45ba1097e9e37b69e3440647a743c62a48f45bd4b2 and existing Worker versions. Only account-preferences.mjs changes in the backend deployment; all other deployed files must byte-match. Production backup/restore, sending-domain authentication and native-wallet permission certification remain separate unresolved gates.
