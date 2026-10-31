# RyGTS CI workers

GitLab rygt-team/RyGTS is the authoritative source. GitHub Actions builds, tests and packages development into separate Release (`ci`) and optimized Debug/Diagnostics (`debug-ci`) ZIPs, then uploads them and their checksums to the matching GitLab Generic Package Registry channels. Debug includes verified symbols and tracing tools. No tagged releases or changelogs are created. See the source repository docs/dev/CI.md.
