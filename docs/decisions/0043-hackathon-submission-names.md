# ADR 0043: The hackathon submission may name the event and its two sponsors

- Status: accepted
- Date: 2026-10-28
- Phase: after 13

## Context

Stepswitch is entered in a hackathon whose official name contains the names of its two
sponsors: the company that runs Token Factory and the company that publishes the Nemotron
models. The event's rules ask for things that working rule 4 forbids:

- the README must say how the project uses the sponsors' models and service, and judges read it
  next to the event's own wording;
- the submission text, the feedback form and the video script name the event, its service and
  its models the way the event does;
- the service's SDKs read two environment variables whose names start with the service's
  company name, and Stepswitch must pass them on verbatim.

ADR 0007 keeps company names out of every committed text by a hash denylist, with a short list
of interoperability identifiers. It already allows URLs and `org/name` model IDs, so the API
host and IDs such as `nvidia/nemotron-3-super-120b-a12b` need nothing new. What it does not
allow is the bare names in prose.

## Decision

1. The scan of `tests/unit/test_repo_hygiene.py` stays on for every file. The sponsor that
   runs Token Factory is added to the denylist, so the rule now also covers that name outside
   the submission.
2. **A narrow scope, by place.** Two names, and only those two, are allowed in two places:
   - files under `hackathon/` (the submission package);
   - the README's hackathon section, between `<!-- hackathon:start -->` and
     `<!-- hackathon:end -->`.
   The two names are the event's sponsors: the company that runs Token Factory and the
   company that publishes Nemotron. They are held as SHA-256 hashes in `EVENT_NAME_HASHES`, the
   same way as the denylist, so the test file names no company itself. Every other company name
   is still a failure in those places, and both names are still a failure everywhere else.
3. **Two environment variables** that the service's own SDK and CLI read verbatim (its API key
   and its project ID) join `ALLOWED_IDENTIFIERS`, as ADR 0007 item 3 allows for variables that
   other software requires. Stepswitch's config names the key's variable in
   `api_key_env`; nothing in the code needs the company's name as a value.
4. Code, configuration, the registry, the docs outside the README section, commit messages and
   claims call the service Token Factory and the models by their model names. The endpoint in
   examples is named `tokenfactory`.
5. Self-tests in the hygiene test use a fictional event sponsor and check both directions: the
   names pass inside the scope, fail outside it, and a third company name fails inside it.

## Consequences

- The submission can use the event's official name and the sponsors' product names as the
  event's rules expect, and the rest of the repository keeps working rule 4 unchanged.
- The scope is two paths and two names. Widening it needs a change to this ADR and to the
  test's self-tests.
- Removing `hackathon/` and the README section after judging restores the previous state with
  no other change.
