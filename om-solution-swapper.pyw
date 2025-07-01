# om solution swapper csvreader python
# original ahk by panic
# python port by omgitsabist

# F8 goes back to the next worst solution
# F9 swaps the current solution out for the next best solution
# F10 updates the metrics overlay
# F11 repopulates past solves overlay with all non superceded solves in selection (TBA)
# F12 repopulates past solves overlay with all solves in selection (TBA)
# double-clicking a solution in the list will swap in that one

# for multiple metrics, i recommend making multiple copies of this script
# after finishing one metric, close the script for it and open the script for the next one

# ---------- SETUP ----------

# this script requires two external python libraries
# pynput - for input detection (https://pynput.readthedocs.io/en/latest/)
# wxpython - for gui (https://wxpython.org/index.html)

# this parser also requires om.py to be in the same directory as this script
# (you can download it here at http://critelli.technology/om.py)

# the game's solutions folder
GAMEFILES = r"path\to\game\solutions\folder"

# the puzzle file
PUZZLE = r"path\to\puzzle"

# a folder with the solutions to be presented
SOLUTIONS = r"path\to\solutions\folder"

# the csv with submission data
DATACSV = r"path\to\data\file.csv"

# text file for current solution metadata
METADATA = r"path\to\metadata.txt"

# text file for past competitors
PAST = r"path\to\past_players.txt"

# exported csv path for scoring
CSV = r"path\to\export\csv\metric.csv"

# list of hosts
HOSTS = ["a", "list", "of", "names"]

# list of teams
TEAMS = {"team name": ["members"]}

# metric functions
# check the simulator metrics section at http://events.critelli.technology/static/metrics.html for the list of metrics
# metrics can be obtained through 
# M("metric name") to simulate the metric 
# M(metric number) to parse from the csv
def Primary():
    return M("cost")

def Secondary():
    return M("cycles")

def Tertiary():
    return M("area")

# extra metric notes (not counted towards scoring)
def Supplement():
    return ""

# solution isn't loaded if return value is greater than 0
def Restriction():
    return M("default restrictions")

# metric abbreviations
METRIC_1 = "c"
METRIC_2 = "g"
METRIC_3 = "a"

# metric names for the export csv
NAME_1 = "Cost"
NAME_2 = "Cycles"
NAME_3 = "Area"

# score formula
def ScoreFormula(index):
    placement = table.GetItem(index, TABLE_COLUMNS.index("#")).GetText()
    score = 300 / (int(placement) + 29)
    return score

# --------- CODE ----------

import os
import shutil
import csv
import wx
import pynput
import om

TABLE_COLUMNS = ["#", "Primary", "Secondary", "Tertiary", "Supplement", "Superseded", "Current", "Submitter", "Pronouns", "Name", "File Name", "Timestamp", "Error"]

current_solution = -1
seen_solutions = []
table: wx.ListCtrl = None
sim: om.Sim = None
solution_key = ""
csv_data = {}
error = ""
notes_frm: wx.Frame = None

def M(metric):
    global error
    if metric == "default restrictions":
        default = M("overlap")
        default += max(0, M("parts of type baron - 1"))
        default += max(0, M("parts of type glyph-disposal") - 1)
        default += M("duplicate reagents") + M("duplicate products")
        default += max(0, M("maximum track gap^2") - 1)
        return default
    if isinstance(metric, str):
        global sim
        try:
            return sim.metric(metric)
        except:
            try:
                return sim.approximate_metric(metric)
            except om.SimError as err:
                global error
                error = err.message
                return -1
    if isinstance(metric, int):
        if metric in range(1, 7):
            global csv_data
            global solution_key
            try:
                return int(csv_data[solution_key][metric-1])
            except:
                return csv_data[solution_key][metric-1]
        else:
            error = "metric number out of range (1-6)"
            return -1

def read_data():
    global csv_data
    csv_data = {}
    with open(DATACSV, mode='r', encoding="utf-8") as file:
        reader = csv.reader(file)
        for line in reader:
            data = {}
            submitter_timestamp = line[0] + line[12]
            data["Pronouns"] = line[1]
            for i in range(6):
                data[i] = line[i+5]
            csv_data[submitter_timestamp] = data

    return csv_data

