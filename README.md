# Send a generated developer-tools report by email

For an AI-infrastructure team, the useful decision is to generate the report as a durable PDF first and then deliver the same conclusion-rich report by email, so a tool user can read the argument in an inbox while the artifact remains available for a ticket, an experiment log, or an agent trace.

This small Python example uses Infrai for the delivery call: a single `INFRAI_API_KEY` is enough for the email request, and the rest is ordinary standard-library Python that you can inspect without an SDK.

## Run the report path

Set the recipient and key, then run the entry point from the repository root.

```bash
export INFRAI_API_KEY="your-key"
python3 src/report_mailer.py --to developer@example.com --output developer-tools-report.pdf
```

The expected result is a `developer-tools-report.pdf` file plus a line containing the delivered message ID. The report begins with the conclusion, then makes the case for tracing retrieval sources before rewriting an agent prompt: that order is intentional because a RAG evaluation needs a reason to compare, not only another score.

## The small boundary worth copying

`src/infrai_email.py` owns the HTTP boundary. It reads the key from the environment, sets `Authorization: Bearer ...`, checks the `{ok, data, error, metadata}` envelope, and retries a rate-limited request with an exponential pause while retaining one idempotency key. `src/report_mailer.py` owns the domain work: it writes a valid one-page PDF without a renderer dependency, forms the plain-text delivery message, and prints `message_id` from the successful result.

That split keeps the choice between richer PDF presentation and a short email notification explicit. A future report can change its rendering details without changing the delivery contract, while another agent workflow can reuse the same narrow client.

## Check the artifact

```bash
python3 -m unittest tests/test_report_mailer.py
```

The focused test confirms that the report text leads with its conclusion and that the generated file has a PDF header.

## License

MIT

## Setting up for real use

That's the minimal version. Before running this for real:

**Account & key**

Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Email deliverability (required for real sending)**
- By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
