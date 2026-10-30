# huSSh — AI-Assisted Scam Message Detection

huSSh is an academic prototype designed to help users identify potentially suspicious messages through AI-assisted risk analysis, explainable warning indicators, and community reporting.

The application provides a Flutter Android client, a responsive web interface, and a FastAPI backend. It combines a machine-learning baseline with heuristic detection rules to assess messages and provide supporting evidence.

**Important:** huSSh is a prototype, not a validated fraud-detection service. Risk classifications are estimates and should not be treated as definitive evidence that a message is safe or fraudulent.

## 1. Key Features

### Scam Message Analysis
- Analyse pasted SMS messages and other suspicious text.
- Display Low, Medium, or High estimated risk.
- Provide a risk index from 0–100.
- Identify warning indicators, including suspicious links, requests for sensitive information, and impersonation patterns.
- Display relevant historical community reports.
- Provide safety recommendations.

### Screenshot Text Extraction
- Select a screenshot containing a message.
- Extract text locally using Google ML Kit on Android.
- Allow users to review or edit the extracted text before analysis.

### Community Reporting
- Publish redacted suspicious-message reports.
- Browse and search community reports.
- Post comments and contribute additional context.
- Indicate that a message was also received.
- Request a report review.

### Reviewer Verification
- Restrict report verification to authorised reviewer accounts.
- Allow reviewers to classify reports as Verified Scam or Verified Legitimate.
- Require an explanation for each verification decision.
- Record reviewer identity, decision details, and timestamps.

### Local Analysis History
- Optionally save analysed messages on the device.
- Reopen previous results.
- Delete saved analyses.

## 2. Technologies Used

| Component | Technology |
|---|---|
| Mobile application | Flutter and Dart |
| Web interface | HTML, CSS and JavaScript |
| Backend API | Python and FastAPI |
| Database | SQLite (local), with PostgreSQL/Docker configuration |
| Machine learning | Scikit-learn, TF-IDF and Logistic Regression |
| Additional detection | Heuristic rules and contextual indicators |
| Screenshot OCR | Google ML Kit Text Recognition |
| Authentication | Token-based sessions and password hashing |
| Version control | Git and GitHub |

## 3. Project Structure

```text
hussh/
├── backend/
│   ├── app.py
│   ├── intelligence.py
│   ├── requirements.txt
│   └── ...
├── mobile/
│   ├── android/
│   ├── assets/
│   │   └── images/
│   │       └── hussh_logo.png
│   ├── lib/
│   │   ├── main.dart
│   │   ├── repositories.dart
│   │   └── view_model.dart
│   └── pubspec.yaml
├── web/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── ...
├── docs/
├── test cases/
└── README.md
```

## 4. Running the Backend

### Requirements

- Python 3.12 or newer, compatible with the listed dependencies
- Internet access for initial package installation

From the project root, create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Start the FastAPI backend:

