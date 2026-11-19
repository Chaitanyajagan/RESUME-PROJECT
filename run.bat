@echo off
echo =======================================================
echo Starting EDUKRON Resume Intelligence & HR Automation
echo =======================================================

IF EXIST .venv\Scripts\streamlit.exe (
    .\.venv\Scripts\streamlit.exe run app.py
) ELSE (
    streamlit run app.py
)

pause
