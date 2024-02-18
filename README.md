# Concert Tickets

This project contains a Python Django web app for creating and managing digital concert tickets. It was built for an orchestra based in Heidelberg, Germany, hence the German texts throughout the app. It provides the following functionality:
- Order form for tickets
- PDF invoice and ticket generation (with QR codes)
- Dashboard with information on sold tickets
- Ability to delete orders until X days before the concert
- Track payments via upload of bank account statement
- Send payment reminders
- Admin view to easily manage events, orders and tickets

In order to set this app up for your own orchestra, you will need to do the following:
- Adapt ct/constants.py to your needs.
- Adapt ct/settings.py to your needs.
- Look through all texts in logic/invoice, logic/tickets and logic/order and adapt them to your needs.
- Create a virtual Python environment and install `pip install -r requirements.txt`.
- Run `python manage.py migrate` to create a local sqlite database for testing.
- Test the app locally.
- Create a Django superuser: Open a terminal on your server. `python manage.py createsuperuser`
- Go to the admin view. <your_url>/admin. Login. Create Event objects for your concerts. Try out the ticket ordering process by opening <your_url>.
-  Deploy the app. We deployed the app on an AWS Lightsail instance, which worked well for us. A step-by-step setup can be found in AWS_SETUP. 
- If you want to scan the tickets at the concert, you will need the Android App at dariusfi/concert-scan. You will also need an additional user, which you can create via the Admin view.
