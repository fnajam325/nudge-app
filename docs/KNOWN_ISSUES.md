# Known issues

Things the team knows about and has not scheduled.

1. **Transaction data is 24 to 48 hours old.** See [ADR-0002](adr/0002-nightly-transaction-sync.md).
2. **Categorization is rules only.** A merchant that matches no rule in `MERCHANT_RULES` stays uncategorized. Nobody has measured the uncategorized rate recently.
3. **Pushes go out at one UTC hour for everyone.** `users.timezone` is collected at signup but the scheduler does not use it.
4. **Experiment assignment is logged when a user is bucketed, not when they see the variant.**
5. **There is no general feature flag service.** Rollouts use experiment traffic percentages.
6. **The apps are not covered here.** The iOS and Android repositories have their own issue lists.
