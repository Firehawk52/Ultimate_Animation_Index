# Security policy

## Reporting a vulnerability

Please do not publish an exploitable security issue in a public GitHub issue. Use
GitHub's private vulnerability reporting feature for the repository when available,
or contact the repository owner privately.

Include the affected version, reproduction steps, expected impact and any suggested
mitigation. Do not include real UserList private keys or other personal data.

## Sensitive local data

Each installation creates an Ed25519 private key in `.userlist-keys/`. The private
key must never be committed, uploaded or shared. The `.gitignore` excludes this
directory by default.

UserList codes intentionally omit favorites, watch status, personal ratings, private
notes and the sender's display name. Imported codes are verified and validated before
browser data is changed.
