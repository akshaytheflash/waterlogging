@echo off
echo Installing dependencies...
pip install -r ml_requirements.txt

echo Running Database Migration...
python scripts/migrate_db.py

echo Training Initial Model...
python scripts/train_model.py

echo Setup Complete!
pause