```powershell
cd backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

The application should be available at:

- Web interface: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- API health endpoint: http://127.0.0.1:8000/api/health

The default local configuration uses SQLite. The database is created automatically during backend startup.

## 5. Running the Flutter Android Application

### Requirements

- Flutter SDK
- Android Studio and Android SDK
- Android emulator or compatible Android device

The Android project files are included in the repository.

From the `mobile` directory:

```powershell
flutter pub get
flutter doctor
flutter devices
```

With the Android emulator running, launch the app:

```powershell
flutter run -d emulator-5554
```

Replace `emulator-5554` if your device has a different identifier.

The Android emulator accesses the local FastAPI server using:

```text
http://10.0.2.2:8000/api
```

Keep the FastAPI server running while testing features that require the backend.

## 6. Running the Web Application

Start the backend as described above, then open:

http://127.0.0.1:8000

When served through FastAPI, the web client can access the backend's analysis, account, community reporting and review features.

The browser-only demonstration has different capabilities and persistence behaviour from the backend-connected application.

## 7. Authentication and Reviewer Access

Users can create community accounts through the application.

New accounts receive the `user` role by default.

The backend also supports a `reviewer` role. Reviewer privileges must be assigned by an authorised operator through the backend environment; ordinary account registration cannot grant reviewer permissions.

Reviewer accounts can access the Review tab, inspect flagged reports, record verification decisions, and provide supporting rationales.

Verification decisions are recorded with the reviewer's identity and timestamp.

## 8. Scam Detection Approach

huSSh uses a hybrid prototype approach combining:

1. TF-IDF text feature extraction.
2. Logistic Regression trained on synthetic scam and legitimate-message examples.
3. Heuristic rules for suspicious language and behaviour.
4. Contextual checks for requests involving credentials, money and impersonation.
5. URL extraction and selected known-brand domain comparisons.
6. Historical report matching using URLs and text similarity.

The detection logic considers categories such as delivery, banking, government impersonation, recruitment, prize scams, account security, and personal impersonation.

The displayed risk index is a heuristic measure, not a calibrated probability.

## 9. Functional Testing

The application has undergone manual testing using an Android emulator, alongside targeted backend classifier checks.

Testing included:

- Suspicious NZ Post delivery messages.
- Legitimate delivery notifications.
- Banking phishing and legitimate banking notifications.
- Government impersonation and legitimate IRD notifications.
- Job scams and legitimate recruitment messages.
- Screenshot OCR and subsequent message analysis.
- Saving and deleting analysis history.
- Community comments.
- Reviewer account access and verification decisions.

### Selected observed results

| Test case | Observed classification | Risk index |
|---|---|---|
| NZ Post phishing — improved detector | High | 74/100 |
| Legitimate NZ Post delivery | Low | 14/100 |
| Kiwibank phishing — improved detector | High | 85/100 |
| Legitimate Kiwibank notification — improved detector | Low | 12/100 |
| IRD phishing | High | 70/100 |
| Legitimate IRD notification | Low | 14/100 |
| Job scam involving an upfront deposit | Medium | 54/100 |
| Legitimate job interview message | Low | 12/100 |

Testing revealed classification weaknesses, including false positives in legitimate banking notifications and underestimated risk in certain phishing and job-scam messages.

Targeted changes improved the banking and delivery examples. The job-scam result remains a documented limitation.

These are selected development and regression tests, not an independent estimate of overall detection accuracy. Additional unseen-message evaluation is needed.

### Backend Tests

The repository also contains backend automated testing and evaluation scripts.

From the `backend` directory:

```powershell
python -m pytest -q
python evaluate.py
```

Run these commands to verify the current test results. Earlier test counts should not be assumed to remain unchanged after classifier modifications.

## 10. Privacy and Security

The prototype includes several privacy and security mechanisms:

- Screenshot text recognition is performed on the device.
- Users can review extracted text before submitting it.
- Analysis history is optional and stored locally.
- Analysis submissions are not intentionally persisted by the analysis endpoint.
- Community reports and comments are stored separately and undergo pattern-based redaction.
- Passwords are salted and hashed.
- Authentication sessions use tokens.
- Reviewer-only operations are protected by server-side role checks.
- Verification decisions are recorded for accountability.

Pattern-based redaction cannot reliably remove all personal information. Users should review their text before publishing reports.

## 11. Limitations and Future Improvements

huSSh remains an academic prototype with several limitations:

- The machine-learning component uses a small synthetic training dataset.
- Detection may produce false positives or fail to recognise unfamiliar scams.
- Risk scores are not calibrated probabilities.
- Some legitimate and unrelated community reports may be incorrectly matched by text similarity.
- Reviewer decisions apply to specific reports, not automatically to similar messages.
- Community reports are not independently verified when initially submitted.
- Account recovery, production-scale monitoring and advanced abuse prevention are not implemented.
- The system has not undergone independent real-world security or classification validation.

Future improvements could include larger independently labelled datasets, additional model evaluation, improved semantic context handling, better similarity matching, broader device testing and more comprehensive automated tests.

## 12. Implementation References

- Flutter: https://docs.flutter.dev/
- FastAPI: https://fastapi.tiangolo.com/
- Scikit-learn: https://scikit-learn.org/
- Google ML Kit Text Recognition: https://pub.dev/packages/google_mlkit_text_recognition
- Flutter Image Picker: https://pub.dev/packages/image_picker

---

**Project:** huSSh — AI-Assisted Scam Message Detection  
**Purpose:** Academic prototype for COMP826 Mobile Systems Development