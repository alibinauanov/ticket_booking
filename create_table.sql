CREATE TABLE Airlines (
    airline_name VARCHAR(20),
    PRIMARY KEY(airline_name)
);

CREATE TABLE AirlineStaff (
    staff_username VARCHAR(20),
    staff_password VARCHAR(20),
    first_name VARCHAR(20),
    last_name VARCHAR(20),
    date_of_birth DATE,
    airline_name VARCHAR(20),
    FOREIGN KEY(airline_name) REFERENCES Airlines(airline_name) ON DELETE CASCADE
);

CREATE TABLE Airplanes (
    airline_name VARCHAR(20),
    airplane_id CHAR(5),
    total_seats SMALLINT,
    PRIMARY KEY(airline_name, airplane_id),
    FOREIGN KEY(airline_name) REFERENCES Airlines(airline_name) ON DELETE CASCADE
);

CREATE TABLE Airports (
    airport_name VARCHAR(20),
    city VARCHAR(20),
    PRIMARY KEY(airport_name)
);

CREATE INDEX AirplaneID_Index ON Airplanes(airplane_id);

CREATE TABLE Flights (
    airline_name VARCHAR(20),
    flight_number CHAR(5),
    airplane_id CHAR(5),
    departure_time DATETIME,
    departure_airport VARCHAR(20),
    arrival_time DATETIME,
    arrival_airport VARCHAR(20),
    ticket_price SMALLINT,
    flight_status VARCHAR(20),
    PRIMARY KEY(airline_name, flight_number),
    FOREIGN KEY(airplane_id) REFERENCES Airplanes(airplane_id) ON DELETE CASCADE,
    FOREIGN KEY(departure_airport) REFERENCES Airports(airport_name) ON DELETE CASCADE,
    FOREIGN KEY(arrival_airport) REFERENCES Airports(airport_name) ON DELETE CASCADE
);

CREATE TABLE Customers (
    customer_email VARCHAR(320),
    customer_name VARCHAR(20),
    customer_password VARCHAR(20),
    building_name VARCHAR(20),
    street VARCHAR(20),
    city VARCHAR(20),
    state VARCHAR(20),
    phone_number CHAR(11),
    passport_number CHAR(9),
    passport_expiration DATE,
    passport_country VARCHAR(20),
    date_of_birth DATE,
    PRIMARY KEY(customer_email)
);

CREATE TABLE BookingAgents (
    agent_email VARCHAR(255),
    agent_password VARCHAR(20),
    booking_agent_id CHAR(5),
    PRIMARY KEY(agent_email)
);

CREATE TABLE Tickets (
    ticket_id CHAR(5),
    airline_name VARCHAR(20),
    flight_number CHAR(5),
    PRIMARY KEY(ticket_id),
    FOREIGN KEY(airline_name, flight_number) REFERENCES Flights(airline_name, flight_number) ON DELETE CASCADE
);

CREATE INDEX BookingAgentID_Index ON BookingAgents(booking_agent_id);

CREATE TABLE Purchases (
    ticket_id CHAR(5),
    customer_email VARCHAR(320),
    booking_agent_email VARCHAR(320),
    purchase_date DATETIME,
    booking_agent_id CHAR(5),
    PRIMARY KEY(ticket_id, customer_email),
    FOREIGN KEY(ticket_id) REFERENCES Tickets(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY(customer_email) REFERENCES Customers(customer_email) ON DELETE CASCADE,
    FOREIGN KEY(booking_agent_email) REFERENCES BookingAgents(agent_email) ON DELETE CASCADE,
    FOREIGN KEY(booking_agent_id) REFERENCES BookingAgents(booking_agent_id) ON DELETE CASCADE
);