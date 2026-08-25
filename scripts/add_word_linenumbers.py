import os
import win32com.client

base_dir = r"c:\研究\CourageeRobotResearch"
docx_path = os.path.join(base_dir, "Frontiers_Submission_Manuscript.docx")
pdf_path = os.path.join(base_dir, "Frontiers_Submission_Manuscript.pdf")

word = win32com.client.Dispatch("Word.Application")
word.Visible = False

try:
    doc = word.Documents.Open(docx_path)
    
    # Enable continuous line numbering for all sections
    for sec in doc.Sections:
        sec.PageSetup.LineNumbering.Active = True
        sec.PageSetup.LineNumbering.StartingNumber = 1
        sec.PageSetup.LineNumbering.CountBy = 1
        sec.PageSetup.LineNumbering.RestartMode = 0 # wdRestartContinuous
        sec.PageSetup.LineNumbering.DistanceFromText = 36 # 0.5 inch

    # Save document
    doc.Save()
    
    # Export to PDF for validation
    doc.ExportAsFixedFormat(pdf_path, 17) # 17 = wdExportFormatPDF
    doc.Close()
    print("Successfully added continuous line numbers and exported PDF!")
finally:
    word.Quit()
