import os
import subprocess
from pathlib import Path

os.chdir(Path(__file__).parent)

schema_dir = Path("../json_schema")
output_dir = Path("../typescript/bec-messages/src/generated_message_types")
for file in os.listdir(schema_dir):
    if file.endswith(".json"):
        outfile = file.split(".")[0] + ".d.ts"
        subprocess.run(["json2ts", str(schema_dir / file), str(output_dir / outfile)])
