RPRMS Sample Dataset — 100 Research Papers
===========================================
The actual seed data is defined inside:
  scripts/seed_sample_data.py

To load the dataset into MySQL, run from project root:
  python scripts/seed_sample_data.py

This script:
- Reads existing departments and uses their real dept_ids
- Creates faculty users if needed (password: Faculty@123)
- Creates real PDF files in uploads/papers/
- Generates QR codes for approved papers
- Records status history for each paper
- Is safe to run multiple times (skips duplicates)
