# Off-device encrypted recovery copy — 17 October 2026

This continues the actual production logical recovery drill in RECOVERY_DRILL_20261017.md. It changes no application, financial model, production database, authentication settings or deployment configuration.

The user was shown the exact private destination, the 728,698-byte encrypted kit, its production database/authentication and Vault recovery contents, and the requirement to keep its key separate. After the user instructed continuation, uploaded only that encrypted kit to a private folder in the existing owner's connected Google Drive. No paid service, shared link permission or new application project was enabled. Account addresses, private Drive identifiers, download credentials and the recovery key are omitted from this public record; the owner handoff retains the private destination.

Read back both folder and file permissions. Each reports shared=false and only the existing owner's permission. The file has the expected folder parent, application/octet-stream MIME type and size. Independently downloaded the complete file through the connector, then checked:

| Check | Actual result |
|---|---|
| Encrypted bytes | 728,698 |
| Download SHA256 equals original | 5a2f7ed38bef8c3ada3b9d746d7531eaaf6a3492588615956d8d96f874eb383a |
| AES-256-GCM authenticated decryption | PASS, using the separate local key |
| Decrypted ZIP SHA256 equals previously validated package | bfbc732a48c090e0bb93f9dd2f29cd8cf8c9554cefa77fc06457b8f4c00de749 |
| Decrypted data written during this check | No; verified in memory, temporary key/plaintext buffers cleared |
| Recovery key uploaded | No |
| Verification time | 2026-10-17T14:58:30.283Z |

This establishes an off-device encrypted copy and a successful byte/authentication round trip. It does not establish independent off-device key custody, a restore on a second machine, automatic retention, a recovery-point/recovery-time commitment, or full provider/service reconstruction. The separate local key still needs protected independent custody. Do not upload it beside the encrypted kit or describe this step as complete disaster recovery.

The previous actual local restore reconciled 102 archived table-data entries and 27,667 rows, including authentication records, and verified Vault logical recovery under a fresh local key. That restore was not repeated for this storage-only step. Existing financial/browser checks retain their exact recorded commit scope. Sending-domain authentication and native-wallet permission UX remain separate launch assurance gates. Added recurring services cost remains $0.
