filepath = 'services/pdf_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix PyFPDF line break (ln=1)
content = content.replace(', new_x="LMARGIN", new_y="NEXT"', ', ln=1')

# Fix PyFPDF return output format
# Replace returns pdf.output() -> return bytes
# Find return pdf.output()
content = content.replace('return pdf.output()', 
'''out = pdf.output(dest="S")
        if isinstance(out, str):
            return out.encode("latin1")
        return out''')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("File updated successfully.")
