from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Create patient failed, Cannot save")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
        return
    print(" *** Account created successfully *** ")


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Create caregiver failed, Cannot save")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
        return
    print(" *** Account created successfully *** ")


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    global current_patient
    # Check 1, if someone is already logged in
    if current_patient is not None or current_caregiver is not None:
        print("Already logged-in")
        return

    # Check 2, check input, 3 in length and have all information
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login patient failed")
        print("Db-error", e)
        quit()
    except Exception as e:
        print("Error occurred when logging in. Please try again!")
        print("Error:", e)
        return

    # check if login was successful
    if patient is None:
        print("Error occurred when logging in. Please try again!")
    else:
        print("Patient logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login caregiver failed")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when logging in. Please try again!")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Error occurred when logging in. Please try again!")
    else:
        print("Caregiver logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    # everyone can look up schedule so we only have to check for input validity
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        # print out schedule on input date
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        select_schedule = "SELECT * FROM Availabilities WHERE Time = %s"
        cursor.execute(select_schedule, d)
        for row in cursor.fetchall():
            print(row[1] + " is available.")

        cursor2 = conn.cursor()

        cursor2.execute("SELECT * FROM Vaccines")
        for row in cursor2.fetchall():
            print(row[0] + " has " + str(row[1]) + " doses")

    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when searching")
        print("Error:", e)
        return
    finally:
        cm.close_connection()


def reserve(tokens):
    # input date, vaccine
    # check if user is patient
    global current_patient
    if current_patient is None:
        print("Please login as a patient first!")
        return

    # Check if input is valid, must be 3 tokens
    if len(tokens) != 3:
        print("Please try again!")
        return

    date = tokens[1]
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    d = datetime.datetime(year, month, day)

    vaccine_name = tokens[2]

    # Check if vaccine name is valid
    if (vaccine_name != "pfizer") and (vaccine_name != "moderna") and (vaccine_name != "j&j"):
        print("Invalid vaccine name, must be pfizer, moderna or j&j")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    # Check if vaccines are available
    check_vaccine = "SELECT * FROM Vaccines WHERE Name = %s"
    cursor.execute(check_vaccine, vaccine_name)
    vaccine_count = cursor.fetchone()
    if vaccine_count[1] == 0:
        print("This vaccine is unavailable")
        return

    # Check if any availabilities on input date
    cursor2 = conn.cursor()
    schedule_check = "SELECT * FROM Availabilities WHERE Time = %s"
    cursor2.execute(schedule_check, d)
    available = cursor2.fetchone()

    if available is None:
        print("No available caregiver on given date")
        return

    # Once we pass all checks, we create a reservation
    # Remove avilability and decrease vaccine count
    # current_patient, d, caregiver, vaccine_name
    giver = available[1]
    id = 0
    try:
        # create id
        cursor6 = conn.cursor()
        cursor6.execute("SELECT MAX(ReservationID) FROM Reservations")
        row = cursor6.fetchone()[0]
        if row is None:
            id = 1
        else:
            id = row + 1
        # reserve
        cursor3 = conn.cursor()
        reserve = "INSERT INTO Reservations VALUES(%s, %s, %s, %s, %s)"
        cursor3.execute(reserve, (id, current_patient.username, d, giver, vaccine_name))
        conn.commit()
        # remove reserved availability
        cursor4 = conn.cursor()
        remove_availablility = "DELETE FROM Availabilities WHERE Time = %s AND Username = %s"
        cursor4.execute(remove_availablility, (d, giver))
        conn.commit()
        # reduce vaccine count
        cursor5 = conn.cursor()
        vaccine = Vaccine(vaccine_name, vaccine_count).get()
        vaccine.decrease_available_doses(1)

    except pymssql.Error as e:
        print("Reservation Failed")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when reserving")
        print("Error:", e)
        return
    print("Reservation completed")




def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")



def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None

    # Checking to make sure vaccine name is one of the three
    if (vaccine_name != "pfizer") and (vaccine_name != "moderna") and (vaccine_name != "j&j"):
        print("Invalid vaccine name, must be pfizer, moderna or j&j")
        return

    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Failed to get Vaccine information")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to get Vaccine information")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Failed to add new Vaccine to database")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Failed to add new Vaccine to database")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Failed to increase available doses for Vaccine")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Failed to increase available doses for Vaccine")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    # check if logged in and which user, patient or caregiver
    global current_caregiver
    global current_patient

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        if current_caregiver is None and current_patient is None:
            print("log in first :)")
            return
        # caregivers, print appointment ID, vaccine name, date, and patient name.
        elif current_caregiver is not None:
            caregiver_search = "select * from reservations where caregiver = %s"
            cursor.execute(caregiver_search, current_caregiver.username)
            result = cursor.fetchall()
            print("Appointments for " + current_caregiver.username + ":")
            for row in result:
                print(str(row[0]) + " " + row[4] + " " + row[2].strftime("%m/%d/%Y") + " " + row[1])
        # patients,   print appointment ID, vaccine name, date, and caregiver name.
        else:
            patient_search = "select * from reservations where patient = %s"
            cursor.execute(patient_search, current_patient.username)
            result = cursor.fetchall()
            print("Appointments for " + current_patient.username + ":")
            for row in result:
                print(str(row[0]) + " " + row[4] + " " + row[2].strftime("%m/%d/%Y") + " " + row[3])
    except pymssql.Error as e:
        print("Error occured when checking appointments")
        print("Db-error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
        return
    finally:
        cm.close_connection()




def logout():
    # logging current login out
    global current_caregiver
    global current_patient
    # give different feedback depending on if login is patient or caregiver
    if current_caregiver is not None:
        current_caregiver = None
        print("Caregiver logged out successfully!")
        return
    elif current_patient is not None:
        current_patient = None
        print("Patient logged out successfully!")
        return
    else:
        print("No account logged in")
        return



def start():
    stop = False
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")  #// TODO: implement login_patient (Part 1)
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date>")  #// TODO: implement search_caregiver_schedule (Part 2)
        print("> reserve <date> <vaccine>") #// TODO: implement reserve (Part 2)
        print("> upload_availability <date>")
        print("> cancel <appointment_id>") #// TODO: implement cancel (extra credit)
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")  #// TODO: implement show_appointments (Part 2)
        print("> logout") #// TODO: implement logout (Part 2)
        print("> Quit")
        print()
        response = ""
        print("> Enter: ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Type in a valid argument")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Try Again")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout()
        elif operation == "quit":
            print("Thank you for using the scheduler, Goodbye!")
            stop = True
        else:
            print("Invalid Argument")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
