"""
Usage:
    python load_knowledge.py <bot_id> <file_path>

Example:
    python load_knowledge.py test knowledge.txt
    python load_knowledge.py test docs/manual.pdf
"""
import sys
from services.rag_service import add_to_knowledge_base
from services.file_parser import parse_file
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) != 3:
    print("Usage: python load_knowledge.py <bot_id> <file_path>")
    sys.exit(1)

bot_id = sys.argv[1]
file_path = sys.argv[2]

with open(file_path, "rb") as f:
    content = f.read()

text = parse_file(content, file_path)
add_to_knowledge_base(bot_id, text)
print(f"Done. Loaded '{file_path}' into bot_id='{bot_id}'")
