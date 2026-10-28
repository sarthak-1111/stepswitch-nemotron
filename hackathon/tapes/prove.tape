# The video's proof segment (2:15-2:35): the results re-checked from the committed runs, with no
# key and nothing billed. Record from the repository root with `vhs hackathon/tapes/prove.tape`.
Output hackathon/tapes/out/prove.mp4

Require uv

Set Shell "bash"
Set FontSize 16
Set Width 1600
Set Height 900
Set Padding 20
Set TypingSpeed 25ms
Set WaitTimeout 5m

Hide
Type "export PS1='$ ' && clear"
Enter
Sleep 500ms
Show

Type "uv run ssw prove --claim C-029 --claim C-030"
Sleep 500ms
Enter
Wait+Screen /passing/
Sleep 4s

Type "uv run ssw prove --render-readme && git status --short README.md claims/"
Sleep 500ms
Enter
Sleep 8s
