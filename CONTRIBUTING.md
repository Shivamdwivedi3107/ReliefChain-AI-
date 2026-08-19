# Contributing to ReliefChain AI

Thank you for your interest in contributing to **ReliefChain AI** — the AI-Powered Disaster Relief Management Platform!

---

## 📜 Code of Conduct & Core Principles
1. **Safety First**: Emergency features operate as decision-support tools for certified responders and humanitarian agencies. Human authority must always be preserved.
2. **Quality & Test Coverage**: All pull requests must maintain 100% test pass rates across the automated pytest suite (`python -m pytest`).
3. **No Hardcoded Secrets**: Secrets, keys, and credentials must never be committed to source control.

---

## 🛠️ Local Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-org/reliefchain-ai.git
   cd reliefchain-ai
   ```

2. **Set Up Python Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Start Local Server**:
   ```bash
   py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```

4. **Run Pytest Suite**:
   ```bash
   py -3 -m pytest
   ```

---

## 🔀 Pull Request Process
1. Create a descriptive feature branch: `git checkout -b feature/spheres-forecasting-enhancement`.
2. Ensure code follows PEP 8 style guidelines.
3. Run the automated test suite to confirm 0 failures.
4. Submit a Pull Request detailing the changes and verification steps.
