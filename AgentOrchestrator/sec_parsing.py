from markitdown import MarkItDown
from bs4 import BeautifulSoup
import copy

table_list = []
# Open File
with open("2025-02-13-10k-AEP.html") as f:
    # Parse HTML File
    soup = BeautifulSoup(f, "html.parser")
    # Find Title Tag
    i = 1
    for table in soup.find_all("table"):
        table_list.append(copy.deepcopy(table))
        table.replaceWith(f"TABLE {i} HERE INSERT HERE ")
        i += 1
    for div in soup.find_all("div", {"style": "display:none"}):
        div.decompose()


# Alter HTML file to see the changes done
with open("gfg.html", "w") as f_output:
    f_output.write(soup.prettify())


md = MarkItDown(enable_plugins=False)
result = md.convert("gfg.html")

with open("Output.txt", "w") as text_file:
    text_file.write(result.text_content)
