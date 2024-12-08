-- Airlines
INSERT INTO Airlines (airline_name) VALUES
('Air Astana'),
('Emirates'),
('Qatar Airways'),
('Turkish Airlines'),
('Lufthansa');

-- AirlineStaff
INSERT INTO AirlineStaff (staff_username, staff_password, first_name, last_name, date_of_birth, airline_name) VALUES
('alex_khan', 'alex123', 'Alex', 'Khan', '1983-09-12', 'Air Astana'),
('sophia_lee', 'secure789', 'Sophia', 'Lee', '1992-05-14', 'Emirates'),
('mohammed_abdullah', 'mohammed123', 'Mohammed', 'Abdullah', '1987-07-19', 'Qatar Airways'),
('linda_brown', 'linda999', 'Linda', 'Brown', '1990-03-22', 'Turkish Airlines'),
('daniel_schmidt', 'daniel2023', 'Daniel', 'Schmidt', '1985-11-05', 'Lufthansa');

-- Airplanes
INSERT INTO Airplanes (airline_name, airplane_id, total_seats) VALUES
('Air Astana', 'A101', 180),
('Air Astana', 'A102', 200),
('Emirates', 'E201', 300),
('Emirates', 'E202', 320),
('Qatar Airways', 'Q301', 250),
('Qatar Airways', 'Q302', 260),
('Turkish Airlines', 'T401', 280),
('Lufthansa', 'L501', 350);

-- Airports
INSERT INTO Airports (airport_name, city) VALUES
('Almaty Airport', 'Almaty'),
('Dubai Airport', 'Dubai'),
('Doha Airport', 'Doha'),
('Istanbul Airport', 'Istanbul'),
('Frankfurt Airport', 'Frankfurt'),
('New York Airport', 'New York');

-- Flights
INSERT INTO Flights (airline_name, flight_number, airplane_id, departure_time, departure_airport, arrival_time, arrival_airport, ticket_price, flight_status) VALUES
('Air Astana', 'F111', 'A101', '2024-12-15 08:00:00', 'Almaty Airport', '2024-12-15 12:00:00', 'Dubai Airport', 450, 'Scheduled'),
('Emirates', 'F222', 'E201', '2024-12-16 10:00:00', 'Dubai Airport', '2024-12-16 14:00:00', 'Istanbul Airport', 650, 'Scheduled'),
('Qatar Airways', 'F333', 'Q301', '2024-12-17 06:00:00', 'Doha Airport', '2024-12-17 10:00:00', 'Frankfurt Airport', 700, 'Scheduled'),
('Turkish Airlines', 'F444', 'T401', '2024-12-18 09:00:00', 'Istanbul Airport', '2024-12-18 13:00:00', 'New York Airport', 1200, 'Scheduled'),
('Lufthansa', 'F555', 'L501', '2024-12-19 07:30:00', 'Frankfurt Airport', '2024-12-19 12:00:00', 'Dubai Airport', 800, 'Scheduled');

-- Customers
INSERT INTO Customers (customer_email, customer_name, customer_password, building_name, street, city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth) VALUES
('david.johnson@gmail.com', 'David Johnson', 'pass123', 'Building10', 'Main Street', 'Almaty', 'Kazakhstan', '87001234567', 'KZ1234567', '2031-06-15', 'Kazakhstan', '1994-01-15'),
('emma.wilson@gmail.com', 'Emma Wilson', 'emma999', 'BlockA', '2nd Street', 'Dubai', 'UAE', '971506789012', 'UAE987654', '2028-11-12', 'UAE', '1991-12-05'),
('li.chen@gmail.com', 'Li Chen', 'password456', 'Tower3', 'Wall Street', 'New York', 'USA', '12034567890', 'USA543219', '2033-07-01', 'USA', '1988-03-22'),
('ayesha.khan@gmail.com', 'Ayesha Khan', 'ayesha123', 'Villa5', 'Palm Street', 'Doha', 'Qatar', '97455812345', 'QA7654321', '2034-04-20', 'Qatar', '1995-06-11'),
('oliver.brown@gmail.com', 'Oliver Brown', 'brown2024', 'House7', 'Garden Street', 'Istanbul', 'Turkey', '90500123456', 'TR4321098', '2030-02-28', 'Turkey', '1990-09-14');

-- BookingAgents
INSERT INTO BookingAgents (agent_email, agent_password, booking_agent_id) VALUES
('agent01@gmail.com', 'agentpass01', 'BA001'),
('agent02@gmail.com', 'agentpass02', 'BA002'),
('agent03@gmail.com', 'agentpass03', 'BA003'),
('agent04@gmail.com', 'agentpass04', 'BA004'),
('agent05@gmail.com', 'agentpass05', 'BA005');

-- Tickets
INSERT INTO Tickets (ticket_id, airline_name, flight_number) VALUES
('T0011', 'Air Astana', 'F111'),
('T0022', 'Emirates', 'F222'),
('T0033', 'Qatar Airways', 'F333'),
('T0044', 'Turkish Airlines', 'F444'),
('T0055', 'Lufthansa', 'F555');

-- Purchases
INSERT INTO Purchases (ticket_id, customer_email, booking_agent_email, purchase_date, booking_agent_id) VALUES
('T0011', 'david.johnson@gmail.com', 'agent01@gmail.com', '2024-11-20 14:00:00', 'BA001'),
('T0022', 'emma.wilson@gmail.com', 'agent02@gmail.com', '2024-11-25 16:00:00', 'BA002'),
('T0033', 'li.chen@gmail.com', 'agent03@gmail.com', '2024-11-30 10:00:00', 'BA003'),
('T0044', 'ayesha.khan@gmail.com', 'agent04@gmail.com', '2024-12-01 18:30:00', 'BA004'),
('T0055', 'oliver.brown@gmail.com', 'agent05@gmail.com', '2024-12-05 12:15:00', 'BA005');