def load_solutions(csv_data):
    data_list = []
    directory = os.fsencode(SOLUTIONS)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".solution"):
            parsed = filename.split('_')
            timestamp = parsed[1]
            submitter = '_'.join(parsed[3:])[:-9]
            try:
                data = csv_data[submitter + timestamp]
            except:
                data = {}
                for column in TABLE_COLUMNS:
                    data[column] = ""
            data["File Name"] = filename

            global sim
            global solution_key
            sim = om.Sim(PUZZLE, os.path.join(SOLUTIONS, filename))
            solution_key = submitter + timestamp

            if Restriction() > 0:
                continue
            
            data["Submitter"] = submitter
            data["Name"] = om.Solution(os.path.join(SOLUTIONS, filename)).name.decode("utf-8")
            data["Timestamp"] = timestamp

            data["Primary"] = Primary()
            data["Secondary"] = Secondary()
            data["Tertiary"] = Tertiary()
            data["Supplement"] = Supplement()
            global error
            data["Error"] = error
            error = ""

            data_list.append(data)

    return data_list

def parse_solutions(data_list):
    data_list = sorted(data_list, key=lambda d: d["Timestamp"])
    data_list = sorted(data_list, key=lambda d: d["Tertiary"], reverse=True)
    data_list = sorted(data_list, key=lambda d: d["Secondary"], reverse=True)
    data_list = sorted(data_list, key=lambda d: d["Primary"], reverse=True)
    data_list = sorted(data_list, key=lambda d: d["Error"], reverse=True)

    aliases = {}
    for team_name in TEAMS:
        for index in TEAMS[team_name]:
            aliases[index] = team_name

    seen = []
    placement = 1
    tie_placement = 1
    previous_metrics = (0, 0, 0)
    for data in reversed(data_list):
        submitter = data["Submitter"]
        primary = data["Primary"]
        secondary = data["Secondary"]
        tertiary = data["Tertiary"]

        if submitter in aliases:
            submitter = aliases[submitter]
            data["Submitter"] = submitter
        
        if submitter not in seen:
            seen.append(submitter)
        else:
            data["Superseded"] = 'x'
            continue

        if data["Error"] != "":
            data["Superseded"] = 'x'
            continue

        if submitter in HOSTS:
            data["Superseded"] = 'h'
        
        if previous_metrics == (primary, secondary, tertiary):
            data["#"] = tie_placement
        else:
            data["#"] = placement
            tie_placement = placement
            previous_metrics = (primary, secondary, tertiary)

        if submitter not in HOSTS:
            placement += 1

    return data_list

def item_selected(event: wx.ListEvent):
    index = event.GetIndex()
    table: wx.ListCtrl = event.GetEventObject()
    set_focus(index)

def set_focus(index):
    for i in range(table.GetItemCount()):
        table.SetItem(i, TABLE_COLUMNS.index("Current"), "")
    table.SetItem(index, TABLE_COLUMNS.index("Current"), ">>")
    table.Focus(index)

    global current_solution
    if index != current_solution:
        place_solution(index)

    current_solution = index

    update_notes()

def place_solution(index):
    if current_solution >= 0:
        old_solution = os.path.join(GAMEFILES, table.GetItem(current_solution, TABLE_COLUMNS.index("File Name")).GetText())
        if os.path.isfile(old_solution):
            os.remove(old_solution)

    filename = table.GetItem(index, TABLE_COLUMNS.index("File Name")).GetText()
    source = os.path.join(SOLUTIONS, filename)
    destination = os.path.join(GAMEFILES, filename)
    shutil.copyfile(source, destination)


def on_release(key):
    if key == pynput.keyboard.Key.f8:
        prev_solution()
    if key == pynput.keyboard.Key.f9:
        next_solution()
    if key == pynput.keyboard.Key.f10:
        update_metadata()

