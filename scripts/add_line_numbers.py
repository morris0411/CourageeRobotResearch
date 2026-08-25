import zipfile
import re
import os

input_docx = "Frontiers_Submission_Manuscript.docx"
output_docx = "Frontiers_Submission_Manuscript_with_lines.docx"

# Add continuous line numbering in Word document.xml / settings.xml
# In Word OpenXML, line numbering on sections is specified by <w:lnNumType w:countBy="1" w:restart="continuous"/> inside <w:sectPr>

with zipfile.ZipFile(input_docx, 'r') as zin:
    doc_xml = zin.read('word/document.xml').decode('utf-8')
    
    # Check if lnNumType already exists
    if 'w:lnNumType' not in doc_xml:
        # Add <w:lnNumType w:countBy="1" w:restart="continuous"/> to all <w:sectPr> elements
        # sectPr usually ends with </w:sectPr>
        doc_xml_modified = re.sub(
            r'(<w:sectPr[^>]*>)',
            r'\1<w:lnNumType w:countBy="1" w:restart="continuous"/>',
            doc_xml
        )
    else:
        doc_xml_modified = doc_xml

    # Write out new docx
    with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, doc_xml_modified.encode('utf-8'))
            else:
                zout.writestr(item, zin.read(item.filename))

print("Successfully injected continuous line numbering into Word document!")
