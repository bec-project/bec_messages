import os
import subprocess
from pathlib import Path

os.chdir(Path(__file__).parent)

schema_dir = Path("../json_schema")
output_dir = Path("../typescript/bec-messages/src/generated_message_types")
names = [f.split(".")[0] for f in os.listdir(schema_dir) if f.endswith(".json")]
# TODO clear the write directory before writing to it
for file in names:
    outfile = file + ".ts"
    subprocess.run(
        ["json2ts", str(schema_dir / (file + ".json")), str(output_dir / outfile)]
    )

with open(output_dir / "index.ts", "w") as f:
    for file in names:
        f.write(f'export {{ {file} }} from "./{file}"\n')
    f.write("\n")