def prev_solution():
    global current_solution

    if current_solution != 0:
        new_solution = current_solution
        new_solution -= 1
        while table.GetItemText(new_solution, TABLE_COLUMNS.index("Superseded")) == "x" and new_solution != 0:
            new_solution -= 1
        
        if table.GetItemText(new_solution, TABLE_COLUMNS.index("Superseded")) == "x" and new_solution == 0:
            return

        set_focus(new_solution)

def next_solution():
    global current_solution

    if current_solution != table.GetItemCount() - 1:
        new_solution = current_solution
        new_solution += 1
        while table.GetItemText(new_solution, TABLE_COLUMNS.index("Superseded")) == "x" and new_solution != table.GetItemCount() - 1:
            new_solution += 1
        set_focus(new_solution)

def get_metadata():
    placement = table.GetItem(current_solution, TABLE_COLUMNS.index("#")).GetText()
    submitter = table.GetItem(current_solution, TABLE_COLUMNS.index("Submitter")).GetText()
    pronouns = table.GetItem(current_solution, TABLE_COLUMNS.index("Pronouns")).GetText()
    name = table.GetItem(current_solution, TABLE_COLUMNS.index("Name")).GetText()
    primary = table.GetItem(current_solution, TABLE_COLUMNS.index("Primary")).GetText()
    secondary = table.GetItem(current_solution, TABLE_COLUMNS.index("Secondary")).GetText()
    tertiary = table.GetItem(current_solution, TABLE_COLUMNS.index("Tertiary")).GetText()

    if placement == "":
        metadata = submitter + "*"
    else:
        metadata = "#" + placement + " " + submitter

    if pronouns != "":
        metadata += " (" + pronouns + ")"
    
    metadata += " - " + name + "\n"

    metadata += primary + METRIC_1
    if secondary != "":
        metadata += "/" + secondary + METRIC_2
    if tertiary != "":
        metadata += "/" + tertiary + METRIC_3

    return metadata

def update_metadata():
    global seen_solutions
    global current_solution

    with open(METADATA, "w") as file:
        metadata = get_metadata()

        file.write(metadata)
        if current_solution not in seen_solutions:
            seen_solutions.append(current_solution)
            seen_solutions = sorted(seen_solutions, reverse=True)

    with open(PAST, "w") as file:
        for i in seen_solutions:
            placement = table.GetItem(i, TABLE_COLUMNS.index("#")).GetText()
            submitter = table.GetItem(i, TABLE_COLUMNS.index("Submitter")).GetText()

            past_list = []
            if i == current_solution:
                if i != max(seen_solutions):
                    past_list.append("> current <\n")
            else:
                if placement == "":
                    past_list.append("--- " + submitter + "*\n")
                else:
                    past_list.append("#" + placement.ljust(3, " ") + " " + submitter + "\n")

            for line in past_list:
                file.write(line)

def update_notes():
    global notes_frm
    notes_frm.Show()
    notes_dir = os.path.join(SOLUTIONS, table.GetItem(current_solution, TABLE_COLUMNS.index("File Name")).GetText() + ".notes.txt")
    metadata = get_metadata()
    if os.path.exists(notes_dir):
        with open(notes_dir, "r", encoding="utf-8") as file:
            content = metadata + "\n\n"
            content += file.read()
            notes_frm.set_text(content)
    else:
        notes_frm.set_text(metadata)


def create_table(frm, data_list):
    table = wx.ListCtrl(frm, -1, style=wx.LC_REPORT)
    table.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL))

    for column_label in TABLE_COLUMNS:
        table.AppendColumn(column_label)

    for i in range(1, 7):
        column = table.GetColumn(i)
        column.SetAlign(wx.LIST_FORMAT_RIGHT)
        table.SetColumn(i, column)

    for data in data_list:
        item = []
        for column in TABLE_COLUMNS:
            if column in data:
                item.append(data[column])
            else:
                item.append("")
        table.Append(item)

    for i in range(len(TABLE_COLUMNS)):
        table.SetColumnWidth(i, -1)

    table.SetColumnWidth(TABLE_COLUMNS.index("Primary"), -2)
    table.SetColumnWidth(TABLE_COLUMNS.index("Secondary"), -2)
    table.SetColumnWidth(TABLE_COLUMNS.index("Tertiary"), -2)
    table.SetColumnWidth(TABLE_COLUMNS.index("Supplement"), -2)
    table.SetColumnWidth(TABLE_COLUMNS.index("Superseded"), -2)
    table.SetColumnWidth(TABLE_COLUMNS.index("Current"), -2)

    table.Bind(wx.EVT_LIST_ITEM_ACTIVATED, item_selected)

    return table

