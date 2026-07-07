import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import sqlite3
import sys
import os
import pandas as pd
import openpyxl

version = "1.0.0"

class ScheduleManagement:
  """This is the class for the ability to create and control
  schedules, tasks, and Azure ticket updates."""
  def __init__(self, title, description, start_date="", end_date=""):
    self._title = title
    self._date = datetime.datetime.now()
    self._completed = False
    self._description = description
    self.db_id = None
    self.start_date = start_date
    self.end_date = end_date

  def task_complete(self):
    """Function for defining when a task is complete"""
    self._completed = True
    return f"{self._title} Task ticket is now complete!"

  def task_details(self):
    """Function for displaying task details and status"""
    status = "Complete" if self._completed else "Pending"
    return f"{self._title} [{status}]: {self._description}"

  @property
  def title(self):
    """This function returns the task title"""
    return self._title

  @property
  def completed(self):
    """This functions returns if the task is completed"""
    return self._completed


class TaskTicket(ScheduleManagement):
  """This is the class to deal with Task tickets
  to allow all details of what is needed to be completed
  on the day."""

  def __init__(self, title, description, start_date="", end_date=""):
    super().__init__(title, description, start_date, end_date)


class AzureTickets(ScheduleManagement):
  """This is the class to deal with Azure Tickets,
  this is to track all completed tickets done by the
  user."""

  def __init__(self, title, description,ticket_number, ticket_url, story_points):
    super().__init__(title, description)
    self._ticket_number = ticket_number
    self._ticket_url = ticket_url
    self._story_points = story_points

  @property
  def ticket_url(self):
    """This function returns the ticket url"""
    return self._ticket_url

  @property
  def ticket_number(self):
    """This function returns the ticket number"""
    return self._ticket_number

  @property
  def story_points(self):
    """This function returns the story points"""
    return self._story_points

class DatabaseManager:
  """This class will act as the database management system for this
  project."""
  def __init__(self, db_name="schedule_management.db"):
    self._db_name = db_name
    self._setup_database()

  def _setup_database(self):
    """This function will set up the master database"""
    with sqlite3.connect(self._db_name) as connection:
      cursor = connection.cursor()

      #creating the unified table
      cursor.execute("""
      CREATE TABLE IF NOT EXISTS tickets(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ticket_type TEXT,
      title TEXT,
      description TEXT,
      is_completed BOOLEAN DEFAULT 0,
      ticket_number TEXT,
      ticket_url TEXT,
      story_points INTEGER,
      start_date TEXT,
      end_date TEXT)
                     """)
      connection.commit()
      try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN start_date TEXT")
        cursor.execute("ALTER TABLE tickets ADD COLUMN end_date TEXT")
        connection.commit()
        print("Database successfully updated!")
      except sqlite3.OperationalError:
        print("Database already up to date!")

  def save_new_ticket(self, ticket_type, title, description, ticket_number="", ticket_url="", story_points=0, start_date="", end_date=""):
    """This function will save a new ticket to the database"""
    with sqlite3.connect(self._db_name) as connection:
      cursor = connection.cursor()

      cursor.execute("""
      INSERT INTO tickets (ticket_type, title, description, is_completed, ticket_number, ticket_url, story_points, start_date, end_date)
                     VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?)"""
                     , (ticket_type, title, description, ticket_number, ticket_url, story_points, start_date, end_date))
      connection.commit()
      return cursor.lastrowid

  def get_all_tickets(self):
    """This function will return all tickets from the database"""
    with sqlite3.connect(self._db_name) as connection:
      cursor = connection.cursor()

      #selecting all we need to see
      cursor.execute("SELECT id, ticket_type, title, description, is_completed, ticket_number, ticket_url, story_points, start_date, end_date FROM tickets")
      return cursor.fetchall()

  def update_ticket_status(self, ticket_id):
    """update a ticket status to be completed"""
    with sqlite3.connect(self._db_name) as connection:
      cursor = connection.cursor()

      """using UPDATE to change an existing row, SET to change the value,
      and WHERE to make sure we only update the specific clicked ticket."""

      cursor.execute("""
        UPDATE tickets
        SET is_completed = 1
        WHERE ID =?""", (ticket_id,))

      connection.commit()

  def wipe_database(self):
    """This function will wipe the database"""
    with sqlite3.connect(self._db_name) as connection:
      cursor = connection.cursor()

      """using DELETE to remove a row, WHERE to make sure we only remove the specific clicked ticket."""
      cursor.execute("""
        DELETE FROM tickets""")
      connection.commit()

