; om solution swapper
; by panic
; with very bad edits by omgitsabist

; at start, measures the Primary(), Secondary() and Tertiary() metrics for
; each solution in the SOLUTIONS folder, then copies the worst one into the
; GAMEFILES folder

; F9 swaps the current solution out for the next best solution
; F8 goes back to the next worst solution
; F7 toggles the visibility of the metrics overlay
; double-clicking a solution in the list will swap in that one

; for multiple metrics, i recommend making multiple copies of this script --
; after finishing one metric, close the script for it and open the script for
; the next one

; set these paths before running!

LIBVERIFY := ""
; the game's solutions folder
GAMEFILES := ""
; the puzzle file
PUZZLE := ""
; a folder with the solutions to be presented
SOLUTIONS := ""
; the csv with submission data
DATACSV := ""
; text file for current solution metadata
METADATA := ""
; text file for past competitors
PAST := ""
; list of hosts
HOSTS := {"someone": 0}
; exported csv path
CSV := ""
; list of teams
TEAMS := {"team name": ["members"]}
; metric shown in the order of the csv
METRIC := 1

; see the "simulator metrics" at
; http://events.critelli.technology/static/metrics.html for the list of metric
; names that can be passed to M()
Primary(primary) {
    return primary
}
Secondary(secondary) {
    return secondary
}
Tertiary(tertiary) {
    return tertiary
}
Supplement() {
    return ""
}
; solutions with Restrictions() > 0 will be skipped
Restrictions(metric) {
    return (metric == "")
}

; metric abbreviations for overlay
a_primary := ""
a_secondary := ""
a_tertiary := ""
; metric names for csv export
n_primary := ""
n_secondary := ""
n_tertiary := ""

; ===

#NoEnv
#Warn
#SingleInstance force
SendMode Input
FileEncoding, UTF-8
placed := ""
row := 1
activeRow := -1
column := {"#": 1, "Primary": 2, "Secondary": 3, "Tertiary": 4, "Supplement": 5, "Superseded": 6, "Current": 7, "Submitter": 8, "Pronouns": 9, "Name": 10, "File Name": 11, "Timestamp": 12, "Error": 13}
DllCall("LoadLibrary", "Str", LIBVERIFY)
Gui, New, , Solution List
Gui, Add, ListView, r30 w700 gListViewUpdate NoSortHdr, #|Primary|Secondary|Tertiary|Supplement|Superseded|Current|Submitter|Pronouns|Name|File Name|Timestamp|Error
LV_ModifyCol(column["Primary"], "Float")
LV_ModifyCol(column["Secondary"], "Float")
LV_ModifyCol(column["Tertiary"], "Float")
LV_ModifyCol(column["Supplement"], "Float")
LV_ModifyCol(column["Superseded"], "Right")
LV_ModifyCol(column["Current"], "Right")
LV_ModifyCol(column["Timestamp"], "Logical")
M(metric) {
    global verifier
    return DllCall("libverify\verifier_evaluate_metric", "Ptr", verifier, "AStr", metric)
}

ALIAS := {}
for key in TEAMS 
    for index in TEAMS[key]
        ALIAS[TEAMS[key][index]] := key

pronouns_by_submitter_timestamp := {}
primary_by_sm := {}
secondary_by_sm := {}
tertiary_by_sm := {}
Loop, Read, %DATACSV%
{
    submitter := ""
    pronouns := ""
    timestamp := ""
    primary := ""
    secondary := ""
    tertiary := ""
    Loop, Parse, A_LoopReadLine, CSV
    {
        if (A_LoopField == "")
            continue
        if (A_Index == 1)
            submitter := A_LoopField
        else if (A_Index == 2)
            pronouns := A_LoopField
        else if (A_Index == 6 and METRIC == 1 or A_Index == 9 and METRIC == 2)
            primary := A_LoopField
        else if (A_Index == 7 and METRIC == 1 or A_Index == 10 and METRIC == 2)
            secondary := A_LoopField
        else if (A_Index == 8 and METRIC == 1 or A_Index == 11 and METRIC == 2)
            tertiary := A_LoopField
        else if (A_Index == 13)
            timestamp := A_LoopField
    }
    key = %submitter%.%timestamp%
    pronouns_by_submitter_timestamp[key] := pronouns
    primary_by_sm[key] := primary
    secondary_by_sm[key] := secondary
    tertiary_by_sm[key] := tertiary
}

