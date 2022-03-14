CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) REFERENCES Caregivers,
    UNIQUE (Time, Username)
);

CREATE TABLE Reservations (
  ReservationID int PRIMARY KEY,
  patient varchar(255) REFERENCES Patients,
  Time date,
  caregiver varchar(255) REFERENCES Caregivers,
  Vaccine varchar(255) REFERENCES Vaccines
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

-- using the following to create some initial availabilties
-- there are two patients and two caregivers, patient1, patient2, giver1 and giveEx
INSERT INTO Availabilities
VALUES ('03-20-2022', 'giver1'),
       ('03-21-2022', 'giver1'),
       ('03-22-2022', 'giver1'),
       ('03-20-2022', 'giveEx'),
       ('03-21-2022', 'giveEx'),
       ('03-22-2022', 'giveEx');

-- Creating some initial data for vaccine availablities
INSERT INTO Vaccines
VALUES ('pfizer', 100),
       ('moderna', 150),
       ('j&j', 200);
