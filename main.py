from flask import Flask, render_template, request, session, url_for, redirect, flash
import mysql.connector
import datetime
import json
import decimal


#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = mysql.connector.connect(host='localhost',
							   port=3307,
                               user='root',
                               password='alibi123',
                               database='ticket_reservation',
							   auth_plugin='mysql_native_password')

# ========================================= check apostraphe =========================================
def escape_single_quotes(x):
    """
    Escapes single quotes in a string to prevent SQL errors or injection attacks.

    Args:
        x (str): The input string to sanitize.

    Returns:
        str: A sanitized string with all single quotes escaped (replaced with two single quotes).

    Notes:
        - Useful for handling user inputs such as names or form fields that may contain single quotes.
        - Ensures compatibility with SQL queries by escaping characters correctly.
    """
    assert type(x) == str
    if "'" not in x:
        return x
    db_x = ''
    for i in x:
        if i == "'":
            db_x += "''"
        else:
            db_x += i
    return db_x

# ========================================= PUBLIC =========================================
@app.route('/')
def public_home():
	return render_template('public_home.html')

@app.route('/public_flight_search', methods=['GET', 'POST'])
def public_flight_search():
    """
    Allows public users to search for flights based on criteria such as:
    - Departure city/airport
    - Arrival city/airport
    - Departure/arrival dates
    - Flight status (defaults to 'upcoming')

    Fetches flight details from the database and displays them.
    """
    departure_city = escape_single_quotes(request.form['departure_city'])
    departure_airport = escape_single_quotes(request.form['departure_airport'])
    arrival_city = escape_single_quotes(request.form['arrival_city'])
    arrival_airport = escape_single_quotes(request.form['arrival_airport'])
    departure_date = request.form['departure_date']
    arrival_date = request.form['arrival_date']

    cursor = conn.cursor()
    query = """
        SELECT 
            airline_name, 
            flight_number, 
            (SELECT city FROM Airports WHERE airport_name = departure_airport) AS departure_city, 
            departure_airport, 
            departure_time, 
            (SELECT city FROM Airports WHERE airport_name = arrival_airport) AS arrival_city, 
            arrival_airport, 
            arrival_time, 
            ticket_price, 
            airplane_id
        FROM Flights
        WHERE 
            departure_airport = IF('{}' = '', departure_airport, '{}') AND
            arrival_airport = IF('{}' = '', arrival_airport, '{}') AND
            flight_status = 'upcoming' AND
            (SELECT city FROM Airports WHERE airport_name = departure_airport) = IF('{}' = '', 
                (SELECT city FROM Airports WHERE airport_name = departure_airport), '{}') AND
            (SELECT city FROM Airports WHERE airport_name = arrival_airport) = IF('{}' = '', 
                (SELECT city FROM Airports WHERE airport_name = arrival_airport), '{}') AND
            DATE(departure_time) = IF('{}' = '', DATE(departure_time), '{}') AND
            DATE(arrival_time) = IF('{}' = '', DATE(arrival_time), '{}')
        ORDER BY airline_name, flight_number
    """
    cursor.execute(query.format(
        departure_airport, departure_airport, 
        arrival_airport, arrival_airport, 
        departure_city, departure_city, 
        arrival_city, arrival_city, 
        departure_date, departure_date, 
        arrival_date, arrival_date
    ))
    data = cursor.fetchall()
    cursor.close()

    if data:  # Has data
        return render_template('public_home.html', upcoming_flights=data)
    else:  # No data
        error = 'Sorry ... Cannot find this flight!'
        return render_template('public_home.html', error1=error)


@app.route('/public_status_search', methods=['GET', 'POST'])
def public_status_search():
    """
    Allows public users to search for the status of a flight based on:
    - Airline name
    - Flight number
    - Departure/arrival dates

    Fetches the flight status from the database and displays it.
    """
    airline_name = escape_single_quotes(request.form['airline_name'])
    flight_num = request.form['flight_num']
    arrival_date = request.form['arrival_date']
    departure_date = request.form['departure_date']

    cursor = conn.cursor()
    query = """
        SELECT *
        FROM Flights
        WHERE 
            flight_number = IF('{}' = '', flight_number, '{}') AND
            DATE(departure_time) = IF('{}' = '', DATE(departure_time), '{}') AND
            DATE(arrival_time) = IF('{}' = '', DATE(arrival_time), '{}') AND
            airline_name = IF('{}' = '', airline_name, '{}')
        ORDER BY airline_name, flight_number
    """
    cursor.execute(query.format(
        flight_num, flight_num, 
        departure_date, departure_date, 
        arrival_date, arrival_date, 
        airline_name, airline_name
    ))
    data = cursor.fetchall()
    cursor.close()

    if data:  # Has data
        return render_template('public_home.html', statuses=data)
    else:  # No data
        error = 'Sorry ... Cannot find this flight!'
        return render_template('public_home.html', error2=error)


# ========================================= CUSTOMER =========================================
@app.route('/customer_login')
def customer_login():
	return render_template('customer_login.html')

@app.route('/customer_register')
def customer_register():
	return render_template('customer_register.html')