Loop, Files, %SOLUTIONS%\*.solution
{
    fullfilename := A_LoopFileName
    SplitPath, fullfilename, name, dir, ext, name_no_ext
    parts := StrSplit(name_no_ext, "_")
    verifier := DllCall("libverify\verifier_create", "AStr", PUZZLE, "AStr", A_LoopFilePath, "Ptr")
    submitter := ""
    maxindex := parts.MaxIndex()
    times := parts.MaxIndex() - 3
    i := 4
    Loop, %times% {
        part := parts[i]
        submitter = %submitter%%part%
        if (i == parts.MaxIndex())
            break
        submitter = %submitter%_
        i := i + 1
    }
    if ( ALIAS.HasKey(submitter) )
        submitter := ALIAS[submitter]
    file := FileOpen(A_LoopFilePath, "r")
    file.Seek(4, 1)
    file.RawRead(byte, 1)
    file.Seek(NumGet(byte, "UInt"), 1)
    file.RawRead(byte, 1)
    len := NumGet(byte, "UInt")
    file.RawRead(bytes, len)
    solution_name := StrGet(&bytes, len, "UTF-8")
    timestamp := parts[2]
    pronounskey = %submitter%.%timestamp%
    if (Restrictions(primary_by_sm[pronounskey]) > 0)
        continue
    LV_Add(, "", Primary(primary_by_sm[pronounskey]), Secondary(secondary_by_sm[pronounskey]), Tertiary(tertiary_by_sm[pronounskey]), Supplement(), "", "", submitter, pronouns_by_submitter_timestamp[pronounskey], solution_name, A_LoopFileName, timestamp, DllCall("libverify\verifier_error", "Ptr", verifier, "AStr"))
    DllCall("libverify\verifier_destroy", "Ptr", verifier)
}
LV_ModifyCol(column["Timestamp"], "Sort")
LV_ModifyCol(column["Tertiary"], "SortDesc")
LV_ModifyCol(column["Secondary"], "SortDesc")
LV_ModifyCol(column["Primary"], "SortDesc")
LV_ModifyCol(column["Error"], "Auto SortDesc")
LV_ModifyCol(column["Submitter"], "Auto Sort")
Loop % LV_GetCount()
{
    LV_GetText(a, A_Index, column["Submitter"])
    LV_GetText(b, A_Index + 1, column["Submitter"])
    LV_GetText(tracks, A_Index, column["Primary"])
    if (HOSTS.HasKey(a))
        LV_Modify(A_Index, "Col6", "h")
    if (a == b)
        LV_Modify(A_Index, "Col6", "x")
}
LV_ModifyCol(column["Timestamp"], "Sort")
LV_ModifyCol(column["Tertiary"], "SortDesc")
LV_ModifyCol(column["Secondary"], "SortDesc")
LV_ModifyCol(column["Primary"], "SortDesc")
LV_ModifyCol(column["Error"], "SortDesc")
LV_ModifyCol(column["Name"], "Auto")
LV_ModifyCol(column["File Name"], "Auto")

