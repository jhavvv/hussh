# Requirements and acceptance status

The attached specification is the source of the requirement identifiers. Implemented code is distinguished from executed acceptance checks.

| Requirement | Implementation | Verification / limit |
|---|---|---|
| FR1 Screenshot | Flutter image picker; browser PNG/JPG chooser | Code present; OCR/device acceptance pending |
| FR2 Text input | Editable text, 10,000-character cap | Backend invalid and valid input tests pass; browser sample tested |
| FR3 OCR | ML Kit on mobile, Tesseract in browser; explicit correction step | Device/browser OCR accuracy not measured |
| FR4 History | Optional device-local save/open/delete | Browser save/open flow tested; Flutter pending |
| FR5 Indicators | URL, email, phone extraction plus heuristic cues | Unit test passes |
| FR6 AI | TF-IDF/logistic regression plus rule cues in FastAPI | Synthetic baseline only; browser-only demo uses rules |
| FR7 Historical comparison | Exact URL and token overlap against report dataset | Match/no-match tests pass; illustrative seed data only |
| FR8 Explanation | Classifier, history, community, trusted evidence separate | API response test and browser inspection pass |
| FR9 Risk result | Low/medium/high composite risk index | High-risk flow tested; not calibrated confidence |
| FR10 Search/feed | Search API and client search; browser category filter | Implemented; capped at 200 reports |
| FR11 Similar reports | Related report cards open detail | Backend match test; browser result inspected |
| FR12 Reporting | Authenticated redacted posts/receipts | API authentication, redaction, confirmation tests pass |
| FR13 Unique evidence | Database unique constraint per report/account | Duplicate-receipt test passes; cross-account abuse remains possible |
| FR14 Comments | Report-bound authenticated comments, redacted | Comment isolation and redaction test passes |
| FR15 Verification | Operator-assigned reviewer; atomic decision and audit | Role, vote conflict, provenance and role injection tests pass |
| NFR1 Explainability | Distinct evidence and non-inherited verification | Tested; heuristic cues are not model-level feature attribution |
| NFR2 Privacy | No screenshot endpoint, no analysis table, opt-in local history | Server no-retention test passes; native cache cleanup untested |
| NFR3 Usability | Responsive UI, clear status, errors, editable OCR | Desktop browser inspected; usability study pending |
| NFR4 Performance | Async clients, quick local baseline | Local classifier timing recorded; <=5-second network median unmeasured |
| NFR5 Reliability | Validation, timeouts, error states, no false result on classifier failure | Input and classifier failure tests pass; device/network testing pending |
| NFR6 Accuracy | Precision/recall/F1 evaluation script | 16 synthetic holdout samples only; independent corpus needed |
| NFR7 Security | Salted hashes, random revocable tokens, roles, HTTPS release requirement | Role/session tests pass; security audit pending |
| NFR8 Scalability | Stateless API with PostgreSQL option | Single-process auth limiter, 200-record matching cap; not load tested |
| NFR9 Compatibility | Flutter Android/iOS sources, responsive web | Native builds and compact device checks pending |
| NFR10 Maintainability | Repository/use-case boundaries, separate intelligence module | Source reviewed; native static analysis pending |
| NFR11 Integrity | Counts never grant verification; immutable-by-API audit records | Role/precedence/audit tests pass |

## Manual acceptance remaining

1. Build Android and iOS; correct any SDK/plugin compatibility findings.
2. Run screenshot OCR with legible, rotated, blurred, empty and oversized images; verify errors and local-only processing.
3. Run the API suite against a disposable PostgreSQL database as well as SQLite.
4. Test multi-device concurrent receipts, reviewer changes, token expiry and connectivity loss.
5. Measure at least 30 end-to-end analyses on a normal connection and record median latency.
6. Evaluate on a licensed, independently labelled, deduplicated held-out corpus; report precision, recall, F1, false negatives and uncertainty.
7. Conduct task-based usability checks at common phone sizes and with screen readers.
