"""What Andy may offer after a web answer, so a look-up can become something useful, always with a yes.

Each web tool returns its line as "next". The conversation suite gives the model the same lines in
its stand-in results (evals/run_suite.py), so it measures what the robot does. Standard library
only: the suite's Nebius job imports this file.
"""

NEXT = {
    "whats_on": ("If one of these sounds good to them, offer to remind them before it starts. Set the reminder "
                 "with set_reminder only after they say yes."),
    "look_up": ("If the answer is about something they plan to do (a visit, an opening time, a deadline), offer "
                "a reminder for it. Set it with set_reminder only after they say yes."),
    "check_message": ("If they ask to let family know, call share_with_family once to prepare a short note. "
                      "Read its confirmation question exactly, wait for a yes, and call it again unchanged. "
                      "Nothing is shared by the proposal."),
}