x := ""
placement := 1
p_placement := 1
p_1 := 0
p_2 := 0
p_3 := 0
c_1 := 0
c_2 := 0
c_3 := 0
Loop % LV_GetCount()
{
    index := LV_GetCount() - A_Index + 1
    LV_GetText(superseded, index, column["Superseded"])
    LV_GetText(submitter, index, column["Submitter"])
    if (superseded == "x")
        continue
    LV_GetText(c_1, index, column["Primary"])
    LV_GetText(c_2, index, column["Secondary"])
    LV_GetText(c_3, index, column["Tertiary"])
    if (p_1 == c_1 and p_2 == c_2 and p_3 == c_3)
        LV_Modify(index, "Col1", p_placement)
    else
        LV_Modify(index, "Col1", placement)
    LV_GetText(p_placement, index, column["#"])
    LV_GetText(p_1, index, column["Primary"])
    LV_GetText(p_2, index, column["Secondary"])
    LV_GetText(p_3, index, column["Tertiary"])
    if (!HOSTS.HasKey(submitter))
        placement++
}
totalplaces := placement - 1
minprimary := 0
Loop % LV_GetCount()
{
    index := LV_GetCount() - A_Index + 1
    LV_GetText(placement, index, column["#"])
    LV_GetText(submitter, index, column["Submitter"])
    if (placement == 1 and !HOSTS.HasKey(submitter)) {
        LV_GetText(minprimary, index, column["Primary"])
        break
    }
}
csvfile := FileOpen(CSV, "w", "UTF-8")
csv := ""
csv = #,Username,Score,%n_primary%,%n_secondary%,%n_tertiary%,Solution Name,Notes`n
solution_name = ""
bestsofar := 0
Loop % LV_GetCount()
{
    index := LV_GetCount() - A_Index + 1
    LV_GetText(superseded, index, column["Superseded"])
    LV_GetText(submitter, index, column["Submitter"])
    if (superseded == "x")
        continue
    LV_GetText(placement, index, column["#"])
    LV_GetText(c_1, index, column["Primary"])
    LV_GetText(c_2, index, column["Secondary"])
    LV_GetText(c_3, index, column["Tertiary"])
    LV_GetText(solution_name, index, column["Name"])
    LV_GetText(supplement, index, column["Supplement"])
    score := 300 / (placement + 29)
    if (HOSTS.HasKey(submitter)) {
        placement = %placement%*
    }
    csv = %csv%%placement%,%submitter%,%score%,%c_1%,%c_2%,%c_3%,"%solution_name%",%supplement%`n
}
csvfile.write(csv)
csvfile.close()
skipDirection := 1
maxlen := 0
file := FileOpen(METADATA, "w")
file.close()
file := FileOpen(PAST, "w")
file.close()
visited := {}
guiname := A_DefaultGui
notesWindowID := "n/a"
Gosub, SkipSuperseded
Gosub, PlaceSolution
LV_Modify(activeRow, "Focus")
Gui, Show
return
ListViewUpdate:
    if (A_GuiEvent = "DoubleClick") {
        row := LV_GetNext()
        Gosub, PlaceSolution
    }
    return
GuiClose:
    FileDelete, %placed%    
    file := FileOpen(METADATA, "w")
    file.close()
    file := FileOpen(PAST, "w")
    file.close()
    ExitApp
PlaceSolution:
    FileDelete, %placed%
    LV_Modify(activeRow, "Col7", "")
    placed := ""
    activeRow := -1
    if (row = 0)
        return
    if (LV_GetText(filename, row, column["File Name"]) = 0)
        return
    placed := GAMEFILES "\" filename
    FileCopy, %SOLUTIONS%\%filename%, %placed%
    FileEncoding, UTF-8
    FileRead, notes, %SOLUTIONS%\%filename%.notes.txt
    LV_GetText(primary, row, column["Primary"])
    LV_GetText(secondary, row, column["Secondary"])
    LV_GetText(tertiary, row, column["Tertiary"])
    LV_GetText(submitter, row, column["Submitter"])
    LV_GetText(pronouns, row, column["Pronouns"])
    LV_GetText(supplement, row, column["Supplement"])
    LV_GetText(solution_name, row, column["Name"])
    LV_GetText(placement, row, column["#"])
    if (!WinExist("ahk_id " notesWindowID)) {
        Gui, Notes:New, , Notes
        Gui, Notes:Add, Edit, r30 vNotesEdit w700
        Gui Notes:+HwndnotesWindowID
        Gui, Notes:Show
    }
    if (pronouns != "")
        pronouns = (%pronouns%)
    GuiControl, Notes:, NotesEdit, #%placement% %submitter% %pronouns% - %primary%%a_primary%/%secondary%%a_secondary%/%tertiary%%a_tertiary% %supplement% (%solution_name%)`n`n%notes%
    Gui, %guiname%:Default
    activeRow := row
    LV_Modify(activeRow, "Vis Focus Col7", ">>")
    return
SkipSuperseded:
    loop {
        LV_GetText(marker, row, column["Superseded"])
        if (marker == "x")
            row := row + skipDirection
        else
            return
    }
WriteMetadata:
    file := FileOpen(METADATA, "w", "UTF-8-RAW")
    LV_GetText(primary, row, column["Primary"])
    LV_GetText(secondary, row, column["Secondary"])
    LV_GetText(tertiary, row, column["Tertiary"])
    LV_GetText(superseded, row, column["Superseded"])
    LV_GetText(submitter, row, column["Submitter"])
    LV_GetText(pronouns, row, column["Pronouns"])
    LV_GetText(placement, row, column["#"])
    LV_GetText(supplement, row, column["Supplement"])
    LV_GetText(solution_name, row, column["Name"])
    metrics := ""
    if (!HOSTS.HasKey(submitter) and !(superseded == "x"))
        metrics = #%placement%
    metrics = %metrics% %submitter%
    if (superseded == "x")
        metrics = %metrics%*
    if (pronouns != "")
        metrics = %metrics% (%pronouns%)
    metrics = %metrics% - %solution_name%
    metrics = %metrics%`n%primary%%a_primary%
    if (a_secondary != "")
        metrics = %metrics%/%secondary%%a_secondary%
    if (a_tertiary != "")
        metrics = %metrics%/%tertiary%%a_tertiary%
    metrics = %metrics%%A_Space%%supplement%
    file.write(metrics)
    file.close()
    return
UpdatePastList:
    file := FileOpen(PAST, "w")
    file.close()
    LV_GetText(superseded, row, column["Superseded"])
    visited[row] := 0
    if (activeRow > bestsofar and superseded != "x")
        bestsofar = %row%
    Loop % LV_GetCount()
    {
        index := LV_GetCount() - A_Index + 1
        LV_GetText(superseded, index, column["Superseded"])
        LV_GetText(submitter, index, column["Submitter"])
        LV_GetText(placement, index, column["#"])
        if (!visited.HasKey(index) or (index == row and index == bestsofar))
            continue
        if (index == row) {
            FileAppend, > current <`n, %PAST%
            continue
        }
        if (!HOSTS.HasKey(submitter) and !(superseded == "x")) {
            FileAppend, #%placement%, %PAST%
            spaces := 3 - StrLen(placement)
            Loop %spaces% {
                FileAppend, %A_Space%, %PAST%
            }
        }
        else
            FileAppend, ---%A_Space%, %PAST%
        if (superseded == "x")
            submitter = %submitter%*
        FileAppend, %submitter%`n, %PAST%
    }
    return
F8::
    Gui, %guiname%:Default
    row := activeRow - 1
    skipDirection := -1
    Gosub, SkipSuperseded
    if (row > 0)
        Gosub, PlaceSolution
    else
        row := 1
    return
F9::
    Gui, %guiname%:Default
    row := activeRow + 1
    skipDirection := 1
    Gosub, SkipSuperseded
    if (row <= LV_GetCount())
        Gosub, PlaceSolution
    else
        row := LV_GetCount()
    return
~F10::
    Gui, %guiname%:Default
    Gosub, WriteMetadata
    Gosub, UpdatePastList
    return
F11::
    Gui, %guiname%:Default
    row := 0
    Loop
    {
        row := LV_GetNext(row)
        if not row
            break
        LV_GetText(superceded, row, column["Superseded"])
        if (superceded != "x") {
            visited[row] := 0
            if (row > bestsofar)
                bestsofar = %row%
        }
    }
    row := activeRow
    Gosub, UpdatePastList
    return
F12::
    Gui, %guiname%:Default
    row := 0
    Loop
    {
        row := LV_GetNext(row)
        if not row
            break
        visited[row] := 0
        if (row > bestsofar)
            bestsofar = %row%
    }
    row := activeRow
    Gosub, UpdatePastList
    return