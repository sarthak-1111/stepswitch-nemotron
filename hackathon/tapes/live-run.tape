# The video's live run (0:15-0:50): one task on Token Factory, each step line naming its model
# and the task's running tokens and dollars.
#
# Before recording, from the repository root:
#   python hackathon/tapes/setup_demo.py --dest /tmp/unit-convert     # Nano-first policy
#   export NEBIUS_API_KEY=<your key>   STEPSWITCH=$(pwd)
# then `vhs hackathon/tapes/live-run.tape`. The tape inherits the shell's environment; the key
# is never typed on screen. A take costs about US$ 0.05 to 0.30 (the run stops at 0.30).
# With the Nano-first policy the gates may fail twice and the task escalates to Ultra; when a
# take has no escalation, use the demo page's "Watch an escalation" replay for 0:50-1:30.
Output hackathon/tapes/out/live-run.mp4

Require uv

Set Shell "bash"
Set FontSize 16
Set Width 1600
Set Height 900
Set Padding 20
Set TypingSpeed 25ms
Set WaitTimeout 15m

Hide
Type "cd /tmp/unit-convert && export PS1='$ ' && clear"
Enter
Sleep 500ms
Show

Type "cat stepswitch.toml | grep -A2 'policy.rules'"
Enter
Sleep 4s

Type `uv run --project "$STEPSWITCH" ssw run --allow-remote --budget-usd 0.3 'Add temperatures to the unit converter: Celsius ("C"), Fahrenheit ("F") and Kelvin ("K"), as a new kind called "temperature". tests/test_temperature.py describes the expected results.'`
Sleep 500ms
Enter
Wait+Screen /Trajectory:/
Sleep 8s