@app.route('/customer_login_auth', methods=['GET', 'POST'])
def customer_login_auth():
    """
    Authenticates a customer based on email and password.
    - Fetches upcoming flights for the logged-in customer.
    - Sets session and redirects to the customer home page on success.
    """
    if "email" in request.form and 'password' in request.form:
        email = request.form['email']
        db_email = escape_single_quotes(email)
        password = request.form['password']

        cursor = conn.cursor()
        query = "SELECT * FROM Customers WHERE customer_email = '{}' AND customer_password = MD5('{}')"
        cursor.execute(query.format(db_email, password))
        data = cursor.fetchone()
        cursor.close()

        if data:
            session['email'] = email
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    Tickets.ticket_id, 
                    Flights.airline_name, 
                    Flights.airplane_id, 
                    Flights.flight_number, 
                    D.city AS departure_city, 
                    Flights.departure_airport, 
                    A.city AS arrival_city, 
                    Flights.arrival_airport, 
                    Flights.departure_time, 
                    Flights.arrival_time, 
                    Flights.flight_status
                FROM 
                    Purchases 
                JOIN 
                    Tickets ON Purchases.ticket_id = Tickets.ticket_id
                JOIN 
                    Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
                JOIN 
                    Airports AS D ON Flights.departure_airport = D.airport_name
                JOIN 
                    Airports AS A ON Flights.arrival_airport = A.airport_name
                WHERE 
                    Purchases.customer_email = '{}' AND Flights.flight_status = 'upcoming'
            """
            cursor.execute(query.format(db_email))
            data1 = cursor.fetchall()
            cursor.close()

            return render_template('customer_home.html', email=email, emailName=email.split('@')[0], view_my_flights=data1)
        else:
            error = 'Invalid login or email'
            return render_template('customer_login.html', error=error)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/customer_register_auth', methods=['GET', 'POST'])
def customer_register_auth():
    """
    Registers a new customer with details such as:
    - Name, email, password, address, phone, passport details, etc.
    - Checks for existing users before inserting.
    - Logs in the customer upon successful registration.
    """
    if "email" in request.form and \
        'name' in request.form and \
        'password' in request.form and \
        'building_number' in request.form and \
        'street' in request.form and \
        'city' in request.form and \
        'state' in request.form and \
        'phone_number' in request.form and \
        'passport_number' in request.form and \
        'passport_expiration' in request.form and \
        'passport_country' in request.form and \
        'date_of_birth' in request.form:
        
        email = request.form['email']
        db_email = escape_single_quotes(email)
        name = request.form['name']
        db_name = escape_single_quotes(name)
        password = request.form['password']
        building_number = escape_single_quotes(request.form['building_number'])
        street = escape_single_quotes(request.form['street'])
        city = escape_single_quotes(request.form['city'])
        state = escape_single_quotes(request.form['state'])
        phone_number = request.form['phone_number']
        passport_number = escape_single_quotes(request.form['passport_number'])
        passport_expiration = request.form['passport_expiration']
        passport_country = escape_single_quotes(request.form['passport_country'])
        date_of_birth = request.form['date_of_birth']

        cursor = conn.cursor()

        query = "SELECT * FROM Customers WHERE customer_email = '{}'"
        cursor.execute(query.format(db_email))
        data = cursor.fetchone()

        if data:
            cursor.close()
            error = "This user already exists"
            return render_template('customer_register.html', error=error)
        else:
            ins = """
                INSERT INTO Customers (
                    customer_email, customer_name, customer_password, 
                    building_name, street, city, state, 
                    phone_number, passport_number, passport_expiration, 
                    passport_country, date_of_birth
                ) 
                VALUES ('{}', '{}', MD5('{}'), '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
            """
            cursor.execute(ins.format(
                db_email, db_name, password, 
                building_number, street, city, state, 
                phone_number, passport_number, passport_expiration, 
                passport_country, date_of_birth
            ))
            conn.commit()

            query = """
                SELECT 
                    Tickets.ticket_id, 
                    Flights.airline_name, 
                    Flights.airplane_id, 
                    Flights.flight_number, 
                    D.city AS departure_city, 
                    Flights.departure_airport, 
                    A.city AS arrival_city, 
                    Flights.arrival_airport, 
                    Flights.departure_time, 
                    Flights.arrival_time, 
                    Flights.flight_status
                FROM 
                    Purchases 
                JOIN 
                    Tickets ON Purchases.ticket_id = Tickets.ticket_id
                JOIN 
                    Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
                JOIN 
                    Airports AS D ON Flights.departure_airport = D.airport_name
                JOIN 
                    Airports AS A ON Flights.arrival_airport = A.airport_name
                WHERE 
                    Purchases.customer_email = '{}' AND Flights.flight_status = 'upcoming'
            """
            cursor.execute(query.format(db_email))
            data1 = cursor.fetchall()
            cursor.close()

            flash("You are logged in")
            session['email'] = email
            return render_template('customer_home.html', email=email, emailName=email.split('@')[0], view_my_flights=data1)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/customer_home')
def customer_home():
    """
    Displays the customer's home page, showing their upcoming flights.
    Requires an active session.
    """
    if session.get('email'):
        email = session['email']
        db_email = escape_single_quotes(email)

        cursor = conn.cursor()

        query = """
            SELECT 
                Tickets.ticket_id, 
                Flights.airline_name, 
                Flights.airplane_id, 
                Flights.flight_number, 
                D.city AS departure_city, 
                Flights.departure_airport, 
                A.city AS arrival_city, 
                Flights.arrival_airport, 
                Flights.departure_time, 
                Flights.arrival_time, 
                Flights.flight_status
            FROM 
                Purchases 
            JOIN 
                Tickets ON Purchases.ticket_id = Tickets.ticket_id
            JOIN 
                Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
            JOIN 
                Airports AS D ON Flights.departure_airport = D.airport_name
            JOIN 
                Airports AS A ON Flights.arrival_airport = A.airport_name
            WHERE 
                Purchases.customer_email = '{}' AND Flights.flight_status = 'upcoming'
        """
        cursor.execute(query.format(db_email))
        data1 = cursor.fetchall()
        cursor.close()

        return render_template('customer_home.html', email=email, emailName=email.split('@')[0], view_my_flights=data1)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/customer_purchase_search')
def customer_purchase_search():
    """
    Renders the search page for purchasing flights.
    Requires an active session.
    """
    if session.get('email'):
        email = session['email'] 
        return render_template('customer_flight_search.html', email=email, emailName=email.split('@')[0])
    else:
        session.clear()
        return render_template('error.html')

@app.route('/customer_spending', methods=['POST', 'GET'])
def customer_spending():
    if session.get('email'):
        email = session['email']
        db_email = escape_single_quotes(email)

        duration = request.form.get("duration", "365")
        
        cursor = conn.cursor()
        query = """
            SELECT SUM(f.ticket_price)
            FROM Purchases p
            JOIN Tickets t ON p.ticket_id = t.ticket_id
            JOIN Flights f ON t.airline_name = f.airline_name AND t.flight_number = f.flight_number
            WHERE p.customer_email = %s 
            AND p.purchase_date BETWEEN DATE_ADD(NOW(), INTERVAL -%s DAY) AND NOW()
        """
        cursor.execute(query, (db_email, duration))
        total_spending_data = cursor.fetchone()
        cursor.close()

        period = request.form.get("period", "6")
        
        from dateutil.relativedelta import relativedelta
        from datetime import datetime

        today = datetime.now()
        past_date = today - relativedelta(months=int(period))

        cursor = conn.cursor()
        query2 = """
            SELECT YEAR(p.purchase_date) AS year, MONTH(p.purchase_date) AS month, SUM(f.ticket_price) AS monthly_spending
            FROM Purchases p
            JOIN Tickets t ON p.ticket_id = t.ticket_id
            JOIN Flights f ON t.airline_name = f.airline_name AND t.flight_number = f.flight_number
            WHERE p.customer_email = %s AND p.purchase_date >= %s
            GROUP BY YEAR(p.purchase_date), MONTH(p.purchase_date)
        """
        cursor.execute(query2, (db_email, past_date.strftime('%Y-%m-%d')))
        monthly_spending_data = cursor.fetchall()
        cursor.close()

        months = []
        monthly_spendings = []
        for i in range(int(period)):
            current_date = past_date + relativedelta(months=i)
            year, month = current_date.year, current_date.month
            month_found = False
            for one_month in monthly_spending_data:
                if one_month[0] == year and one_month[1] == month:
                    monthly_spendings.append(int(one_month[2]))
                    month_found = True
                    break
            if not month_found:
                monthly_spendings.append(0)
            months.append(current_date.strftime("%Y-%m"))

        return render_template(
            'customer_spending.html',
            email=email,
            emailName=email.split('@')[0],
            total_spending_data=total_spending_data[0] if total_spending_data else 0,
            duration=duration,
            period=period,
            months=months,
            monthly_spendings=monthly_spendings
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/customer_flight_search', methods=['GET', 'POST'])
def customer_flight_search():
    """
    Allows customers to search for flights based on various criteria:
    - Departure city/airport, arrival city/airport, and dates.
    - Displays available flights and their ticket details.
    """
    if session.get('email'):
        email = session['email']
        db_email = escape_single_quotes(email)
        departure_city = escape_single_quotes(request.form['departure_city'])
        departure_airport = escape_single_quotes(request.form['departure_airport'])
        arrival_city = escape_single_quotes(request.form['arrival_city'])
        arrival_airport = escape_single_quotes(request.form['arrival_airport'])
        departure_date = request.form['departure_date']
        arrival_date = request.form['arrival_date']

        cursor = conn.cursor()

        query1 = """
            SELECT 
                Flights.airline_name, 
                Flights.airplane_id, 
                Flights.flight_number, 
                D.city AS departure_city, 
                Flights.departure_airport, 
                A.city AS arrival_city, 
                Flights.arrival_airport, 
                Flights.departure_time, 
                Flights.arrival_time, 
                Flights.ticket_price, 
                Flights.flight_status, 
                (Airplanes.total_seats - 
                (SELECT COUNT(*) FROM Tickets WHERE Tickets.flight_number = Flights.flight_number AND Tickets.airline_name = Flights.airline_name)) AS num_tickets_left
            FROM 
                Flights
            JOIN 
                Airports AS D ON Flights.departure_airport = D.airport_name
            JOIN 
                Airports AS A ON Flights.arrival_airport = A.airport_name
            JOIN 
                Airplanes ON Flights.airline_name = Airplanes.airline_name AND Flights.airplane_id = Airplanes.airplane_id
            WHERE 
                D.city = IF('{}' = '', D.city, '{}') AND 
                Flights.departure_airport = IF('{}' = '', Flights.departure_airport, '{}') AND 
                A.city = IF('{}' = '', A.city, '{}') AND 
                Flights.arrival_airport = IF('{}' = '', Flights.arrival_airport, '{}') AND 
                DATE(Flights.departure_time) = IF('{}' = '', DATE(Flights.departure_time), '{}') AND 
                DATE(Flights.arrival_time) = IF('{}' = '', DATE(Flights.arrival_time), '{}')
            ORDER BY 
                Flights.airline_name, Flights.flight_number
        """
        cursor.execute(query1.format(
            departure_city, departure_city, 
            departure_airport, departure_airport, 
            arrival_city, arrival_city, 
            arrival_airport, arrival_airport, 
            departure_date, departure_date, 
            arrival_date, arrival_date
        ))
        data = cursor.fetchall()
        cursor.close()

        if data:
            return render_template('customer_flight_search.html', email=email, emailName=email.split('@')[0], upcoming_flights=data)
        else:
            error = 'Sorry ... Flight does not exist!'
            return render_template('customer_flight_search.html', email=email, emailName=email.split('@')[0], error1=error)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/customer_buy_tickets', methods=['GET', 'POST'])
def customer_buy_tickets():
    if session.get('email'):
        email = session['email']
        db_email = escape_single_quotes(email)

        # Fetch airline names from the Airlines table
        cursor = conn.cursor()
        cursor.execute("SELECT airline_name FROM Airlines")
        airline_names = cursor.fetchall()
        cursor.close()

        # Get the selected airline and flight number
        selected_airline = request.args.get('airline_name')
        selected_flight = request.args.get('flight_num')

        if request.method == 'POST':
            airline_name = escape_single_quotes(request.form['airline_name'])
            flight_num = request.form['flight_num']

            # Check if there are available flights for the selected airline and flight number
            cursor = conn.cursor()
            query = """
                SELECT * 
                FROM Flights 
                INNER JOIN Airplanes ON Flights.airline_name = Airplanes.airline_name 
                                    AND Flights.airplane_id = Airplanes.airplane_id
                WHERE Flights.airline_name = '{}' 
                AND Flights.flight_number = '{}' 
                AND (Airplanes.total_seats - 
                    (SELECT COUNT(*) 
                        FROM Tickets 
                        WHERE Tickets.flight_number = Flights.flight_number 
                        AND Tickets.airline_name = Flights.airline_name)) > 0
            """
            cursor.execute(query.format(airline_name, flight_num))
            data = cursor.fetchall()
            cursor.close()

            if data:
                cursor = conn.cursor()
                query_id = """
                    SELECT ticket_id 
                    FROM Tickets 
                    ORDER BY ticket_id DESC 
                    LIMIT 1
                """
                cursor.execute(query_id)
                ticket_id_data = cursor.fetchone()
                new_ticket_id = int(ticket_id_data[0]) + 1 if ticket_id_data else 1

                # Insert the new ticket into the Tickets and Purchases tables
                ins1 = """
                    INSERT INTO Tickets (ticket_id, airline_name, flight_number) 
                    VALUES ('{}', '{}', '{}')
                """
                cursor.execute(ins1.format(new_ticket_id, airline_name, flight_num))

                ins2 = """
                    INSERT INTO Purchases (ticket_id, customer_email, booking_agent_email, purchase_date) 
                    VALUES ('{}', '{}', NULL, CURDATE())
                """
                cursor.execute(ins2.format(new_ticket_id, db_email))

                conn.commit()
                cursor.close()

                message1 = 'Ticket bought successfully!'
                return render_template('customer_flight_search.html', email=email, message1=message1, airline_names=airline_names)
            else:
                error = 'No ticket available for the selected flight.'
                return render_template('customer_flight_search.html', error2=error, email=email, emailName=email.split('@')[0], airline_names=airline_names)
        else:
            # Handle GET request (render the form with airline names)
            return render_template('customer_flight_search.html', email=email, emailName=email.split('@')[0], airline_names=airline_names, selected_airline=selected_airline, selected_flight=selected_flight)

    else:
        session.clear()
        return render_template('error.html')






# ========================================= BOOKING AGENT =========================================
@app.route('/agent_login')
def agent_login():
	return render_template('agent_login.html')

@app.route('/agent_register')
def agent_register():
	return render_template('agent_register.html')

@app.route('/agent_login_auth', methods=['GET', 'POST'])
def agent_login_auth():
    """
    Authenticate the booking agent's login credentials
    If valid, retrieve the agent's ID and associated flight bookings
    Otherwise, display an error message
    """
    if "email" in request.form and 'password' in request.form:
        email = request.form['email']
        db_email = escape_single_quotes(email)
        password = request.form['password']

        cursor = conn.cursor()
        query = """
            SELECT * 
            FROM BookingAgents 
            WHERE agent_email = '{}' AND agent_password = MD5('{}')
        """
        cursor.execute(query.format(db_email, password))
        data = cursor.fetchone()
        cursor.close()

        if data:
            cursor = conn.cursor()

            query1 = """
                SELECT booking_agent_id 
                FROM BookingAgents 
                WHERE agent_email = '{}'
            """
            cursor.execute(query1.format(db_email))
            data1 = cursor.fetchone()

            query2 = """
                SELECT 
                    Tickets.ticket_id, 
                    Flights.airline_name, 
                    Flights.flight_number, 
                    Flights.departure_time, 
                    Flights.arrival_time, 
                    D.city AS departure_city, 
                    Flights.departure_airport, 
                    A.city AS arrival_city, 
                    Flights.arrival_airport, 
                    Flights.ticket_price, 
                    Flights.flight_status
                FROM 
                    Purchases 
                JOIN 
                    Tickets ON Purchases.ticket_id = Tickets.ticket_id
                JOIN 
                    Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
                JOIN 
                    Airports AS D ON Flights.departure_airport = D.airport_name
                JOIN 
                    Airports AS A ON Flights.arrival_airport = A.airport_name
                WHERE 
                    Purchases.booking_agent_email = '{}'
            """
            cursor.execute(query2.format(db_email))
            data2 = cursor.fetchall()
            cursor.close()

            session['BA_email'] = email
            return render_template(
                'agent_home.html',
                email=email,
                emailName=email.split('@')[0],
                view_my_flights=data2,
                booking_agent_id=data1[0] if data1 else None
            )
        else:
            error = 'Invalid login or email'
            return render_template('agent_login.html', error=error)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/agent_register_auth', methods=['GET', 'POST'])
def agent_register_auth():
    """
    Handle booking agent registration
    Check if the agent already exists; if not, register and fetch their flights
    Redirect to the agent home page with success or error messages
    """
    if "email" in request.form and 'password' in request.form and 'booking_agent_id' in request.form:
        email = request.form['email']
        db_email = escape_single_quotes(email)
        password = request.form['password']
        booking_agent_id = request.form['booking_agent_id']

        cursor = conn.cursor()

        query = "SELECT * FROM BookingAgents WHERE agent_email = '{}'"
        cursor.execute(query.format(db_email))
        data = cursor.fetchone()

        if data:
            cursor.close()
            error = "This user already exists"
            return render_template('agent_register.html', error=error)
        else:
            ins = """
                INSERT INTO BookingAgents (agent_email, agent_password, booking_agent_id) 
                VALUES ('{}', MD5('{}'), '{}')
            """
            cursor.execute(ins.format(db_email, password, booking_agent_id))
            conn.commit()

            query1 = """
                SELECT booking_agent_id 
                FROM BookingAgents 
                WHERE agent_email = '{}'
            """
            cursor.execute(query1.format(db_email))
            data1 = cursor.fetchone()

            query2 = """
                SELECT 
                    Tickets.ticket_id, 
                    Flights.airline_name, 
                    Flights.flight_number, 
                    Flights.departure_time, 
                    Flights.arrival_time, 
                    D.city AS departure_city, 
                    Flights.departure_airport, 
                    A.city AS arrival_city, 
                    Flights.arrival_airport, 
                    Flights.ticket_price, 
                    Flights.flight_status
                FROM 
                    Purchases 
                JOIN 
                    Tickets ON Purchases.ticket_id = Tickets.ticket_id
                JOIN 
                    Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
                JOIN 
                    Airports AS D ON Flights.departure_airport = D.airport_name
                JOIN 
                    Airports AS A ON Flights.arrival_airport = A.airport_name
                WHERE 
                    Purchases.booking_agent_email = '{}'
            """
            cursor.execute(query2.format(db_email))
            data2 = cursor.fetchall()
            cursor.close()

            session['BA_email'] = email
            flash("You are logged in")
            return render_template(
                'agent_home.html',
                email=email,
                emailName=email.split('@')[0],
                view_my_flights=data2,
                booking_agent_id=data1[0] if data1 else None
            )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/agent_home')
def agent_home():
    """
    Display the booking agent's home page
    Retrieve the agent's ID and view their booked flights
    """
    if session.get('BA_email'):
        email = session['BA_email']
        db_email = escape_single_quotes(email)

        cursor = conn.cursor()

        query1 = """
            SELECT booking_agent_id 
            FROM BookingAgents 
            WHERE agent_email = '{}'
        """
        cursor.execute(query1.format(db_email))
        data1 = cursor.fetchone()

        query2 = """
            SELECT 
                Tickets.ticket_id, 
                Purchases.customer_email, 
                Purchases.purchase_date, 
                Flights.airline_name, 
                Flights.flight_number, 
                D.city, 
                Flights.departure_airport, 
                Flights.departure_time, 
                A.city, 
                Flights.arrival_airport, 
                Flights.arrival_time, 
                Flights.ticket_price
            FROM 
                Purchases 
            JOIN 
                Tickets ON Purchases.ticket_id = Tickets.ticket_id
            JOIN 
                Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
            JOIN 
                Airports AS D ON Flights.departure_airport = D.airport_name
            JOIN 
                Airports AS A ON Flights.arrival_airport = A.airport_name
            WHERE 
                Purchases.booking_agent_email = '{}'
        """
        cursor.execute(query2.format(db_email))
        data2 = cursor.fetchall()
        cursor.close()

        return render_template(
            'agent_home.html',
            email=email,
            emailName=email.split('@')[0],
            view_my_flights=data2,
            booking_agent_id=data1[0] if data1 else None
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/agent_purchase_search')
def agent_purchase_search():
    """
    # Render the purchase search page for agents
    # Allows agents to search for flights and manage purchases
    """
    if session.get('BA_email'):
        email = session['BA_email'] 
        return render_template('agent_purchase_search.html', email=email, emailName=email.split('@')[0], )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/agent_commission', methods=['POST', 'GET'])
def agent_commission():
    """
    Calculate and display the agent's total commission, average commission,
    and ticket sales count over a specified time period
    """
    if session.get('BA_email'):
        email = session['BA_email']
        db_email = escape_single_quotes(email)

        cursor = conn.cursor()

        duration = request.form.get("duration")
        if duration is None:
            duration = "30"

        query = """
			SELECT 
				SUM(Flights.ticket_price * 0.1) AS total_commission, 
				AVG(Flights.ticket_price * 0.1) AS average_commission, 
				COUNT(Tickets.ticket_id) AS ticket_count
			FROM 
				Purchases
			JOIN 
				Tickets ON Purchases.ticket_id = Tickets.ticket_id
			JOIN 
				Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
			WHERE 
				Purchases.booking_agent_email = '{}' 
				AND (Purchases.purchase_date BETWEEN DATE_ADD(NOW(), INTERVAL -{} DAY) AND NOW())
		"""
        cursor.execute(query.format(db_email, duration))
        commission_data = cursor.fetchone()
        cursor.close()

        total_com = commission_data[0] if commission_data[0] else 0
        avg_com = commission_data[1] if commission_data[1] else 0
        count_ticket = commission_data[2] if commission_data[2] else 0

        return render_template(
            'agent_commission.html',
            email=email,
            emailName=email.split('@')[0],
            total_com=total_com,
            avg_com=avg_com,
            count_ticket=count_ticket,
            duration=duration
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/agent_customers_ranking')
def agent_customers_ranking():
    """
    Display the top customers associated with the booking agent
    Ranked by tickets sold and total commission within specific time frames
    """
    if session.get('BA_email'):
        email = session['BA_email']
        db_email = escape_single_quotes(email)

        cursor = conn.cursor()

        query1 = """
            SELECT 
                Purchases.customer_email, 
                COUNT(Tickets.ticket_id) AS ticket_count
            FROM 
                Purchases
            JOIN 
                Tickets ON Purchases.ticket_id = Tickets.ticket_id
            WHERE 
                Purchases.booking_agent_email = '{}' 
                AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 183
            GROUP BY 
                Purchases.customer_email
            ORDER BY 
                ticket_count DESC
        """
        cursor.execute(query1.format(db_email))
        ticket_data = cursor.fetchall()
        cursor.close()

        l = len(ticket_data)
        if l >= 5:
            ppl1 = [ticket_data[i][0] for i in range(5)]
            tickets = [ticket_data[i][1] for i in range(5)]
        else:
            ppl1 = [ticket_data[i][0] for i in range(l)]
            tickets = [ticket_data[i][1] for i in range(l)]
            for _ in range(5 - l):
                ppl1.append(' ')
                tickets.append(0)

        cursor = conn.cursor()

        query2 = """
			SELECT 
				Purchases.customer_email, 
				SUM(Flights.ticket_price) * 0.1 AS total_commission
			FROM 
				Purchases
			JOIN 
				Tickets ON Purchases.ticket_id = Tickets.ticket_id
			JOIN 
				Flights ON Tickets.airline_name = Flights.airline_name AND Tickets.flight_number = Flights.flight_number
			WHERE 
				Purchases.booking_agent_email = '{}' 
				AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
			GROUP BY 
				Purchases.customer_email
			ORDER BY 
				total_commission DESC
		"""

        cursor.execute(query2.format(db_email))
        commission_data = cursor.fetchall()
        cursor.close()

        l2 = len(commission_data)
        if l2 >= 5:
            ppl2 = [commission_data[i][0] for i in range(5)]
            commissions = [int(commission_data[i][1]) for i in range(5)]
        else:
            ppl2 = [commission_data[i][0] for i in range(l2)]
            commissions = [int(commission_data[i][1]) for i in range(l2)]
            for _ in range(5 - l2):
                ppl2.append(' ')
                commissions.append(0)

        return render_template(
            'agent_customers_ranking.html',
            email=email,
            emailName=email.split('@')[0],
            ppl1=ppl1,
            ppl2=ppl2,
            tickets=tickets,
            commissions=commissions
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/agent_search_flight', methods=['GET', 'POST'])
def agent_search_flight():
    """
    Allow booking agents to search for flights based on various criteria
    Return matching flights or display an error message if no matches are found
    """
    if session.get('BA_email'):
        email = session['BA_email']
        db_email = escape_single_quotes(email)
        departure_city = escape_single_quotes(request.form['departure_city'])
        departure_airport = escape_single_quotes(request.form['departure_airport'])
        arrival_city = escape_single_quotes(request.form['arrival_city'])
        arrival_airport = escape_single_quotes(request.form['arrival_airport'])
        departure_date = request.form['departure_date']
        arrival_date = request.form['arrival_date']

        cursor = conn.cursor()
        query = """
            SELECT booking_agent_id 
            FROM BookingAgents 
            WHERE agent_email = '{}'
        """
        cursor.execute(query.format(db_email))
        agent_data = cursor.fetchone()
        cursor.close()

        if not agent_data:
            agent_id_error = 'You are not a registered booking agent'
            return render_template('agent_purchase_search.html', error1=agent_id_error)

        booking_agent_id = agent_data[0]

        cursor = conn.cursor()
        query2 = """
            SELECT 
                Flights.airplane_id, 
                Flights.flight_number, 
                D.city AS departure_city, 
                Flights.departure_airport, 
                A.city AS arrival_city, 
                Flights.arrival_airport, 
                Flights.departure_time, 
                Flights.arrival_time, 
                Flights.flight_status, 
                Flights.ticket_price, 
                Flights.airline_name, 
                (Airplanes.total_seats - 
                (SELECT COUNT(*) 
                FROM Tickets 
                WHERE Tickets.flight_number = Flights.flight_number AND Tickets.airline_name = Flights.airline_name)) AS num_tickets_left
            FROM 
                Flights
            JOIN 
                Airports AS D ON Flights.departure_airport = D.airport_name
            JOIN 
                Airports AS A ON Flights.arrival_airport = A.airport_name
            JOIN 
                Airplanes ON Flights.airline_name = Airplanes.airline_name AND Flights.airplane_id = Airplanes.airplane_id
            WHERE 
                D.city = IF('{}' = '', D.city, '{}') AND 
                Flights.departure_airport = IF('{}' = '', Flights.departure_airport, '{}') AND 
                A.city = IF('{}' = '', A.city, '{}') AND 
                Flights.arrival_airport = IF('{}' = '', Flights.arrival_airport, '{}') AND 
                DATE(Flights.departure_time) = IF('{}' = '', DATE(Flights.departure_time), '{}') AND 
                DATE(Flights.arrival_time) = IF('{}' = '', DATE(Flights.arrival_time), '{}')
            ORDER BY 
                Flights.airline_name, Flights.flight_number
        """
        cursor.execute(query2.format(
            departure_city, departure_city, 
            departure_airport, departure_airport, 
            arrival_city, arrival_city, 
            arrival_airport, arrival_airport, 
            departure_date, departure_date, 
            arrival_date, arrival_date
        ))
        data = cursor.fetchall()
        cursor.close()

        if data:
            return render_template(
                'agent_purchase_search.html',
                email=email,
                emailName=email.split('@')[0],
                upcoming_flights=data
            )
        else:
            error = 'Sorry ... Cannot find this flight!'
            return render_template(
                'agent_purchase_search.html',
                email=email,
                emailName=email.split('@')[0],
                error1=error
            )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/agent_buy_tickets', methods=['GET', 'POST'])
def agent_buy_tickets():
    """
    Handle ticket purchase by booking agents
    Validate agent's credentials, customer email, and flight availability
    Insert the new ticket and purchase records if valid, otherwise display errors
    """
    if session.get('BA_email'):
        email = session['BA_email']
        db_email = escape_single_quotes(email)
        airline_name = escape_single_quotes(request.form.get("airline_name"))
        flight_num = request.form.get("flight_num")
        customer_email = escape_single_quotes(request.form['customer_email'])

        cursor = conn.cursor()
        query = """
            SELECT booking_agent_id 
            FROM BookingAgents 
            WHERE agent_email = '{}'
        """
        cursor.execute(query.format(db_email))
        agent_data = cursor.fetchone()
        cursor.close()

        if not agent_data:
            agent_id_error = 'You are not a booking agent'
            return render_template('agent_purchase_search.html', error2=agent_id_error)

        booking_agent_id = agent_data[0]

        cursor = conn.cursor()
        query = """
            SELECT * 
            FROM Customers 
            WHERE customer_email = '{}'
        """
        cursor.execute(query.format(customer_email))
        cus_data = cursor.fetchone()
        cursor.close()

        if not cus_data:
            email_error = 'Your customer is not registered.'
            return render_template('agent_purchase_search.html', error2=email_error)

        cursor = conn.cursor()
        query = """
            SELECT Flights.*, 
                (Airplanes.total_seats - 
                    (SELECT COUNT(*) 
                    FROM Tickets 
                    WHERE Tickets.flight_number = Flights.flight_number 
                    AND Tickets.airline_name = Flights.airline_name)) AS available_seats
            FROM Flights
            JOIN Airplanes ON Flights.airline_name = Airplanes.airline_name 
                        AND Flights.airplane_id = Airplanes.airplane_id
            WHERE Flights.airline_name = '{}' 
            AND Flights.flight_number = '{}'
            HAVING available_seats > 0
        """
        cursor.execute(query.format(airline_name, flight_num))
        flight_data = cursor.fetchall()
        cursor.close()

        if not flight_data:
            ticket_error = 'No ticket available for this flight.'
            return render_template('agent_purchase_search.html', error2=ticket_error, email=email, emailName=email.split('@')[0])
        else:
            cursor = conn.cursor()
            query_id = """
                SELECT ticket_id 
                FROM Tickets 
                ORDER BY ticket_id DESC 
                LIMIT 1
            """
            cursor.execute(query_id)
            ticket_id_data = cursor.fetchone()
            new_ticket_id = int(ticket_id_data[0]) + 1 if ticket_id_data else 1

            ins1 = """
                INSERT INTO Tickets (ticket_id, airline_name, flight_number) 
                VALUES ('{}', '{}', '{}')
            """
            cursor.execute(ins1.format(new_ticket_id, airline_name, flight_num))

            ins2 = """
                INSERT INTO Purchases (ticket_id, customer_email, booking_agent_email, purchase_date) 
                VALUES ('{}', '{}', '{}', CURDATE())
            """
            cursor.execute(ins2.format(new_ticket_id, customer_email, db_email))

            conn.commit()
            cursor.close()

            message = 'Ticket bought successfully!'
            return render_template('agent_purchase_search.html', message=message, email=email, emailName=email.split('@')[0])
    else:
        session.clear()
        return render_template('error.html')


# ========================================= AIRLINE STAFF =========================================
@app.route('/staff_login')
def staff_login():
	return render_template('staff_login.html')

@app.route('/staff_register')
def staff_register():
	return render_template('staff_register.html')

@app.route('/staff_login_auth', methods=['GET', 'POST'])
def staff_login_auth():
    """
    Authenticate the airline staff's login credentials
    Fetch and display upcoming flights managed by the logged-in staff
    """
    if "username" in request.form and 'password' in request.form:
        username = request.form['username']
        db_username = escape_single_quotes(username)
        password = request.form['password']

        cursor = conn.cursor()
        query = """
            SELECT * 
            FROM AirlineStaff 
            WHERE staff_username = '{}' AND staff_password = MD5('{}')
        """
        cursor.execute(query.format(db_username, password))
        data = cursor.fetchone()

        if data:
            query1 = """
                SELECT 
                    AirlineStaff.staff_username, 
                    Flights.airline_name, 
                    Flights.airplane_id, 
                    Flights.flight_number, 
                    Flights.departure_airport, 
                    Flights.arrival_airport, 
                    Flights.departure_time, 
                    Flights.arrival_time
                FROM 
                    Flights
                JOIN 
                    AirlineStaff ON Flights.airline_name = AirlineStaff.airline_name
                WHERE 
                    AirlineStaff.staff_username = '{}' 
                    AND Flights.flight_status = 'upcoming' 
                    AND DATEDIFF(CURDATE(), DATE(Flights.departure_time)) < 30
            """
            cursor.execute(query1.format(db_username))
            data1 = cursor.fetchall()
            cursor.close()

            session['username'] = username
            return render_template('staff_home.html', username=username, posts=data1)
        else:
            cursor.close()
            error = 'Invalid login or username'
            return render_template('staff_login.html', error=error)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_register_auth', methods=['GET', 'POST'])
def staff_register_auth():
    """
    Handle airline staff registration
    Verify the airline name and ensure the username is unique
    Redirect to the home page with success or error messages
    """
    if "username" in request.form and \
       "password" in request.form and \
       "first_name" in request.form and \
       "last_name" in request.form and \
       "date_of_birth" in request.form and \
       "airline_name" in request.form:
        username = request.form['username']
        db_username = escape_single_quotes(username)
        password = request.form['password']
        first_name = request.form['first_name']
        db_first_name = escape_single_quotes(first_name)
        last_name = request.form['last_name']
        db_last_name = escape_single_quotes(last_name)
        date_of_birth = request.form['date_of_birth']
        airline_name = escape_single_quotes(request.form['airline_name'])

        cursor = conn.cursor()

        query = """
            SELECT * 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(query.format(db_username))
        data = cursor.fetchone()
        if data:
            cursor.close()
            error = "This user already exists"
            return render_template('staff_register.html', error=error)

        query = """
            SELECT airline_name 
            FROM Airlines 
            WHERE airline_name = '{}'
        """
        cursor.execute(query.format(airline_name))
        data = cursor.fetchone()

        if data:
            ins = """
                INSERT INTO AirlineStaff (staff_username, staff_password, first_name, last_name, date_of_birth, airline_name) 
                VALUES ('{}', '{}', '{}', '{}', '{}', '{}')
            """
            cursor.execute(ins.format(db_username, password, db_first_name, db_last_name, date_of_birth, airline_name))
            conn.commit()

            query1 = """
                SELECT 
                    AirlineStaff.staff_username, 
                    Flights.airline_name, 
                    Flights.airplane_id, 
                    Flights.flight_number, 
                    Flights.departure_airport, 
                    Flights.arrival_airport, 
                    Flights.departure_time, 
                    Flights.arrival_time
                FROM 
                    Flights
                JOIN 
                    AirlineStaff ON Flights.airline_name = AirlineStaff.airline_name
                WHERE 
                    AirlineStaff.staff_username = '{}' 
                    AND Flights.flight_status = 'upcoming' 
                    AND DATEDIFF(DATE(Flights.departure_time), CURDATE()) < 30
            """
            cursor.execute(query1.format(db_username))
            data1 = cursor.fetchall()
            cursor.close()

            flash("You are logged in")
            session['username'] = username
            return render_template('staff_home.html', username=username, posts=data1)
        else:
            cursor.close()
            error = "This airline doesn't exist"
            return render_template('staff_register.html', error=error)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_home')
def staff_home():
    """
    Display the home page for logged-in airline staff
    Fetch upcoming flights associated with the staff's airline
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        query = """
            SELECT 
                AirlineStaff.staff_username, 
                Flights.airline_name, 
                Flights.airplane_id, 
                Flights.flight_number, 
                Flights.departure_airport, 
                Flights.arrival_airport, 
                Flights.departure_time, 
                Flights.arrival_time
            FROM 
                Flights
            JOIN 
                AirlineStaff ON Flights.airline_name = AirlineStaff.airline_name
            WHERE 
                AirlineStaff.staff_username = '{}' 
                AND Flights.flight_status = 'upcoming' 
                AND DATEDIFF(CURDATE(), DATE(Flights.departure_time)) < 30
        """
        cursor.execute(query.format(db_username))
        data1 = cursor.fetchall()
        cursor.close()

        return render_template('staff_home.html', username=username, posts=data1)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_search_flight', methods=['GET', 'POST'])
def staff_search_flight():
    """
    Allow staff to search for flights by departure/arrival details and date
    Return flight data or display an error if no flights match the criteria
    """
    if session.get('username'):
        departure_city = escape_single_quotes(request.form['departure_city'])
        departure_airport = escape_single_quotes(request.form['departure_airport'])
        arrival_city = escape_single_quotes(request.form['arrival_city'])
        arrival_airport = escape_single_quotes(request.form['arrival_airport'])
        departure_date = request.form['departure_date']
        arrival_date = request.form['arrival_date']
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        query = """
            SELECT 
                Flights.airline_name, 
                Flights.airplane_id, 
                Flights.flight_number, 
                D.city AS departure_city, 
                Flights.departure_airport, 
                A.city AS arrival_city, 
                Flights.arrival_airport, 
                Flights.departure_time, 
                Flights.arrival_time, 
                Flights.flight_status, 
                Flights.ticket_price
            FROM 
                Flights
            JOIN 
                Airports AS D ON Flights.departure_airport = D.airport_name
            JOIN 
                Airports AS A ON Flights.arrival_airport = A.airport_name
            JOIN 
                AirlineStaff ON Flights.airline_name = AirlineStaff.airline_name
            WHERE 
                D.city = IF('{}' = '', D.city, '{}') AND 
                Flights.departure_airport = IF('{}' = '', Flights.departure_airport, '{}') AND 
                A.city = IF('{}' = '', A.city, '{}') AND 
                Flights.arrival_airport = IF('{}' = '', Flights.arrival_airport, '{}') AND 
                DATE(Flights.departure_time) = IF('{}' = '', DATE(Flights.departure_time), '{}') AND 
                DATE(Flights.arrival_time) = IF('{}' = '', DATE(Flights.arrival_time), '{}') AND 
                AirlineStaff.staff_username = '{}'
            ORDER BY 
                Flights.airline_name, Flights.flight_number
        """
        cursor.execute(query.format(
            departure_city, departure_city, 
            departure_airport, departure_airport, 
            arrival_city, arrival_city, 
            arrival_airport, arrival_airport, 
            departure_date, departure_date, 
            arrival_date, arrival_date, 
            db_username
        ))
        data = cursor.fetchall()

        query_staff = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(query_staff.format(db_username))
        data1 = cursor.fetchall()
        cursor.close()

        if data:
            return render_template(
                'staff_flight_info.html', 
                username=username, 
                upcoming_flights=data, 
                posts=data1
            )
        else:
            error = 'Sorry ... Cannot find this flight!'
            return render_template(
                'staff_flight_info.html', 
                username=username, 
                error1=error, 
                posts=data1
            )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_flight')
def staff_flight():
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(query.format(db_username))
        data1 = cursor.fetchall()
        cursor.close()

        return render_template('staff_flight_info.html', username=username, posts=data1)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_insert_data')
def staff_insert_data():
    """
    Render a form for staff to add flight or airplane information
    Include existing airplane details for reference
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)
        cursor = conn.cursor()

        query_staff = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(query_staff.format(db_username))
        data2 = cursor.fetchall()

        query_airplane = """
            SELECT Airplanes.airplane_id, Airplanes.total_seats 
            FROM Airplanes
            JOIN AirlineStaff ON Airplanes.airline_name = AirlineStaff.airline_name
            WHERE AirlineStaff.staff_username = '{}'
        """
        cursor.execute(query_airplane.format(db_username))
        data1 = cursor.fetchall()
        cursor.close()

        return render_template(
            'staff_insert_data.html', 
            username=username, 
            airplane=data1, 
            posts=data2
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/change_status_flight', methods=['GET', 'POST'])
def change_status_flight():
    # Allow staff to update the status of a specific flight
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)
        status = request.form['change_status_flight']
        flight_number = request.form['flight_num']

        cursor = conn.cursor()

        upd = """
            UPDATE Flights 
            SET flight_status = '{}' 
            WHERE flight_number = '{}'
        """
        cursor.execute(upd.format(status, flight_number))
        conn.commit()

        query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(query.format(db_username))
        data1 = cursor.fetchall()
        cursor.close()

        message = 'Status changed successfully!'
        return render_template(
            'staff_flight_info.html', 
            username=username, 
            message=message, 
            posts=data1
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/add_flight', methods=['GET', 'POST'])
def add_flight():
    """
    Allow staff to add a new flight
    Validate input such as departure/arrival airports, airplane availability, and seat limits
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        flight_number = request.form['flight_num']
        departure_airport = escape_single_quotes(request.form['departure_airport'])
        departure_date = request.form['departure_date']
        departure_time = request.form['departure_time']
        arrival_airport = escape_single_quotes(request.form['arrival_airport'])
        arrival_date = request.form['arrival_date']
        arrival_time = request.form['arrival_time']
        price = request.form['price']
        number = request.form['number']
        status = request.form['status']
        airplane_id = request.form['airplane_id']

        cursor = conn.cursor()

        airline_query = """
            SELECT airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(airline_query.format(db_username))
        airline_name = cursor.fetchone()
        if not airline_name:
            cursor.close()
            return render_template('staff_insert_data.html', error1="Invalid airline staff", username=username)
        airline_name = airline_name[0]

        airport_query = """
            SELECT airport_name 
            FROM Airports 
            WHERE airport_name = '{}'
        """
        cursor.execute(airport_query.format(departure_airport))
        if not cursor.fetchone():
            cursor.close()
            return render_template('staff_insert_data.html', error1="Departure airport doesn't exist", username=username)

        cursor.execute(airport_query.format(arrival_airport))
        if not cursor.fetchone():
            cursor.close()
            return render_template('staff_insert_data.html', error1="Arrival airport doesn't exist", username=username)

        airplane_query = """
            SELECT airplane_id 
            FROM Airplanes 
            WHERE airline_name = '{}' AND airplane_id = '{}'
        """
        cursor.execute(airplane_query.format(airline_name, airplane_id))
        if not cursor.fetchone():
            cursor.close()
            return render_template('staff_insert_data.html', error1="Airplane doesn't exist", username=username)

        seat_query = """
            SELECT total_seats 
            FROM Airplanes 
            WHERE airline_name = '{}' AND airplane_id = '{}'
        """
        cursor.execute(seat_query.format(airline_name, airplane_id))
        airplane_info = cursor.fetchone()
        if airplane_info:
            total_seats = airplane_info[0]
            if int(number) > int(total_seats):
                cursor.close()
                return render_template('staff_insert_data.html', error1="Not enough seats on the airplane", username=username)
        else:
            cursor.close()
            return render_template('staff_insert_data.html', error1="Error retrieving seat information", username=username)

        flight_query = """
            SELECT flight_number 
            FROM Flights 
            WHERE airline_name = '{}' AND flight_number = '{}'
        """
        cursor.execute(flight_query.format(airline_name, flight_number))
        if cursor.fetchone():
            cursor.close()
            return render_template('staff_insert_data.html', error1="This flight already exists", username=username)

        insert_query = """
            INSERT INTO Flights (airline_name, flight_number, departure_airport, departure_time, 
                                 arrival_airport, arrival_time, ticket_price, flight_status, airplane_id)
            VALUES ('{}', '{}', '{}', '{} {}', '{}', '{} {}', '{}', '{}', '{}')
        """
        cursor.execute(insert_query.format(
            airline_name, flight_number, departure_airport, departure_date, departure_time,
            arrival_airport, arrival_date, arrival_time, price, status, airplane_id
        ))
        conn.commit()

        airplane_details_query = """
            SELECT airplane_id, total_seats 
            FROM Airplanes 
            WHERE airline_name = '{}'
        """
        cursor.execute(airplane_details_query.format(airline_name))
        airplanes = cursor.fetchall()
        cursor.close()

        message1 = "New flight added successfully!"
        return render_template('staff_insert_data.html', message1=message1, username=username, airplane=airplanes)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/insert_airplane', methods=['GET', 'POST'])
def insert_airplane():
    """
    Allow staff to add a new airplane to the airline's fleet
    Ensure the airplane ID is unique within the airline
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        airplane_id = request.form['airplane_id']
        seats = request.form['seats']

        cursor = conn.cursor()

        airline_query = """
            SELECT airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(airline_query.format(db_username))
        airline_name = cursor.fetchone()
        if not airline_name:
            cursor.close()
            return render_template('staff_insert_data.html', error2="Invalid airline staff", username=username)
        airline_name = airline_name[0]

        airplane_check_query = """
            SELECT airline_name, airplane_id 
            FROM Airplanes 
            WHERE airline_name = '{}' AND airplane_id = '{}'
        """
        cursor.execute(airplane_check_query.format(airline_name, airplane_id))
        if cursor.fetchone():
            cursor.close()
            error2 = "This airplane already exists"
            return render_template('staff_insert_data.html', error2=error2, username=username)

        insert_query = """
            INSERT INTO Airplanes (airline_name, airplane_id, total_seats) 
            VALUES ('{}', '{}', '{}')
        """
        cursor.execute(insert_query.format(airline_name, airplane_id, seats))
        conn.commit()

        airplane_details_query = """
            SELECT airplane_id, total_seats 
            FROM Airplanes 
            WHERE airline_name = '{}'
        """
        cursor.execute(airplane_details_query.format(airline_name))
        airplanes = cursor.fetchall()
        cursor.close()

        message2 = "New airplane added successfully!"
        return render_template('staff_insert_data.html', message2=message2, username=username, airplane=airplanes)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/insert_airport', methods=['GET', 'POST'])
def insert_airport():
    """
    Allow staff to add a new airport
    Verify the airport name is unique before adding
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)
        airport_name = escape_single_quotes(request.form['airport_name'])
        airport_city = escape_single_quotes(request.form['airport_city'])

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        staff_details = cursor.fetchall()

        airport_check_query = """
            SELECT airport_name 
            FROM Airports 
            WHERE airport_name = '{}'
        """
        cursor.execute(airport_check_query.format(airport_name))
        airport_exists = cursor.fetchone()

        airplane_query = """
            SELECT airplane_id, total_seats 
            FROM Airplanes 
            JOIN AirlineStaff ON Airplanes.airline_name = AirlineStaff.airline_name
            WHERE AirlineStaff.staff_username = '{}'
        """
        cursor.execute(airplane_query.format(db_username))
        airplane_details = cursor.fetchall()

        cursor.close()

        if airport_exists:
            error3 = "This airport already exists"
            return render_template(
                'staff_insert_data.html', 
                error3=error3, 
                username=username, 
                airplane=airplane_details, 
                posts=staff_details
            )

        cursor = conn.cursor()
        insert_airport_query = """
            INSERT INTO Airports (airport_name, city) 
            VALUES ('{}', '{}')
        """
        cursor.execute(insert_airport_query.format(airport_name, airport_city))
        conn.commit()
        cursor.close()

        message3 = "New airport added successfully!"
        return render_template(
            'staff_insert_data.html', 
            message3=message3, 
            username=username, 
            airplane=airplane_details, 
            posts=staff_details
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_agent')
def staff_agent():
    """
    Display booking agents ranked by commission earned and tickets sold
    Include details for both monthly and yearly performance
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        adata = cursor.fetchall()

        commission_query = """
            SELECT BookingAgents.agent_email, BookingAgents.booking_agent_id, SUM(Flights.ticket_price) * 0.1 AS commission 
            FROM BookingAgents 
            NATURAL JOIN Purchases 
            NATURAL JOIN Tickets AS T
            JOIN Flights ON T.airline_name = Flights.airline_name AND T.flight_number = Flights.flight_number
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE AirlineStaff.staff_username = '{}' 
            AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY BookingAgents.agent_email, BookingAgents.booking_agent_id 
            ORDER BY commission DESC 
            LIMIT 5
        """
        cursor.execute(commission_query.format(db_username))
        data1 = cursor.fetchall()

        month_query = """
            SELECT BookingAgents.agent_email, BookingAgents.booking_agent_id, COUNT(T.ticket_id) AS ticket_count 
            FROM BookingAgents 
            NATURAL JOIN Purchases 
            NATURAL JOIN Tickets AS T
            JOIN Flights ON T.airline_name = Flights.airline_name AND T.flight_number = Flights.flight_number
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE AirlineStaff.staff_username = '{}' 
            AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 30
            GROUP BY BookingAgents.agent_email, BookingAgents.booking_agent_id 
            ORDER BY ticket_count DESC 
            LIMIT 5
        """
        cursor.execute(month_query.format(db_username))
        data2 = cursor.fetchall()

        year_query = """
            SELECT BookingAgents.agent_email, BookingAgents.booking_agent_id, COUNT(T.ticket_id) AS ticket_count 
            FROM BookingAgents 
            NATURAL JOIN Purchases 
            NATURAL JOIN Tickets AS T
            JOIN Flights ON T.airline_name = Flights.airline_name AND T.flight_number = Flights.flight_number
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE AirlineStaff.staff_username = '{}' 
            AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY BookingAgents.agent_email, BookingAgents.booking_agent_id 
            ORDER BY ticket_count DESC 
            LIMIT 5
        """
        cursor.execute(year_query.format(db_username))
        data3 = cursor.fetchall()

        all_agents_query = """
            SELECT agent_email, booking_agent_id 
            FROM BookingAgents
        """
        cursor.execute(all_agents_query)
        data = cursor.fetchall()

        cursor.close()

        return render_template(
            'staff_agent.html', 
            username=username, 
            commission=data1, 
            month=data2, 
            year=data3, 
            posts=data, 
            adata=adata
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_customer')
def staff_customer():
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        data2 = cursor.fetchall()

        frequent_customer_query = """
            SELECT 
                Customers.customer_email, 
                Customers.customer_name, 
                COUNT(Tickets.ticket_id) AS ticket_count
            FROM 
                Customers
            JOIN Purchases ON Customers.customer_email = Purchases.customer_email
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE 
                AirlineStaff.staff_username = '{}' 
                AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY 
                Customers.customer_email, Customers.customer_name
            ORDER BY 
                ticket_count DESC 
            LIMIT 1
        """
        cursor.execute(frequent_customer_query.format(db_username))
        data1 = cursor.fetchall()
        cursor.close()

        return render_template(
            'staff_customer.html', 
            frequent=data1, 
            username=username, 
            cdata=data2
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_customer_flight', methods=['GET', 'POST'])
def staff_customer_flight():
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        # Initialize variables
        cusflight = None
        flightcus = None
        error = None
        error3 = None

        cursor = conn.cursor()

        # Query to fetch airline staff details
        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        cdata = cursor.fetchall()

        # Handle customer email search
        if 'customer_email' in request.form:
            email = request.form['customer_email']
            db_email = escape_single_quotes(email)

            customer_flight_query = """
                SELECT DISTINCT 
                    Flights.airplane_id, 
                    Flights.flight_number, 
                    Flights.departure_airport, 
                    Flights.arrival_airport, 
                    Flights.departure_time, 
                    Flights.arrival_time, 
                    Flights.flight_status 
                FROM 
                    Customers
                JOIN Purchases ON Customers.customer_email = Purchases.customer_email
                NATURAL JOIN Tickets 
                NATURAL JOIN Flights 
                JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
                WHERE 
                    Customers.customer_email = '{}' 
                    AND AirlineStaff.staff_username = '{}'
            """
            cursor.execute(customer_flight_query.format(db_email, db_username))
            cusflight = cursor.fetchall()

            if not cusflight:
                # Check if the customer exists
                customer_exists_query = """
                    SELECT customer_email 
                    FROM Customers 
                    WHERE customer_email = '{}'
                """
                cursor.execute(customer_exists_query.format(db_email))
                customer_exists = cursor.fetchone()

                if customer_exists:
                    error = "Customer did not take any flight"
                else:
                    error = "No such customer"

        # Handle flight number search
        if 'flight_num' in request.form:
            flight_num = request.form['flight_num']
            db_flight_num = escape_single_quotes(flight_num)

            flight_customer_query = """
                SELECT DISTINCT 
                    Customers.customer_email, 
                    Customers.customer_name
                FROM 
                    Customers
                JOIN Purchases ON Customers.customer_email = Purchases.customer_email
                NATURAL JOIN Tickets 
                NATURAL JOIN Flights 
                JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
                WHERE 
                    Flights.flight_number = '{}' 
                    AND AirlineStaff.staff_username = '{}'
            """
            cursor.execute(flight_customer_query.format(db_flight_num, db_username))
            flightcus = cursor.fetchall()

            if not flightcus:
                error3 = "No customers found for this flight number"

        # Query to find the most frequent customer
        frequent_customer_query = """
            SELECT 
                Customers.customer_email, 
                Customers.customer_name, 
                COUNT(Tickets.ticket_id) AS ticket_count 
            FROM 
                Customers
            JOIN Purchases ON Customers.customer_email = Purchases.customer_email
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE 
                AirlineStaff.staff_username = '{}' 
                AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY 
                Customers.customer_email, Customers.customer_name
            ORDER BY 
                ticket_count DESC 
            LIMIT 1
        """
        cursor.execute(frequent_customer_query.format(db_username))
        frequent = cursor.fetchall()

        cursor.close()

        # Render the results
        return render_template(
            'staff_customer.html',
            cusflight=cusflight,
            flightcus=flightcus,
            frequent=frequent,
            username=username,
            cdata=cdata,
            error=error,
            error3=error3
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_flight_customer', methods=['GET', 'POST'])
def staff_flight_customer():
    """
    Fetch and display all flights taken by a specific customer
    Show an error if the customer does not exist or has no flights
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)
        flight_number = request.form['flight_num']

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        cdata = cursor.fetchall()

        flight_customer_query = """
            SELECT DISTINCT 
                Customers.customer_email, 
                Customers.customer_name 
            FROM 
                Customers
            JOIN Purchases ON Customers.customer_email = Purchases.customer_email
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE 
                Flights.flight_number = '{}' 
                AND AirlineStaff.staff_username = '{}'
        """
        cursor.execute(flight_customer_query.format(flight_number, db_username))
        data3 = cursor.fetchall()

        frequent_customer_query = """
            SELECT 
                Customers.customer_email, 
                Customers.customer_name, 
                COUNT(Tickets.ticket_id) AS ticket_count 
            FROM 
                Customers
            JOIN Purchases ON Customers.customer_email = Purchases.customer_email
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE 
                AirlineStaff.staff_username = '{}' 
                AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY 
                Customers.customer_email, Customers.customer_name
            ORDER BY 
                ticket_count DESC 
            LIMIT 1
        """
        cursor.execute(frequent_customer_query.format(db_username))
        data1 = cursor.fetchall()

        cursor.close()

        error3 = None
        if data3:
            return render_template(
                'staff_customer.html', 
                flightcus=data3, 
                frequent=data1, 
                username=username, 
                cdata=cdata
            )
        else:
            cursor = conn.cursor()
            flight_exists_query = """
                SELECT flight_number 
                FROM Flights 
                NATURAL JOIN AirlineStaff 
                WHERE flight_number = '{}' 
                  AND AirlineStaff.staff_username = '{}'
            """
            cursor.execute(flight_exists_query.format(flight_number, db_username))
            flight_exists = cursor.fetchone()
            cursor.close()

            if flight_exists:
                error3 = "Flight has no customers"
            else:
                error3 = "No such flight"

            return render_template(
                'staff_customer.html', 
                error3=error3, 
                frequent=data1, 
                username=username, 
                cdata=cdata
            )
    else:
        session.clear()
        return render_template('error.html')
	
@app.route('/staff_destination')
def staff_destination():
    """
    Display top destination cities for the airline based on ticket sales
    Show data for the past 3 months and the past year
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        data1 = cursor.fetchall()

        month_query = """
            SELECT 
                Airports.city AS airport_city, 
                COUNT(Tickets.ticket_id) AS ticket_count 
            FROM 
                Purchases 
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN Airports ON Airports.airport_name = Flights.arrival_airport
            WHERE 
                DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 90
            GROUP BY 
                Airports.city
            ORDER BY 
                ticket_count DESC
            LIMIT 3
        """
        cursor.execute(month_query)
        month = cursor.fetchall()

        year_query = """
            SELECT 
                Airports.city AS airport_city, 
                COUNT(Tickets.ticket_id) AS ticket_count 
            FROM 
                Purchases 
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN Airports ON Airports.airport_name = Flights.arrival_airport
            WHERE 
                DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY 
                Airports.city
            ORDER BY 
                ticket_count DESC
            LIMIT 3
        """
        cursor.execute(year_query)
        year = cursor.fetchall()

        cursor.close()

        return render_template(
            'staff_destintation.html', 
            month=month, 
            year=year, 
            username=username, 
            posts=data1
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_revenue')
def staff_revenue():
    """
    Display the airline's revenue for direct and indirect bookings
    Include monthly and yearly revenue breakdowns
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        data2 = cursor.fetchall()

        monthly_direct_query = """
            SELECT SUM(Flights.ticket_price) 
            FROM Purchases 
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE AirlineStaff.staff_username = '{}' 
              AND Purchases.booking_agent_id IS NULL 
              AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 30
            GROUP BY AirlineStaff.airline_name
        """
        cursor.execute(monthly_direct_query.format(db_username))
        mdirect = cursor.fetchone()
        mdirect = [int(mdirect[0])] if mdirect else [0]

        monthly_indirect_query = """
            SELECT SUM(Flights.ticket_price) 
            FROM Purchases 
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE AirlineStaff.staff_username = '{}' 
              AND Purchases.booking_agent_id IS NOT NULL 
              AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 30
            GROUP BY AirlineStaff.airline_name
        """
        cursor.execute(monthly_indirect_query.format(db_username))
        mindirect = cursor.fetchone()
        mindirect = [int(mindirect[0])] if mindirect else [0]

        yearly_direct_query = """
            SELECT SUM(Flights.ticket_price) 
            FROM Purchases 
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE AirlineStaff.staff_username = '{}' 
              AND Purchases.booking_agent_id IS NULL 
              AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY AirlineStaff.airline_name
        """
        cursor.execute(yearly_direct_query.format(db_username))
        ydirect = cursor.fetchone()
        ydirect = [int(ydirect[0])] if ydirect else [0]

        yearly_indirect_query = """
            SELECT SUM(Flights.ticket_price) 
            FROM Purchases 
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE AirlineStaff.staff_username = '{}' 
              AND Purchases.booking_agent_id IS NOT NULL 
              AND DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365
            GROUP BY AirlineStaff.airline_name
        """
        cursor.execute(yearly_indirect_query.format(db_username))
        yindirect = cursor.fetchone()
        yindirect = [int(yindirect[0])] if yindirect else [0]

        cursor.close()

        return render_template(
            'staff_revenue.html', 
            username=username, 
            mdirect=mdirect, 
            mindirect=mindirect, 
            ydirect=ydirect, 
            yindirect=yindirect, 
            posts=data2
        )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_tickets')
def staff_tickets():
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        data2 = cursor.fetchall()

        cursor.close()

        return render_template('staff_tickets.html', username=username, posts=data2)
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_fix_ticket', methods=['GET', 'POST'])
def staff_fix_ticket():
    # Show ticket sales trends for the past month or year
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)
        duration = request.form.get("duration")
        fallticket = None

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        data2 = cursor.fetchall()

        if duration == 'tmonth':
            ticket_query = """
                SELECT 
                    YEAR(Purchases.purchase_date) AS year, 
                    MONTH(Purchases.purchase_date) AS month, 
                    COUNT(Tickets.ticket_id) AS ticket_count
                FROM 
                    Purchases 
                NATURAL JOIN Tickets 
                NATURAL JOIN Flights 
                JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
                WHERE 
                    DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 30 
                    AND AirlineStaff.staff_username = '{}'
                GROUP BY 
                    year, month
                ORDER BY 
                    year, month
            """
            cursor.execute(ticket_query.format(db_username))
            fallticket = cursor.fetchall()

        elif duration == 'tyear':
            ticket_query = """
                SELECT 
                    YEAR(Purchases.purchase_date) AS year, 
                    MONTH(Purchases.purchase_date) AS month, 
                    COUNT(Tickets.ticket_id) AS ticket_count
                FROM 
                    Purchases 
                NATURAL JOIN Tickets 
                NATURAL JOIN Flights 
                JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
                WHERE 
                    DATEDIFF(CURDATE(), DATE(Purchases.purchase_date)) < 365 
                    AND AirlineStaff.staff_username = '{}'
                GROUP BY 
                    year, month
                ORDER BY 
                    year, month
            """
            cursor.execute(ticket_query.format(db_username))
            fallticket = cursor.fetchall()

        cursor.close()

        if fallticket:
            fs = f"{fallticket[0][0]}-{fallticket[0][1]}"
            fe = f"{fallticket[-1][0]}-{fallticket[-1][1]}"
            ftime = [f"{row[0]}-{row[1]}" for row in fallticket]
            fmonthticket = [row[2] for row in fallticket]
            ftotal = sum(fmonthticket)

            return render_template(
                'staff_tickets.html', 
                fs=fs, 
                fe=fe, 
                ft=ftotal, 
                ftime=ftime, 
                fmonthticket=fmonthticket, 
                fticket=fallticket, 
                username=username, 
                posts=data2
            )
        else:
            ferror = "No tickets sold!"
            return render_template(
                'staff_tickets.html', 
                ferror=ferror, 
                username=username, 
                posts=data2
            )
    else:
        session.clear()
        return render_template('error.html')

@app.route('/staff_ticket', methods=['GET', 'POST'])
def staff_ticket():
    """
    Fetch and display ticket sales for a custom date range
    Summarize data by month and show the total tickets sold
    """
    if session.get('username'):
        username = session['username']
        db_username = escape_single_quotes(username)
        start = request.form['start']
        end = request.form['end']

        cursor = conn.cursor()

        staff_query = """
            SELECT staff_username, airline_name 
            FROM AirlineStaff 
            WHERE staff_username = '{}'
        """
        cursor.execute(staff_query.format(db_username))
        data2 = cursor.fetchall()

        ticket_query = """
            SELECT 
                YEAR(Purchases.purchase_date) AS year, 
                MONTH(Purchases.purchase_date) AS month, 
                COUNT(Tickets.ticket_id) AS ticket_count
            FROM 
                Purchases 
            NATURAL JOIN Tickets 
            NATURAL JOIN Flights 
            JOIN AirlineStaff ON AirlineStaff.airline_name = Flights.airline_name
            WHERE 
                Purchases.purchase_date > '{}' 
                AND Purchases.purchase_date < '{}' 
                AND AirlineStaff.staff_username = '{}'
            GROUP BY 
                year, month
            ORDER BY 
                year, month
        """
        cursor.execute(ticket_query.format(start, end, db_username))
        allticket = cursor.fetchall()

        cursor.close()

        if allticket:
            s = f"{allticket[0][0]}-{allticket[0][1]}"
            e = f"{allticket[-1][0]}-{allticket[-1][1]}"
            time = [f"{row[0]}-{row[1]}" for row in allticket]
            monthticket = [row[2] for row in allticket]
            total = sum(monthticket)

            return render_template(
                'staff_tickets.html', 
                s=s, 
                e=e, 
                t=total, 
                time=time, 
                monthticket=monthticket, 
                ticket=allticket, 
                username=username, 
                posts=data2
            )
        else:
            error = "No tickets sold in the specified period"
            return render_template(
                'staff_tickets.html', 
                error=error, 
                username=username, 
                posts=data2
            )
    else:
        session.clear()
        return render_template('error.html')


@app.route('/logout')
def logout():
	session.clear()
	return redirect('/customer_login')


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
