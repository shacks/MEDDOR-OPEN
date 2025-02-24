# MedDor Notes

[![License](https://img.shields.io/github/license/shacks/MEDDOR-OPEN)](LICENSE)
[![Issues](https://img.shields.io/github/issues/shacks/MEDDOR-OPEN)](https://github.com/shacks/MEDDOR-OPEN/issues)

MedDor Notes is a secure and streamlined medical note-taking solution designed **by doctors, for doctors**. With HIPAA compliant processing, MedDor Notes ensures your patient data stays private and secure—everything runs locally with no remote data storage.

---

## Overview

MedDor Notes is built with **Streamlit** and integrates with **Supabase** to manage user data and prompts. It’s designed to:
- **Record Patient Consultations**: Easily capture audio during consultations.
- **Convert Recordings to Text**: Use AI-powered transcription.
- **Analyze & Summarize Medical Notes**: Automatically generate concise summaries in a standard medical format.

When a new user logs in, the application checks for a pre-existing prompt in the Supabase database. If none is found, it creates a default prompt that guides the summarization process.

---

## Default Prompt

If a user doesn’t have a saved prompt, the following default is automatically inserted:

```text
Given medical notes or transcription, produce a concise summary in standard medical format:
- No duplication of information between sections.
- All lab results must only appear in the "Labs" section.
- All future actions/items must be included in the "Action Plan" section.

**Sections:**
- **CC**: Reason for visit/consultation
- **HPI**: Patient complaints, history, context
- **Treatments Tried**: List
- **Physical Exam**: List
- **Labs**: All laboratory results
- **Imaging**: List
- **Diagnosis/Impression**: List
- **Action Plan**: List
```

---

## Features

- **User Authentication**:  
  Login with Google using a secure app password. Automatic user prompt initialization based on your email.

- **Core Functionalities**:
  - 🎙️ **Audio Recorder**: Record and save consultations locally.
  - 🎯 **Audio Summary**: Convert audio recordings into summarized text.
  - 📝 **Notes Summary**: Summarize medical notes with AI.

- **Additional Options**:
  - ⚙️ **Payments & Settings**: Customize your AI prompt and manage subscriptions.
  - ❓ **Support & Feedback**: Get help and share your insights.

- **Privacy & Security**:
  - HIPAA compliant processing.
  - No data storage—everything remains on your device.
  - Secure AI processing for medical documentation.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/shacks/MEDDOR-OPEN.git
cd MEDDOR-OPEN
```

Set up a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Configure your secrets:

Set up your Supabase credentials and the `app_password` in your Streamlit secrets file (e.g., `.streamlit/secrets.toml`).

---

## How to Run

Activate your virtual environment (if not already active):

```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

Run the Streamlit app:

```bash
streamlit run app.py
```

Open your browser:

Once the app is running, your default web browser should open a new tab at [http://localhost:8501](http://localhost:8501). If it doesn’t, open your browser and go to that URL manually.

**Interacting with the Application:**

- **Not Logged In**:  
  You’ll see a welcome screen prompting for the app password and a Google Login button.

- **Logged In**:  
  After logging in, the app will initialize your default prompt (if not already set), display core features with page links, show your available credits, and provide a Logout option.

---

## Project Structure

```plaintext
MEDDOR-OPEN/
├── app.py               # Main entry point for the Streamlit app
├── pages/               # Contains feature-specific pages:
│   ├── 1_Audio Recorder.py
│   ├── 2_Audio Summarization.py
│   ├── 3_Notes Summarization.py
│   ├── 4_Payments & Settings.py
│   └── 5_Support & Feedback.py
├── components/          # Custom components (e.g., available_credits)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## Contributing

Contributions are welcome! To contribute:

1. **Fork the repository.**
2. **Create a feature branch:**

   ```bash
   git checkout -b feature/my-feature
   ```

3. **Commit your changes:**

   ```bash
   git commit -m "Add my feature"
   ```

4. **Push to your branch:**

   ```bash
   git push origin feature/my-feature
   ```

5. **Open a Pull Request** against the main repository.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or support, please open an issue on GitHub or contact the maintainers directly.

---

MedDor Notes – Simple, Secure, Efficient  
Created by Doctors, for Doctors
