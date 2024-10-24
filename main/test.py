import qrcode
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import smtplib
import io
import os
from datetime import datetime
import mysql.connector
from mysql.connector import Error

try:
    # Establish a connection
    connection = mysql.connector.connect(
        host='',        # Replace with your host, e.g., 'localhost'
        database='',  # Replace with your database name
        user='',      # Replace with your username
        password=''    # Replace with your password
    )


except Error as e:
    print(f"Error: {e}")
    exit(0)

cursor = connection.cursor()
sql_query = '''SELECT * FROM attendees
ORDER BY UID ASC;
'''
cursor.execute(sql_query)
data_list = cursor.fetchall()



class EmailSender:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
            
    def generate_qr_code(self, data):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to bytes buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        return img_buffer.getvalue()

    def send_email(self, recipient_email, qr_data, subject, body_text, attachment_filename):
        # Create the email message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient_email

        # Add text body
        text_part = MIMEText(body_text, 'plain')
        msg.attach(text_part)

        # Generate and attach QR code
        qr_image = self.generate_qr_code(qr_data)
        image_part = MIMEImage(qr_image)
        image_part.add_header('Content-ID', '<qr_code>')
        msg.attach(image_part)
        image_part.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
        msg.attach(image_part)

        # Send the email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email to {recipient_email}: {str(e)}")
            return False


def main():

    # Email configuration
    SMTP_SERVER = "smtp.gmail.com"  # Change as needed
    SMTP_PORT = 587
    SENDER_EMAIL = ""  # Replace with your email
    SENDER_PASSWORD = ""  # Replace with your app password
    
    # Initialize email sender
    email_sender = EmailSender(SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD)


    os.chdir(r"C:\Users\lenovo\OneDrive\Desktop\qrcode_mail\main")

    log_filename = f"logs/email_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    successful_sends = 0
    failed_sends = 0

    with open(log_filename, 'w') as log_file:
        for data in data_list:
            print(f"{data[0]} => {data[1]} {data[2]}")

            # Email content
            subject = "Techvaganza Entry Pass - See You There! <3"
            body_template = f"""Congratulations! You have successfully registered for Techvaganza 2024.


User ID: {data[0]}

User Name: {data[1]} {data[2]}


Note:

Your QR code has been sent below. Please keep this QR code with you for verification purposes

Rules:

1. Gates will close at 3:00 PM. No one will be allowed to enter after this time.
2. Please carry your Student ID card or Government ID card for verification.
3. You can register for the events later upon arriving on campus, but make sure you are registered as an attendee atleast.

Events you've registered for:\n"""
            cursor.execute(f"SELECT EventID FROM participating WHERE UserID = {data[0]}")
            user_data = cursor.fetchall()

            if not (user_data):
                pass
            else:
                for (i, EventID) in enumerate(user_data):
                    print(i, EventID[0])
                    cursor.execute(f"SELECT EventName from events Where EventID ={EventID[0]}")
                    event_name = cursor.fetchone()

                    body_template += f"\t {i+1}. : {event_name[0]} \n"

            

            success = email_sender.send_email(data[3], data[0], subject, body_template, f"QR : {data[1] + data[2]})")
            
            if success:
                successful_sends += 1
                log_file.write(f"Successfully sent to: {data[3]}, {data[1] + data[2]}\n")
            else:
                failed_sends += 1
                log_file.write(f"Failed to send to: {data[3]}, {data[1] + data[2]}\n")



    # Print summary
    print(f"Email sending completed.")
    print(f"Successful sends: {successful_sends}")
    print(f"Failed sends: {failed_sends}")
    print(f"Log file created at: {log_filename}")



if __name__ == "__main__":
    main()