def write_csv():
    if os.path.exists(CSV):
        with open(CSV, "w", newline='') as file:
            writer = csv.writer(file, delimiter=',')
            writer.writerow(["#", "Username", "Score", NAME_1, NAME_2, NAME_3, "Solution Name", "Notes"])

            for i in reversed(range(table.GetItemCount())):
                superseded = table.GetItem(i, TABLE_COLUMNS.index("Superseded")).GetText()
                if superseded == "x":
                    continue

                placement = table.GetItem(i, TABLE_COLUMNS.index("#")).GetText()
                submitter = table.GetItem(i, TABLE_COLUMNS.index("Submitter")).GetText()
                name = table.GetItem(i, TABLE_COLUMNS.index("Name")).GetText()
                primary = table.GetItem(i, TABLE_COLUMNS.index("Primary")).GetText()
                secondary = table.GetItem(i, TABLE_COLUMNS.index("Secondary")).GetText()
                tertiary = table.GetItem(i, TABLE_COLUMNS.index("Tertiary")).GetText()
                supplement = table.GetItem(i, TABLE_COLUMNS.index("Supplement")).GetText()

                score = ScoreFormula(i)
                if superseded == 'h':
                    placement += "*"

                writer.writerow([placement, submitter, score, primary, secondary, tertiary, name, supplement])


class Solutions(wx.Frame):
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(Solutions, self).__init__(*args, **kw)

        global table

        self.SetInitialSize(wx.Size(1000, 590))
        self.Bind(wx.EVT_CLOSE, self.on_close)
        table = create_table(self, data_list)

    def on_close(self, event):
        old_solution = os.path.join(GAMEFILES, table.GetItem(current_solution, TABLE_COLUMNS.index("File Name")).GetText())
        if os.path.isfile(old_solution):
            os.remove(old_solution)
        
        with open(METADATA, "w") as file:
            file.write("")

        with open(PAST, "w") as file:
            file.write("")

        exit()

class Notes(wx.Frame):
    text: wx.TextCtrl = None
    panel: wx.Panel = None
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(Notes, self).__init__(*args, **kw)

        self.SetInitialSize(wx.Size(600, 500))
        self.Bind(wx.EVT_CLOSE, self.on_notes_close)
        self.panel = wx.Panel(self)
        self.text = wx.TextCtrl(self.panel, style=wx.TE_READONLY | wx.TE_MULTILINE, size=self.GetSize())
        sizer = wx.BoxSizer()
        sizer.Add(self.text, wx.SizerFlags().Border(wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, 10))
        self.panel.SetSizer(sizer)

        self.SetBackgroundColour(wx.Colour(255, 255, 255, 255))

    def set_text(self, content):
        self.text.SetLabel("")
        self.text.write(content)
        self.text.ShowPosition(0)
        
    def on_notes_close(self, event):
        self.Hide()

if __name__ == "__main__":
    csv_data = read_data()
    data_list = load_solutions(csv_data)
    data_list = parse_solutions(data_list)

    listener = pynput.keyboard.Listener(on_release=on_release)
    listener.start()

    app = wx.App()

    metric_name = METRIC_1 + METRIC_2 + METRIC_3
    solution_frm = Solutions(None, title="OM Solution Swapper - " + om.Puzzle(PUZZLE).name.decode("utf-8") + " " + metric_name.upper())
    solution_frm.Show()

    notes_frm = Notes(None, title="Notes")
    notes_frm.Show()

    set_focus(0)
    if table.GetItemText(current_solution, TABLE_COLUMNS.index("Superseded")) == "x":
        next_solution()
    write_csv()
    
    app.MainLoop()