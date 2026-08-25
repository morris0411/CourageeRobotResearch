$currDir = Get-Location
$docPath = Join-Path $currDir.Path "Frontiers_Submission_Manuscript.docx"
$pdfPath = Join-Path $currDir.Path "Frontiers_Submission_Manuscript.pdf"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docPath)
    foreach ($sec in $doc.Sections) {
        $sec.PageSetup.LineNumbering.Active = $true
        $sec.PageSetup.LineNumbering.StartingNumber = 1
        $sec.PageSetup.LineNumbering.CountBy = 1
        $sec.PageSetup.LineNumbering.RestartMode = 0 # wdRestartContinuous
        $sec.PageSetup.LineNumbering.DistanceFromText = 36
    }
    $doc.Save()
    $doc.ExportAsFixedFormat($pdfPath, 17)
    $doc.Close()
    Write-Output "Word continuous line numbers applied and PDF exported successfully!"
} finally {
    $word.Quit()
}
