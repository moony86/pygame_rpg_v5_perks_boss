# Archive policy

`notes/legacy-build-command.txt` preserves the scratch command previously called `123.txt`. Use `build.bat` and `readme/BUILD_GAME.md` instead.

No runtime modules are archived: static imports connect all six runtime packages to the entry point, including editor code. Legacy skills remain active features and need a gameplay decision before removal.

Generated local builds, snapshots and captures are ignored in place. Deleted duplicate source is recoverable from the previous base commit.
