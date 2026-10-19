# Campus Study Desk launch checklist

Do not launch publicly until every release blocker is complete.

## Source and interface
- [x] Replace the purple-gradient hero with a restrained, content-first layout.
- [x] Remove the decorative CSS illustration and external Google Fonts dependency.
- [x] Remove interface animation and smooth-scroll effects.
- [x] Use a real, data-backed lecture count and indexed-chunk count. No testimonials, customer counters, review cards, or invented performance claims are included.
- [x] Add a local SVG favicon.
- [x] Add in-app Privacy policy and Terms and conditions pages with footer links.
- [x] Keep `.env`, `cookies.txt`, local vector indexes, transcripts, uploads, and Python cache files out of the clean source bundle.
- [x] Add a safe `.env.example` for the keys used by the current Python source.

## Required before public release
- [ ] Connect the purchased custom domain through the hosting provider and domain registrar. Confirm DNS records, HTTPS/TLS, and the final canonical URL. This cannot be completed from source files alone.
- [ ] Check the deployed site builder/hosting layer for any injected “Made with AI” attribution. No such text was found in the supplied local source, so there was no local source tag to remove.
- [ ] Replace the legal-page launch notice with the operator's real legal/business name and monitored contact email.
- [ ] Confirm the applicable jurisdiction and any required consumer/privacy notices with qualified legal review.
- [ ] Confirm actual retention and deletion behaviour for uploads, transcripts, indexes, generated answers, logs, and backups. Update the privacy policy accordingly.
- [ ] Confirm which external AI/transcription providers are active in production and update the privacy policy if the configuration differs from the code paths inspected.
- [ ] Add authentication or an equivalent deployment-level access restriction, plus user-specific data isolation. The current FastAPI routes have no built-in user authentication or per-user authorization and operate on a shared lecture store. Do not expose this instance to the public internet with real student material until access control is implemented and tested.
- [ ] Add abuse protection and rate limits for upload, processing, and model-backed endpoints.
- [ ] Test upload limits, delete/rename operations, server access controls, HTTPS, error handling, and API-key handling on the production deployment.
- [ ] Run the project tests and a browser smoke test against the deployed backend.

## Credentials note
The provided archive contained a populated `.env` and a `cookies.txt` file. They are not included in the clean source bundle. If the entries are active credentials or session cookies, rotate/revoke them before deployment and keep future secrets outside version control.