class ScheduleManagementWindow(QMainWindow):
  """This is the start of the GUI Application
  for the Schedule Management System."""
  def __init__(self):
    super().__init__()

    #set the window properties and title
    self._db_db_name = None
    self.setWindowTitle("Schedule Management System")
    self.resize(800,600)

    #database setup
    self._db = DatabaseManager()

    #database wipe
    self._db.wipe_database()

    #the storage list for all tasks
    self._all_tickets = []

    #Master Container
    #is a layout container that will move with the window
    central_container = QWidget()
    layout = QVBoxLayout()

    #Tab Manager
    self.tabs = QTabWidget()

    #Task Ticket Tab
    self.tab_standard = QWidget()
    #Azure Ticket Tab
    self.tab_azure = QWidget()

    #add the tab pages to the manager
    self.tabs.addTab(self.tab_standard, "Standard Tasks")
    self.tabs.addTab(self.tab_azure, "Azure Tickets")


    #building tab 1 for tasks
    standard_layout = QVBoxLayout()

    self.task_field = QLineEdit()
    self.task_field.setPlaceholderText("Enter a task")

    #calendar widget
    self.start_date_edit = QDateEdit()
    self.start_date_edit.setCalendarPopup(True)
    self.start_date_edit.setDate(QDate.currentDate())

    self.end_date_edit = QDateEdit()
    self.end_date_edit.setCalendarPopup(True)
    self.end_date_edit.setDate(QDate.currentDate())



    self.add_button = QPushButton("Add Task")
    self.add_button.clicked.connect(self.add_task)

    #adding the widgets to the layout
    standard_layout.addWidget(self.task_field)
    standard_layout.addWidget(QLabel("Start Date:"))
    standard_layout.addWidget(self.start_date_edit)
    standard_layout.addWidget(QLabel("End Date:"))
    standard_layout.addWidget(self.end_date_edit)
    standard_layout.addWidget(self.add_button)
    self.tab_standard.setLayout(standard_layout)

    #building tab 2 for Azure Tickets
    azure_layout = QVBoxLayout()

    self.azure_title = QLineEdit()
    self.azure_title.setPlaceholderText("Azure Ticket Title")

    self.azure_number = QLineEdit()
    self.azure_number.setPlaceholderText("Azure Ticket Number")

    self.azure_url = QLineEdit()
    self.azure_url.setPlaceholderText("Azure Ticket URL")

    self.azure_story_points = QLineEdit()
    self.azure_story_points.setPlaceholderText("Azure Ticket Story Points")

    self.add_azure_button = QPushButton("Add Azure Ticket")
    self.add_azure_button.clicked.connect(self.add_azure_ticket)

    azure_layout.addWidget(self.azure_title)
    azure_layout.addWidget(self.azure_number)
    azure_layout.addWidget(self.azure_url)
    azure_layout.addWidget(self.azure_story_points)
    azure_layout.addWidget(self.add_azure_button)
    self.tab_azure.setLayout(azure_layout)

    #Build the master list
    self.task_list = QListWidget()
    self.task_list.itemChanged.connect(self.complete_task)

    self.update_to_excel = QPushButton("Export to Excel")
    self.update_to_excel.clicked.connect(self.export_to_excel)

    #Lock all the build together
    layout.addWidget(self.tabs)
    layout.addWidget(self.task_list)
    layout.addWidget(self.update_to_excel)
    central_container.setLayout(layout)
    self.setCentralWidget(central_container)

    #load all saved tickets
    self.load_saved_tickets()

  def export_to_excel(self):
    "Method to trigger an export of data to excel"
    with sqlite3.connect("schedule_management.db") as conn:
      task_data = pd.read_sql_query("""SELECT * FROM tickets where ticket_type = 'Task'""", conn)
      azure_data = pd.read_sql_query("""SELECT * FROM tickets where ticket_type = 'Azure'""", conn)

    with pd.ExcelWriter('schedule_management.xlsx') as writer:
      task_data.to_excel(writer, sheet_name="Tasks", index=False)
      azure_data.to_excel(writer, sheet_name="Azure Tickets", index=False)

    answer = QMessageBox.question(
      self,
      "Export to Excel Completed",
      "Data successfully imported to Excel! \n\nDo you want to wipe the current data and start fresh?",
      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if answer == QMessageBox.StandardButton.Yes:
      #wiping the database
      self._db.wipe_database()
      #clearing the front end of all the list
      self.task_list.clear()
      self._all_tickets.clear()

  def add_task(self):
    """Method triggered when the 'Add Task' button is clicked."""
    input_text = self.task_field.text()
    start_str = self.start_date_edit.date().toString(Qt.ISODate)
    end_str = self.end_date_edit.date().toString(Qt.ISODate)

    # Check if the text box is empty
    if not input_text:
      # Pop up a native macOS error/warning box!
      warning = QMessageBox()
      warning.setIcon(QMessageBox.Warning)
      warning.setWindowTitle("Missing Information")
      warning.setText("You cannot add an empty task!")
      warning.setInformativeText("Please type a task title before clicking Add.")
      warning.exec()
      return  # This acts as your "exit cause" for the method. It stops running right here.

    #building the backend object
    new_task = TaskTicket(title=input_text, description="Created via GUI", start_date=start_str, end_date=end_str)
    #Keeps it in short-term storage
    self._all_tickets.append(new_task)
    #Saves it to the database
    generate_id = self._db.save_new_ticket(ticket_type="Task", title=input_text, description="Created via GUI",start_date=start_str, end_date=end_str)
    new_task.db_id = generate_id

    list_item = QListWidgetItem(new_task.title)
    list_item.setCheckState(Qt.Unchecked)
    list_item.setData(Qt.UserRole, new_task)

    self.task_list.addItem(list_item)
    self.task_field.clear()

  def add_azure_ticket(self):
    """Method triggered when the 'Add Azure Ticket' button is clicked."""
    input_title = self.azure_title.text()
    input_number = self.azure_number.text()
    input_url = self.azure_url.text()
    input_story_points = self.azure_story_points.text()

    if not input_title:
      warning = QMessageBox()
      warning.setIcon(QMessageBox.Warning)
      warning.setWindowTitle("Missing Information")
      warning.setText("You cannot add an empty ticket!")
      warning.setInformativeText("Please type a ticket title before clicking Add.")
      warning.exec()
      return

    if not input_number:
      warning = QMessageBox()
      warning.setIcon(QMessageBox.Warning)
      warning.setWindowTitle("Missing Number")
      warning.setText("You cannot add an empty ticket!")
      warning.setInformativeText("Please type a ticket number before clicking Add.")
      warning.exec()
      return

    if not input_url:
      warning = QMessageBox()
      warning.setIcon(QMessageBox.Warning)
      warning.setWindowTitle("Missing URL")
      warning.setText("You cannot add a ticket without a URL")
      warning.setInformativeText("Please add a URL before clicking Add.")
      warning.exec()
      return

    try:
      points_int = int(input_story_points)
    except ValueError:
      warning = QMessageBox()
      warning.setIcon(QMessageBox.Warning)
      warning.setWindowTitle("Missing Story Points")
      warning.setText("You cannot add a ticket without story points")
      warning.setInformativeText("Please add story points before clicking Add.")
      warning.exec()
      return

    #build the object
    new_azure_ticket = AzureTickets(
      title=input_title,
      description="Created via Azure Tab",
      ticket_number=input_number,
      ticket_url=input_url,
      story_points=points_int)

    #adding this to backend storage
    self._all_tickets.append(new_azure_ticket)
    #saving to the database
    generate_id = self._db.save_new_ticket(ticket_type="Azure", title=input_title, description="Created via Azure Tab", ticket_number=input_number, ticket_url=input_url, story_points=points_int)
    new_azure_ticket.db_id = generate_id

    #UI magic Trick
    list_item = QListWidgetItem(new_azure_ticket.title)
    list_item.setCheckState(Qt.Unchecked)

    #Hides the rich Azure Object
    list_item.setData(Qt.UserRole, new_azure_ticket)

    #makes this visible on the screen
    self.task_list.addItem(list_item)

    #reset the forms
    self.azure_title.clear()
    self.azure_number.clear()
    self.azure_url.clear()
    self.azure_story_points.clear()


  def complete_task(self, item):
    """Method triggered when a checkbox is clicked."""

    if item.checkState() == Qt.Checked:
      backend_ticket = item.data(Qt.UserRole)
      success_message = backend_ticket.task_complete()
      print(success_message)


      self._db.update_ticket_status(backend_ticket.db_id)

      self.task_list.blockSignals(True)
      item.setText(f"[Complete] {backend_ticket.title}")
      item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
      self.task_list.blockSignals(False)

  def load_saved_tickets(self):
    """Method to load saved tasks from the database."""

    saved_tickets = self._db.get_all_tickets()

    for row in saved_tickets:
      ticket_id, ticket_type, title, description, is_completed, ticket_number, ticket_url, story_points, start_date, end_date = row
      if ticket_type == "Task":
        new_task = TaskTicket(title=title, description=description, start_date=start_date, end_date=end_date)
        new_task.db_id = ticket_id
        self._all_tickets.append(new_task)
        list_item = QListWidgetItem(new_task.title)
        list_item.setCheckState(Qt.Unchecked)
        list_item.setData(Qt.UserRole, new_task)
        self.task_list.addItem(list_item)
      elif ticket_type == "Azure":
        new_azure_ticket = AzureTickets(title=title, description=description, ticket_number=ticket_number, ticket_url=ticket_url, story_points=story_points)
        new_azure_ticket.db_id = ticket_id
        self._all_tickets.append(new_azure_ticket)
        list_item = QListWidgetItem(new_azure_ticket.title)
        list_item.setCheckState(Qt.Unchecked)
        list_item.setData(Qt.UserRole, new_azure_ticket)
        self.task_list.addItem(list_item)

      if is_completed:
        list_item.setCheckState(Qt.Checked)
        list_item.setText(f"[Completed] {title}")
        list_item.setFlags(list_item.flags() & ~Qt.ItemIsUserCheckable)

        backend_obj = list_item.data(Qt.UserRole)
        backend_obj.task_complete()
      else:
        list_item.setCheckState(Qt.Unchecked)

def main():
  """This is the main function to start the application."""
  #Start the Application
  app = QApplication(sys.argv)

  #instantiate the window
  window = ScheduleManagementWindow()
  window.show()

  #to allow the application to exit
  sys.exit(app.exec())

import subprocess


def build_exe():
  exe_name = f"Task_and_Azure_Ticket_Management_{version}"

  subprocess.run([
      sys.executable, "-m", "PyInstaller",
      "--onefile",
      "--noconsole",
      "--name", f"Task_and_Azure_Ticket_Management_{version}",
      "--collect-all", "PySide6",
      __file__
  ])

  print(f"\n✅ Build complete: dist/{exe_name}.exe")


if __name__ == "__main__":
    if "--build" in sys.argv:
        build_exe()
    else:
        main()
